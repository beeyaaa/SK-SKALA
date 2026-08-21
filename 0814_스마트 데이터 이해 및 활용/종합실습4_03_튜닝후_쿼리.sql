-- 종합실습 4: Q1~Q10 튜닝 후 쿼리
-- 실행 순서: 02_튜닝인덱스_생성.sql -> 이 파일
--
-- [각 문항 실행법]
--   ① EXPLAIN 블록: Scan/Join 방식, Buffers, Execution Time을 기록한다.
--   ② 바로 아래 결과 블록: 튜닝 전의 실제 결과와 같은지 확인한다.
--   ※ 업무 결과는 같아야 하고, 접근 방식과 처리 비용만 개선되어야 한다.
--
-- [튜닝 결과에서 주로 확인할 용어]
--   Seq Scan = 테이블을 처음부터 순서대로 읽는 방식
--   Index Scan = 인덱스에서 조건에 맞는 위치를 찾아 읽는 방식
--   Nested Loop = 바깥쪽 행마다 안쪽 입력을 반복 탐색하는 조인
--   Hash Join = 한쪽 입력을 해시 테이블로 만든 뒤 키를 비교하는 조인
--   loops = 해당 실행계획 노드가 반복 실행된 횟수
--   SARG 조건 = 컬럼을 함수로 감싸지 않아 인덱스 범위 탐색이 가능한 조건

SET search_path = ecom, public;

-- Q1. 최근 1개월 SARG 범위 조건 + 한 번의 조인/집계
-- 튜닝: 주문별 상관 서브쿼리 대신 orders와 order_items를 한 번 조인해 합산한다.
-- [① 실행계획 확인용] 날짜 범위 및 인덱스 사용 여부 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                 -- 튜닝 후 실행계획과 성능 측정
SELECT COALESCE(ROUND(SUM(oi.line_total), 2), 0) AS total_sales_1m -- 총매출, NULL이면 0
FROM ecom.orders o                                 -- 주문 테이블
JOIN ecom.order_items oi ON oi.order_id = o.order_id -- 주문상품을 한 번 조인
WHERE o.order_status IN ('paid', 'shipped', 'delivered') -- 실매출 주문만 포함
  AND o.order_ts >= now() - INTERVAL '1 month';    -- 컬럼을 변환하지 않는 인덱스 친화적 조건

SELECT COALESCE(ROUND(SUM(oi.line_total), 2), 0) AS total_sales_1m -- [②] 실제 총매출 확인
FROM ecom.orders o
JOIN ecom.order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('paid', 'shipped', 'delivered')
  AND o.order_ts >= now() - INTERVAL '1 month';

-- Q2. 주문별 매출을 먼저 계산해 COUNT(DISTINCT)를 제거
-- 튜닝: 주문별로 한 행을 만든 뒤 중복 제거 없이 order_id를 집계한다.
-- [① 실행계획 확인용] 주문별 선집계 후 월별 집계 계획 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)
WITH order_totals AS (                             -- 주문별 금액을 먼저 만드는 CTE
    SELECT o.order_id,
           date_trunc('month', o.order_ts)::date AS sales_month,
           SUM(oi.line_total) AS order_total       -- 주문상품을 주문 단위로 합산
    FROM ecom.orders o
    JOIN ecom.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('paid', 'shipped', 'delivered')
    GROUP BY o.order_id, o.order_ts
)
SELECT sales_month,
       COUNT(order_id) AS order_count,             -- 주문당 한 행이므로 주문번호 집계
       ROUND(SUM(order_total), 2) AS revenue,
       ROUND(AVG(order_total), 2) AS aov
FROM order_totals
GROUP BY sales_month
ORDER BY sales_month;

WITH order_totals AS (                             -- [②] 실제 월별 결과 조회
    SELECT o.order_id, date_trunc('month', o.order_ts)::date AS sales_month,
           SUM(oi.line_total) AS order_total
    FROM ecom.orders o
    JOIN ecom.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('paid', 'shipped', 'delivered')
    GROUP BY o.order_id, o.order_ts
)
SELECT sales_month, COUNT(order_id) AS order_count,
       ROUND(SUM(order_total), 2) AS revenue,
       ROUND(AVG(order_total), 2) AS aov
FROM order_totals
GROUP BY sales_month
ORDER BY sales_month;

