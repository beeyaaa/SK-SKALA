#!/bin/bash

# HTTP MCP Server - Stateless Test Script
# Stateless는 세션 상태를 유지하지 않으므로 DELETE /mcp 불필요
# 모든 요청이 독립적으로 처리됨

set -e

MCP_URL="http://localhost:8081/mcp"  # Stateless 포트
QUESTION="모든 사용자 정보를 검색해줘"

echo "=========================================="
echo "HTTP MCP Server - Stateless Test"
echo "=========================================="
echo "MCP URL: $MCP_URL"
echo "Question: $QUESTION"
echo ""

# Step 1: Initialize (세션 ID 획득 - Stateless에서는 선택적)
echo "[1/4] Initialize - JSON Response"
echo "------------------------------------------"
echo ">>> REQUEST:"
curl -s -v -X POST "$MCP_URL" \
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
echo ""

# Step 2: List available tools
echo "[2/4] List Tools - JSON Response"
echo "------------------------------------------"
echo ">>> REQUEST:"
curl -s -v -X POST "$MCP_URL" \
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

echo "$TOOLS_RESPONSE" | jq '.'
echo ""

read -p "Continue to next step? (y/n): " -n 1 -r < /dev/tty
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi
echo ""

# Step 3: Call getAllUsers tool
echo "[3/4] Call Tool: getAllUsers - JSON Response"
echo "------------------------------------------"
echo ">>> REQUEST:"
curl -s -v -X POST "$MCP_URL" \
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

# Step 4: Extract and display user information
echo "[4/4] User Information (Full Response)"
echo "------------------------------------------"
echo "$USERS_RESPONSE" | jq '.'
echo ""

echo "=========================================="
echo "✓ Stateless Test Completed"
echo "Note: Stateless 프로토콜은 세션 상태를 유지하지 않습니다."
echo "      DELETE /mcp 호출이 필요하지 않습니다."
echo "=========================================="
