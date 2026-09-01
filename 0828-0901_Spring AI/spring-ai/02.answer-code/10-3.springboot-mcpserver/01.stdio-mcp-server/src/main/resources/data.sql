-- User 초기 데이터
INSERT INTO users (id, name, email, created_at, updated_at) VALUES
(1, 'John Smith', 'john.smith@gmail.com', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2, 'Sarah Johnson', 'sarah.johnson@gmail.com', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(3, 'Michael Brown', 'michael.brown@gmail.com', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(4, 'Emily Davis', 'emily.davis@gmail.com', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(5, 'David Wilson', 'david.wilson@gmail.com', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Product 초기 데이터
INSERT INTO products (id, name, description, price, stock, created_at, updated_at) VALUES
(1, 'Laptop', 'High-performance laptop with 16GB RAM and 512GB SSD', 1299.99, 25, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2, 'Wireless Mouse', 'Ergonomic wireless mouse with USB receiver', 29.99, 150, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(3, 'Mechanical Keyboard', 'RGB mechanical keyboard with Cherry MX switches', 149.99, 80, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(4, 'Monitor', '27-inch 4K UHD monitor with HDR support', 399.99, 45, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(5, 'USB-C Hub', '7-in-1 USB-C hub with HDMI, USB 3.0, and SD card reader', 49.99, 200, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
