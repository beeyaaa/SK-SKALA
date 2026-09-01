# 개요
현재 이 프로젝트는 @Tool  실습용으로 만든 코드이다. 
이 코드를 MCP Server 코드로 변경하고자 한다. 
이때 변경을 최소화하면서 무엇을 바꾸게 되면 MCP Server로 전환하는지를 직관적으로 이해하도록 해서 
@Tool 과 @McpTool @ToolParam 과 @McpToolParam의 차리를 이해다호록 해야 한다.

# 규칙
복잡하게 만들지 마라
Markdown 파일 생성이나 comment 작성시 아이콘을 사용하지 마라
MCPClient 와 MCP Server 간 통신 방식은 Streamable HTTP protocol을 사용한다. 
spring 2.0.0 기준으로 작성한다


# 작서해야 할 것
기존 tools 패키지 아래에 Tool들을 유지하고 
MCP Server로 전환하는 부분을 추가하고
필요없는 코드는 제거한다.

그리고 이 전환 과정에서의 추가, 변경, 삭제 에 대한 것은 
MCP-Transformation-guide.md를 작성해서 
기존 Tool을 MCP Server 로 전환 시 추가, 변경, 제거되는 것에 대해 설명한다. 

# MCP Client는 여기 별도 디렉토리로 작성하기
MCP-Client로 전환되는 부분에 대해서는 
디렉토리를 mcp-client 디렉토리를 만들고 
Client로 넘어가는 부분을 정리 작성한다.
UI는 기존 방식을 그대로 유지한다

