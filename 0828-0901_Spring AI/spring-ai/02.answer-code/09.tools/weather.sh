#!/bin/bash

# 1. 변수 설정
PATH_URI="/data/2.5/weather"
QUERY="q=Seoul&units=metric&lang=kr"
API_KEY="e23e2d3fd2df53fb845e7e506a63e958"

# 2. curl 실행 및 jq 출력 (에러메시지 숨김 옵션 -s 포함)
curl -s -X GET "https://api.openweathermap.org${PATH_URI}?${QUERY}&appid=${API_KEY}" | jq