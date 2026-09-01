# MCP Client Test Scripts

HTTP MCP 서버를 테스트하기 위한 shell script 모음입니다.

**주의**: 현재 Streamable/SSE 프로토콜은 세션 관리 문제로 인해 스크립트가 완전히 동작하지 않을 수 있습니다. Stateless 프로토콜을 권장합니다.

## 스크립트 목록 (실행 순서)

### 01. http-sse-test.sh ⚠️
**SSE 프로토콜 테스트 (Stateful) - 세션 관리 이슈**

- **포트**: 8081
- **특징**: 세션 상태 유지, 실시간 서버 푸시 이벤트
- **세션 종료**: DELETE /mcp 필요
- **상태**: 세션 ID 관리 문제로 일부 동작하지 않음

```bash
./01.http-sse-test.sh
```

### 02. http-streamable-test.sh ⚠️
**Streamable HTTP 프로토콜 테스트 (Stateful) - 세션 관리 이슈**

- **포트**: 8082
- **특징**: 세션 상태 유지, SSE 스트리밍 지원
- **세션 종료**: DELETE /mcp 필요
- **상태**: 세션 ID 관리 문제로 일부 동작하지 않음

```bash
./02.http-streamable-test.sh
```

### 03. http-stateless-test.sh ✅
**Stateless 프로토콜 테스트 - 권장**

- **포트**: 8083
- **특징**: 무상태, 세션 관리 없음
- **세션 종료**: DELETE /mcp 불필요
- **상태**: 정상 동작

```bash
./03.http-stateless-test.sh
```

## 전체 테스트 실행

```bash
# Stateless만 실행 (권장)
./03.http-stateless-test.sh

# 전체 순차 실행 (세션 이슈 있음)
for script in 01.http-sse-test.sh 02.http-streamable-test.sh 03.http-stateless-test.sh; do
  echo "Running $script..."
  ./$script
  echo ""
  sleep 2
done
```

## 사전 요구사항

1. **HTTP MCP 서버 실행**:
   ```bash
   cd ../http-mcp-server
   
   # SSE (포트 8081)
   java -jar target/http-mcp-server-1.0.0.jar --spring.profiles.active=sse
   
   # Streamable (포트 8082)
   java -jar target/http-mcp-server-1.0.0.jar --spring.profiles.active=streamable
   
   # Stateless (포트 8083)
   java -jar target/http-mcp-server-1.0.0.jar --spring.profiles.active=stateless
   ```

2. **필수 도구**:
   - `curl`: HTTP 요청
   - `jq`: JSON 파싱 및 출력

## 프로토콜 비교

| 프로토콜 | 포트 | 세션 상태 | DELETE /mcp | SSE 스트리밍 | 사용 사례 |
|---------|------|----------|-------------|-------------|---------|
| **SSE** | 8081 | 유지 | 필요 | 지원 | 실시간 이벤트 |
| **Streamable** | 8082 | 유지 | 필요 | 지원 | 유연한 HTTP 통신 |
| **Stateless** | 8083 | 무상태 | 불필요 | 미지원 | 마이크로서비스 |

## 응답 형식

### JSON 응답 (Accept: application/json)
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"id\":1,\"name\":\"John Smith\",\"email\":\"john.smith@gmail.com\"}]"
      }
    ]
  }
}
```

### SSE 스트리밍 응답 (Accept: text/event-stream)
```
data: {"jsonrpc":"2.0","id":4,"result":{"content":[{"type":"text","text":"..."}]}}
```

## MCP 메서드

### initialize
서버 초기화 및 세션 생성 (Stateful 프로토콜에서 필수)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "clientInfo": { "name": "cli-test", "version": "1.0" },
    "protocolVersion": "2025-03-26",
    "capabilities": {}
  }
}
```

### tools/list
사용 가능한 도구 목록 조회

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

**응답**: User Tools (7개), Product Tools (6개)

### tools/call
특정 도구 실행

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "getAllUsers",
    "arguments": {}
  }
}
```

### DELETE /mcp
세션 종료 (Stateful 프로토콜에서만 필요)

```bash
curl -X DELETE http://localhost:8081/mcp
```

## 사용 가능한 Tools

### User Tools
1. `getAllUsers` - 모든 사용자 조회
2. `getUserById` - ID로 사용자 조회
3. `getUserByEmail` - 이메일로 사용자 조회
4. `searchUsersByName` - 이름으로 사용자 검색
5. `createUser` - 사용자 생성
6. `updateUser` - 사용자 수정
7. `deleteUser` - 사용자 삭제

### Product Tools
1. `getAllProducts` - 모든 상품 조회
2. `getProductById` - ID로 상품 조회
3. `searchProductsByName` - 상품명으로 검색
4. `createProduct` - 상품 생성
5. `updateProduct` - 상품 수정
6. `deleteProduct` - 상품 삭제

## 문제 해결

### 서버 연결 실패
```bash
# 서버 상태 확인
curl http://localhost:8081/actuator/health
curl http://localhost:8082/actuator/health
curl http://localhost:8083/actuator/health
```

### jq 명령어 없음
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

### 스크립트 실행 권한
```bash
chmod +x *.sh
```

## 참고 자료

- [Spring AI MCP Server Documentation](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-server-boot-starter-docs.html)
- [Streamable-HTTP MCP Servers](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-streamable-http-server-boot-starter-docs.html)
- [Stateless MCP Servers](https://docs.spring.io/spring-ai/reference/api/mcp/mcp-stateless-server-boot-starter-docs.html)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/specification)
