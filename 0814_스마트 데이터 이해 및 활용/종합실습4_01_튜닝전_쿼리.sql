-- 종합실습 4: Q1~Q10 튜닝 전 쿼리
-- 실행 순서: 00_튜닝인덱스_초기화.sql -> 이 파일
-- DBeaver에서는 각 Q의 EXPLAIN과 SELECT를 함께 선택해 실행 후 화면을 캡처한다.
--
-- [각 문항 실행법]
--   ① 실행계획 확인용: EXPLAIN부터 해당 쿼리의 세미콜론(;)까지 실행
--      -> Scan/Join 방식, Buffers, Execution Time을 기록하고 캡처한다.
--   ② 실제 결과 확인용: 바로 아래의 같은 SELECT를 세미콜론(;)까지 실행
--      -> 구매·재무팀에 전달할 실제 숫자/목록을 확인하고 캡처한다.
--   ※ ①과 ②는 같은 업무 로직이며 EXPLAIN의 유무만 다르다.
--   ※ 이 파일은 튜닝 비교를 위해 일부러 비효율적인 SQL 형태를 포함한다.
--
-- [EXPLAIN 항목 뜻]
--   ANALYZE = 쿼리를 실제로 실행하여 실제 소요시간과 행 수를 측정
--   BUFFERS = 메모리/디스크 페이지를 얼마나 읽었는지 표시
--   SUMMARY = Planning Time과 Execution Time 요약 표시

SET search_path = ecom, public;

-- =========================================================
-- Q1. 최근 1개월 실제 판매 총액
-- 문제점: order_ts를 EXTRACT 함수로 변환해 일반 B-tree 범위 탐색을 어렵게 하고,
--         주문마다 order_items를 다시 읽는 상관 서브쿼리를 사용한다.
-- =========================================================
-- [① 실행계획 확인용] EXPLAIN부터 첫 번째 세미콜론까지 실행
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                 -- 실제 실행계획·버퍼·실행시간 측정
SELECT COALESCE(SUM((                              -- 주문별 금액을 합산하고 NULL이면 0 반환
           SELECT SUM(oi.line_total)               -- 해당 주문의 주문상품 금액 합계
           FROM ecom.order_items oi                -- order_items 테이블 별칭은 oi
           WHERE oi.order_id = o.order_id          -- 바깥 주문번호를 참조하는 상관 서브쿼리
       )), 0) AS total_sales_1m                    -- 결과 컬럼명: 최근 1개월 총매출
FROM ecom.orders o                                 -- orders 테이블 별칭은 o
WHERE o.order_status IN ('paid', 'shipped', 'delivered') -- 실제 매출로 인정할 주문 상태
  AND EXTRACT(EPOCH FROM o.order_ts)               -- 주문시각을 초 단위 숫자로 변환
      >= EXTRACT(EPOCH FROM now() - INTERVAL '1 month'); -- 현재로부터 1개월 이내만 조회
      
-- [②] 실행계획 없이 실제 총매출 조회
SELECT COALESCE(SUM((                              
           SELECT SUM(oi.line_total)
           FROM ecom.order_items oi
           WHERE oi.order_id = o.order_id
       )), 0) AS total_sales_1m
FROM ecom.orders o
WHERE o.order_status IN ('paid', 'shipped', 'delivered')
  AND EXTRACT(EPOCH FROM o.order_ts)
      >= EXTRACT(EPOCH FROM now() - INTERVAL '1 month');

