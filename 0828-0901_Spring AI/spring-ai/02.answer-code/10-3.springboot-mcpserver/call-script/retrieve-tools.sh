#!/bin/bash

# shellcheck disable=SC2086
curl -s -X POST http://localhost:8081/mcp \
  -H "Accept: text/event-stream, application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }' | jq


