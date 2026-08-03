# Day 1 종합 실습 실행결과

- 실행 시각(UTC): 2026-08-03T09:05:20.354285+00:00
- API 수집 성공: 3/3
- 검증 오류: 0건

## API 응답 시간

- weather: 1005.12ms
- country: 279.02ms
- ip_location: 276.46ms

## 검증 데이터 건수

- weather: 72건
- country: 1건
- ip_location: 1건

## CSV/Parquet 성능 비교

| 데이터셋 | 형식 | 행 | 쓰기(초) | 읽기(초) | 크기(bytes) |
|---|---:|---:|---:|---:|---:|
| weather | CSV | 72 | 0.000493 | 0.001263 | 4843 |
| weather | Parquet | 72 | 0.000319 | 0.000433 | 4680 |
| country | CSV | 1 | 0.000106 | 0.000186 | 130 |
| country | Parquet | 1 | 0.000275 | 0.000364 | 3946 |
| ip_location | CSV | 1 | 0.000109 | 0.000278 | 190 |
| ip_location | Parquet | 1 | 0.000374 | 0.000444 | 6095 |
