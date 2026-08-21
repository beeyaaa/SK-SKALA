-- 종합실습 4: Q1~Q10 공통 튜닝 인덱스
-- 실매출 주문만 대상으로 하는 부분 인덱스로 크기와 유지 비용을 줄인다.

SET search_path = ecom, public;

CREATE INDEX IF NOT EXISTS idx_orders_sales_ts_order
    ON ecom.orders (order_ts, order_id)
    INCLUDE (customer_id, coupon_code)
    WHERE order_status IN ('paid', 'shipped', 'delivered');

-- RFM/재구매 분석은 고객별 구매시각 순서가 핵심이다.
CREATE INDEX IF NOT EXISTS idx_orders_sales_customer_ts_order
    ON ecom.orders (customer_id, order_ts, order_id)
    INCLUDE (coupon_code)
    WHERE order_status IN ('paid', 'shipped', 'delivered');

-- 주문 단위 선집계 시 heap 접근을 줄이기 위한 커버링 인덱스다.
CREATE INDEX IF NOT EXISTS idx_order_items_order_cover
    ON ecom.order_items (order_id)
    INCLUDE (product_id, line_total);

-- 제품/카테고리 매출 집계를 위한 반대 방향 커버링 인덱스다.
CREATE INDEX IF NOT EXISTS idx_order_items_product_cover
    ON ecom.order_items (product_id)
    INCLUDE (order_id, line_total);

-- 상품별 리뷰 건수와 평균 평점을 index-only scan으로 계산할 수 있다.
CREATE INDEX IF NOT EXISTS idx_reviews_product_rating_cover
    ON ecom.reviews (product_id)
    INCLUDE (rating);

-- 부족 재고만 담는 작은 부분 인덱스다.
CREATE INDEX IF NOT EXISTS idx_inventory_low_stock
    ON ecom.inventory (product_id)
    INCLUDE (qty_on_hand, reorder_point)
    WHERE qty_on_hand < reorder_point;

ANALYZE ecom.orders;
ANALYZE ecom.order_items;
ANALYZE ecom.reviews;
ANALYZE ecom.inventory;

