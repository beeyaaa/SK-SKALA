-- 종합실습 4: PostgreSQL의 3가지 물리 조인 비교
-- 목적: 동일한 업무 쿼리를 NLJ, Hash Join, Merge Join으로 각각 실행하여
--       처리 방식, Buffers, Execution Time의 차이를 비교한다.
-- 주의: enable_* 설정은 교육용으로 실행계획을 강제하기 위한 것이다.
--       운영 환경에서는 특정 조인을 강제하지 않고 옵티마이저의 선택에 맡기는 것이 일반적이다.
--
-- [캡처할 항목]
-- ① 실행계획 안의 Nested Loop / Hash Join / Merge Join 문구
-- ② 최상위 노드의 Buffers: shared hit, read 값
-- ③ 실행계획 하단의 Planning Time과 Execution Time
-- ④ Settings에 표시된 비활성화 설정

SET search_path = ecom, public;                    -- 객체 이름 앞에 스키마를 생략하면 ecom을 먼저 탐색

-- 공통 업무 질의
-- 최근 30일 동안 paid, shipped, delivered 상태인 주문과 주문상품을 연결하여 총매출을 계산한다.
-- 세 테스트는 업무 로직과 결과가 같고, 물리적인 조인 방식만 다르다.

-- =========================================================
-- 1. Nested Loop Join(NLJ)
-- =========================================================
-- 처리 방식: 바깥쪽 입력의 각 행마다 안쪽 입력에서 일치하는 행을 반복해서 찾는다.
-- 유리한 조건: 바깥쪽 결과가 작고, 안쪽 조인 키에 인덱스가 있을 때 유리하다.
-- 확인할 실행계획: Nested Loop와 안쪽의 Index Scan 또는 Index Only Scan

BEGIN;                                             -- SET LOCAL이 현재 테스트에만 적용되도록 트랜잭션 시작
SET LOCAL enable_hashjoin = off;                   -- Hash Join 후보를 비활성화
SET LOCAL enable_mergejoin = off;                  -- Merge Join 후보를 비활성화
SET LOCAL enable_nestloop = on;                    -- Nested Loop Join 후보만 활성화

EXPLAIN (ANALYZE, BUFFERS, SETTINGS, SUMMARY)      -- 실제 실행시간·버퍼·변경 설정·요약을 함께 출력
SELECT ROUND(SUM(oi.line_total), 2) AS total_sales_30d -- 주문상품 금액을 합산하고 소수점 둘째 자리까지 표시
FROM ecom.orders o                                 -- 주문 헤더 테이블, 별칭 o
JOIN ecom.order_items oi                           -- 주문별 상품과 금액이 저장된 상세 테이블, 별칭 oi
  ON oi.order_id = o.order_id                      -- 주문번호가 같은 주문과 주문상품을 연결하는 동등 조인
WHERE o.order_status IN ('paid', 'shipped', 'delivered') -- 실제 매출로 인정하는 주문 상태만 포함
  AND o.order_ts >= CURRENT_DATE - 30;             -- 오늘을 기준으로 최근 30일 주문만 조회

ROLLBACK;                                          -- 설정 변경을 취소하여 다음 조인 테스트에 영향을 주지 않음

-- =========================================================
-- 2. Hash Join
-- =========================================================
-- 처리 방식: 작은 입력의 조인 키로 메모리에 해시 테이블을 만들고 큰 입력의 키를 대조한다.
-- 유리한 조건: 정렬되지 않은 대량 데이터의 동등 조인이고 해시 테이블이 메모리에 들어갈 때 유리하다.
-- 확인할 실행계획: Hash Join, Hash, Hash Cond

BEGIN;                                             -- Hash Join 테스트용 독립 트랜잭션 시작
SET LOCAL enable_hashjoin = on;                    -- Hash Join 후보 활성화
SET LOCAL enable_mergejoin = off;                  -- Merge Join 후보 비활성화
SET LOCAL enable_nestloop = off;                   -- Nested Loop Join 후보 비활성화

EXPLAIN (ANALYZE, BUFFERS, SETTINGS, SUMMARY)      -- 실제 Hash Join 계획과 실행 통계 출력
SELECT ROUND(SUM(oi.line_total), 2) AS total_sales_30d -- 세 조인에서 동일해야 하는 최근 30일 총매출
FROM ecom.orders o                                 -- 필터 조건을 가진 주문 테이블
JOIN ecom.order_items oi                           -- 주문에 속한 상품별 금액 테이블
  ON oi.order_id = o.order_id                      -- Hash Cond로 사용할 주문번호 동등 조건
