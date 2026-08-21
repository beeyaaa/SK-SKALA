-- 종합실습 4: 일별 GMV Materialized View 생성·조회·갱신
--
-- [목적]
-- orders와 order_items를 매번 조인·집계하지 않고 일별 결과를 미리 저장하여 빠르게 조회한다.
-- 일반 View는 조회할 때마다 원본 쿼리를 실행하지만 Materialized View는 계산 결과를 실제로 저장한다.
-- 저장된 결과는 원본 테이블이 변경돼도 자동으로 바뀌지 않으므로 REFRESH가 필요하다.
--
-- [GMV 정의]
-- paid, shipped, delivered 상태의 주문에 포함된 order_items.line_total 합계이다.
-- cancelled, refunded, created 상태의 주문은 매출에서 제외한다.
--
-- [실행 및 캡처 순서]
-- ① DROP부터 ANALYZE까지 실행: MV 생성, UNIQUE 인덱스 생성, 최초 데이터 적재
-- ② 원본 테이블 집계 EXPLAIN 실행: 조인·집계 비용과 Execution Time 캡처
-- ③ MV 조회 EXPLAIN 실행: 저장된 결과 조회 비용과 Execution Time 캡처
-- ④ 실제 MV SELECT 실행: 일별 주문 수와 GMV 결과 캡처
-- ⑤ CONCURRENTLY REFRESH 실행: 갱신 성공 화면 캡처

SET search_path = ecom, public;                    -- 스키마 생략 시 ecom을 먼저 찾고 그다음 public 탐색

-- =========================================================
-- 1. 기존 Materialized View 제거
-- =========================================================
-- 같은 이름의 MV가 이미 존재해도 재실행할 수 있도록 먼저 제거한다.
-- IF EXISTS를 사용하므로 MV가 없어도 오류가 아니라 안내 메시지만 출력된다.

DROP MATERIALIZED VIEW IF EXISTS ecom.mv_daily_gmv; -- 기존 MV와 그 MV에 속한 인덱스를 함께 제거

-- =========================================================
-- 2. 일별 GMV Materialized View 생성
-- =========================================================
-- WITH NO DATA로 구조와 정의만 먼저 생성하고 데이터는 뒤의 REFRESH에서 적재한다.

CREATE MATERIALIZED VIEW ecom.mv_daily_gmv AS      -- 일별 집계 결과를 저장할 MV 생성 시작
SELECT date_trunc('day', o.order_ts)::date AS sales_day, -- 주문시각을 일 단위로 자르고 date 형식으로 변환
       COUNT(DISTINCT o.order_id) AS order_count,  -- 주문상품 조인으로 중복된 주문번호를 제거한 일별 주문 수
       ROUND(SUM(oi.line_total), 2) AS gmv         -- 주문상품 금액의 일별 합계를 소수점 둘째 자리로 표시
FROM ecom.orders o                                 -- 주문일시·주문상태가 저장된 주문 테이블
JOIN ecom.order_items oi                           -- 상품별 판매금액이 저장된 주문상품 테이블
  ON oi.order_id = o.order_id                      -- 주문번호가 같은 주문과 주문상품을 연결
WHERE o.order_status IN ('paid', 'shipped', 'delivered') -- 실제 매출로 인정하는 상태만 포함
GROUP BY date_trunc('day', o.order_ts)::date       -- 같은 날짜의 주문상품 금액을 한 행으로 집계
WITH NO DATA;                                      -- 생성 시에는 데이터를 넣지 않고 빈 구조만 생성

-- =========================================================
-- 3. 동시 갱신을 위한 UNIQUE 인덱스 생성
-- =========================================================
-- REFRESH MATERIALIZED VIEW CONCURRENTLY를 사용하려면 모든 행을 유일하게 식별할 수 있어야 한다.
-- 이 MV는 날짜별로 한 행만 존재하므로 sales_day를 고유키로 사용한다.

CREATE UNIQUE INDEX ux_mv_daily_gmv_sales_day      -- MV의 날짜 중복을 금지하는 UNIQUE 인덱스 이름
    ON ecom.mv_daily_gmv (sales_day);              -- 날짜 한 개가 MV의 각 행을 유일하게 식별

-- =========================================================
-- 4. 최초 데이터 적재 및 통계정보 수집
-- =========================================================
-- WITH NO DATA로 만들었으므로 최초 1회는 일반 REFRESH로 데이터를 채워야 한다.
-- 빈 MV에는 CONCURRENTLY를 바로 사용할 수 없으므로 먼저 일반 REFRESH를 실행한다.

REFRESH MATERIALIZED VIEW ecom.mv_daily_gmv;       -- MV 정의 쿼리를 실행하여 일별 결과를 실제로 저장
ANALYZE ecom.mv_daily_gmv;                         -- MV의 행 수와 값 분포 통계를 수집하여 실행계획 선택에 활용

