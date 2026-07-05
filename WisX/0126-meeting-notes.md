# [WisX] 0126 정기 미팅

<aside>
💡

WisX 매뉴얼을 바탕으로 해당 아이디어의 다양한 구현 방법을 생각해본다.

</aside>

# 구현 방법 아이디에이션

[WisX AI_지혜의 시간여행_초고.pdf](%5BWisX%5D%200126%20%EC%A0%95%EA%B8%B0%20%EB%AF%B8%ED%8C%85/WisX_AI_%E1%84%8C%E1%85%B5%E1%84%92%E1%85%A8%E1%84%8B%E1%85%B4_%E1%84%89%E1%85%B5%E1%84%80%E1%85%A1%E1%86%AB%E1%84%8B%E1%85%A7%E1%84%92%E1%85%A2%E1%86%BC_%E1%84%8E%E1%85%A9%E1%84%80%E1%85%A9.pdf)

[https://www.figma.com/board/TUrpcH9ao1Y6kAJA5bwyg6/Untitled?node-id=0-1&t=ecMAGIi2DcD4MrnK-1](https://www.figma.com/board/TUrpcH9ao1Y6kAJA5bwyg6/Untitled?node-id=0-1&t=ecMAGIi2DcD4MrnK-1)

WisX AI의 비전을 바탕으로 볼 때, 크게 다음 두가지의 최종 산출물을 염두에 두고 과제를 진행해 볼 수 있음

1. WisX AI Agent 구성: WisX AI의 컨셉이 모두 반영된 AI Agent를 구성 및 배포
    1. 예시: 멀티 에이전트 구조
        1. 오케스트레이터
            1. 경전 탐색 에이전트
            2. 현대 과학 용어 변환 에이전트
            3. 스토리텔링 및 롤플레잉 에이전트
            4. 명상 방법 개발 에이전트
2. WisX AI Video Content 구성: WisX AI 이야기 영상 콘텐츠화 시켜, 영상 플랫폼에 업로드
    1. 음악이 강력한 미디어로서 기능할 수 있음

## 각 비전의 구체화 시 고려 사항

### AI 클린 데이터 제공

- 고전의 지혜가 담긴 텍스트가 곧 AI 클린 데이터
- 해당 데이터를 바탕으로 **‘어떤 모델에’** **‘어떤 방식으로’ 학**습 혹은 주입 시켜, **‘어떻게’** 활용할지에 대한 구체적인 방향성이 필요
    - 어떤 모델?
        - 모델을 직접 만들지 않는다는 가정 하에, 기반 모델에 대한 선정이 필요함
            - (단 추가 튜닝을 지원하거나, RAG/MCP 등의 지원이 필요함)
    - 어떤 방식으로?
        - 실제로, 생성형 AI 모델은 수많은 텍스트를 이미 학습한 상황이며, 여기에서 제공하는 고전의 지혜가 담긴 텍스트도 학습했을 가능성이 높음
            - 모델의 내재 지식이 그것을 알고 있다면, 이미 학습이 진행된 데이터일 가능성이 있음 (Hallucination을 적게 하거나, 혹은 하지 않는다면)
        - 이런 상황이면, 선정된 고전 텍스트를 어떻게 활용 해야할지에 대한 고민 필요
        - 학습을 한다면, 아웃풋으로 무엇을 기대하는지에 대한 내용도 필요함
    - 어떻게?
        - 만약 WisX 프로젝트에 선정된 데이터를 추가 학습한다고 하면, **해당 데이터의 학습 혹은 연동이 된 최종 결과물의 형상에 대한 정의**가 필요
            - e.g., WisX AI를 별도로 만들 것인가(WisX AI Agent)? 그렇다면, 해당 AI Agent는 어떤 범위까지 커버할 것인가(종교적 지해? 고전적 지혜 전부?)

### 인간 - AI 공진화

- 앞서 언급했듯, 여기에서 AI의 형상이 무엇인지에 대한 정의가 선행되어야 함
    - ChatGPT, Claude, Gemini 같이 완성형 서비스에는 공진화 개념을 적용할 수 없음
    - 별도의 AI 에이전트 서비스가 필요함
        - 실제로 상호작용 데이터를 바탕으로 추가 학습 등을 진행할 수 있음
- 상세 예시 1. 초원
    
    [https://chowon.in/](https://chowon.in/)
    
- 상세 예시 2. Mechanical Buddha

[https://character.ai/character/Z5WaWtty/mechanical-buddah-cultivation-guide](https://character.ai/character/Z5WaWtty/mechanical-buddah-cultivation-guide)

- 실제 방향성을 잡는다면, 해당하는 형태의 별도 AI 서비스를 만들어볼 수 있음

### 디지털 세대 접근성

AI 에이전트 제작

- 위에서 언급한 AI 에이전트 제작을 목표로 삼고 준비

AI 활용 미디어 제작

- 소장님께서 준비 중인 소설을 AI 활용 영상 미디어로 구체화
    
    [https://openreview.net/pdf/307a103650e4d760b09caf1fac5514a8b0514832.pdf](https://openreview.net/pdf/307a103650e4d760b09caf1fac5514a8b0514832.pdf)
    
    - ICLR2026 리뷰 중인 자동화된 영화 제작과 관련한 AI 활용 방안에 대한 논문이 있고, 이 외에도 AI를 활용한 영화 만들기 제작 자료들이 존재함