-- =========================================================
-- Q2. 월별 주문 수, 매출, AOV
-- 문제점: 상세 행을 먼저 모두 조인한 뒤 COUNT(DISTINCT)로 중복을 제거한다.
-- =========================================================
-- [① 실행계획 확인용] 월별 집계의 Scan/Join과 실행시간 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                 -- 실제 실행계획과 성능 측정
SELECT date_trunc('month', o.order_ts)::date AS sales_month, -- 주문시각을 월 단위로 묶음
       COUNT(DISTINCT o.order_id) AS order_count,  -- 상세행 중복을 제거한 주문 수
       ROUND(SUM(oi.line_total), 2) AS revenue,    -- 월별 매출 합계, 소수점 둘째 자리
       ROUND(SUM(oi.line_total) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS aov -- 주문당 평균금액
FROM ecom.orders o                                 -- 주문 테이블
JOIN ecom.order_items oi ON oi.order_id = o.order_id -- 주문번호로 주문상품 연결
WHERE o.order_status IN ('paid', 'shipped', 'delivered') -- 실매출 주문만 포함
GROUP BY 1                                         -- SELECT 첫 번째 컬럼인 월로 그룹화
ORDER BY 1;                                        -- 월 오름차순 정렬

SELECT date_trunc('month', o.order_ts)::date AS sales_month, -- [②] 실제 월별 결과 조회
       COUNT(DISTINCT o.order_id) AS order_count,
       ROUND(SUM(oi.line_total), 2) AS revenue,
       ROUND(SUM(oi.line_total) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS aov
FROM ecom.orders o
JOIN ecom.order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('paid', 'shipped', 'delivered')
GROUP BY 1
ORDER BY 1;

-- =========================================================
-- Q3. 최근 90일 카테고리 Top 10
-- 문제점: 비-SARG 날짜 조건을 사용하고 상세 데이터를 그대로 집계한다.
-- =========================================================
-- [① 실행계획 확인용] 최근 90일 필터와 테이블 조인 계획 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                 -- 실제 실행계획과 성능 측정
SELECT c.category_id,
       c.category_name,
       ROUND(SUM(oi.line_total), 2) AS revenue_90d -- 카테고리별 최근 90일 매출
FROM ecom.orders o                                 -- 주문에서 시작
JOIN ecom.order_items oi ON oi.order_id = o.order_id -- 주문상품 연결
JOIN ecom.products p ON p.product_id = oi.product_id -- 상품 연결
JOIN ecom.categories c ON c.category_id = p.category_id -- 카테고리 연결
WHERE o.order_status IN ('paid', 'shipped', 'delivered') -- 실매출 주문만 포함
  AND o.order_ts::date >= CURRENT_DATE - 90        -- timestamp를 date로 변환해 최근 90일 필터
GROUP BY c.category_id, c.category_name            -- 카테고리별로 묶어 합산
ORDER BY revenue_90d DESC, c.category_id           -- 매출이 큰 순서로 정렬
LIMIT 10;                                          -- 상위 10개만 표시

SELECT c.category_id,                              -- [②] 실제 Top 10 결과 조회
       c.category_name,
       ROUND(SUM(oi.line_total), 2) AS revenue_90d
FROM ecom.orders o
JOIN ecom.order_items oi ON oi.order_id = o.order_id
JOIN ecom.products p ON p.product_id = oi.product_id
JOIN ecom.categories c ON c.category_id = p.category_id
WHERE o.order_status IN ('paid', 'shipped', 'delivered')
  AND o.order_ts::date >= CURRENT_DATE - 90
GROUP BY c.category_id, c.category_name
ORDER BY revenue_90d DESC, c.category_id
LIMIT 10;

-- =========================================================
-- Q4. 제품별 누적매출 RANK() Top 20
-- 문제점: 600개 제품 각각에 대해 매출 상관 서브쿼리를 실행한다.
-- =========================================================
-- [① 실행계획 확인용] 반복 SubPlan의 loops와 실행시간 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                 -- 실제 실행계획과 반복 횟수 측정
WITH product_revenue AS (                          -- 제품별 매출 중간 결과 CTE 시작
    SELECT p.product_id,
           p.product_name,
           COALESCE((                              -- 매출이 없으면 NULL 대신 0
               SELECT SUM(oi.line_total)           -- 제품별 주문상품 금액 합산
               FROM ecom.order_items oi
               JOIN ecom.orders o ON o.order_id = oi.order_id
               WHERE oi.product_id = p.product_id
                 AND o.order_status IN ('paid', 'shipped', 'delivered')
           ), 0) AS revenue
    FROM ecom.products p
), ranked AS (                                     -- 매출 결과에 순위를 붙이는 두 번째 CTE
    SELECT product_id,
           product_name,
           revenue,
           RANK() OVER (ORDER BY revenue DESC) AS revenue_rank -- 매출 내림차순 공동 순위
    FROM product_revenue
    WHERE revenue > 0
)
SELECT product_id, product_name, ROUND(revenue, 2) AS revenue, revenue_rank
FROM ranked
WHERE revenue_rank <= 20                           -- 순위가 20위 이내인 제품만 표시
ORDER BY revenue_rank, product_id;

WITH product_revenue AS (                          -- [②] 실제 제품별 매출 순위 조회
    SELECT p.product_id,
           p.product_name,
           COALESCE((
               SELECT SUM(oi.line_total)
               FROM ecom.order_items oi
               JOIN ecom.orders o ON o.order_id = oi.order_id
               WHERE oi.product_id = p.product_id
                 AND o.order_status IN ('paid', 'shipped', 'delivered')
           ), 0) AS revenue
    FROM ecom.products p
), ranked AS (
    SELECT product_id, product_name, revenue,
           RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
    FROM product_revenue
    WHERE revenue > 0
)
SELECT product_id, product_name, ROUND(revenue, 2) AS revenue, revenue_rank
FROM ranked
WHERE revenue_rank <= 20
ORDER BY revenue_rank, product_id;

-- =========================================================
-- Q5. 고객별 RFM
-- 문제점: 고객마다 최근 구매·빈도·금액을 각각 다시 조회한다.
-- 화면에는 M(금액) 상위 20명만 표시한다.
-- 의미: Recency=최근 구매 후 경과일, Frequency=구매 빈도, Monetary=구매 금액이다.
-- =========================================================
-- [① 실행계획 확인용] 고객별 반복 서브쿼리와 loops 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                 -- 고객별 반복 서브쿼리 비용 측정
SELECT c.customer_id,
       c.full_name,
       CURRENT_DATE - (                            -- 오늘에서 최근 구매일을 빼 경과일 계산
           SELECT MAX(o.order_ts)::date            -- 고객의 가장 최근 실구매일
           FROM ecom.orders o
           WHERE o.customer_id = c.customer_id
             AND o.order_status IN ('paid', 'shipped', 'delivered')
       ) AS recency_days,                          -- R: 최근 구매 후 경과일
       (
           SELECT COUNT(o.order_id)                -- 고객의 실구매 주문번호 수
           FROM ecom.orders o
           WHERE o.customer_id = c.customer_id
             AND o.order_status IN ('paid', 'shipped', 'delivered')
       ) AS frequency,                             -- F: 구매 빈도
       (
           SELECT COALESCE(SUM(oi.line_total), 0)  -- 고객의 주문상품 총매출
           FROM ecom.orders o
           JOIN ecom.order_items oi ON oi.order_id = o.order_id
           WHERE o.customer_id = c.customer_id
             AND o.order_status IN ('paid', 'shipped', 'delivered')
       ) AS monetary                               -- M: 구매 금액
FROM ecom.customers c
WHERE EXISTS (                                     -- 실구매 이력이 있는 고객만 포함
    SELECT 1
    FROM ecom.orders o
    WHERE o.customer_id = c.customer_id
      AND o.order_status IN ('paid', 'shipped', 'delivered')
)
ORDER BY monetary DESC, c.customer_id
LIMIT 20;

SELECT c.customer_id,                              -- [②] 실제 고객별 RFM 결과 조회
       c.full_name,
       CURRENT_DATE - (
           SELECT MAX(o.order_ts)::date FROM ecom.orders o
           WHERE o.customer_id = c.customer_id
             AND o.order_status IN ('paid', 'shipped', 'delivered')
       ) AS recency_days,
       (
           SELECT COUNT(o.order_id) FROM ecom.orders o
           WHERE o.customer_id = c.customer_id
             AND o.order_status IN ('paid', 'shipped', 'delivered')
       ) AS frequency,
       (
           SELECT COALESCE(SUM(oi.line_total), 0)
           FROM ecom.orders o
           JOIN ecom.order_items oi ON oi.order_id = o.order_id
           WHERE o.customer_id = c.customer_id
             AND o.order_status IN ('paid', 'shipped', 'delivered')
       ) AS monetary
FROM ecom.customers c
WHERE EXISTS (
    SELECT 1 FROM ecom.orders o
    WHERE o.customer_id = c.customer_id
      AND o.order_status IN ('paid', 'shipped', 'delivered')
)
ORDER BY monetary DESC, c.customer_id
LIMIT 20;

-- =========================================================
-- Q6. 첫 구매 후 30일 내 재구매율
-- 문제점: 고객별 첫 구매를 구한 뒤 각 고객마다 EXISTS 서브플랜을 실행한다.
-- =========================================================
-- [① 실행계획 확인용] 고객별 EXISTS 반복 탐색 비용 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                 -- EXISTS 반복 탐색 비용 측정
WITH first_purchase AS (                           -- 고객별 첫 구매시각 CTE
    SELECT customer_id, MIN(order_ts) AS first_ts  -- MIN으로 최초 구매시각 계산
    FROM ecom.orders
    WHERE order_status IN ('paid', 'shipped', 'delivered')
    GROUP BY customer_id
)
SELECT COUNT(fp.customer_id) AS purchasing_customers,
       COUNT(fp.customer_id) FILTER (WHERE EXISTS ( -- 30일 내 추가 주문이 있는 고객만 계산
           SELECT 1
           FROM ecom.orders o2
           WHERE o2.customer_id = fp.customer_id
             AND o2.order_status IN ('paid', 'shipped', 'delivered')
             AND o2.order_ts > fp.first_ts
             AND o2.order_ts <= fp.first_ts + INTERVAL '30 days' -- 첫 구매 후 30일까지
       )) AS repurchased_customers,
       ROUND(100.0 * COUNT(fp.customer_id) FILTER (WHERE EXISTS (
           SELECT 1
           FROM ecom.orders o3
           WHERE o3.customer_id = fp.customer_id
             AND o3.order_status IN ('paid', 'shipped', 'delivered')
             AND o3.order_ts > fp.first_ts
             AND o3.order_ts <= fp.first_ts + INTERVAL '30 days'
       )) / NULLIF(COUNT(fp.customer_id), 0), 2) AS repurchase_rate_pct -- 0 나누기 방지 후 재구매율 계산
FROM first_purchase fp;

WITH first_purchase AS (                           -- [②] 실제 재구매율 결과 조회
    SELECT customer_id, MIN(order_ts) AS first_ts
    FROM ecom.orders
    WHERE order_status IN ('paid', 'shipped', 'delivered')
    GROUP BY customer_id
)
SELECT COUNT(fp.customer_id) AS purchasing_customers,
       COUNT(fp.customer_id) FILTER (WHERE EXISTS (
           SELECT 1 FROM ecom.orders o2
           WHERE o2.customer_id = fp.customer_id
             AND o2.order_status IN ('paid', 'shipped', 'delivered')
             AND o2.order_ts > fp.first_ts
             AND o2.order_ts <= fp.first_ts + INTERVAL '30 days'
       )) AS repurchased_customers,
       ROUND(100.0 * COUNT(fp.customer_id) FILTER (WHERE EXISTS (
           SELECT 1 FROM ecom.orders o3
           WHERE o3.customer_id = fp.customer_id
             AND o3.order_status IN ('paid', 'shipped', 'delivered')
             AND o3.order_ts > fp.first_ts
             AND o3.order_ts <= fp.first_ts + INTERVAL '30 days'
       )) / NULLIF(COUNT(fp.customer_id), 0), 2) AS repurchase_rate_pct
FROM first_purchase fp;

-- =========================================================
-- Q7. 재고가 재주문 임계치보다 낮은 상품
-- 문제점: 각 행마다 같은 inventory 행의 임계치를 상관 조회한다.
-- =========================================================
-- [① 실행계획 확인용] inventory 반복 조회와 Scan 방식 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                 -- 재고 테이블 접근 방식과 비용 측정
SELECT p.product_id, p.sku, p.product_name,
       i.qty_on_hand, i.reorder_point,              -- 현재고와 재주문 기준 수량
       i.reorder_point - i.qty_on_hand AS shortage_qty -- 보충이 필요한 부족수량
FROM ecom.products p
JOIN ecom.inventory i ON i.product_id = p.product_id
WHERE i.qty_on_hand < (                             -- 현재고가 재주문 기준보다 낮은 행
    SELECT MAX(i2.reorder_point)                    -- 같은 재고행의 기준을 다시 조회
    FROM ecom.inventory i2
    WHERE i2.product_id = i.product_id
)
ORDER BY shortage_qty DESC, p.product_id
LIMIT 20;

SELECT p.product_id, p.sku, p.product_name,         -- [②] 실제 부족 재고 상품 조회
       i.qty_on_hand, i.reorder_point,
       i.reorder_point - i.qty_on_hand AS shortage_qty
FROM ecom.products p
JOIN ecom.inventory i ON i.product_id = p.product_id
WHERE i.qty_on_hand < (
    SELECT MAX(i2.reorder_point) FROM ecom.inventory i2
    WHERE i2.product_id = i.product_id
)
ORDER BY shortage_qty DESC, p.product_id
LIMIT 20;

-- =========================================================
-- Q8. 평점 4.5 이상, 리뷰 50개 이상 효자상품
-- 문제점: 상품마다 AVG와 COUNT를 SELECT와 WHERE에서 반복 계산한다.
-- =========================================================
-- [① 실행계획 확인용] 제품별 리뷰 반복 집계 횟수 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                 -- 반복되는 리뷰 서브쿼리 비용 측정
SELECT p.product_id,
       p.product_name,
       ROUND((SELECT AVG(r.rating) FROM ecom.reviews r
              WHERE r.product_id = p.product_id), 2) AS avg_rating, -- 제품별 평균평점
       (SELECT COUNT(r.review_id) FROM ecom.reviews r
        WHERE r.product_id = p.product_id) AS review_count -- 제품별 리뷰 수
FROM ecom.products p
WHERE (SELECT AVG(r.rating) FROM ecom.reviews r     -- 평균평점을 다시 계산
       WHERE r.product_id = p.product_id) >= 4.5
  AND (SELECT COUNT(r.review_id) FROM ecom.reviews r -- 리뷰 수를 다시 계산
       WHERE r.product_id = p.product_id) >= 50
ORDER BY avg_rating DESC, review_count DESC, p.product_id;

SELECT p.product_id,                               -- [②] 실제 효자상품 결과 조회
       p.product_name,
       ROUND((SELECT AVG(r.rating) FROM ecom.reviews r
              WHERE r.product_id = p.product_id), 2) AS avg_rating,
       (SELECT COUNT(r.review_id) FROM ecom.reviews r
        WHERE r.product_id = p.product_id) AS review_count
FROM ecom.products p
WHERE (SELECT AVG(r.rating) FROM ecom.reviews r
       WHERE r.product_id = p.product_id) >= 4.5
  AND (SELECT COUNT(r.review_id) FROM ecom.reviews r
       WHERE r.product_id = p.product_id) >= 50
ORDER BY avg_rating DESC, review_count DESC, p.product_id;

-- =========================================================
-- Q9. 쿠폰 사용 여부별 평균 주문금액
-- 문제점: 상세 행 조인 후 COUNT(DISTINCT)로 주문 수를 복원한다.
-- 의미: AOV는 전체 매출을 중복 없는 주문 수로 나눈 주문당 평균금액이다.
-- =========================================================
-- [① 실행계획 확인용] 상세행 조인과 DISTINCT 집계 비용 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                 -- 상세행 조인과 중복 제거 비용 측정
SELECT CASE WHEN o.coupon_code IS NULL THEN '미사용' ELSE '사용' END AS coupon_group, -- 쿠폰 여부 분류
       COUNT(DISTINCT o.order_id) AS order_count,   -- 중복을 제거한 주문 수
       ROUND(SUM(oi.line_total) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS aov -- 주문당 평균금액
FROM ecom.orders o
JOIN ecom.order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('paid', 'shipped', 'delivered')
GROUP BY 1
ORDER BY 1;

SELECT CASE WHEN o.coupon_code IS NULL THEN '미사용' ELSE '사용' END AS coupon_group, -- [②] 실제 비교 결과
       COUNT(DISTINCT o.order_id) AS order_count,
       ROUND(SUM(oi.line_total) / NULLIF(COUNT(DISTINCT o.order_id), 0), 2) AS aov
FROM ecom.orders o
JOIN ecom.order_items oi ON oi.order_id = o.order_id
WHERE o.order_status IN ('paid', 'shipped', 'delivered')
GROUP BY 1
ORDER BY 1;

-- =========================================================
-- Q10. 누적매출 상위 1% 고객의 최근 60일 매출
-- 문제점: 3,000명 각각의 누적매출을 상관 서브쿼리로 계산하고,
--         선정된 상위 30명의 최근 60일 매출도 다시 상관 조회한다.
-- 기준: 전체 고객 3,000명의 누적매출로 정확히 30명을 먼저 선정한다.
-- 주의: 누적매출로 30명을 먼저 선정한 다음, 그 고객들의 최근 60일 매출을 표시한다.
-- =========================================================
-- [① 실행계획 확인용] 고객별 반복 집계와 최근 60일 SubPlan 비용 확인
EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                 -- 고객별 반복 집계 비용 측정
WITH lifetime_sales AS (                           -- 고객별 누적매출 CTE
    SELECT c.customer_id,
           c.full_name,
           (
               SELECT COALESCE(SUM(oi.line_total), 0) -- 고객 한 명의 누적매출 계산
               FROM ecom.orders o
               JOIN ecom.order_items oi ON oi.order_id = o.order_id
               WHERE o.customer_id = c.customer_id
                 AND o.order_status IN ('paid', 'shipped', 'delivered')
           ) AS lifetime_revenue
    FROM ecom.customers c
), ranked AS (                                     -- 누적매출 순위 계산 CTE
    SELECT customer_id,
           full_name,
           lifetime_revenue,
           ROW_NUMBER() OVER (                     -- 중복 없는 순번을 1부터 부여
               ORDER BY lifetime_revenue DESC, customer_id
           ) AS lifetime_rank,
           COUNT(customer_id) OVER () AS customer_count -- 전체 고객 수를 각 행에 표시
    FROM lifetime_sales
)
SELECT r.customer_id,
       r.full_name,
       r.lifetime_rank,
       ROUND(r.lifetime_revenue, 2) AS lifetime_revenue,
       ROUND((
           SELECT COALESCE(SUM(oi.line_total), 0)
           FROM ecom.orders o
           JOIN ecom.order_items oi ON oi.order_id = o.order_id
           WHERE o.customer_id = r.customer_id
             AND o.order_status IN ('paid', 'shipped', 'delivered')
             AND o.order_ts >= now() - INTERVAL '60 days' -- 선정 고객의 최근 60일 매출
       ), 2) AS revenue_60d
FROM ranked r
WHERE r.lifetime_rank <= CEIL(r.customer_count * 0.01) -- 전체 고객의 상위 1%, 정확히 30명
ORDER BY r.lifetime_rank;

WITH lifetime_sales AS (                           -- [②] 실제 상위 30명 결과 조회
    SELECT c.customer_id, c.full_name,
           (
               SELECT COALESCE(SUM(oi.line_total), 0)
               FROM ecom.orders o
               JOIN ecom.order_items oi ON oi.order_id = o.order_id
               WHERE o.customer_id = c.customer_id
                 AND o.order_status IN ('paid', 'shipped', 'delivered')
           ) AS lifetime_revenue
    FROM ecom.customers c
), ranked AS (
    SELECT customer_id, full_name, lifetime_revenue,
           ROW_NUMBER() OVER (
               ORDER BY lifetime_revenue DESC, customer_id
           ) AS lifetime_rank,
           COUNT(customer_id) OVER () AS customer_count
    FROM lifetime_sales
)
SELECT r.customer_id, r.full_name, r.lifetime_rank,
       ROUND(r.lifetime_revenue, 2) AS lifetime_revenue,
       ROUND((
           SELECT COALESCE(SUM(oi.line_total), 0)
           FROM ecom.orders o
           JOIN ecom.order_items oi ON oi.order_id = o.order_id
           WHERE o.customer_id = r.customer_id
             AND o.order_status IN ('paid', 'shipped', 'delivered')
             AND o.order_ts >= now() - INTERVAL '60 days'
       ), 2) AS revenue_60d
FROM ranked r
WHERE r.lifetime_rank <= CEIL(r.customer_count * 0.01)
ORDER BY r.lifetime_rank;
