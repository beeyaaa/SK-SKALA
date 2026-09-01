#!/bin/bash

curl -s -X POST http://localhost:8080/ai/chat -H "Content-Type: application/x-www-form-urlencoded" -d "question=사용 가능한 도구 목록을 알려줘"

# curl -s -X POST http://localhost:8080/ai/chat -H "Content-Type: application/x-www-form-urlencoded" -d "question=모든 사용자 정보를 조회해줘"