-- =========================================================
-- 5. 원본 테이블을 직접 조인·집계하는 실행계획
-- =========================================================
-- 비교 기준이 되는 원본 쿼리이다.
-- orders와 order_items를 읽고 Join, Aggregate, Sort를 수행하므로 MV 조회보다 작업량이 많을 수 있다.
-- 캡처할 값: 최상위 Buffers, Planning Time, Execution Time, Join/Aggregate 노드

EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                -- 원본 쿼리를 실제 실행하여 버퍼와 실행시간 측정
SELECT date_trunc('day', o.order_ts)::date AS sales_day, -- 주문일을 일 단위로 변환
       COUNT(DISTINCT o.order_id) AS order_count,  -- 조인 후 중복을 제거한 일별 주문 수
       ROUND(SUM(oi.line_total), 2) AS gmv         -- 일별 총 상품 판매금액
FROM ecom.orders o                                 -- 원본 주문 테이블 읽기
JOIN ecom.order_items oi                           -- 원본 주문상품 테이블 읽기
  ON oi.order_id = o.order_id                      -- 주문번호를 기준으로 원본 테이블 두 개 조인
WHERE o.order_status IN ('paid', 'shipped', 'delivered') -- 실매출 상태만 집계
GROUP BY date_trunc('day', o.order_ts)::date       -- 날짜별로 주문 수와 GMV 계산
ORDER BY sales_day DESC                            -- 가장 최근 날짜부터 정렬
LIMIT 30;                                          -- 최근 30개 날짜만 출력

-- =========================================================
-- 6. Materialized View 조회 실행계획
-- =========================================================
-- 이미 계산되어 저장된 sales_day, order_count, gmv만 읽는다.
-- 원본 테이블 조인과 GROUP BY가 사라지는지 원본 실행계획과 비교한다.
-- 캡처할 값: Scan 방식, 최상위 Buffers, Planning Time, Execution Time

EXPLAIN (ANALYZE, BUFFERS, SUMMARY)                -- MV 조회를 실제 실행하여 버퍼와 실행시간 측정
SELECT sales_day,                                  -- MV에 저장된 매출 날짜
       order_count,                                -- MV에 저장된 일별 주문 수
       gmv                                         -- MV에 저장된 일별 GMV
FROM ecom.mv_daily_gmv                             -- 원본 조인 대신 사전 집계된 MV만 조회
ORDER BY sales_day DESC                            -- 가장 최근 날짜부터 정렬
LIMIT 30;                                          -- 최근 30개 날짜만 출력

-- =========================================================
-- 7. Materialized View 실제 결과 확인
-- =========================================================
-- EXPLAIN 없이 실행하여 구매·재무팀에 전달할 실제 일별 결과를 확인한다.

SELECT sales_day,                                  -- 일별 매출 기준 날짜
       order_count,                                -- 해당 날짜의 중복 없는 실매출 주문 수
       gmv                                         -- 해당 날짜의 주문상품 총매출
FROM ecom.mv_daily_gmv                             -- 미리 저장된 일별 집계 결과 조회
ORDER BY sales_day DESC                            -- 최근 날짜부터 표시
LIMIT 30;                                          -- 최근 30일분 결과 표시

-- =========================================================
-- 8. 서비스 조회를 유지하면서 Materialized View 갱신
-- =========================================================
-- CONCURRENTLY는 갱신 중에도 기존 MV에 대한 일반 조회를 가능하게 한다.
-- 이 명령을 사용하려면 위에서 생성한 UNIQUE 인덱스가 반드시 존재해야 한다.
-- 원본 데이터 변경분을 증분 반영하는 방식이 아니라 MV 전체 결과를 다시 계산한다.

REFRESH MATERIALIZED VIEW CONCURRENTLY ecom.mv_daily_gmv; -- 조회 잠금을 줄이면서 최신 원본 데이터로 갱신

-- =========================================================
-- 9. 오후 3시 자동 갱신 설계 예시(선택사항)
-- =========================================================
-- pg_cron 확장 기능이 설치된 PostgreSQL 환경에서만 사용할 수 있다.
-- 로컬 환경에 pg_cron이 없다면 아래 코드는 주석 상태로 두고 실행하지 않는다.

-- CREATE EXTENSION IF NOT EXISTS pg_cron;         -- pg_cron 확장이 없으면 생성
-- SELECT cron.schedule(                            -- 정해진 시각에 실행할 작업 등록
--     'refresh-ecom-daily-gmv-1500',               -- 스케줄 작업을 식별하는 고유 이름
--     '0 15 * * *',                                -- 매일 15시 00분에 실행하는 cron 표현식
--     $$REFRESH MATERIALIZED VIEW CONCURRENTLY ecom.mv_daily_gmv$$ -- 자동 실행할 갱신 명령
-- );

-- 등록 확인 예시
-- SELECT jobid, schedule, command
-- FROM cron.job;

-- 등록한 작업 해제 예시
-- SELECT cron.unschedule('refresh-ecom-daily-gmv-1500');
