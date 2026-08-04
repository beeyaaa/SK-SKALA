-- 초기 사용자 데이터
INSERT INTO users (username, password, email, balance, created_at, updated_at) VALUES
('user1', 'password1', 'user1@example.com', 1000000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('user2', 'password2', 'user2@example.com', 2000000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('user3', 'password3', 'user3@example.com', 3000000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- 초기 주식 데이터
INSERT INTO stocks (code, name, current_price, previous_price, created_at, updated_at) VALUES
('005930', '삼성전자', 70000, 69000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('000660', 'SK하이닉스', 120000, 118000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('035420', 'NAVER', 200000, 195000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('035720', '카카오', 50000, 48000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('051910', 'LG화학', 450000, 440000, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
