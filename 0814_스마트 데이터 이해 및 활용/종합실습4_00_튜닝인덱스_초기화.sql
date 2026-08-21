-- 종합실습 4: 튜닝 전 실행계획 재현용
-- 아래 인덱스만 제거하며, 교재 원본 스키마의 인덱스는 보존한다.

SET search_path = ecom, public;

DROP INDEX IF EXISTS ecom.idx_orders_sales_ts_order;
DROP INDEX IF EXISTS ecom.idx_orders_sales_customer_ts_order;
DROP INDEX IF EXISTS ecom.idx_order_items_order_cover;
DROP INDEX IF EXISTS ecom.idx_order_items_product_cover;
DROP INDEX IF EXISTS ecom.idx_reviews_product_rating_cover;
DROP INDEX IF EXISTS ecom.idx_inventory_low_stock;

ANALYZE ecom.orders;
ANALYZE ecom.order_items;
ANALYZE ecom.reviews;
ANALYZE ecom.inventory;

