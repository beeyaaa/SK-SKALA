#!/bin/bash

# MCP Stateless Streamable-HTTP Test Script
# Usage: ./script/mcp-client.sh [CAR_NUMBER]

set -e

MCP_URL="http://localhost:8081/mcp"
CAR_NUMBER="${1:-533나4567}"

echo "=========================================="
echo "MCP Stateless Streamable-HTTP Test Script"
echo "=========================================="
echo "MCP URL: $MCP_URL"
echo "Car Number: $CAR_NUMBER"
echo ""

# Step 1: Initialize (optional) & get session id if provided by server
# 1) 초기화 (세션 ID 획득) - Streamable-HTTP: JSON 응답
curl -s -v -X POST $MCP_URL \
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

echo ""

# shellcheck disable=SC2086
curl -s -X POST "$MCP_URL" \
  -H "Accept: text/event-stream, application/json" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | grep -q "checkCarNumber" && echo "✓ checkCarNumber tool found"
echo ""

# Step 3: tools/call(checkCarNumber)
echo "[3/3] Checking car number: $CAR_NUMBER"
# shellcheck disable=SC2086
curl -s -X POST "$MCP_URL" \
  -H "Accept: text/event-stream, application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "checkCarNumber",
      "arguments": { "carNumber": "'"$CAR_NUMBER"'" }
    }
  }' | jq

echo ""

# Extract result
IS_REGISTERED=$(echo "$RESULT" | grep -o '"text":"[^"]*"' | sed 's/"text":"\([^"]*\)"/\1/')
echo "=========================================="
echo "Result: Car $CAR_NUMBER is registered: $IS_REGISTERED"
echo "=========================================="
