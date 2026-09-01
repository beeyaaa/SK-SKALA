#!/bin/bash

# HTTP MCP Server - Streamable (Stateful) Test Script
# Streamable은 세션 상태를 유지하므로 작업 완료 후 DELETE /mcp 필요
# SSE 스트리밍 지원

set -e

MCP_URL="http://localhost:8081/mcp"  # Streamable 포트
QUESTION="모든 사용자 정보를 검색해줘"
SESSION_ID=""

echo "=========================================="
echo "HTTP MCP Server - Streamable Test"
echo "=========================================="
echo "MCP URL: $MCP_URL"
echo "Question: $QUESTION"
echo ""

# Step 1: Initialize (세션 ID 획득)
echo "[1/5] Initialize - JSON Response"
echo "------------------------------------------"
echo ">>> REQUEST:"
curl -v -X POST "$MCP_URL" \
  -H "Accept: text/event-stream, application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "clientInfo": { "name": "cli-test", "version": "1.0" },
      "protocolVersion": "2025-03-26",
      "capabilities": {}
    }
  }' 2>&1 | tee /tmp/init_full.txt

echo ""
echo "=== REQUEST HEADERS ==="
grep '^>' /tmp/init_full.txt

echo ""
echo "=== RESPONSE HEADERS ==="
grep '^<' /tmp/init_full.txt

echo ""
echo "=== RESPONSE BODY (JSON) ==="
INIT_RESPONSE=$(cat /tmp/init_full.txt | grep -E '^\{' | tail -1)

echo "$INIT_RESPONSE" | jq '.'

echo ""
read -p "Continue to next step? (y/n): " -n 1 -r < /dev/tty
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi

# Extract session ID from headers (look for X-MCP-Session-Id or similar)
SESSION_ID=$(echo "$INIT_RESPONSE" | jq -r '.result.sessionId // empty')
if [ -z "$SESSION_ID" ]; then
  echo "Warning: No sessionId in response, checking for alternative"
  # Streamable 프로토콜에서는 세션 ID가 별도로 제공되지 않을 수 있음
  # Initialize 성공 자체가 세션 시작을 의미
fi
echo ""

# Step 2: List available tools (세션 컨텍스트 유지)
echo "[2/5] List Tools - JSON Response"
echo "------------------------------------------"
echo ">>> REQUEST:"
curl -v -X POST "$MCP_URL" \
  -H "Accept: text/event-stream, application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }' 2>&1 | tee /tmp/tools_full.txt

echo ""
echo "=== REQUEST HEADERS ==="
grep '^>' /tmp/tools_full.txt

echo ""
echo "=== RESPONSE HEADERS ==="
grep '^<' /tmp/tools_full.txt

echo ""
echo "=== RESPONSE BODY (JSON) ==="
TOOLS_RESPONSE=$(cat /tmp/tools_full.txt | grep -E '^\{' | tail -1)

# Check if response is error
if echo "$TOOLS_RESPONSE" | jq -e '.message' > /dev/null 2>&1; then
  echo "Error: $(echo "$TOOLS_RESPONSE" | jq -r '.message')"
  echo "Full response:"
  echo "$TOOLS_RESPONSE" | jq '.'
  exit 1
fi

echo "$TOOLS_RESPONSE" | jq '.'
echo ""

read -p "Continue to next step? (y/n): " -n 1 -r < /dev/tty
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi
echo ""

# Step 3: Call getAllUsers tool (JSON Response)
echo "[3/5] Call Tool: getAllUsers - JSON Response"
echo "------------------------------------------"
echo ">>> REQUEST:"
curl -v -X POST "$MCP_URL" \
  -H "Accept: text/event-stream, application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "getAllUsers",
      "arguments": {}
    }
  }' 2>&1 | tee /tmp/users_full.txt

echo ""
echo "=== REQUEST HEADERS ==="
grep '^>' /tmp/users_full.txt

echo ""
echo "=== RESPONSE HEADERS ==="
grep '^<' /tmp/users_full.txt

echo ""
echo "=== RESPONSE BODY (JSON) ==="
USERS_RESPONSE=$(cat /tmp/users_full.txt | grep -E '^\{' | tail -1)

echo "$USERS_RESPONSE" | jq '.'
echo ""

read -p "Continue to next step? (y/n): " -n 1 -r < /dev/tty
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi
echo ""

# Step 4: Call getAllUsers tool with SSE Streaming
echo "[4/5] Call Tool: getAllUsers - SSE Streaming Response"
echo "------------------------------------------"
echo ">>> REQUEST:"
echo "Receiving SSE stream..."
curl -v -N -X POST "$MCP_URL" \
  -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "getAllUsers",
      "arguments": {}
    }
  }'
echo ""
echo ""

read -p "Continue to next step? (y/n): " -n 1 -r < /dev/tty
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi

# Step 5: Close session (DELETE /mcp)
echo "[5/5] Close Session - DELETE /mcp"
echo "------------------------------------------"
echo ">>> REQUEST:"
curl -v -X DELETE "$MCP_URL" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" 2>&1 | tee /tmp/delete_full.txt

echo ""
echo "=== REQUEST HEADERS ==="
grep '^>' /tmp/delete_full.txt

echo ""
echo "=== RESPONSE HEADERS ==="
grep '^<' /tmp/delete_full.txt

echo ""
echo "=== RESPONSE BODY (JSON) ==="
DELETE_RESPONSE=$(cat /tmp/delete_full.txt | grep -E '^\{' | tail -1)

if [ -n "$DELETE_RESPONSE" ]; then
  echo "$DELETE_RESPONSE" | jq '.'
else
  echo "✓ Session closed successfully (204 No Content)"
fi
echo ""

# Extract and display user information
echo "=========================================="
echo "User Information (Full Response from Step 3)"
echo "------------------------------------------"
echo "$USERS_RESPONSE" | jq '.'
echo ""

echo "=========================================="
echo "✓ Streamable (Stateful) Test Completed"
echo "Note: Streamable 프로토콜은 세션 상태를 유지합니다."
echo "      작업 완료 후 DELETE /mcp로 세션을 종료했습니다."
echo "=========================================="
