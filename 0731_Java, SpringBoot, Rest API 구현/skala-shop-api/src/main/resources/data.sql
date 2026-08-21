-- Fashion product seed data. Existing names are not inserted again on restart.
INSERT INTO product (product_name, product_price)
SELECT '오버핏 블레이저', 129000
WHERE NOT EXISTS (
    SELECT 1 FROM product WHERE product_name = '오버핏 블레이저'
);

INSERT INTO product (product_name, product_price)
SELECT '클래식 코튼 셔츠', 59000
WHERE NOT EXISTS (
    SELECT 1 FROM product WHERE product_name = '클래식 코튼 셔츠'
);

INSERT INTO product (product_name, product_price)
SELECT '와이드 데님 팬츠', 79000
WHERE NOT EXISTS (
    SELECT 1 FROM product WHERE product_name = '와이드 데님 팬츠'
);

INSERT INTO product (product_name, product_price)
SELECT '레더 미니백', 89000
WHERE NOT EXISTS (
    SELECT 1 FROM product WHERE product_name = '레더 미니백'
);

INSERT INTO product (product_name, product_price)
SELECT '러닝 스니커즈', 109000
WHERE NOT EXISTS (
    SELECT 1 FROM product WHERE product_name = '러닝 스니커즈'
);
