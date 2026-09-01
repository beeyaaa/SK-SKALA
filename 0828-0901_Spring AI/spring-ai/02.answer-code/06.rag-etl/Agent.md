## 프로젝트 개요

이 프로젝트는 spring AI 2.0.0을 기준으로 ChatClient 동기 비동기 기능에 대한 교육용 샘플 코드이다. 

### 필요 사항

- Java 21 이상
- Maven 3.6 이상
- OpenAI API Key


### 작성 코드
1. src/main/resources/documents/대한민국헌법(19880225).txt 파일을 읽어서 VectorDB에 저장하는 코드를 작성한다
    - 작성 코드 이름은 TxtEtlSErvice.java 이다.
    - spring AI의 RAG ETL 코드를 학습하기 위한 코드이다.
    - Token Text Spliter 는 openapi embedding small 기준으로 적합한 설정을 넣어주면 된다.
    - Extract, Transform, Load를 구현한다. 
    - 각 구현은 extract, transformer, load 3가지 method로 분리해서 구현하고 
    - 외부에서 호출하는 경우 fluentAPI로 extract, transformer, load를 구현하도록 한다. 
    - 이 코드는 학습용으로 복잡하지 않고 RAG의 ETL을 이해하는것에 맞추면 된다. 
2. TxtEtlController.java를 구현하고 이것은 TxtEtlService의 API 를 fluent API로 호출한다. 
   - extract 호출 시 파일 명을 입력으로 넣으면 이것을 로딩한다. 
  
3. UI는 기존에 있는 tymeleaf를 그대로 두고 index.html에 왼쪽에 있는 메뉴에 RAG-ETL 을 추가하고 
이것을 선택하면 resources/documents 아래에 있는 파일 명과 확장자를 읽어와서 화면에 표시한다
화면에서 파일을 선택하면 이 파일 명과 확장자 를 기준으로 
- txt 이면 TxtEtlController.java에 executeETL() 메소드가 호출되고 이것은 TxtEtlService.java 메소드를 호출해서 Vector DB에 저장한다.
- pdf 이면 pdftEtlController.java에 executeETL() 메소드가 호출되고 이것은 pdfEtlService.java 메소드를 호출해서 Vector DB에 저장한다.


# 규칙
- 이미지 아이콘을 사용하지 않는다.
- 실습 코드이므로 개념을 명확하게 이해 할 수 있도록 간결한 코드를 작성한다
