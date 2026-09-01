## 프로젝트 개요

이 프로젝트는 spring AI 2.0.0을 기준으로 ChatClient 동기 비동기 기능에 대한 교육용 샘플 코드이다. 

### 필요 사항

- Java 21 이상
- Maven 3.6 이상
- OpenAI API Key

### 환경 변수 설정

OpenAI API Key를 환경 변수로 설정해야 합니다:
현재 환경 변수로 사전에 설정되어 있습니다. 
application.yaml
applicaiton.yaml에는 chatgpt, antropic, gemini 3가지를 지원하도록 하고 Chat GPT 남겨놓고 나머지는 comment out 해줘

```bash
export OPENAI_API_KEY=your-openai-api-key-here
```
### 제공 코드
1. MyController 는 아래의 동기와 동일하게 동작하는 비동기 모두를 지원하는 Controller를 제공
```bash
@RestController
class MyController {

    private final ChatClient chatClient;

    //Autoconfigured ChatClient.Builder is injected
    public MyController(ChatClient.Builder chatClientBuilder) {
        this.chatClient = chatClientBuilder.build();
    }

    @GetMapping("/ai")
    public String generation(@RequestParam String userInput) {
        //The Fluent API in Action
        return this.chatClient.prompt()
                .user(userInput)
                .call()
                .content()
            
    }
}

```

2. UI는 
- tymeleaf 로 작성하되 복잡하지 않고 ChatGPT 와 Chat을 하고 그 결과를 화면에 표시하도록 구성
- LLM 의 response 가 기본 Markdown으로 응답하는 경우 이것을 제대로 표시하도록 제공
- html은 Cache되지 않고 계속해서 접속시마다 static resource를 browser 로 가져오도록 구성
- 화면 제목은 SKALA Spring AI 로 표시하고
- input prompt넣는 박스 상단에는 대화를 위한 질문을 입력하세요로 표시
- input prompt 넣는 박스에는 default 값으로 "너를 소개 시켜줘"라고 들어가게 해서 입력이 없음녀 그것을 사용하고 사용자가  입력을 넣으면 사용자 입력을 input prompt로 사용하게 해줘
  

### 빌드 및 실행

```bash
# 프로젝트 빌드
mvn clean install

# 애플리케이션 실행
mvn spring-boot:run
```

### 접속

브라우저에서 다음 주소로 접속:

```
http://localhost:8080
```