-- Q3. 기간/상태로 orders를 먼저 축소하고 SARG 범위 조건 사용
-- 튜닝: 최근 90일 실매출 주문만 먼저 골라 조인해야 할 행 수를 줄인다.
-- [① 실행계획 확인용] 최근 주문 선필터와 조인 계획 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)
WITH recent_sales AS MATERIALIZED (                -- 최근 주문을 먼저 계산해 저장하는 CTE
    SELECT order_id
    FROM ecom.orders
    WHERE order_status IN ('paid', 'shipped', 'delivered')
      AND order_ts >= CURRENT_DATE - 90            -- 컬럼을 변환하지 않는 최근 90일 조건
)
SELECT c.category_id,
       c.category_name,
       ROUND(SUM(oi.line_total), 2) AS revenue_90d
FROM recent_sales rs
JOIN ecom.order_items oi ON oi.order_id = rs.order_id
JOIN ecom.products p ON p.product_id = oi.product_id
JOIN ecom.categories c ON c.category_id = p.category_id
GROUP BY c.category_id, c.category_name
ORDER BY revenue_90d DESC, c.category_id
LIMIT 10;

WITH recent_sales AS MATERIALIZED (                -- [②] 실제 카테고리 Top 10 조회
    SELECT order_id
    FROM ecom.orders
    WHERE order_status IN ('paid', 'shipped', 'delivered')
      AND order_ts >= CURRENT_DATE - 90
)
SELECT c.category_id, c.category_name,
       ROUND(SUM(oi.line_total), 2) AS revenue_90d
FROM recent_sales rs
JOIN ecom.order_items oi ON oi.order_id = rs.order_id
JOIN ecom.products p ON p.product_id = oi.product_id
JOIN ecom.categories c ON c.category_id = p.category_id
GROUP BY c.category_id, c.category_name
ORDER BY revenue_90d DESC, c.category_id
LIMIT 10;

-- Q4. 전체 매출을 한 번만 집계한 뒤 RANK 적용
-- 튜닝: 제품마다 매출을 다시 찾지 않고 전체 데이터를 한 번 읽어 제품별로 묶는다.
-- [① 실행계획 확인용] 반복 SubPlan이 제거됐는지 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)
WITH product_revenue AS (                          -- 전체 데이터를 제품별로 한 번 집계
    SELECT p.product_id,
           p.product_name,
           SUM(oi.line_total) AS revenue
    FROM ecom.orders o
    JOIN ecom.order_items oi ON oi.order_id = o.order_id
    JOIN ecom.products p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('paid', 'shipped', 'delivered')
    GROUP BY p.product_id, p.product_name
), ranked AS (                                     -- 집계 결과에 순위를 부여
    SELECT product_id, product_name, revenue,
           RANK() OVER (ORDER BY revenue DESC) AS revenue_rank -- 매출 내림차순 공동 순위
    FROM product_revenue
)
SELECT product_id, product_name, ROUND(revenue, 2) AS revenue, revenue_rank
FROM ranked
WHERE revenue_rank <= 20
ORDER BY revenue_rank, product_id;

WITH product_revenue AS (                          -- [②] 실제 제품별 순위 조회
    SELECT p.product_id, p.product_name, SUM(oi.line_total) AS revenue
    FROM ecom.orders o
    JOIN ecom.order_items oi ON oi.order_id = o.order_id
    JOIN ecom.products p ON p.product_id = oi.product_id
    WHERE o.order_status IN ('paid', 'shipped', 'delivered')
    GROUP BY p.product_id, p.product_name
), ranked AS (
    SELECT product_id, product_name, revenue,
           RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
    FROM product_revenue
)
SELECT product_id, product_name, ROUND(revenue, 2) AS revenue, revenue_rank
FROM ranked
WHERE revenue_rank <= 20
ORDER BY revenue_rank, product_id;

