#!/bin/bash

# 1) 초기화 (세션 ID 획득) - Streamable-HTTP: JSON 응답
curl -v -X POST http://localhost:8081/mcp \
  -H "Accept: text/event-stream, application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "clientInfo": { "name": "cli", "version": "1.0" },
      "protocolVersion": "2025-03-26",
      "capabilities": {}
    }
  }' | jq