WHERE o.order_status IN ('paid', 'shipped', 'delivered') -- 취소·환불·생성 상태를 매출에서 제외
  AND o.order_ts >= CURRENT_DATE - 30;             -- 최근 30일 범위만 남겨 조인 대상 축소

ROLLBACK;                                          -- Hash Join 강제 설정 해제

-- =========================================================
-- 3. Merge Join
-- =========================================================
-- 처리 방식: 양쪽 입력을 조인 키 순서로 정렬한 뒤 앞에서부터 순차적으로 비교한다.
-- 유리한 조건: 입력이 이미 조인 키로 정렬돼 있거나 정렬 비용이 낮은 대량 조인에 유리하다.
-- 확인할 실행계획: Merge Join, Merge Cond, 필요하면 Sort 노드

BEGIN;                                             -- Merge Join 테스트용 독립 트랜잭션 시작
SET LOCAL enable_hashjoin = off;                   -- Hash Join 후보 비활성화
SET LOCAL enable_mergejoin = on;                   -- Merge Join 후보 활성화
SET LOCAL enable_nestloop = off;                   -- Nested Loop Join 후보 비활성화

EXPLAIN (ANALYZE, BUFFERS, SETTINGS, SUMMARY)      -- 실제 Merge Join 계획과 실행 통계 출력
SELECT ROUND(SUM(oi.line_total), 2) AS total_sales_30d -- 동일한 총매출을 계산하여 결과의 일관성 확인
FROM ecom.orders o                                 -- 주문 테이블
JOIN ecom.order_items oi                           -- 주문상품 테이블
  ON oi.order_id = o.order_id                      -- Merge Cond로 사용할 주문번호 동등 조건
WHERE o.order_status IN ('paid', 'shipped', 'delivered') -- 실매출 상태만 포함
  AND o.order_ts >= CURRENT_DATE - 30;             -- 최근 30일 주문만 포함

ROLLBACK;                                          -- Merge Join 강제 설정 해제

-- =========================================================
-- 4. 옵티마이저 기본 선택 확인(참고용)
-- =========================================================
-- 세 조인 강제 설정을 기본값으로 되돌린 다음 PostgreSQL이 비용을 기준으로 선택한 계획을 확인한다.
-- 이 결과는 NLJ·Hash·Merge 비교표의 필수 캡처가 아니라 본인 환경의 결론 작성에 참고한다.

RESET enable_hashjoin;                             -- Hash Join 설정을 세션 기본값으로 복원
RESET enable_mergejoin;                            -- Merge Join 설정을 세션 기본값으로 복원
RESET enable_nestloop;                             -- Nested Loop Join 설정을 세션 기본값으로 복원

EXPLAIN (ANALYZE, BUFFERS, SETTINGS, SUMMARY)      -- 옵티마이저가 자유롭게 선택한 기본 실행계획 확인
SELECT ROUND(SUM(oi.line_total), 2) AS total_sales_30d -- 기본 계획의 최근 30일 총매출 계산
FROM ecom.orders o                                 -- 주문 테이블
JOIN ecom.order_items oi                           -- 주문상품 테이블
  ON oi.order_id = o.order_id                      -- 주문번호 기준 동등 조인
WHERE o.order_status IN ('paid', 'shipped', 'delivered') -- 실매출 상태만 포함
  AND o.order_ts >= CURRENT_DATE - 30;             -- 최근 30일 주문만 조회

-- 실행계획이 아닌 실제 결과값을 별도로 확인한다.
-- 아래 값은 세 물리 조인을 강제했을 때도 모두 동일해야 한다.
SELECT ROUND(SUM(oi.line_total), 2) AS total_sales_30d -- 리포트에 참고할 실제 최근 30일 총매출
FROM ecom.orders o                                 -- 주문 테이블
JOIN ecom.order_items oi                           -- 주문상품 테이블
  ON oi.order_id = o.order_id                      -- 주문번호로 주문상품 연결
WHERE o.order_status IN ('paid', 'shipped', 'delivered') -- 실제 판매 상태만 포함
  AND o.order_ts >= CURRENT_DATE - 30;             -- 오늘 기준 최근 30일만 조회