-- Q5. 주문별 매출 선집계 후 고객별 한 번의 GROUP BY로 RFM 산출
-- 튜닝: 고객 한 명마다 세 가지 서브쿼리를 반복하는 작업을 제거한다.
-- [① 실행계획 확인용] 고객별 반복 조회 대신 한 번에 집계하는지 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)
WITH order_totals AS (                             -- 주문별 금액을 먼저 집계
    SELECT o.order_id, o.customer_id, o.order_ts,
           SUM(oi.line_total) AS order_total
    FROM ecom.orders o
    JOIN ecom.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('paid', 'shipped', 'delivered')
    GROUP BY o.order_id, o.customer_id, o.order_ts
), rfm AS (                                        -- 주문별 결과를 고객별 RFM으로 재집계
    SELECT customer_id,
           CURRENT_DATE - MAX(order_ts)::date AS recency_days, -- 최근 구매 경과일
           COUNT(order_id) AS frequency,           -- 구매 주문번호 수
           SUM(order_total) AS monetary            -- 고객 총매출
    FROM order_totals
    GROUP BY customer_id
)
SELECT c.customer_id, c.full_name,
       r.recency_days, r.frequency, ROUND(r.monetary, 2) AS monetary
FROM rfm r
JOIN ecom.customers c ON c.customer_id = r.customer_id
ORDER BY r.monetary DESC, c.customer_id
LIMIT 20;

WITH order_totals AS (                             -- [②] 실제 고객별 RFM 조회
    SELECT o.order_id, o.customer_id, o.order_ts,
           SUM(oi.line_total) AS order_total
    FROM ecom.orders o
    JOIN ecom.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('paid', 'shipped', 'delivered')
    GROUP BY o.order_id, o.customer_id, o.order_ts
), rfm AS (
    SELECT customer_id, CURRENT_DATE - MAX(order_ts)::date AS recency_days,
           COUNT(order_id) AS frequency, SUM(order_total) AS monetary
    FROM order_totals
    GROUP BY customer_id
)
SELECT c.customer_id, c.full_name,
       r.recency_days, r.frequency, ROUND(r.monetary, 2) AS monetary
FROM rfm r
JOIN ecom.customers c ON c.customer_id = r.customer_id
ORDER BY r.monetary DESC, c.customer_id
LIMIT 20;

-- Q6. 윈도 함수로 첫 구매시각을 한 번 표시한 뒤 고객별 BOOL_OR 집계
-- [① 실행계획 확인용] Window와 BOOL_OR 집계 계획 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)
WITH purchase_sequence AS (
    SELECT customer_id,
           order_ts,
           MIN(order_ts) OVER (PARTITION BY customer_id) AS first_ts -- 각 주문행에 고객 첫 구매시각 표시
    FROM ecom.orders
    WHERE order_status IN ('paid', 'shipped', 'delivered')
), customer_flags AS (
    SELECT customer_id,
           BOOL_OR(order_ts > first_ts             -- 조건을 만족하는 추가 주문이 하나라도 있으면 TRUE
                   AND order_ts <= first_ts + INTERVAL '30 days') AS repurchased_30d
    FROM purchase_sequence
    GROUP BY customer_id
)
SELECT COUNT(customer_id) AS purchasing_customers,
       COUNT(customer_id) FILTER (WHERE repurchased_30d) AS repurchased_customers,
       ROUND(100.0 * COUNT(customer_id) FILTER (WHERE repurchased_30d)
             / NULLIF(COUNT(customer_id), 0), 2) AS repurchase_rate_pct
FROM customer_flags;

WITH purchase_sequence AS (                        -- [②] 실제 재구매율 결과 조회
    SELECT customer_id, order_ts,
           MIN(order_ts) OVER (PARTITION BY customer_id) AS first_ts
    FROM ecom.orders
    WHERE order_status IN ('paid', 'shipped', 'delivered')
), customer_flags AS (
    SELECT customer_id,
           BOOL_OR(order_ts > first_ts
                   AND order_ts <= first_ts + INTERVAL '30 days') AS repurchased_30d
    FROM purchase_sequence
    GROUP BY customer_id
)
SELECT COUNT(customer_id) AS purchasing_customers,
       COUNT(customer_id) FILTER (WHERE repurchased_30d) AS repurchased_customers,
       ROUND(100.0 * COUNT(customer_id) FILTER (WHERE repurchased_30d)
             / NULLIF(COUNT(customer_id), 0), 2) AS repurchase_rate_pct
FROM customer_flags;

-- Q7. 직접 조건 + 저재고 부분 인덱스
-- 튜닝: 저재고 행만 저장한 부분 인덱스를 이용해 필요한 후보를 빠르게 찾는다.
-- [① 실행계획 확인용] 저재고 부분 인덱스 사용 여부 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)
SELECT p.product_id, p.sku, p.product_name,
       i.qty_on_hand, i.reorder_point,
       i.reorder_point - i.qty_on_hand AS shortage_qty
