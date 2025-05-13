# 회의 시뮬레이터 (Multi-Persona Meeting Simulator)

이 프로젝트는 Streamlit과 Google Gemini API를 사용하여 다양한 성향의 AI 페르소나가 참여하는 회의를 시뮬레이션합니다.

## 🌟 주요 기능

*   **다중 페르소나**: 각기 다른 MBTI, 톤, 적극성을 가진 전략 전문가 페르소나 3명 참여.
*   **AI 기반 대화**: Google Gemini API (`gemini-2.0-flash`)를 통해 페르소나의 응답 생성.
*   **턴 기반 진행**: 사용자와 페르소나가 번갈아 가며 발언.
*   **랜덤 발언자 선택**: 페르소나 턴에는 1~2명의 페르소나가 랜덤으로 발언.
*   **채팅 UI**: Streamlit을 사용하여 직관적인 채팅 인터페이스 제공.
*   **회의 관리**: 회의 주제 설정, 회의 로그 저장 및 초기화 기능.

## 🛠️ 설정 방법

1.  **저장소 복제**:
    ```bash
    git clone https://your-repository-url.git
    cd meeting-simulator
    ```

2.  **가상 환경 생성 및 활성화** (권장):
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate  # Windows
    ```

3.  **필수 라이브러리 설치**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **.env 파일 생성**:
    프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 Google API 키를 입력합니다.
    ```
    GOOGLE_API_KEY="여기에_당신의_Google_API_키를_입력하세요"
    ```
    Google API 키는 [Google AI Studio](https://aistudio.google.com/app/apikey)에서 얻을 수 있습니다.

## ▶️ 실행 방법

1.  터미널에서 다음 명령어를 실행합니다:
    ```bash
    streamlit run app.py
    ```

2.  웹 브라우저가 자동으로 열리거나, 터미널에 표시된 URL (보통 `http://localhost:8501`)로 접속합니다.

## 📝 PRD 기반 구현

이 애플리케이션은 제공된 Product Requirements Document (PRD)를 기반으로 개발되었습니다.

*   **페르소나**: `personas.json`에 정의된 3명의 전략 전문가.
*   **회의 흐름**:
    *   사용자가 회의 주제를 입력하여 시작합니다.
    *   사용자가 먼저 발언합니다.
    *   사용자 발언 후, 페르소나 턴으로 전환되어 1~2명의 페르소나가 랜덤으로 응답합니다.
    *   응답은 Gemini API를 통해 생성됩니다.
    *   모든 대화는 로그로 기록됩니다.
*   **UI 기능**:
    *   회의 주제 입력 필드 (사이드바).
    *   실시간 채팅 UI (메인 화면).
    *   회의 초기화 및 로그 저장 기능 (사이드바).

## 🔧 향후 개선 가능성 (PRD 외)

*   페르소나의 적극성 지수(Assertiveness Index)를 실제 발언 확률에 연동.
*   회의 중 페르소나 설정 변경 기능.
*   대화 요약 기능.
*   다양한 프리셋 회의 주제 제공. 