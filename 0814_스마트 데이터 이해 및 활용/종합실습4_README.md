# 종합실습 4 실행 및 제출 안내

## 1. 최종 실행 순서

| 순서 | 파일 | 목적 |
|---:|---|---|
| 1 | `종합실습4_ecom_schema_postgres_테이블생성.sql` | `ecom` 스키마·테이블·함수 생성 |
| 2 | `종합실습4_ecom_seed_postgres_데이터입력.sql` | 랜덤 실습 데이터 적재 |
| 3 | `종합실습4_00_튜닝인덱스_초기화.sql` | 추가 튜닝 인덱스 제거·통계 갱신 |
| 4 | `종합실습4_01_튜닝전_쿼리.sql` | Q1~Q10 튜닝 전 계획·결과 캡처 |
| 5 | `종합실습4_02_튜닝인덱스_생성.sql` | 부분/커버링 인덱스 생성·통계 갱신 |
| 6 | `종합실습4_03_튜닝후_쿼리.sql` | Q1~Q10 튜닝 후 계획·결과 및 Q11 캡처 |
| 7 | `종합실습4_04_조인3종_비교.sql` | NLJ·Hash·Merge Join 비교 |
| 8 | `종합실습4_05_Materialized_View.sql` | MV 생성·원본/MV 성능 비교·갱신 |

## 2. DBeaver 실행 방법

### 최초 환경설정

1. Local PostgreSQL 연결을 연다.
2. 새 데이터베이스를 사용하려면 `practice4` 등을 생성하고 연결한다.
3. 파일 1번을 전체 실행한다.
4. 파일 2번을 전체 실행한다.
5. 아래 건수를 확인한다.

```sql
SELECT 'customers' AS table_name, COUNT(customer_id) FROM ecom.customers
UNION ALL SELECT 'orders', COUNT(order_id) FROM ecom.orders
UNION ALL SELECT 'order_items', COUNT(order_item_id) FROM ecom.order_items
UNION ALL SELECT 'reviews', COUNT(review_id) FROM ecom.reviews;
```

### Q1~Q10 튜닝 전 캡처

1. 파일 3번을 전체 실행한다.
2. 파일 4번에서 문항별 `EXPLAIN (ANALYZE, BUFFERS, SUMMARY)`와 바로 아래 결과 `SELECT`를 실행한다.
3. SQL·실행계획·결과가 보이도록 캡처한다.
4. 다음 이름으로 저장한다: `Q01_튜닝전.png` ~ `Q10_튜닝전.png`.

### Q1~Q10 튜닝 후 캡처

1. 파일 5번을 전체 실행한다.
2. 파일 6번에서 같은 방식으로 문항별 EXPLAIN과 결과 SELECT를 실행한다.
3. 다음 이름으로 저장한다: `Q01_튜닝후.png` ~ `Q10_튜닝후.png`.
4. Q11은 두 함수의 정상 분모 결과와 0 분모 결과를 별도로 캡처한다.

### 캡처 위치

```text
실행결과/화면/
├── Q01_튜닝전.png
├── Q01_튜닝후.png
├── ...
├── Q10_튜닝전.png
├── Q10_튜닝후.png
└── Q11_함수비교.png
```

## 3. 문항별 요구사항 해석

- Q1: `now() - interval '1 month'` 이후의 `paid/shipped/delivered` 주문만 집계한다.
- Q2: 월별 주문 수는 `COUNT(DISTINCT order_id)`, AOV는 주문별 매출 기준으로 계산한다.
- Q3: 최근 90일 주문을 `order_items → products → categories`로 연결한다.
- Q4: 제품별 매출을 먼저 집계한 후 `RANK()`를 적용한다.
- Q5: 고객별 최근 구매일, 주문 횟수, 총매출을 계산한다.
- Q6: 고객별 첫 구매 이후 30일 이내 추가 실구매 여부를 확인한다.
- Q7: `qty_on_hand < reorder_point`인 상품을 찾는다.
- Q8: `AVG(rating) >= 4.5 AND COUNT(review_id) >= 50`을 적용한다.
- Q9: 주문별 금액을 먼저 계산한 후 쿠폰 사용 여부별 평균을 비교한다.
- Q10: 전체 고객 3,000명의 누적매출 순위를 먼저 계산해 상위 1%인 30명을 선정하고, 선정된 고객의 최근 60일 매출을 제시한다.
- Q11: `ecom.f_safe_div(100,0)`은 `0`, `ecom.safe_div(100,0)`은 `NULL`을 반환한다.

## 4. 조인 3종 캡처 방법

파일 7번을 순서대로 실행하고 각 계획의 최상위 물리 조인 노드를 확인한다.

| 조인 | 확인할 실행계획 노드 | 일반적으로 유리한 조건 |
|---|---|---|
| Nested Loop Join | `Nested Loop` | 외부 입력이 작고 내부 조인 키 인덱스가 있을 때 |
| Hash Join | `Hash Join` | 큰 비정렬 동등 조인, 작은 build 입력이 메모리에 들어갈 때 |
| Merge Join | `Merge Join` | 두 입력이 조인 키로 정렬돼 있거나 정렬 비용이 낮을 때 |

캡처 권장 파일명: `JOIN_01_NLJ.png`, `JOIN_02_HASH.png`, `JOIN_03_MERGE.png`.

## 5. Materialized View 실행 방법

파일 8번을 전체 실행하면 다음 작업이 순서대로 수행된다.

1. 기존 `mv_daily_gmv` 제거
2. 일별 주문 수와 GMV를 저장하는 MV 생성
3. 동시 갱신용 UNIQUE 인덱스 생성
4. 최초 일반 `REFRESH`
5. 원본 JOIN·GROUP BY 계획 확인
6. MV 조회 계획·결과 확인
7. `REFRESH MATERIALIZED VIEW CONCURRENTLY` 확인

캡처 권장 파일명: `MV_01_생성.png`, `MV_02_원본계획.png`, `MV_03_MV조회.png`, `MV_04_갱신.png`.

## 6. 리포트 작성

- 작성 틀: `종합실습4_제출리포트_작성틀.md`
- 옵티마이저 선택과제: `종합실습4_06_DBMS별_옵티마이저_비교.md`
- 전후 실행시간, Buffers, Scan/Join 방식은 본인 캡처의 값을 기입한다.

## 7. 주의사항

- 시드가 `random()`을 사용하므로 재적재할 때마다 결과와 실행시간이 달라진다.
- 튜닝 전후 비교는 반드시 같은 데이터 적재 세션에서 진행한다.
- `EXPLAIN ANALYZE`는 실제 쿼리를 실행한다.
- 기존 `실행결과`·PNG·HTML은 추가 안내 전 조건으로 생성된 참고 산출물이다. 새 제출에는 본인이 다시 캡처한 결과와 `종합실습4_제출리포트_작성틀.md`를 사용한다.