FROM ecom.inventory i
JOIN ecom.products p ON p.product_id = i.product_id
WHERE i.qty_on_hand < i.reorder_point              -- 현재고가 재주문 기준보다 낮은 행만 필터
ORDER BY shortage_qty DESC, p.product_id
LIMIT 20;

SELECT p.product_id, p.sku, p.product_name,         -- [②] 실제 부족 재고 상품 조회
       i.qty_on_hand, i.reorder_point,
       i.reorder_point - i.qty_on_hand AS shortage_qty
FROM ecom.inventory i
JOIN ecom.products p ON p.product_id = i.product_id
WHERE i.qty_on_hand < i.reorder_point
ORDER BY shortage_qty DESC, p.product_id
LIMIT 20;

-- Q8. 리뷰 테이블을 한 번만 읽고 GROUP BY/HAVING 적용
-- 튜닝: 제품별 AVG와 COUNT를 한 번 계산하고 HAVING에서 두 조건을 함께 적용한다.
-- [① 실행계획 확인용] reviews를 한 번만 집계하는지 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)
SELECT p.product_id,
       p.product_name,
       ROUND(AVG(r.rating), 2) AS avg_rating,       -- 제품별 평균평점
       COUNT(r.review_id) AS review_count          -- 제품별 리뷰번호 수
FROM ecom.reviews r
JOIN ecom.products p ON p.product_id = r.product_id
GROUP BY p.product_id, p.product_name
HAVING AVG(r.rating) >= 4.5                         -- 집계 후 평균평점 조건 적용
   AND COUNT(r.review_id) >= 50                    -- 집계 후 리뷰 수 조건 적용
ORDER BY avg_rating DESC, review_count DESC, p.product_id;

SELECT p.product_id, p.product_name,                -- [②] 실제 효자상품 결과 조회
       ROUND(AVG(r.rating), 2) AS avg_rating,
       COUNT(r.review_id) AS review_count
FROM ecom.reviews r
JOIN ecom.products p ON p.product_id = r.product_id
GROUP BY p.product_id, p.product_name
HAVING AVG(r.rating) >= 4.5
   AND COUNT(r.review_id) >= 50
ORDER BY avg_rating DESC, review_count DESC, p.product_id;

-- Q9. 주문별 매출 선집계로 DISTINCT 제거
-- 튜닝: 주문별 금액을 먼저 한 행으로 만든 뒤 그룹별 AVG(order_total)을 계산한다.
-- [① 실행계획 확인용] 주문별 선집계 후 AVG 계산 계획 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)
WITH order_totals AS (
    SELECT o.order_id,
           (o.coupon_code IS NOT NULL) AS used_coupon, -- 쿠폰 사용 여부를 TRUE/FALSE로 변환
           SUM(oi.line_total) AS order_total        -- 주문별 총금액
    FROM ecom.orders o
    JOIN ecom.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('paid', 'shipped', 'delivered')
    GROUP BY o.order_id, o.coupon_code
)
SELECT CASE WHEN used_coupon THEN '사용' ELSE '미사용' END AS coupon_group,
       COUNT(order_id) AS order_count,
       ROUND(AVG(order_total), 2) AS aov            -- 주문별 금액의 평균
FROM order_totals
GROUP BY used_coupon
ORDER BY coupon_group;

WITH order_totals AS (                             -- [②] 실제 쿠폰 그룹 비교 결과 조회
    SELECT o.order_id, (o.coupon_code IS NOT NULL) AS used_coupon,
           SUM(oi.line_total) AS order_total
    FROM ecom.orders o
    JOIN ecom.order_items oi ON oi.order_id = o.order_id
    WHERE o.order_status IN ('paid', 'shipped', 'delivered')
    GROUP BY o.order_id, o.coupon_code
)
SELECT CASE WHEN used_coupon THEN '사용' ELSE '미사용' END AS coupon_group,
       COUNT(order_id) AS order_count, ROUND(AVG(order_total), 2) AS aov
FROM order_totals
GROUP BY used_coupon
ORDER BY coupon_group;

