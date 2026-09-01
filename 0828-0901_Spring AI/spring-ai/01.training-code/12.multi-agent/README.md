# Multi-Agent 실습 가이드

## 목표

`11.simple-agent`에서 만든 "역할 + Tool"로 정의된 Agent 여러 개를, 하나의 Orchestrator가
상황에 맞게 골라 쓰는 orchestration 기반 Multi-Agent 구조로 확장해 본다

Multi-Agent는 다음 한 문장으로 이해한다.

> **Tool로 Agent를 감싸고 OrcheatratorAgent가 그 Tool을 호출해서 Multi-Agent를 만든다.**

이 코드는 향후 여러분이 직접 자신만의 Multi-Agent를 만들 때 뼈대로 재사용할 Seed Code 입니다.

## 의존성 및 기반 구조

- Spring AI 2.0.0 기준으로 작성한다.
- `11.simple-agent`의 `FileManagerAgent`, `WeatherGuideAgent`, 그리고 그 안에서 쓰던 Tool
  (`FileSystemTool`, `WeatherTools`, `DateTimeTools`)을 그대로 재사용한다. 
- 전문 Agent 자체의 내부 구현(System Prompt, 보유 Tool)은 바꿀 필요가 없다.

## 핵심 구현 가이드

### 1. Agent를 Tool로 감싸기

기존 전문 Agent(`FileManagerAgent`, `WeatherGuideAgent`)의 `ask(request, conversationId)`를
그대로 호출하는 `@Tool` 메서드를 만든다.  
이 Tool들이 Orchestrator가 하위 Agent에게 위임하는 창구가 된다.

- Tool의 `description`이 사실상 라우팅 규칙이다. Orchestrator LLM은 이 설명만 보고 어떤 Tool을
  호출할지 판단하므로, 각 전문 Agent가 무엇을 잘하는지 명확하게 적어야 한다.
- 세션별 대화 맥락을 하위 Agent에도 이어주려면 `conversationId`를 어떤 방식으로든 함께 전달해야 한다.  
  (`ToolContext`를 활용하는 방법을 검토해보라.)

### 2. Orchestrator Agent 정의

새로운 Agent 하나를 추가한다. 이 Agent는:

- 직접 도메인 지식으로 답하지 않고, 전문 Agent에게 위임하는 것이 본업이라는 점을 System Prompt에 명시한다.
- 1번에서 만든 "Agent 래핑 Tool"들을 `tools`로 바인딩한다.
- 필요하다면 하나의 요청 안에서 여러 전문 Agent를 순서대로 호출하고, 그 결과를 종합해서 답하도록 지시한다.

### 3. 진입점 단순화

컨트롤너는 개별 Agent를 호출하는 방식이 아니라 모든 요청을 Orchestrator 가 받아서 
어떤 Agent를 사용할지를 Orchestrator Agent가 스스로 판단하고 개발 Agent를 호출해서 통합 처리하도록 한다. 

### 4. Multi-Agent의 가치가 드러나는 예시 준비

파일 Agent 혼자서도, 날씨 Agent 혼자서도 끝낼 수 없고 반드시 두 Agent가 협업해야 풀리는 질문을
기본 추천 질문으로 둔다. 
(예: 특정 도시 날씨를 확인해서 파일에 그 날씨 결과를 저장해라 등 ) 

## 결과물 기준

아래 조건을 만족하면 실습이 완료된 것으로 본다.

1. "서울 날씨를 확인해서 파일로 저장해줘"류의 질문을 보내면, 로그(SimpleLoggerAdvisor)나 응답 내용을 통해
   Orchestrator가 날씨 조회와 파일 생성을 모두 수행했다는 것을 확인할 수 있다.
2. 파일 관련 질문만 보내면 파일 관리 Agent에게만, 날씨 관련 질문만 보내면 날씨 안내 Agent에게만
   위임되고, 불필요한 Agent까지 함께 호출되지 않는다.
3. 같은 브라우저 세션 안에서는 Orchestrator와 하위 Agent 모두 이전 대화 맥락을 유지한다.
4. 코드 상에서 "전문 Agent → Tool로 래핑 → Orchestrator가 바인딩"이라는 흐름이 한눈에 보인다.
