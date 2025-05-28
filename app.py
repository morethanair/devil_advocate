import streamlit as st
import google.generativeai as genai
import json
import random
import os
import time
from dotenv import load_dotenv
from datetime import datetime

# --- 초기 설정 ---

# 환경 변수 로드 (.env 파일 필요)
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Google API 키 설정
if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 생성하고 API 키를 입력해주세요.")
    st.stop()

# Streamlit 페이지 설정
st.set_page_config(
    page_title="회의 시뮬레이터",
    page_icon="🤝",
    layout="wide"
)

# --- 데이터 로드 및 모델 설정 ---

@st.cache_data # 페르소나 데이터 캐싱
def load_personas():
    """personas.json 파일에서 페르소나 데이터를 로드합니다."""
    try:
        with open("personas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("personas.json 파일을 찾을 수 없습니다.")
        return []
    except json.JSONDecodeError:
        st.error("personas.json 파일 형식이 올바르지 않습니다.")
        return []
    except Exception as e:
        st.error(f"페르소나 파일 로드 중 오류 발생: {e}")
        return []

# Gemini 모델 설정
try:
    model = genai.GenerativeModel("gemini-2.0-flash") # PRD 명시 모델
except Exception as e:
    st.error(f"Gemini 모델 로드 실패: {e}. API 키 또는 모델 이름을 확인하세요.")
    model = None # 모델 로드 실패 시 None으로 설정

# --- 세션 상태 초기화 ---

if "personas" not in st.session_state:
    st.session_state.personas = load_personas()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "meeting_topic" not in st.session_state:
    st.session_state.meeting_topic = ""
if "is_meeting_started" not in st.session_state:
    st.session_state.is_meeting_started = False
if "user_name" not in st.session_state:
    st.session_state.user_name = "사용자"
if "current_turn" not in st.session_state:
    st.session_state.current_turn = "user" # 시작은 사용자 턴
if "meeting_summary" not in st.session_state:
    st.session_state.meeting_summary = None # 요약 내용 저장
if "meeting_log_markdown_content" not in st.session_state:
    st.session_state.meeting_log_markdown_content = None
if "show_copyable_log" not in st.session_state:
    st.session_state.show_copyable_log = False

# --- 핵심 로직 함수 ---

def get_response_from_gemini(persona, chat_history_text, topic):
    """Gemini API를 호출하여 페르소나의 응답을 생성합니다."""
    if not model:
        return "Gemini 모델이 로드되지 않았습니다."
    try:
        prompt = f"""
        당신은 여성 패션 이커머스 플랫폼 회사에 근무하는 '{persona['name']}'라는 이름의 전략 전문가입니다.
        당신의 성향은 {persona['mbti']}이며, MBTI 성향에 맞는 방식으로 문제를 파악하고 사고합니다.
        현재 회의 주제는 '{topic}'입니다.
        지금까지의 대화 내용은 다음과 같습니다:
        --- 대화 시작 ---
        {chat_history_text}
        --- 대화 끝 ---
        이제 당신의 입장에서 회의 주제에 대해 간결하게 1~3 문장으로 발언해주세요.
        기존의 대화에 순응하기 보다 의식적으로 반대하는 의견을 제시하지만, 타당한 의견에 대해서는 반대를 멈추세요.
        당신의 성향에 일치하는 개념을 제시하고 대화하지만, 직접적으로 MBTI를 드러내지는 않습니다.
        지나치게 추상적이거나 모호한 답변을 피하고 실제 비즈니스에서 발생할 수 있는 상황을 가정하여 구체성 있는 발언을 하세요.
        당신의 성향과 성별을 고려하여 말투를 적절히 사용하세요. 대화라는 점으로 고려해 캐주얼한 말투를 사용해도 좋습니다.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini API 호출 중 오류 발생: {e}")
        return f"응답 생성 실패 ({persona['name']})"

def select_persona_speakers(personas):
    """PRD 기준: 페르소나 턴에 1~2명을 랜덤하게 선택합니다."""
    if not personas:
        return []
    num_speakers = random.randint(1, min(len(personas), 2)) # 1명 또는 2명 선택
    return random.sample(personas, num_speakers)

def start_meeting(topic):
    """회의를 시작하고 상태를 초기화합니다."""
    st.session_state.meeting_topic = topic
    st.session_state.is_meeting_started = True
    st.session_state.chat_history = [{"role": "system", "content": f"회의 시작: {topic}"}]
    st.session_state.current_turn = "user" # 항상 사용자가 먼저 시작

def reset_meeting():
    """회의 상태를 초기화합니다."""
    st.session_state.meeting_topic = ""
    st.session_state.is_meeting_started = False
    st.session_state.chat_history = []
    st.session_state.current_turn = "user"
    st.session_state.meeting_summary = None # 요약 내용도 초기화
    st.session_state.meeting_log_markdown_content = None # 생성된 로그 내용 초기화
    st.session_state.show_copyable_log = False # 복사 영역 숨김

def save_meeting_log():
    """현재 회의 로그를 Markdown 파일로 저장하고, 세션 상태에 복사 가능한 형태로 저장합니다."""
    if not st.session_state.chat_history:
        st.warning("저장할 회의 로그가 없습니다.")
        return None
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meeting_log_{timestamp}.md"

        markdown_content = f"# 회의 로그 ({timestamp})\n\n"
        markdown_content += f"**주제:** {st.session_state.meeting_topic}\n"
        markdown_content += f"**참여자:** {st.session_state.user_name} (사용자), "
        markdown_content += ", ".join([p['name'] for p in st.session_state.personas]) + "\n\n"
        markdown_content += "---\n\n"

        for message in st.session_state.chat_history:
            role = message.get("role", "unknown")
            content = message.get("content", "").strip()
            if role == "system":
                markdown_content += f"*({content})*\n\n"
            else:
                display_role = "사용자" if role == st.session_state.user_name else role
                markdown_content += f"**{display_role}:** {content}\n\n"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        st.session_state.meeting_log_markdown_content = markdown_content
        st.session_state.show_copyable_log = True
        st.success(f"회의 로그가 {filename} 에 저장되었고, 메인 화면에서 복사할 수 있습니다.")
        return filename
    except Exception as e:
        st.error(f"로그 저장 실패: {e}")
        return None

def handle_user_message(user_input):
    """사용자 메시지를 처리하고 페르소나 턴으로 전환합니다."""
    if user_input and st.session_state.is_meeting_started:
        st.session_state.chat_history.append({
            "role": st.session_state.user_name,
            "content": user_input
        })
        st.session_state.current_turn = "persona" # 페르소나 턴으로 변경

def get_targeted_persona_from_user_message(user_message, personas_list, recent_chat_history=None):
    """
    Gemini API를 사용하여 사용자의 메시지에서 특정 페르소나가 지목되었는지,
    또는 최근 대화 내용을 참조하는지 판단합니다.
    지목/참조된 페르소나의 이름을 반환하거나, 없으면 None을 반환합니다.
    """
    if not model:
        return None
    if not user_message.strip():
        return None

    persona_names = [p["name"] for p in personas_list]
    persona_names_str = ", ".join(persona_names)

    history_context = "최근 대화 내용은 다음과 같습니다:\n"
    if recent_chat_history:
        for msg in recent_chat_history:
            history_context += f"{msg.get('role', '알 수 없음')}: {msg.get('content', '')}\n"
    else:
        history_context += " (최근 대화 내용 없음)\n"

    prompt = f"""
    사용자의 다음 메시지를 분석해주세요:
    사용자 메시지: "{user_message}"

    {history_context}
    회의 참석자 목록은 다음과 같습니다: {persona_names_str}

    위 사용자 메시지가 다음 중 하나에 해당합니까?
    1. 회의 참석자 ({persona_names_str}) 중 특정 한 명의 이름을 명시적으로 부르는 경우
    2. 위에 제시된 '최근 대화 내용' 중 특정 참석자의 발언을 명확히 지칭하거나 이어가는 경우

    - 만약 그렇다면, 해당 참석자의 이름만 정확히 응답해주세요. (예: {persona_names_str} 중 하나)
    - 그렇지 않거나, 누구를 지칭하는지 애매하거나, 여러 명을 지칭하거나, 아무도 지칭하지 않는다면 "None"이라고 응답해주세요.

    응답은 반드시 참석자 이름 또는 "None" 중 하나여야 합니다. 다른 설명이나 부연은 절대 추가하지 마십시오.
    """
    try:
        response = model.generate_content(prompt)
        candidate_name = response.text.strip()

        if candidate_name in persona_names:
            return candidate_name
        else:
            return None
    except Exception as e:
        st.error(f"Gemini API (대상 분석) 호출 중 오류 발생: {e}")
        return None

def generate_persona_responses():
    """페르소나 턴일 때 응답을 생성하고 사용자 턴으로 전환합니다."""
    if st.session_state.current_turn == "persona" and st.session_state.is_meeting_started:
        speakers_to_respond = []
        targeted_persona_name = None

        if st.session_state.chat_history:
            last_message_obj = st.session_state.chat_history[-1]
            if last_message_obj.get("role") == st.session_state.user_name:
                user_last_message_content = last_message_obj.get("content", "")

                # 사용자 메시지 직전의 페르소나 발언들 (최대 3개) 추출
                # 시스템 메시지나 다른 사용자 메시지는 제외하고 페르소나 발언만 필터링
                recent_persona_msgs_for_context = []
                # 사용자 메시지 바로 앞부터 역순으로 탐색
                for i in range(len(st.session_state.chat_history) - 2, -1, -1):
                    msg = st.session_state.chat_history[i]
                    # 페르소나 이름 목록 가져오기
                    persona_names_list = [p["name"] for p in st.session_state.personas]
                    if msg.get("role") in persona_names_list: # 페르소나 발언인지 확인
                        recent_persona_msgs_for_context.insert(0, msg) # 맨 앞에 추가하여 순서 유지
                    if len(recent_persona_msgs_for_context) >= 3: # 최대 3개까지만
                        break
                
                targeted_persona_name = get_targeted_persona_from_user_message(
                    user_last_message_content,
                    st.session_state.personas,
                    recent_persona_msgs_for_context # 최근 페르소나 발언 전달
                )

        if targeted_persona_name:
            targeted_speaker_obj = next((p for p in st.session_state.personas if p["name"] == targeted_persona_name), None)
            if targeted_speaker_obj:
                speakers_to_respond = [targeted_speaker_obj]
        else:
            speakers_to_respond = select_persona_speakers(st.session_state.personas)

        if not speakers_to_respond:
            st.session_state.current_turn = "user"
            return

        responses_to_add = []
        for speaker_persona in speakers_to_respond:
            chat_history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history + responses_to_add])
            with st.spinner(f"{speaker_persona['name']} 응답 생성 중..."):
                response_text = get_response_from_gemini(speaker_persona, chat_history_text, st.session_state.meeting_topic)
            responses_to_add.append({
                "role": speaker_persona["name"],
                "content": response_text
            })

        st.session_state.chat_history.extend(responses_to_add)
        st.session_state.current_turn = "user"

# --- 추가된 함수: 회의 요약 ---
def summarize_meeting(chat_history, topic, user_name):
    """Gemini API를 사용하여 회의 내용을 요약합니다."""
    if not model:
        return "Gemini 모델이 로드되지 않았습니다."
    if not chat_history:
        return "요약할 회의 내용이 없습니다."

    # 시스템 메시지 제외 및 역할 이름 통일
    history_text = ""
    for msg in chat_history:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if role != "system":
            # 사용자 이름 통일 (세션 상태의 이름 사용)
            display_role = "사용자" if role == user_name else role
            history_text += f"{display_role}: {content}\\n"

    prompt = f"""
    다음은 '{topic}'에 대한 회의 기록입니다.

    --- 회의 기록 시작 ---
    {history_text}
    --- 회의 기록 끝 ---

    위 회의 기록을 바탕으로 다음 형식에 맞춰 회의를 평가해주세요

    # Agenda
    - (회의 주제를 명확히 기술)

    # Discussion
    - (주요 논의 사항들을 간결하게 요약)

    # Feedback
    - (회의 결과와 논의 방식에 대해 목표달성과 효율성 관점에서 평가하고 개선 사항을 제시)

    결과는 마크다운 형식으로 작성해주세요.
    """
    try:
        with st.spinner("회의 내용을 요약 중입니다..."):
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini API 요약 호출 중 오류 발생: {e}")
        return "회의 요약 생성에 실패했습니다."

# --- Streamlit UI 구성 ---

st.title("🤖 멀티마인드 회의실")
st.caption("이 앱은 서로 다른 성향의 가상 페르소나들이 회의에 참여하여, 나의 사고를 다각도로 확장하고, 복잡한 문제에 대한 더 나은 판단을 돕기 위해 설계되었습니다.")

# --- 이모지 매핑 ---
persona_emojis = {
    "Alex": "💡", # ENTP, 혁신적 아이디어
    "Ben": "📊",  # ISTJ, 데이터/분석
    "Chloe": "🤝" # ESFJ, 협력/관계
}
user_emoji = "🧑‍💻" # 사용자

# --- 이하 생략 ---