-- Q10. 전체 3,000명의 누적매출과 최근 60일 매출을 한 번에 집계한 뒤
--      누적매출 상위 1%(30명)를 정확히 선정
-- 튜닝: 누적매출과 60일 매출을 한 번의 GROUP BY로 동시에 계산한다.
-- [① 실행계획 확인용] 고객별 SubPlan 없이 한 번에 집계하는지 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)
WITH customer_sales AS (
    SELECT c.customer_id,
           c.full_name,
           COALESCE(SUM(oi.line_total), 0) AS lifetime_revenue, -- 고객 누적매출
           COALESCE(SUM(oi.line_total) FILTER (
               WHERE o.order_ts >= now() - INTERVAL '60 days'
           ), 0) AS revenue_60d                    -- 같은 집계에서 최근 60일 매출만 합산
    FROM ecom.customers c
    LEFT JOIN ecom.orders o                        -- 주문 없는 고객도 전체 3,000명에 포함
      ON o.customer_id = c.customer_id
     AND o.order_status IN ('paid', 'shipped', 'delivered')
    LEFT JOIN ecom.order_items oi ON oi.order_id = o.order_id
    GROUP BY c.customer_id, c.full_name
), ranked AS (
    SELECT customer_id, full_name, lifetime_revenue, revenue_60d,
           ROW_NUMBER() OVER (                     -- 누적매출 순서대로 중복 없는 순번 부여
               ORDER BY lifetime_revenue DESC, customer_id
           ) AS lifetime_rank,
           COUNT(customer_id) OVER () AS customer_count -- 전체 고객 수를 각 행에 표시
    FROM customer_sales
)
SELECT customer_id, full_name, lifetime_rank,
       ROUND(lifetime_revenue, 2) AS lifetime_revenue,
       ROUND(revenue_60d, 2) AS revenue_60d
FROM ranked
WHERE lifetime_rank <= CEIL(customer_count * 0.01) -- 전체 고객 중 상위 1%, 정확히 30명
ORDER BY lifetime_rank;

WITH customer_sales AS (                           -- [②] 실제 상위 30명 결과 조회
    SELECT c.customer_id, c.full_name,
           COALESCE(SUM(oi.line_total), 0) AS lifetime_revenue,
           COALESCE(SUM(oi.line_total) FILTER (
               WHERE o.order_ts >= now() - INTERVAL '60 days'
           ), 0) AS revenue_60d
    FROM ecom.customers c
    LEFT JOIN ecom.orders o
      ON o.customer_id = c.customer_id
     AND o.order_status IN ('paid', 'shipped', 'delivered')
    LEFT JOIN ecom.order_items oi ON oi.order_id = o.order_id
    GROUP BY c.customer_id, c.full_name
), ranked AS (
    SELECT customer_id, full_name, lifetime_revenue, revenue_60d,
           ROW_NUMBER() OVER (
               ORDER BY lifetime_revenue DESC, customer_id
           ) AS lifetime_rank,
           COUNT(customer_id) OVER () AS customer_count
    FROM customer_sales
)
SELECT customer_id, full_name, lifetime_rank,
       ROUND(lifetime_revenue, 2) AS lifetime_revenue,
       ROUND(revenue_60d, 2) AS revenue_60d
FROM ranked
WHERE lifetime_rank <= CEIL(customer_count * 0.01)
ORDER BY lifetime_rank;

-- Q11. 스키마와 시드에 정의된 두 함수의 정상 분모 결과 비교
-- [① 정상 분모] 분모가 0이 아니면 두 함수가 같은 계산 결과를 반환
SELECT ecom.f_safe_div(
           SUM(oi.line_total), COUNT(DISTINCT o.order_id)
       ) AS schema_f_safe_div_aov,
       ecom.safe_div(
           SUM(oi.line_total), COUNT(DISTINCT o.order_id)
       ) AS seed_safe_div_aov
FROM ecom.orders o
JOIN ecom.order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('paid', 'shipped', 'delivered');

-- 차이점: f_safe_div는 0, safe_div는 NULL을 반환한다.
-- [② 0 분모] 0 반환과 NULL 반환의 업무 정책 차이 확인
SELECT ecom.f_safe_div(100, 0) AS schema_function_returns_zero, -- 0으로 나누면 숫자 0
       ecom.safe_div(100, 0) AS seed_function_returns_null;     -- 0으로 나누면 NULL(값 없음)
