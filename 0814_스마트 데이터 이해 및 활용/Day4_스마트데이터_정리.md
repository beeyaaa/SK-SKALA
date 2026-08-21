# ☁️ Day 4 — 스마트 데이터 이해 및 활용

> 💡 **Day 4 한 줄 요약**
> Day 1~3이 **"DB 한 대를 어떻게 잘 쓰나"** 였다면, Day 4는 **"DB를 어디에 두고, 어떻게 지키고, 어떻게 굴리나"**.
> 세 덩어리 — **DB 안에서 코드 돌리기(SP·Trigger)** · **DB를 클라우드로(Cloud·DW·트렌드)** · **운영(보안·백업·모니터링)**.

**출처** : AI 서비스를 위한 SW 기초 Full-stack Engineering (AI캠퍼스, 4일) > 4. 스마트 데이터 이해 및 활용 (백정열 / SK AX, 2026.6)
**범위** : 전체 482p 중 **Day 4 = 347~481p** (24~33장)

---

## 📑 Day 4 목차

| # | 장 | 부제 | 핵심 질문 |
|---|---|------|-----------|
| 24 | [Stored Procedure & 함수](#24-stored-procedure--함수) | 4개 DBMS 문법 · DETERMINISTIC/IMMUTABLE · 보안 모델 | DB 안에서 코드를 돌린다는 건? |
| 25 | [Trigger & 이벤트 처리](#25-trigger--이벤트-처리) | 감사 로그 · CDC · 배치 · 실행 순서 제어 | 자동으로 반응하게 하려면? |
| 26 | [Cloud DB 개요](#26-cloud-db-개요) | On-Prem vs DBaaS · RDS/Aurora · Cloud SQL · Azure | 어디에 DB를 둘 것인가? |
| 27 | [서버리스 & 분산 Cloud DB](#27-서버리스--분산-cloud-db) | Aurora Serverless v2 · Spanner · Cosmos · Neon | 서버를 아예 안 만질 수 있나? |
| 28 | [데이터 웨어하우스 & 분석 DB](#28-데이터-웨어하우스--분석-db) | OLTP vs OLAP · 프루닝 · 벡터화 · BigQuery | 분석용 DB는 왜 따로 있나? |
| 29 | [현재의 트렌드](#29-현재의-트렌드) | NewSQL · 시계열 · Vector DB · AI+DB · Edge | 지금 뭐가 뜨고 있나? |
| 30 | [보안 및 권한 관리](#30-보안-및-권한-관리) | 인증·인가·SQL Injection·암호화·RLS·감사 | 어떻게 지키나? |
| 31 | [백업·복구 & 고가용성](#31-백업복구--고가용성) | Full/Incremental/PITR · Replication · Failover | 죽으면 어떻게 살리나? |
| 32 | [모니터링 및 운영](#32-모니터링-및-운영) | TPS·QPS·Latency · Prometheus+Grafana | 아픈 걸 어떻게 미리 아나? |
| 33 | [종합실습 – 4](#33-종합실습--4) | ecommerce 매출 분석 (11문항) | 4일치를 한 번에 |

---

# 24. Stored Procedure & 함수

> 📌 **다루는 것** : 4개 DBMS 문법 · DETERMINISTIC/IMMUTABLE · 보안 모델 · 실무 포인트

## 24-1. ⭐ Stored Procedure vs 함수 — 뭐가 다른가

| 구분 | **Stored Procedure** | **함수 (Function, UDF)** |
|------|---------------------|-------------------------|
| **역할** | 여러 SQL문을 묶어 한 번에 실행 (**작업 절차**) | 계산해서 **결과값을 돌려주는** 함수 |
| **리턴값** | 있어도 되고 없어도 되고 | **반드시 1개 이상 결과 반환** |
| **호출 방법** | `CALL` 또는 `EXEC` | `SELECT fn_함수()` 형태 |
| **주 사용처** | 데이터 변경, 트랜잭션, **배치 작업** | **SELECT 안에서** 계산, 데이터 변환 |
| **트랜잭션 제어** | ✅ 가능 (`BEGIN`/`COMMIT`/`ROLLBACK`) | ❌ 불가능 (DML 금지) |
| **부작용(DML)** | ✅ INSERT/UPDATE/DELETE 가능 | ❌ 대부분 **읽기 전용** |
| **핵심 비유** | **작업 단위** (batch 작업 중심) | **계산 도구** (연산기) |

> 🔑 **한 줄 구분**
> **"값을 돌려주면 함수, 일을 시키면 프로시저"**

---

## 24-2. 함수 예시 — 4개 DBMS (부가세 10% 계산)

```sql
-- MySQL / MariaDB
CREATE FUNCTION fn_vat(amount DECIMAL(10,2))
RETURNS DECIMAL(10,2) DETERMINISTIC     -- 같은 입력 = 항상 같은 결과
BEGIN RETURN amount * 0.1; END;

SELECT order_id, fn_vat(total_amount) AS vat FROM orders;

-- PostgreSQL
CREATE OR REPLACE FUNCTION fn_vat(amount NUMERIC)
RETURNS NUMERIC LANGUAGE sql IMMUTABLE  -- IMMUTABLE: 인덱스 표현식에도 사용 가능
AS $$ SELECT amount * 0.1 $$;

CREATE INDEX idx_tax ON orders ((fn_vat(total_amount)));  -- 함수 기반 인덱스 가능!

-- SQL Server (인라인 테이블 함수 — 가장 빠름)
CREATE FUNCTION dbo.fn_vat(@amount DECIMAL(10,2))
RETURNS TABLE AS RETURN (SELECT @amount * 0.1 AS tax);

-- Oracle
CREATE OR REPLACE FUNCTION fn_vat(p_amount NUMBER)
RETURN NUMBER RESULT_CACHE DETERMINISTIC  -- 결과 메모리 캐시
IS BEGIN RETURN p_amount * 0.1; END;
/
```

> ✅ **키워드 요약**
> **MySQL** → `DETERMINISTIC` / **PostgreSQL** → `IMMUTABLE`·`STABLE`·`VOLATILE` / **Oracle** → `RESULT_CACHE`

---

## 24-3. ⭐ 함수 성능 키워드 — DB별 최적화 힌트

### PostgreSQL — 함수 안정성 3단계

| 레벨 | 의미 | 효과 |
|------|------|------|
| **IMMUTABLE** | 같은 입력 = **항상** 같은 결과 | 🏆 **인덱스 표현식·상수 폴딩 가능** |
| **STABLE** | **같은 쿼리 안에서는** 변하지 않음 | 쿼리 내 재사용 |
| **VOLATILE** (기본값) | **언제나 변할 수 있음** (`random()`, `now()`) | 최적화 불가 |

> 🔑 **함수 기반 인덱스를 걸려면 반드시 `IMMUTABLE`이어야 합니다.** (Day 3 안티패턴 3의 해법이 여기서 완성됩니다)

### 나머지 DBMS

| DBMS | 키워드 | 내용 |
|------|--------|------|
| **MySQL/MariaDB** | `DETERMINISTIC` | 동일 입력 = 항상 같은 결과 선언 → **복제(replication)/캐싱 시 안전**<br>반대는 `NOT DETERMINISTIC`(기본값) — `random()`, `NOW()` 포함 시 |
| **SQL Server** | 인라인 vs 스칼라 | **인라인 테이블 함수(iTVF)** — 내부 SQL 그대로 펼쳐서 실행 → **빠름**<br>⚠️ **스칼라 함수** — **행마다 호출 → 느림** (2019+부터 자동 인라이닝 일부 지원) |
| **Oracle** | `RESULT_CACHE` | 같은 입력이 여러 번 들어오면 결과를 **메모리에 저장, 재사용** |

> 💬 **자료의 결론 문장**
> **"자주 바뀌는 로직은 앱 코드, 공통 계산은 DB 함수, Cloud 환경에서 실행 시간 제한 주의"**

---

## 24-4. Stored Procedure 예시 — 4개 DBMS (연도별 매출 상위 5명)

```sql
-- MySQL
DELIMITER $$
CREATE PROCEDURE sp_top_customers(IN p_year INT)
BEGIN
  SELECT c.customer_id, SUM(o.total_amount) AS total_sales
  FROM   orders o JOIN customers c ON o.customer_id = c.customer_id
  WHERE  YEAR(o.order_date) = p_year
  GROUP BY c.customer_id ORDER BY total_sales DESC LIMIT 5;
END$$
DELIMITER ;
CALL sp_top_customers(2024);

-- PostgreSQL
CREATE OR REPLACE PROCEDURE sp_top_customers(p_year INT) LANGUAGE plpgsql AS $$
BEGIN
  SELECT c.customer_id, SUM(o.total_amount)
  FROM   orders o JOIN customers c ON c.customer_id = o.customer_id
  WHERE  EXTRACT(YEAR FROM o.order_date) = p_year
  GROUP BY c.customer_id ORDER BY 2 DESC LIMIT 5;
END; $$;
CALL sp_top_customers(2024);

-- SQL Server
CREATE PROCEDURE sp_top_customers @year INT
AS
BEGIN
  SELECT TOP 5 c.customer_id, SUM(o.total_amount) AS total_sales
  FROM   orders o JOIN customers c ON c.customer_id = o.customer_id
  WHERE  YEAR(o.order_date) = @year
  GROUP BY c.customer_id ORDER BY total_sales DESC;
END;
GO

-- Oracle
CREATE OR REPLACE PROCEDURE sp_top_customers(p_year NUMBER) AS
BEGIN
  FOR r IN (
    SELECT customer_id, SUM(total_amount) total_sales
    FROM   orders
    WHERE  EXTRACT(YEAR FROM order_date) = p_year
    GROUP BY customer_id ORDER BY total_sales DESC
    FETCH FIRST 5 ROWS ONLY
  ) LOOP
    DBMS_OUTPUT.PUT_LINE(r.customer_id || ': ' || r.total_sales);
  END LOOP;
END;
/
```

> 💡 **문법 차이 요약** : `DELIMITER $$`(MySQL) / `LANGUAGE plpgsql AS $$`(PG) / `@변수` + `GO`(SQL Server) / `FOR ... LOOP` + `/`(Oracle)

---

## 24-5. ⚠️ 보안 모델 — DEFINER vs INVOKER

> **"이 프로시저는 누구의 권한으로 실행되는가?"**

| DBMS | 키워드 | 의미 | ⚠️ 주의사항 |
|------|--------|------|------------|
| **MySQL/MariaDB** | `SQL SECURITY DEFINER/INVOKER` | **DEFINER** : 작성자 권한<br>**INVOKER** : 호출자 권한 | **SQL Injection + DEFINER = 권한 상승 위험**<br>`search_path` 고정 필수 |
| **PostgreSQL** | `SECURITY DEFINER/INVOKER` | 함수 **소유자 권한**으로 실행 | DEFINER 함수는 **`search_path` 하이재킹 주의** |
| **SQL Server** | `WITH EXECUTE AS OWNER/CALLER` | OWNER : 소유자 / CALLER : 호출자 | **소유권 체이닝(dbo 통일)** 으로 단순화 권장 |
| **Oracle** | `AUTHID DEFINER/CURRENT_USER` | 기본 : **정의자 권한** | PL/SQL에서 **ROLE이 아닌 직접 GRANT 권한만 유효** |

> 🚨 **왜 위험한가**
> `DEFINER`로 만든 프로시저에 SQL Injection 구멍이 있으면, **공격자가 "작성자(보통 관리자)의 권한"으로** 임의 SQL을 실행하게 됩니다. **권한 상승(Privilege Escalation)** 공격입니다.

---

## 24-6. 에러 처리 패턴

| DBMS | 문법 |
|------|------|
| **PostgreSQL** | `EXCEPTION` 블록으로 오류 포착 |
| **MySQL** | `DECLARE ... HANDLER FOR SQLEXCEPTION` |
| **Oracle** | `EXCEPTION WHEN OTHERS THEN ...` |
| **SQL Server** | `TRY...CATCH` 블록 |

### 트랜잭션 롤백 패턴 (주문 생성 SP)

```
재고 확인 → 주문 헤더 INSERT → 주문 아이템 INSERT → 재고 UPDATE
    ↓ 재고 부족 시
전체 ROLLBACK + 에러 발생
    ↓ 모든 단계 성공 시
COMMIT
```

**PostgreSQL 실전 예시**

```sql
CREATE OR REPLACE PROCEDURE sp_create_order(
  p_customer_id BIGINT,
  p_items       JSONB          -- [{"product_id":1,"qty":2}, ...]
) LANGUAGE plpgsql AS $$
DECLARE
  v_order_id BIGINT;
  v_item     JSONB;
  v_stock    INT;
  v_price    NUMERIC;
BEGIN
  -- 1. 주문 헤더 생성
  INSERT INTO orders (customer_id, status) VALUES (p_customer_id, 'created')
  RETURNING id INTO v_order_id;

  -- 2. 각 아이템 처리
  FOR v_item IN SELECT * FROM jsonb_array_elements(p_items) LOOP
    -- 재고 확인 (FOR UPDATE로 동시성 처리)   ← Day 3의 비관적 Lock!
    SELECT stock_qty, price INTO v_stock, v_price
    FROM   products WHERE id = (v_item->>'product_id')::INT FOR UPDATE;

    IF v_stock < (v_item->>'qty')::INT THEN
      RAISE EXCEPTION '재고 부족: product_id=%', (v_item->>'product_id');
    END IF;

    -- 주문 아이템 삽입 + 재고 차감
    INSERT INTO order_items (order_id, product_id, qty, unit_price)
    VALUES (v_order_id, (v_item->>'product_id')::INT, (v_item->>'qty')::INT, v_price);

    UPDATE products SET stock_qty = stock_qty - (v_item->>'qty')::INT
    WHERE  id = (v_item->>'product_id')::INT;
  END LOOP;

  UPDATE orders SET status = 'paid' WHERE id = v_order_id;
  -- EXCEPTION 시 자동 ROLLBACK (PG의 기본 동작)
END;$$;

CALL sp_create_order(42, '[{"product_id":1,"qty":2},{"product_id":3,"qty":1}]');
```

> 💡 **Day 3와 이어집니다** — `FOR UPDATE`(비관적 Lock)로 동시에 같은 상품을 주문할 때 재고가 음수가 되는 것을 막습니다.

### 커서(Cursor)

- 결과 집합을 **행 단위로 순회** 처리
- ⚠️ **대용량 데이터는 Set-based 처리 권장** (커서는 느림)

---

## 24-7. ⭐ SP vs 앱 코드 — 어디에 둘 것인가

| **DB에 두기** | **앱에 두기** |
|---|---|
| **공통 계산 로직** | **자주 바뀌는 비즈니스 로직** |
| **트리거로 호출** | **외부 API 연동** |
| **배치 작업** | **복잡한 조건 분기** |

> 🔑 **판단 기준** : **자주 바뀌면 앱, 안 바뀌고 공통이면 DB.**
> DB에 넣은 로직은 **Git 버전관리·테스트·배포가 어렵습니다.**

---

# 25. Trigger & 이벤트 처리

> 📌 **다루는 것** : 감사 로그 · CDC · 배치 · DBMS별 비교 · 실행 순서 제어

## 25-1. Trigger 기본 개념

> **특정 DML/DDL 이벤트 발생 시 DB가 자동 실행하는 코드**

| 요소 | 종류 |
|------|------|
| **타이밍** | `BEFORE` / `AFTER` / `INSTEAD OF`(뷰 전용) |
| **범위** | **행 단위**(row-level, `FOR EACH ROW`) / **문장 단위**(statement-level) |
| **가상 테이블** | `OLD`/`NEW` (MySQL/PG/Oracle) · `inserted`/`deleted` (SQL Server) |

### ✅ Trigger가 잘 맞는 경우

| 용도 | 예시 |
|------|------|
| **감사 로그(Audit)** | 누가 언제 무엇을 바꿨는지 자동 기록 |
| **기본값/유효성 보강** | `created_at` 자동 세팅, 파생 컬럼 계산 |
| **비즈니스 규칙 보강** | 재고 수량 음수 방지 |
| **소프트 삭제/버전 관리** | 삭제 시 아카이브 테이블로 이동 |

### ❌ 피해야 할 경우

| 안티패턴 | 왜 |
|----------|-----|
| **외부 연동** (API 호출, 장시간 작업) | **트랜잭션 연장, 장애 전파** |
| **순서 의존 / 상호참조 트리거** | **유지보수 지옥** |
| **대량 DML에 row 트리거 남발** | → **statement 트리거 또는 배치로 전환** |

> 🚨 **가장 중요한 원칙**
> ## **트리거에서 외부 API 호출 금지**
> → **트리거 → 로그 테이블/토픽 적재 → 비동기 소비자** 패턴을 쓰세요.
> (Day 3의 **Outbox 패턴**이 정확히 이 이야기입니다)

---

## 25-2. Trigger 예시 — PostgreSQL 감사 로그

**Row-level (행마다 실행)**

```sql
CREATE TABLE audit_log(
  id BIGSERIAL PRIMARY KEY, table_name TEXT, op TEXT,
  row_json JSONB, at TIMESTAMPTZ DEFAULT now()
);

CREATE OR REPLACE FUNCTION trg_sales_ai() RETURNS trigger AS $$
BEGIN
  INSERT INTO audit_log(table_name, op, row_json)
  VALUES ('sales', TG_OP, to_jsonb(NEW));
  RETURN NEW;
END$$ LANGUAGE plpgsql;

CREATE TRIGGER sales_ai
AFTER INSERT ON sales
FOR EACH ROW EXECUTE FUNCTION trg_sales_ai();
```

**Statement-level + Transition table (대량 DML에 효율적)** ⭐

```sql
CREATE OR REPLACE FUNCTION trg_sales_stmt_ai() RETURNS trigger AS $$
BEGIN
  INSERT INTO audit_log(table_name, op, row_json)
  SELECT 'sales', TG_OP, to_jsonb(n) FROM new_table AS n;   -- Transition table
  RETURN NULL;
END$$ LANGUAGE plpgsql;

CREATE TRIGGER sales_stmt_ai AFTER INSERT ON sales
REFERENCING NEW TABLE AS new_table
FOR EACH STATEMENT EXECUTE FUNCTION trg_sales_stmt_ai();
```

> 🔑 **차이가 큽니다**
> 10만 건을 INSERT하면 —
> - **Row-level** : 트리거 **10만 번** 실행
> - **Statement-level** : 트리거 **1번** 실행 (Transition table로 10만 건을 한 번에 처리)

---

## 25-3. Trigger 예시 — MySQL / SQL Server / Oracle

```sql
-- MySQL (row-level only, BEFORE/AFTER)
DELIMITER //
CREATE TRIGGER sales_bi BEFORE INSERT ON sales FOR EACH ROW
BEGIN SET NEW.created_at = COALESCE(NEW.created_at, NOW()); END//

CREATE TRIGGER sales_ai AFTER INSERT ON sales FOR EACH ROW
BEGIN
  INSERT INTO audit_log(table_name, op, row_json)
  VALUES ('sales','INSERT',JSON_OBJECT('id',NEW.id,'amount',NEW.amount));
END//
DELIMITER ;
-- ⚠️ 같은 테이블(sales) 수정 시 오류(1442)

-- SQL Server (AFTER/INSTEAD OF, inserted/deleted 가상 테이블)
CREATE TRIGGER dbo.trg_sales_ai ON dbo.Sales AFTER INSERT AS BEGIN
  SET NOCOUNT ON;
  INSERT INTO dbo.AuditLog(table_name,op,row_json,at)
  SELECT 'Sales','INSERT',(SELECT * FROM inserted FOR JSON PATH),SYSUTCDATETIME();
END;

-- Oracle (BEFORE row 기본값)
CREATE OR REPLACE TRIGGER sales_bi BEFORE INSERT ON sales FOR EACH ROW
BEGIN :NEW.created_at := NVL(:NEW.created_at, SYSTIMESTAMP); END;
/
```

---

## 25-4. ⭐ DBMS별 Trigger 기능 비교

| 항목 | PostgreSQL | MySQL | MariaDB | SQL Server | Oracle |
|------|:---:|:---:|:---:|:---:|:---:|
| **Row/Statement 트리거** | **둘 다** | **Row만** | **Row만** | **Statement만**<br>(다중행은 inserted/deleted에 반영) | **둘 다** |
| **INSTEAD OF (뷰)** | 지원 | ❌ 미지원 | 지원 | 지원 | 지원 |
| **Transition table** | 지원 | ❌ 미지원 | 지원 | inserted/deleted로 대체 | ❌ 미지원 |
| **DDL/Event 트리거** | **Event Trigger** | ❌ | ❌ | **DDL Trigger** | **DDL Trigger** |
| **실행 순서 제어** | 명시적 지정 어려움<br>(의존 금지) | `FOLLOWS`/`PRECEDES` | `FOLLOWS` | `sp_settriggerorder` | `FOLLOWS` |
| **같은 테이블 재수정** | 가능(주의) | **❌ 금지 (오류 1442)** | 유사 | 가능(주의) | 가능하나 **Mutating table** 제약 |
| **Autonomous Tx** | ❌ | ❌ | ❌ | ❌ | ✅ `PRAGMA AUTONOMOUS_TRANSACTION` |
| **보안 컨텍스트** | 함수에 `SECURITY DEFINER` 가능 | 트리거는 **DEFINER 계정 권한** | DEFINER | `EXECUTE AS`로 전환 가능 | 디파이너 권한 |

> 🔑 **설계에 큰 영향을 주는 두 가지**
> **MySQL은 row 트리거만**, **SQL Server는 statement 트리거 중심**입니다.
> 같은 로직을 옮길 때 구조를 통째로 바꿔야 할 수 있습니다.

---

## 25-5. 이벤트 처리 아키텍처 — 배치 · 알림 · CDC

### 스케줄 작업 (배치)

| DBMS | 도구 |
|------|------|
| **MySQL/MariaDB** | **EVENT Scheduler** (`SET GLOBAL event_scheduler = ON;`) |
| **PostgreSQL** | ⚠️ **내장 스케줄러 없음** → **`pg_cron`** 확장 또는 외부 스케줄러 |
| **SQL Server** | **SQL Server Agent** (작업/스케줄) |
| **Oracle** | **`DBMS_SCHEDULER`**(권장) / `DBMS_JOB`(구버전) |

### 알림 / 메시징

| DBMS | 도구 |
|------|------|
| **PostgreSQL** | **`LISTEN`/`NOTIFY`** — `PERFORM pg_notify('channel', payload)` → 앱 실시간 수신 |
| **SQL Server** | Service Broker, Event Notifications |
| **Oracle** | Advanced Queuing (AQ) |

### CDC (Change Data Capture)

> **DB 변경을 실시간 이벤트 스트림으로**

| DBMS | 방식 |
|------|------|
| **MySQL/MariaDB** | **Binlog** 기반 CDC → **Debezium** → Kafka |
| **PostgreSQL** | **Logical Decoding** (wal2json, pgoutput) → Debezium → Kafka |
| **SQL Server** | **CDC 내장**, Change Tracking 내장 |
| **Oracle** | **GoldenGate** (표준 솔루션) |

---

## 25-6. Trigger 심화 — Event Trigger & NOTIFY

### ① DDL 변경 이력 자동 기록 (PostgreSQL Event Trigger)

```sql
CREATE TABLE ddl_history (
  id          BIGSERIAL PRIMARY KEY,
  event_tag   TEXT,
  object      TEXT,
  executed_by TEXT DEFAULT current_user,
  at          TIMESTAMPTZ DEFAULT now()
);

CREATE OR REPLACE FUNCTION fn_ddl_logger() RETURNS event_trigger AS $$
DECLARE r RECORD;
BEGIN
  FOR r IN SELECT * FROM pg_event_trigger_ddl_commands() LOOP
    INSERT INTO ddl_history(event_tag, object)
    VALUES (r.command_tag, r.object_identity);
  END LOOP;
END$$ LANGUAGE plpgsql;

CREATE EVENT TRIGGER ddl_logger ON ddl_command_end
EXECUTE FUNCTION fn_ddl_logger();
```

**활용** : 스키마 변경 감시·차단 / 네이밍 규칙 자동 검사 / DDL 변경 이력 자동 기록

### ② 실시간 알림 (NOTIFY/LISTEN)

```sql
CREATE OR REPLACE FUNCTION fn_notify_order() RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify('order_channel', row_to_json(NEW)::TEXT);
  RETURN NEW;
END$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_order_notify AFTER INSERT ON orders
FOR EACH ROW EXECUTE FUNCTION fn_notify_order();

-- 앱에서 수신 (Python psycopg2)
-- conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
-- cur.execute("LISTEN order_channel")
-- while True: select.select([conn],...); conn.poll(); print(conn.notifies.pop())
```

**용도** : 실시간 대시보드 갱신 / 웹소켓 푸시 알림

### ③ 트리거로 간단한 CDC 구현

> Debezium 없이도 가능합니다.
> **변경 내용을 outbox 테이블에 기록 → 별도 프로세스가 읽어서 처리**

---

## 25-7. ⭐ Trigger vs Application — 선택 기준

| **트리거** | **앱** |
|---|---|
| **어떤 경로로 데이터가 변경되어도 반드시 실행**<br>(감사·무결성) | 비즈니스 로직 |
| | 외부 시스템 호출 |
| | 복잡한 흐름 제어 |

> 🔑 **일반 원칙**
> ## **트리거는 짧고 결정적으로, 외부 의존성 없이**
>
> 트리거의 유일한 강점은 **"우회 불가능"** 입니다. 배치로 넣든 수동 INSERT를 하든 무조건 실행됩니다. 그래서 **감사 로그와 무결성**에만 쓰는 게 맞습니다.

---

# 26. Cloud DB 개요

> 📌 **다루는 것** : On-Prem vs DBaaS · AWS RDS & Aurora · GCP Cloud SQL · Azure Database

## 26-1. On-Prem vs DBaaS vs Cloud-Native

| 구분 | **On-Prem** | **DBaaS**<br>(RDS/Cloud SQL) | **Cloud-Native**<br>(Aurora/Spanner) |
|------|---|---|---|
| **프로비저닝** | 서버 구매, 설치, 랙 | **콘솔에서 몇 분 내 생성** | 스토리지·복제 구조 전용화 |
| **확장성** | 수직 확장 (교체·증설 느림) | 수직 + 수평 (리드 리플리카) | **설계부터 분산, 자동 복구, 글로벌** |
| **고가용성** | DBA가 직접 RAC, AG 구성 | **Multi-AZ 자동 장애 조치** | **스토리지 레벨 6-way 복제** |
| **운영/패치** | DBA·시스템팀 책임 | 서비스가 백업·패치 자동화 | 더 높은 자동화 수준 |
| **비용** | **CAPEX(선투자)** + OPEX | **OPEX(사용량 기반)** | OPEX + egress + 전용 기능 비용 |
| **커스터마이징** | **OS, Filesystem, 확장 자유** | ⚠️ 슈퍼유저 제한, 확장 제한 | ⚠️ 제한이 더 클 수 있음 |

---

## 26-2. ⭐ DBaaS가 해주는 것 vs 우리가 할 일

| ✅ **DBaaS가 해주는 것** | ⚠️ **우리(고객)가 해야 하는 것** |
|---|---|
| 하드웨어/스토리지 관리 | **스키마/인덱스/쿼리 최적화**<br>**(핵심! DBaaS라도 책임 면제 아님)** |
| 장애 디스크 교체 | DB 파라미터 전략 (초기/운영 프로파일) |
| 백업/스냅샷 스케줄링 | **보안정책 설계** (권한/암호화/네트워크 경계) |
| 보관/복구 기능 제공 | 비용/성능 **SLO 설계와 관측**(옵서버빌리티) |
| 모니터링 지표/알림 | **메이저 버전 Upgrade** |
| 엔진 소규모 패치(마이너) | **호환성 검증** |
| 고가용성 토폴로지 (Multi-AZ, 자동 장애조치) | |

> 🚨 **가장 흔한 오해**
> **"클라우드로 옮기면 튜닝 안 해도 된다"** — ❌ 틀렸습니다.
> **Day 3에서 배운 인덱스·실행계획·쿼리 튜닝은 클라우드에서도 100% 우리 책임**입니다.

---

## 26-3. AWS RDS vs Aurora

| 항목 | **AWS RDS** | **Amazon Aurora** |
|------|---|---|
| **아키텍처** | 엔진 원본 그대로 관리형 운영 | **Compute/스토리지 분리, 3AZ 6중 복제** |
| **스토리지** | EBS 기반 | **10GB 단위 자동 확장, 최대 128TB** |
| **고가용성** | Multi-AZ 대기 | **스토리지 동기 복제 + 빠른 장애 조치** |
| **읽기 확장** | 읽기 복제본 추가 | **리더 엔드포인트, Serverless v2** |
| **글로벌** | 일부 엔진 기능 의존 | **Global Database** (10개 Region, 수십 ms) |
| **특화 기능** | Blue/Green 배포, RDS Proxy | **Backtrack · Parallel Query · Serverless v2** |
| **선택 기준** | **엔진 호환성 최우선**, 중소규모 | **읽기 부하↑, 고가용성, 빠른 장애 조치** 필요 |

---

## 26-4. GCP Cloud SQL & Azure Database

| 서비스 | 핵심 |
|--------|------|
| **GCP Cloud SQL** | MySQL·PostgreSQL·SQL Server 지원 / Enterprise·Enterprise Plus 에디션<br>**Regional HA** (기본/대기 구성, 자동 페일오버), Read Replica<br>**IAM DB Auth** — 서비스 계정/IAM 토큰 로그인 (PostgreSQL 중심)<br>최대 **64TB** 스토리지, 오토그로스 |
| **Azure Database** | MySQL/PostgreSQL **Flexible Server** (Zonal/Zone-redundant HA 선택)<br>**Zone-redundant HA — SLA 99.99%** (⚠️ Burstable 티어는 HA 미지원)<br>**Microsoft Entra ID(Azure AD)** 인증 연동 |
| **Azure SQL Database** | **Serverless** — 자동 일시중지/재개, 간헐 트래픽에 비용 효율<br>**Hyperscale** — 대용량(수TB급) 신속 백업/복구, 수평 확장<br>**Managed Instance** — On-Prem SQL Server 호환성 강조 |
| **GCP AlloyDB** | **로그-분리형 아키텍처**, 분석/OLTP **혼합 워크로드** 성능 강조 |

---

## 26-5. ⭐ Cloud DB 선택 의사결정 4단계

| 단계 | 판단 기준 |
|------|-----------|
| **1단계 — 규제/컴플라이언스** | **데이터 주권(Data Residency)** — 특정 국가/리전 저장 의무?<br>GDPR·개인정보보호법·금융 규제 — 외부 클라우드 반출 금지?<br>→ **제약 있으면 On-Prem 또는 특정 리전 Cloud** |
| **2단계 — 팀 역량** | **DBA 전문가 있는가?** → On-Prem 가능<br>**DevOps 팀 작은가?** → **DBaaS 권장** (운영 부담 최소화) |
| **3단계 — 워크로드 특성** | 트래픽 **예측 가능·안정적** → 고정 인스턴스 (RDS/Cloud SQL)<br>트래픽 **급변·간헐적** → **서버리스** (Aurora Serverless v2·Neon)<br>**글로벌 사용자·멀티리전 일관성** → **Spanner/CockroachDB** |
| **4단계 — 비용 총합 (TCO)** | **On-Prem** : CAPEX(서버 구매) + OPEX(인건비·전기·유지보수)<br>**DBaaS** : OPEX(사용량) + **Data Egress + IOPS + 백업 스토리지**<br>⚠️ **간과하기 쉬운 비용 — Egress·IOPS·API 호출** |

> 💬 **[정오] 원본 383p** 의 "3단계 — 쿼리 개선 / 4단계 — 아키텍처 개선" 슬라이드는 **Day 3의 SQL 튜닝 체크리스트가 잘못 복사된 것**으로 보입니다. Cloud DB 선택 프레임워크의 3·4단계는 위 표(워크로드 특성 / 비용 총합)가 맞습니다.

---

# 27. 서버리스 & 분산 Cloud DB

> 📌 **다루는 것** : Aurora Serverless v2 · Google Spanner · Cosmos DB · PlanetScale · Neon · Supabase

## 27-1. 주요 서비스 4종

| 서비스 | 특징 | ⚠️ 주의 |
|--------|------|--------|
| **Aurora Serverless v2**<br>(MySQL/PG 호환) | **ACU 단위 자동 스케일**<br>급증 트래픽 수동 스케일링 불필요<br>Global DB·Backtrack 옵션<br>**간헐적/변동성 큰 OLTP에 적합** | **스케일 이벤트 시 지연 변화**<br>→ 커넥션 풀·읽기/쓰기 분리 설계 |
| **Google Cloud Spanner**<br>(True Distributed SQL) | **Paxos/TrueTime 기반**<br>글로벌 트랜잭션 + 외부 일관성<br>**Strict Serializability 보장**<br>전역 스키마/SQL, **멀티리전에서 단일 DB처럼** | **스키마·핫스팟 설계 중요** |
| **Azure Cosmos DB**<br>(다중 모델·일관성 선택) | NoSQL — 문서·키값·Cassandra·MongoDB 다중 API<br>**5단계 일관성 레벨 선택 가능**<br>전 지구적 확장, IoT/이벤트, 세션 데이터 | **낮은 일관성 → 앱 로직 보완** 필요 |
| **PlanetScale / Neon / Supabase**<br>(차세대 개발자 DB) | **PlanetScale** — Vitess 기반, **브랜칭·Online DDL**<br>**Neon** — **scale-to-zero**, 스토리지-컴퓨트 분리<br>**Supabase** — Postgres + Auth + Realtime + Edge Functions | — |

---

## 27-2. 서버리스/분산 vs 전통 RDBMS

| 항목 | **전통 RDBMS** | **서버리스/분산 Cloud DB** |
|------|---|---|
| **용량 계획** | 인스턴스 크기 **수동 관리** | **자동 스케일** (Aurora v2/Neon — scale-to-zero) |
| **일관성 모델** | 단일 노드에 강한 일관성 | **글로벌 일관성**(Spanner), **선택형**(Cosmos 5단계) |
| **다지역 복제, DR** | 수동 구성 | **Managed Global** (Spanner·Cosmos·Aurora Global) |
| **스키마 변경** | ⚠️ Lock, 다운타임 위험 | **Online DDL, 브랜칭** |
| **비용 모델** | 고정 (**유휴 비용 높음**) | **사용량 기반, 유휴 절감**(scale-to-zero) |

---

## 27-3. ⭐ MSA 환경 DB 패턴 선택 가이드

| 패턴 | 설명 | 적합 상황 | ⚠️ 주의 사항 |
|------|------|-----------|-------------|
| **Database per Service** | 서비스별 독립 DB 소유 | 마이크로서비스 독립 배포 | **Cross-service 조인 불가**, 데이터 중복 |
| **Saga (Choreography)** | 이벤트 기반 자율 조정 | 서비스 간 결합 최소화 | 분산 트랜잭션 복잡, **보상 트랜잭션 설계 필요** |
| **Saga (Orchestration)** | 중앙 코디네이터가 조정 | 복잡한 워크플로우 제어 | **코디네이터 단일 장애 포인트** |
| **CQRS** | 읽기/쓰기 모델 분리 | 읽기/쓰기 부하 불균형 시 | **이벤트 발생 시 일관성 허용** 필요 |
| **Outbox Pattern** | 트랜잭션 내 이벤트 발행 보장 | At-least-once 전달 필요 | **멱등성 소비자 구현 필요** |
| **Event Sourcing** | 상태가 아닌 **이벤트 저장** | 이력, 감사, 타임 트래블 | 복잡한 쿼리, 읽기 성능 고려 |

> 💡 **Outbox의 "멱등성 소비자"란** — at-least-once는 **같은 이벤트가 2번 올 수 있다**는 뜻입니다. 소비자가 "이미 처리한 이벤트면 무시"하도록 만들어야 중복 결제 같은 사고가 안 납니다.

---

# 28. 데이터 웨어하우스 & 분석 DB

> 📌 **다루는 것** : OLTP vs OLAP · 파티션 프루닝 · 벡터화 실행 · Redshift · BigQuery · Snowflake · ClickHouse

## 28-1. ⭐ OLTP vs OLAP

| 구분 | **OLTP** (운영 DB) | **OLAP** (분석 DB/DWH) |
|------|---|---|
| **목적** | **트랜잭션 처리** (쇼핑, 결제, 재고) | **다차원 분석, 집계** (매출 등) |
| **워크로드** | 잦은 **단건 읽기/쓰기**, 낮은 지연 | **대량 스캔 및 집계**, 높은 처리량 |
| **스키마** | **정규화** (보통 3NF) | **De-normalize** (스타, 스노우플레이크) |
| **인덱스** | B-Tree, PK, UK — **포인트 질의**에 최적 | **파티션, 클러스터링, 컬럼형 저장** — Full Scan 최적 |
| **트랜잭션** | **강한 ACID**, 짧은 트랜잭션 | **일괄/배치 적재**, 읽기 일관성(Snapshot) |
| **저장 형식** | **행 지향** (Row store) | **컬럼 지향** (Columnar : Parquet/ORC) |
| **최적화** | 인덱스 튜닝, 조인 순서 | **파티션 프루닝, 컬럼 프루닝, 벡터화** |

> 🔑 **행 지향 vs 컬럼 지향이 핵심입니다**
> ```
> [행 지향]  주문1의 모든 컬럼 → 주문2의 모든 컬럼 → ...
>            "주문 1건 전체를 읽기" 에 유리  (OLTP)
>
> [컬럼 지향]  모든 주문의 금액 → 모든 주문의 날짜 → ...
>            "금액 컬럼만 1억 건 합산" 에 유리  (OLAP)
> ```

---

## 28-2. ⭐ 분석 DB 핵심 기술 3가지

### ① 파티션 프루닝 (Partition Pruning)

> 필요한 **날짜/범위의 파티션만 읽고** 나머지는 무시

| 제품 | 방식 |
|------|------|
| **BigQuery** | `PARTITION BY DATE(event_time)` → WHERE 해당 파티션만 스캔 |
| **Snowflake** | **마이크로파티션 통계**로 범위 밖 파일 자동 스킵 |
| **ClickHouse** | `PARTITION BY toDate(ts)` + `ORDER BY`로 범위별 병렬 처리 |

**효과** : I/O **수십~수백 배** 절감 (⚠️ **BigQuery/Snowflake는 스캔 바이트 과금** — 비용 직결)

### ② 컬럼 프루닝 (Column Pruning)

> **SELECT한 컬럼만** 디스크에서 읽고 나머지는 **완전히 스킵**

> 🚨 **BigQuery는 스캔 바이트량이 SELECT 컬럼 수에 따라 즉시 줄어듭니다.**
> ## **`SELECT *` 절대 금지! 필요한 컬럼만 명시**
> Day 3의 안티패턴 1이 여기서는 **돈 문제**가 됩니다.

### ③ 벡터화 실행 (Vectorized Execution)

> 행 단위가 아닌 **컬럼 단위 벡터(1000개씩)로 묶어 CPU SIMD 명령어로 처리**

- **BigQuery / Snowflake / DuckDB / ClickHouse** — 모두 벡터화 실행 엔진 채택
- **효과** : CPU 효율↑, 캐시 효율↑, 병렬 처리 용이

---

## 28-3. 분석 DB 제품별 비교

| 제품 | 아키텍처 | 강점 | 비용 모델 | 적합 시나리오 |
|------|---|---|---|---|
| **Amazon Redshift** | MPP (리더 + Compute slice) | **AWS 생태계** (S3, Glue, SageMaker) | 노드 기반 + Serverless 옵션 | AWS 중심 Data Lake + DWH |
| **Google BigQuery** | **서버리스**, Storage/Compute 완전 분리 | 간단 운영, ML/GIS/BI Engine 통합 | ⚠️ **스캔 바이트 과금** (절약 중요!) | GCP 중심, 완전한 서버리스 |
| **Azure Synapse** | MPP SQL 풀 + 서버리스 + Spark 통합 | **MS 환경** (PowerBI, AD, Fabric) | 일시 중지·재개 | MS 생태계, Spark + SQL 혼합 |
| **Snowflake** | 스토리지·Compute 분리, **멀티 가상 WH** | 운영 단순성, **데이터 쉐어링**, VARIANT | 초 단위 과금, 일시 중지 | **멀티 클라우드**, 운영 단순화 |
| **ClickHouse** | 컬럼형 OLAP, **MergeTree 엔진** | **초저지연 실시간 집계**, 비용 효율, 오픈소스 | 자가호스팅 가능 | 이벤트·로그·시계열 **실시간 분석** |

### 제품 선택 가이드

| 요구사항 | 추천 | Why |
|---|---|---|
| 완전 서버리스 + GCP 중심 | **BigQuery** | 서버리스 DWH, 스캔 바이트 과금, 운영 최소 |
| AWS 생태계 + S3 레이크 | **Redshift** | AWS 밀착, Dist/Sort Key 설계로 최적화 |
| MS PowerBI + Spark + SQL | **Azure Synapse** | MS 생태계, Fabric·PowerBI 연동 |
| 운영 단순 + Data Sharing | **Snowflake** | 멀티 클라우드, JSON, 자동 튜닝 |
| **초저지연 실시간 집계** | **ClickHouse** | 이벤트·로그·시계열, 비용 효율, 오픈소스 |

---

## 28-4. 스타 스키마 & DW 설계

### 스타 스키마 (Star Schema)

```
        [고객 디멘전]
              │
[상품 디멘전]─┼─[★ 팩트 테이블 ★]─┼─[시간 디멘전]
              │   (매출액·수량)     │
        [지역 디멘전]
```

| 구성 | 특징 |
|------|------|
| **팩트 테이블** | **거래·이벤트** (매출액·수량·클릭수)<br>**크고 Append-only**, **시간 파티션** |
| **디멘전 테이블** | 사용자/상품/시간/지역<br>**비교적 작고 SCD Type 2 이력** 적용 |

### 설계 규칙 5가지

| 규칙 | 내용 |
|------|------|
| **Surrogate Key** | 디멘전에 **정수형 대체키** 사용 (자연키는 속성으로 유지) |
| **팩트는 얇게 길게** | 많은 행(append-only), **측정값(measure)과 FK만** |
| **역할 차원**(Role-Playing) | 날짜를 한 번 만들고 `order_date`·`ship_date`로 **별칭** |
| **Junk Dimension** | Y/N, 소수 플래그들을 묶어 **작은 디멘전으로** |
| **Conformed Dimension** | 여러 마트에서 **같은 정의로 재사용** (카테고리·지역) |

### 스노우플레이크 vs 3NF DW

| 방식 | 언제 |
|------|------|
| **스노우플레이크** | 디멘전을 다시 정규화 → **계층이 자주 바뀔 때** (카테고리·지역) 선별 사용 |
| **3NF DW** | 원천/코어 레이어는 3NF → **소비 레이어(mart)는 스타** |
| **Cloud DW** (BigQuery·Snowflake) | **조인 비용이 낮으면** 정규화보다 **넓은 테이블** 선호 |

---

## 28-5. 실전 DDL — BigQuery & ClickHouse

```sql
-- Google BigQuery: 파티션 + 클러스터
CREATE TABLE mart.fact_sales
PARTITION BY DATE(event_ts)              -- 날짜별 파티션 (스캔 비용 절감)
CLUSTER BY user_id, item_id AS           -- 클러스터: user_id 정렬 후 item_id
SELECT event_ts, user_id, item_id, qty, amount, channel
FROM   stg.sales_cleaned;

-- 파티션 프루닝: 특정 날짜만 스캔
SELECT SUM(amount) FROM mart.fact_sales
WHERE  event_ts >= '2024-01-01' AND event_ts < '2024-04-01';
-- → Q1 파티션만 스캔, 나머지 완전 스킵
```

```sql
-- ClickHouse: MergeTree 엔진 (초고속 실시간 OLAP)
CREATE TABLE fact_events (
  event_time DateTime,
  user_id    UInt64,
  action     LowCardinality(String),     -- 카디널리티 낮은 컬럼 최적화
  amount     Decimal(12,2)
) ENGINE = MergeTree
PARTITION BY toDate(event_time)          -- 날짜별 파티션
ORDER BY (user_id, event_time)           -- 정렬 키 = 스킵 인덱스
TTL event_time + INTERVAL 90 DAY;        -- 90일 후 자동 삭제

-- 실시간 집계 (ms 단위 응답)
SELECT user_id, COUNT(), SUM(amount) FROM fact_events
WHERE  action = 'purchase' AND event_time >= today() - 7
GROUP BY user_id ORDER BY SUM(amount) DESC LIMIT 10;
```

---

# 29. 현재의 트렌드

> 📌 **다루는 것** : NewSQL · 시계열 DB · Vector DB & pgvector RAG · AI+DB · GraphQL · Edge DB

## 29-1. NewSQL — SQL + 트랜잭션 + 수평 확장

### 등장 배경

| | 강점 | 약점 |
|---|---|---|
| **전통 RDBMS** | 강한 ACID + SQL | ❌ 수평 확장 어려움 |
| **NoSQL** | 수평 확장 쉬움 | ❌ 트랜잭션/SQL/조인 약함 |
| **NewSQL** | 🏆 **3박자 모두** | Shared-nothing 분산 + **Raft/Paxos** + MVCC |

### 대표 제품

| 제품 | 아키텍처 | 강점 | ⚠️ 약점 |
|------|---|---|---|
| **CockroachDB** | 키-값 스토어 위에 SQL 레이어<br>**Range 단위 자동 샤딩**, Raft 그룹 복제 | **단순 운영**(모든 노드 동등)<br>자동 분산/리밸런싱<br>**기본 SERIALIZABLE** | 멀티리전 쓰기 시 **합의 왕복으로 지연 증가**<br>스키마 설계 최적화 필요 |
| **TiDB** (PingCAP) | MySQL 호환 SQL(TiDB) + **TiKV**(분산 KV, Raft) + PD + **TiFlash**(OLAP) | **HTAP** (OLTP+OLAP 동시)<br>**MySQL 생태계 완전 호환** | 클러스터 구성요소 이해 필요<br>**운영 복잡도** |

> 🔑 **선택 가이드**
> **강한 일관성 + 기본 SERIALIZABLE** → **CockroachDB**
> **MySQL 호환 유지 + 수평 확장 + HTAP** → **TiDB**

---

## 29-2. 시계열 DB & Vector DB

### 시계열 DB

| 제품 | 특징 | 주의 |
|------|------|------|
| **TimescaleDB**<br>(PostgreSQL 확장) | **Hypertable** — time + space 파티션 자동화<br>**Continuous Aggregates** — 자동 MV(집계 뷰 실시간 갱신)<br>Compression, Retention policy 내장<br>🏆 **표준 SQL 그대로, Postgres 에코시스템 유지** | — |
| **InfluxDB** | 시계열 전용 **고속 쓰기·압축**<br>내장 Retention, Downsampling 파이프라인 | ⚠️ **SQL 문법과 다름** (Flux/InfluxQL)<br>표준 조인·트랜잭션 개념 제한 |

> **선택** : **SQL 생태계 유지 → TimescaleDB** / **고속 ingest 특화 → InfluxDB**

### Vector DB — AI 시대의 유사도 검색

| 제품 | 특징 |
|------|------|
| **pgvector** (PostgreSQL 확장) | `vector` 타입 + **HNSW/IVF 인덱스** + **SQL·트랜잭션·JOIN 그대로** |
| **Pinecone** | **완전 관리형**, 초대규모 클러스터 운영, 필터링, 멀티테넌시 |
| **Weaviate** | 오픈소스 + 매니지드, **BM25 + 벡터 하이브리드**, GraphQL/REST API |

> 🔑 **선택** : **DB 내 SQL+조인 → pgvector** / **초대규모+운영단순 → Pinecone** / **오픈소스+API유연 → Weaviate**

### TimescaleDB 실전 예시

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE metrics (
  ts      TIMESTAMPTZ NOT NULL,
  host    TEXT NOT NULL,
  cpu_pct DOUBLE PRECISION,
  mem_mb  INT
);
SELECT create_hypertable('metrics', 'ts');       -- 시간 파티션 자동화

-- Continuous Aggregate: 5분 단위 평균 자동 집계
CREATE MATERIALIZED VIEW metrics_5m WITH (timescaledb.continuous) AS
SELECT time_bucket('5 minutes', ts) AS bucket,
       host, AVG(cpu_pct) AS cpu_avg, AVG(mem_mb) AS mem_avg
FROM   metrics
GROUP BY bucket, host;

-- 보존 정책: 30일 초과 데이터 자동 삭제
SELECT add_retention_policy('metrics', INTERVAL '30 days');
```

> 💡 **Day 2의 Materialized View 기억나시죠?** 거기선 **수동 REFRESH**가 필요했는데, TimescaleDB의 **Continuous Aggregate는 자동 갱신**됩니다.

---

## 29-3. pgvector — RAG 하이브리드 검색

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;          -- 전문검색

CREATE TABLE knowledge_base (
  id         BIGSERIAL PRIMARY KEY,
  title      TEXT NOT NULL,
  content    TEXT,
  chunk_idx  INT DEFAULT 0,
  embedding  VECTOR(1536),                       -- OpenAI text-embedding-3-small
  search_ts  TSVECTOR,                           -- 한국어 FTS
  created_at TIMESTAMPTZ DEFAULT now()
);

-- HNSW 인덱스 (코사인 유사도 기준)
CREATE INDEX ON knowledge_base USING HNSW (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
CREATE INDEX ON knowledge_base USING GIN (search_ts);

-- 하이브리드 검색 (벡터 70% + 키워드 30%)
WITH vector_search AS (
  SELECT id, 1 - (embedding <=> $1::VECTOR) AS vec_score
  FROM   knowledge_base ORDER BY embedding <=> $1::VECTOR LIMIT 20
),
keyword_search AS (
  SELECT id, ts_rank(search_ts, plainto_tsquery('korean', $2)) AS kw_score
  FROM   knowledge_base WHERE search_ts @@ plainto_tsquery('korean', $2)
)
SELECT kb.title, kb.content,
       COALESCE(vs.vec_score,0)*0.7 + COALESCE(ks.kw_score,0)*0.3 AS hybrid_score
FROM   knowledge_base kb
  LEFT JOIN vector_search  vs ON vs.id = kb.id
  LEFT JOIN keyword_search ks ON ks.id = kb.id
WHERE  vs.id IS NOT NULL OR ks.id IS NOT NULL
ORDER BY hybrid_score DESC LIMIT 5;
```

> ✅ **RAG 한 줄 정의**
> **문서를 임베딩으로 DB에 저장 → 질문 임베딩으로 유사 문서 검색 → LLM 컨텍스트 주입**

---

## 29-4. AI/ML + DB 통합 패턴 3가지

| 패턴 | 내용 | 장단점 |
|------|------|--------|
| **① in-DB ML**<br>(DB 안에서 ML) | **BigQuery ML, Snowflake Snowpark, SQL Server ML Services, PostgreSQL MADlib**<br>SQL로 회귀/분류/시계열/클러스터링 모델 직접 실행 | ✅ **데이터 이동 없음** (보안/규정 준수), 재현성/권한 통합<br>❌ 모델 다양성·최신성은 PyTorch/TF 대비 제한 |
| **② RAG** | 원문 → 임베딩 → Vector DB 저장 → 질문 유사 문서 검색 → LLM 컨텍스트 주입 | **품질 핵심** : Chunking/필터/**재순위(re-ranking)**, 최신성 갱신, 출처 보강<br>**pgvector + PostgreSQL** — SQL+트랜잭션+조인으로 완전한 RAG 파이프라인 |
| **③ 피처 스토어 + 실시간 예측** | **Feast** 같은 피처 스토어로 오프라인/온라인 일관성 유지 (훈련/서빙 스키마 동일)<br>**DB/DWH** = 오프라인 피처 소스, **Redis** = 온라인 피처 | 내장 ML/UDTF/외부 함수 활용 |

---

## 29-5. GraphQL + DB & Edge DB

### GraphQL + DB 패턴

| 항목 | 내용 |
|------|------|
| **문제** | REST는 **Over-fetch**(필요 이상) / **Under-fetch**(필요 이하) |
| **GraphQL** | 클라이언트가 **필요한 필드만 질의** → 불필요한 데이터 전송 없음 |
| **Hasura** | PostgreSQL 위에서 **즉시 GraphQL API 생성** + 권한·RLS 연동 + 구독(실시간) |
| **PostGraphile** | 스키마로 GraphQL 자동 생성, PostgreSQL 기능 깊게 활용 |
| **Prisma** | 타입 세이프 ORM, GraphQL 서버와 궁합 좋음 (Next.js 등) |
| ⚠️ **주의** | **N+1 쿼리 방지 (DataLoader)**, 권한·멀티테넌시, CDN 캐싱 전략 |

### Edge DB 패턴

| 항목 | 내용 |
|------|------|
| **동기** | 전 세계 사용자에게 **낮은 지연(ms)**, 엣지 함수와 가까운 데이터 |
| **Turso** | libSQL/SQLite 분산 → 엣지 노드에서 SQLite |
| **Cloudflare D1** | SQLite 기반, Workers와 통합 |
| **Neon/PlanetScale** | 서버리스 PG/MySQL, 분리형 스토리지·브랜치·자동 스케일 |
| **패턴** | **읽기 = 로컬 엣지 캐시 + 쓰기 = 중앙 합의** (최종 일관성) |
| ⚠️ **주의** | GDPR/**데이터 거주성**, 일관성 선택·**충돌 해결(CRDT)** 전략 |

---

## 29-6. ⭐ 목적별 DB 선택

| 데이터 유형 | 적합 DB | 이유 | 예시 |
|---|---|---|---|
| **트랜잭션 데이터** | **PostgreSQL, MySQL** | ACID 보장, 관계 무결성 | 주문, 결제, 사용자 |
| **세션, 캐시** | **Redis**, Memcached | 인메모리, 초저지연 | 장바구니, 세션, Rate Limit |
| **검색 인덱스** | **Elasticsearch**, OpenSearch | 역방향 인덱스, 전문 검색 | 상품 검색, 로그 분석 |
| **시계열 데이터** | **TimescaleDB**, InfluxDB | 타임 파티션, 집계 최적화 | IoT 센서, APM 메트릭 |
| **임베딩/벡터** | **pgvector**, Qdrant | ANN 인덱스, 유사도 검색 | RAG, 추천, 이미지 검색 |
| **그래프 데이터** | **Neo4j**, Amazon Neptune | 관계 탐색, 경로 쿼리 | SNS 친구 관계, 사기 탐지 |
| **분석/리포팅** | **BigQuery**, Snowflake | 컬럼형, 대용량 스캔 | BI 대시보드, 데이터마트 |

> 🔑 **"단일 DBMS → 목적별 DB 혼용"** 이 현재의 흐름입니다. (**Polyglot Persistence**)

---

## 29-7. AI 시대 DB 엔지니어의 역할 변화

| **전통 DBA 역할** | **AI 시대 추가 역할** |
|---|---|
| 스키마 설계, 인덱스 최적화, 백업·복구, 성능 튜닝 | **Vector DB 설계** — 임베딩 차원, 인덱스, 하이브리드 검색 |
| 쿼리 실행계획 분석, Lock 관리, 장애 대응 | **Feature Store 관리** — 학습/서빙 피처 일관성 보장 |
| 인프라 운영 — 아키텍처 설계·비용 최적화·파라미터 튜닝 | **AI 파이프라인 DB 통합** — ETL/ELT·Streaming·in-DB ML |
| | **LLM 기반 SQL 자동 생성·검증**<br>(AI가 만든 쿼리의 **성능·보안 검토**) |
| | 온프레미스 → **멀티 클라우드 DB 전략** 수립 |
| | 단일 DBMS → **목적별 DB 혼용** |

---

# 30. 보안 및 권한 관리

> 📌 **다루는 것** : 인증·인가·SQL Injection·암호화·Row-Level Security·감사

## 30-1. DB 보안 전체 구조 5단

| 계층 | 질문 |
|------|------|
| **인증 (Authentication)** | **누가 접속했는가** (아이디/비번, AD/IAM) |
| **인가 (Authorization)** | **그 사람이 무엇을 할 수 있나** (권한: SELECT/INSERT 등) |
| **입력검증/파라미터 바인딩** | **악성 입력**으로부터 SQL을 보호 |
| **암호화** | **네트워크 전송(TLS)** 과 **저장(디스크/TDE/컬럼)** 에서 데이터 보호 |
| **감사 (Audit)** | **누가 언제 무슨 쿼리** 실행했는지 기록 |

> 🔑 **관통하는 원칙 : 최소 권한 원칙(Least Privilege) — 필요한 것만 준다**

---

## 30-2. 사용자·역할·권한 — 4개 DBMS

```sql
-- PostgreSQL (가장 직관적)
CREATE ROLE app_reader NOLOGIN;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_reader;
CREATE ROLE app_user LOGIN PASSWORD 'secret';
GRANT app_reader TO app_user;

-- MySQL (8.0 이상 권장 방식)
CREATE ROLE 'app_reader';
GRANT SELECT ON mydb.* TO 'app_reader';
CREATE USER 'app_user'@'%' IDENTIFIED BY 'secret';
GRANT 'app_reader' TO 'app_user'@'%';

-- SQL Server (Windows/AD 연동 가능)
CREATE ROLE app_reader;
GRANT SELECT ON SCHEMA::dbo TO app_reader;
CREATE LOGIN app_user WITH PASSWORD='secret';
CREATE USER app_user FOR LOGIN app_user;
EXEC sp_addrolemember 'app_reader','app_user';

-- Oracle (권한이 매우 세세함)
CREATE ROLE APP_READER;
GRANT CREATE SESSION TO APP_READER;
GRANT SELECT ON HR.EMPLOYEES TO APP_READER;
CREATE USER APP_USER IDENTIFIED BY secret;
GRANT APP_READER TO APP_USER;
```

> 💡 **공통 패턴** : **① 역할 만들기 → ② 역할에 권한 주기 → ③ 사용자 만들기 → ④ 사용자에게 역할 주기**
> 사용자에게 직접 권한을 주지 않는 것이 핵심입니다.

### PostgreSQL Role 개념

> **PostgreSQL에서는 User와 Role을 구분하지 않고 "Role"로 통합**
> 단, **`LOGIN` 속성 여부**에 따라 실제 사용자로 쓸 수 있는지 결정

| Role 속성 | 설명 |
|---|---|
| **LOGIN** | 실제 사용자로 **로그인 가능** |
| **NOSUPERUSER** | 슈퍼유저 아님 (기본) |
| **CREATEDB, CREATEROLE** | DB나 Role 생성 가능 여부 |
| **INHERIT** | 부모 Role 권한 **상속** 가능 |

```sql
CREATE ROLE analyst LOGIN PASSWORD 'analyst_pw';
CREATE ROLE dev_user LOGIN PASSWORD 'dev_pw' CREATEDB;
CREATE ROLE readonly_user LOGIN PASSWORD 'readonly_pw' NOSUPERUSER;
DROP ROLE readonly_user;

\du    -- psql 명령으로 확인
SELECT rolname, rolsuper, rolcreatedb, rolcanlogin FROM pg_roles;
```

### GRANT 대상별 권한

| 대상 | 부여 가능한 권한 | 예시 |
|------|---|---|
| **Database** | CONNECT, TEMP | `GRANT CONNECT ON DATABASE db TO user;` |
| **Schema** | USAGE, CREATE | `GRANT USAGE ON SCHEMA public TO user;` |
| **Table** | SELECT, INSERT, UPDATE, DELETE, REFERENCES | `GRANT SELECT ON sales TO analyst;` |
| **Function** | EXECUTE | `GRANT EXECUTE ON FUNCTION calc_tax() TO user;` |

---

## 30-3. ⭐ RBAC 권한 설계안 (실무 예시)

| 역할명 | 설명 | 권한 구성 |
|--------|------|-----------|
| **data_engineer** | 데이터 적재/정제 담당 | INSERT, UPDATE, TRUNCATE, SELECT, 특정 CREATE |
| **data_analyst** | 리포트 및 분석 전용 | **SELECT (READ-ONLY)**, EXECUTE on 분석 함수 |
| **api_user** | 프론트/백엔드 연결 계정 | **SELECT on VIEW** 또는 제한된 TABLE, **직접 테이블 접근 불허** |
| **etl_user** | 스케줄러 등 ETL 자동화 | INSERT, TRUNCATE, SELECT on 대상 테이블 |
| **admin_user** | 시스템 관리용 | ALL PRIVILEGES + CREATEDB, CREATEROLE, LOGIN, SUPERUSER |

> 🔑 **일반적으로 `api_user`, `analyst_user`는 직접 테이블에 접근시키지 않고 VIEW를 통해 간접적으로 제한된 데이터만 제공**

### VIEW 기반 보안

```sql
-- 분석가용 (급여 제외)
CREATE VIEW v_employee_basic AS
SELECT emp_id, emp_name, department FROM employee;

-- API 사용자용 (급여·이름 제거)
CREATE VIEW v_employee_api AS
SELECT emp_id, department FROM employee;

GRANT SELECT ON v_employee_basic TO data_analyst;
GRANT SELECT ON v_employee_api   TO api_user;

-- ⚠️ 테이블 직접 접근은 차단되어야 함
REVOKE ALL ON employee FROM data_analyst, api_user;
```

### 권한 모니터링 쿼리

```sql
-- 현재 역할 목록 및 속성
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolcanlogin
FROM   pg_roles ORDER BY rolname;

-- 사용자별 테이블 권한
SELECT grantee, table_schema, table_name, privilege_type
FROM   information_schema.role_table_grants
WHERE  grantee IN ('data_engineer', 'data_analyst', 'api_user')
ORDER BY grantee, table_name;

-- 특정 사용자의 함수 권한
SELECT grantee, routine_schema, routine_name, privilege_type
FROM   information_schema.role_routine_grants
WHERE  grantee = 'data_analyst';

-- 특정 테이블에 부여된 권한 전체
SELECT * FROM information_schema.role_table_grants WHERE table_name = 'sales';

-- 현재 세션 사용자
SELECT current_user, session_user;
```

### 최소 권한 설계 패턴 5가지

- 시스템 계정 / 스키마 소유자 **분리**
- **역할 단위로** 권한 부여
- 애플리케이션 계정은 **역할만** 사용
- **DDL 권한 분리** (운영 금지)
- **감사·모니터링**

---

## 30-4. Row-Level Security (행 단위 보안) — 멀티테넌시

> **같은 테이블에서 사용자가 볼 수 있는 행(데이터)을 제한**

```sql
-- PostgreSQL
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY customer_policy ON orders
FOR SELECT USING (customer_id = current_setting('app.customer_id')::int);

-- 앱이 세션에 고객ID를 설정하면 그 고객 데이터만 조회 가능
SELECT set_config('app.customer_id','42', true);
```

```sql
-- SQL Server (SESSION_CONTEXT 이용)
CREATE SCHEMA Security;
CREATE FUNCTION Security.fnOrderPredicate(@cust_id int)
RETURNS TABLE WITH SCHEMABINDING AS
RETURN SELECT 1 AS fn WHERE @cust_id = CAST(SESSION_CONTEXT(N'customer_id') AS int);

CREATE SECURITY POLICY OrderFilter
ADD FILTER PREDICATE Security.fnOrderPredicate(customer_id) ON dbo.Orders
WITH (STATE = ON);

EXEC sp_set_session_context @key=N'customer_id', @value=42;
```

> 💡 **Day 1의 멀티테넌시 3패턴 기억나시죠?** **Pool Model**(단일 DB + tenant_id)의 안전장치가 바로 이 RLS입니다. 앱이 `WHERE tenant_id=` 를 빼먹어도 **DB가 막아줍니다.**

---

## 30-5. ⭐ SQL Injection — 원인과 방어

### 원인

> 개발자가 **사용자 입력을 직접 SQL 문자열에 붙여넣음** → 공격자가 **SQL 구조를 변경** 가능

```python
# 🚨 절대 금지!!!!!! (문자열 포맷)
sql = f"SELECT * FROM users WHERE name = '{user_input}'"
cur.execute(sql)
# user_input = "' OR '1'='1"  →  전체 사용자 조회됨
```

### 1차 방어 — 파라미터 바인딩 (Prepared Statement)

```python
# ✅ psycopg2 (Postgres)
cur.execute("SELECT * FROM users WHERE name = %s", (user_input,))
```

> **DB가 SQL과 값의 경계를 분리**해서 처리하므로, 값 안에 어떤 SQL을 넣어도 **값으로만** 취급됩니다.

### 2차 보강 — 화이트리스트 검증

> ⚠️ **`ORDER BY`, 컬럼 이름은 파라미터 바인딩이 안 됩니다.**

```python
# ORDER BY에 사용자 입력을 직접 넣으면 위험 → 화이트리스트로 검증
if order not in ('name', 'created_at'):
    order = 'created_at'
sql = f"SELECT * FROM items ORDER BY {order}"
```

### ORM은 안전한가?

| | 답 |
|---|---|
| **대부분의 ORM** | 파라미터 바인딩을 **자동으로 해줘 기본적으로 안전** |
| ⚠️ **하지만** | ORM의 **raw SQL**이나 `.execute(text(...))`에 **입력을 직접 포맷팅하면 취약** |
| **결론** | **ORM 사용 시에도 ORM의 파라미터 바인딩 API만 사용하라** |

> ⚠️ **또 하나의 함정** : **저장 프로시저/뷰만으로는 자동 방어가 아닙니다.**
> 내부에서 **동적 SQL(concat)** 을 만들면 동일하게 취약합니다.

---

## 30-6. 암호화 — 3계층

| 계층 | 내용 | 장단점 |
|------|------|--------|
| **전송 암호화 (TLS)** | 클라이언트 ↔ DB 연결을 암호화 | **항상 켜자** |
| **디스크 암호화 / TDE** | DB 파일(데이터파일, 백업)을 자동 암호화 → **앱은 모름** | ✅ **복구·백업까지 암호화**<br>❌ **컬럼 단위 제어 불가**<br>Oracle, SQL Server, 대부분 클라우드 DB 제공 |
| **컬럼 암호화** | 민감 컬럼만 암호화<br>**PostgreSQL** : `pgcrypto` → bytea로 저장<br>**SQL Server** : **Always Encrypted** (클라이언트 측 키, DB는 암호문만) | ✅ **민감 데이터만 타겟**, 검색 통제 가능<br>❌ **인덱스/검색 제약, 성능 저하** |

```sql
-- PostgreSQL pgcrypto 예시
CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO customers (name, ssn_enc)
VALUES ('Alice', pgp_sym_encrypt('111-22-3333', 'mypassword'));

-- 복호화
SELECT pgp_sym_decrypt(ssn_enc, 'mypassword') FROM customers;
```

---

## 30-7. 클라우드 DB에서 달라지는 점

| 항목 | 내용 |
|------|------|
| **키 관리** | 클라우드는 **KMS(키 관리 서비스)** 제공<br>🚨 **키 권한을 잃으면 백업 복구 불가 → 키 관리 중요!** |
| **IAM/AD 연동** | 사용자를 DB 계정 대신 **클라우드 계정(IAM/Azure AD)** 으로 관리 → 중앙관리 편함 |
| **감사 & 로깅** | 클라우드 로그(Audit)를 쉽게 연결해 자동 보관·알림<br>**AWS RDS** : IAM 인증, KMS 키 / **GCP Cloud SQL** : Cloud KMS, IAM / **Azure SQL** : Azure AD, Key Vault |

> 🔑 **클라우드에서는 DB 권한 + 클라우드 권한을 함께 설계**해야 합니다.

### CloudDB 권한 관리

| 서비스 | 방식 |
|--------|------|
| **Google Cloud Spanner** | **IAM 기반 Role/Permission** (Spanner Admin, Database Admin, Database User)<br>**FGAC**(Fine-grained access control)로 DB 내부 개체 단위까지<br>프로젝트/인스턴스/DB/테이블 단위 Role 할당 |
| **Amazon Aurora/RDS** | **IAM 연동** (Option Group/Security Group)로 인스턴스·DB 수준 접근 제어<br>**엔진별 자체 SQL 권한 관리 + IAM 동시 활용** |
| **기타 Cloud/NoSQL** | **RBAC** (ScyllaDB, Cassandra) — 계층적 역할/권한, 역할 간 상속구조<br>클라우드 관리 콘솔, REST API/SDK 통한 권한 배포·회수 |

### 대표 명령어 비교

| DBMS | 계정 생성 | 권한 부여/회수 | 역할 관리 | 세분화 단위 |
|---|---|---|---|---|
| **MySQL** | `CREATE/DROP USER` | `GRANT/REVOKE` | `CREATE ROLE` | 글로벌/DB/테이블/컬럼/객체 |
| **PostgreSQL** | `CREATE ROLE` | `GRANT/REVOKE` | `CREATE ROLE` | DB/스키마/테이블/시퀀스/함수/그룹 |
| **Oracle** | `CREATE USER` | `GRANT/REVOKE` | `CREATE ROLE` | 시스템/객체/롤 단위 |
| **SQL Server** | `CREATE LOGIN/USER` | `GRANT/REVOKE/`**`DENY`** | `CREATE ROLE` | 서버/DB/스키마/객체/시스템 |
| **Cloud Spanner** | IAM 계정 | IAM Role 지정 | DB Role + IAM | 프로젝트/인스턴스/DB/테이블/열 |
| **Aurora/RDS** | IAM 계정/그룹 | SQL + IAM 권한 | DB Role + IAM | DB 인스턴스/객체/Security Group |

---

## 30-8. ⚠️ 흔히 하는 실수 & 체크리스트

| 실수 | 해결 |
|------|------|
| **애플리케이션에 DB 관리자 권한을 줌** | **역할 분리, 최소권한** |
| **클라우드 KMS 키 권한을 삭제** | 키 권한 정책 **문서화**, 백업 키 관리 |
| **로그에 민감정보(SSN, 패스워드) 평문으로 남김** | **마스킹/로그 필터링** 및 민감컬럼 암호화 |
| **`ORDER BY` 같은 파라미터를 검증 없이 사용** | **화이트리스트로 검증** |

### ✅ 핵심 체크리스트 6가지

- [ ] **TLS 강제 적용**
- [ ] 앱은 **Prepared Statement / ORM 안전 API만** 사용
- [ ] DB 사용자·역할 설계 → **최소권한** 적용
- [ ] 민감데이터는 **컬럼 암호화 또는 TDE** 적용 결정
- [ ] 클라우드 **키 관리는 팀 문서화 + 백업키 보관**
- [ ] **감사 로그(누가 언제)** 설정 및 모니터링

---

# 31. 백업·복구 & 고가용성

> 📌 **다루는 것** : Full/Incremental/PITR · Replication · Failover · Cloud 백업

## 31-1. Multi-AZ 구조 (AWS 예시)

```
        AWS Region (서울)
┌────────────────┐        ┌────────────────┐
│      AZ-A      │  동기  │      AZ-B      │
│   Primary DB   │◄──────►│   Standby DB   │
│  (읽기/쓰기)    │  복제  │  (복제만, 읽기X) │
└────────────────┘        └────────────────┘
         ↓ Primary 장애 시 자동 전환 (Failover)
```

| 요소 | 내용 |
|------|------|
| **Primary DB** | 실제로 애플리케이션이 접속해서 읽고 쓰는 주 DB |
| **Standby DB** | **동기 복제**로 항상 같은 데이터 유지 (⚠️ 읽기 불가) |
| **동기 복제** | 쓰기가 완료되려면 **두 DB 모두 쓰기가 끝나야 "성공"** → **RPO(데이터 손실) ≈ 0** |
| **Failover** | Primary가 죽으면 AWS가 **자동으로 Standby를 승격** → **RTO(복구 시간) 수 분 내** |

---

## 31-2. ⭐ 백업 유형 비교

| 백업 유형 | 설명 | 특징 | DBMS 구현 |
|---|---|---|---|
| **Full Backup** | 전체 데이터 스냅샷 | **가장 느림, 가장 완전** | `pg_dump`, `mysqldump`, RMAN |
| **Incremental** | **마지막 백업 이후** 변경분만 | **빠름**<br>복구 시 Full + Incremental 조합 | WAL 아카이브, Binlog, RMAN |
| **Differential** | **마지막 Full 이후** 전체 변경분 | Incremental보다 **복구 간단** | SQL Server 지원 |
| **PITR** (시점 복구) | **특정 시점**으로 복구 | 🏆 **오염된 트랜잭션 직전으로 복구** | WAL + 기록 시점 지정 |
| **논리적 백업** | SQL 덤프 (INSERT 문) | **이식성 높음**, 느림 | `pg_dump`, `mysqldump` |
| **물리적 백업** | 데이터 파일 직접 복사 | **빠름**, 동일 환경 필요 | `pg_basebackup`, `xtrabackup` |

> 💡 **Incremental vs Differential**
> ```
> Full(일) → Inc(월) → Inc(화) → Inc(수)    복구: Full + 월 + 화 + 수  (조합 복잡)
> Full(일) → Diff(월) → Diff(화) → Diff(수)  복구: Full + 수만          (간단, 용량 큼)
> ```

---

## 31-3. PITR & Streaming Replication (PostgreSQL)

### PITR (Point-In-Time Recovery)

- **오염 이전 시점으로 복구**
- **Base backup + WAL 아카이브** 보관 → `recovery_target_time` 설정
- 🏆 **실수로 DELETE한 직전 시점으로 복구 가능**

```
# postgresql.conf
archive_mode    = on
archive_command = 'cp %p /backup/wal/%f'
```

### Streaming Replication

| 항목 | 내용 |
|------|------|
| **방식** | Primary → Standby **실시간 복제**, WAL 스트리밍 |
| **Hot Standby** | **SELECT 쿼리 허용** (읽기 분산) |
| **Synchronous** | COMMIT 시 **Standby 응답 대기** → **RPO=0**, ⚠️ 성능 저하 |
| **Asynchronous** | **COMMIT 즉시 응답** → RPO>0, **기본값**, 성능 우수 |

### Failover 전략

| 도구 | 설명 |
|------|------|
| **Patroni** | Python 기반 **HA 클러스터 매니저** — Primary 장애 시 자동 Standby 승격 |
| **pg_auto_failover / Repmgr** | 대안 HA 도구 |
| **Cloud** | RDS Multi-AZ / Aurora → **장애 조치 자동** (CNAME 전환, 수십 초) |

### ⭐ DR 목표 — RPO vs RTO

| 지표 | 의미 |
|------|------|
| **RPO** (Recovery Point Objective) | **최대 허용 데이터 손실 시간** — "얼마나 잃어도 되나" |
| **RTO** (Recovery Time Objective) | **최대 허용 서비스 다운 시간** — "얼마나 멈춰도 되나" |

---

## 31-4. DBMS별 백업·복구·HA 비교

| DBMS | 백업 도구 | HA 솔루션 | Cloud 옵션 |
|---|---|---|---|
| **PostgreSQL** | `pg_dump`, `pg_basebackup`, WAL | Patroni, Repmgr | RDS Multi-AZ, Aurora, Cloud SQL HA |
| **MySQL** | `mysqldump`, `xtrabackup`, `mysqlpump` | **Group Replication**, ProxySQL, MHA | RDS Multi-AZ, Aurora, Cloud SQL |
| **Oracle** | **RMAN** (Recovery Manager) | **RAC**, **Data Guard**, GoldenGate | Autonomous DB, Exadata Cloud |
| **SQL Server** | SSMS Backup, Maintenance Plan | **Always On AG**, Failover Cluster | Azure SQL MI, RDS for SQL Server |
| **Cloud (공통)** | 스냅샷, **PITR UI (슬라이더)** | Multi-AZ, Region 자동 장애조치 | 크로스 리전 Read Replica / Global DB |

---

## 31-5. 고가용성 솔루션 심화

| 솔루션 | 내용 |
|--------|------|
| **Oracle RAC**<br>(Real Application Clusters) | 여러 인스턴스가 **공유 스토리지(ASM)** 동시 접근<br>**Cache Fusion** — 노드 간 데이터 블록 캐시 일관성<br>대형 엔터프라이즈, 무정지 요구, 읽기/쓰기 모두 확장<br>⚠️ **AWS RDS for Oracle은 RAC 미지원** (Exadata on AWS는 가능) |
| **SQL Server Always On AG** | DB 집합 단위 **HA/DR + 읽기 스케일아웃**<br>**동기식(HA)** — RPO=0, 성능 약간 저하 / **비동기식(DR)** — 지연 허용<br>보조 복제본에서 **읽기 전용 리포팅** 가능<br>RDS Multi-AZ는 내부적으로 AG 활용 |
| **PostgreSQL FDW**<br>(Foreign Data Wrapper) | **`postgres_fdw`** — 원격 PostgreSQL 테이블을 **로컬처럼 참조**<br>이기종 DB 조인, **데이터 가상화**, 점진적 마이그레이션<br>**Logical Replication** — 테이블 단위 Pub/Sub 복제<br>용도 : 테이블 단위 증분 복제, **무중단 마이그레이션**, 읽기 분산 |

---

# 32. 모니터링 및 운영

> 📌 **다루는 것** : TPS·QPS·Latency · Slow Query · Prometheus+Grafana · Cloud 모니터링

## 32-1. 모니터링이란 — 건강검진 비유

| 서버 | 사람 |
|------|------|
| **CPU, 메모리** | 몸의 체력 |
| **TPS, QPS** | **심장 박동 수** |
| **Latency(지연시간)** | **혈압** |
| **로그(Log)** | 건강기록 |
| **모니터링 도구** | 의사/청진기 |

> 🔑 **DB 모니터링은 DB의 건강을 체크하고, 이상 징후를 미리 발견하는 일**

---

## 32-2. ⭐ 기본 지표 3가지

| 용어 | 뜻 | 한 줄 | 예시 |
|------|-----|------|------|
| **TPS**<br>(Transactions Per Second) | 초당 **트랜잭션** 수 | "1초에 몇 건의 **거래가 끝났는가**" | 쇼핑몰 결제 100건/초 |
| **QPS**<br>(Queries Per Second) | 초당 **쿼리** 수 | "1초에 몇 번 **DB에 물어봤는가**" | SELECT/INSERT/UPDATE 등 포함 |
| **Latency**<br>(지연시간) | 요청~응답 걸린 시간 | "**응답 속도**" | 쿼리 실행에 0.05초 |

> ☕ **카페 비유로 외우기**
> - **QPS** → 초당 **주문** 수
> - **TPS** → 초당 **결제 완료** 수
> - **Latency** → 한 잔 **나오기까지** 시간
>
> **QPS = 얼마나 많은 일을 처리하는지 / TPS = 얼마나 많은 거래가 완료되는지 / Latency = 얼마나 빠른지**

---

## 32-3. 모니터링 툴

| 도구 | 역할 | 설명 |
|------|------|------|
| **Prometheus** | **데이터 수집** | DB나 서버에서 지표를 주기적으로 모아 저장 |
| **Grafana** | **시각화** | Prometheus 데이터를 그래프로 표시 |
| **Datadog** | 통합 모니터링 SaaS | DB, 서버, 네트워크를 한 번에 관리 (유료) |
| **CloudWatch** | AWS 전용 | RDS나 EC2 상태를 자동으로 표시 |

### Prometheus + Grafana 흐름

```
① Prometheus가 DB에서 "현재 CPU 몇 %, TPS 몇?" 데이터를 수집
② Grafana가 그 데이터를 Dashboard로 시각화
```

**대시보드에 올릴 것** : 초당 쿼리(QPS) 그래프 / **p95 지연시간** 그래프 / **복제 지연(replica lag)** 그래프 / Active connection 수
→ **DB용 심전도 모니터**

### Cloud DB 모니터링

| Cloud | 서비스 | 특징 |
|-------|--------|------|
| **AWS RDS/Aurora** | CloudWatch + **Performance Insights** | 그래프 + **상위 느린 쿼리 자동 분석** |
| **GCP Cloud SQL** | Cloud Monitoring + **Query Insights** | 쿼리별 평균 응답시간 바로 확인 |
| **Azure DB** | Azure Monitor + Workbooks | 시각화 대시보드 템플릿 제공 |

> ⚠️ Cloud에서는 자동 수집되지만, **세세한 로그를 보려면 "Logs Export"를 켜야 합니다.**

---

## 32-4. ⭐ 이상 징후 확인

| 증상 | 원인 가능성 | RDBMS | Cloud DB |
|------|---|---|---|
| **쿼리가 갑자기 느려짐** | 인덱스 없음, **통계 오래됨** | `EXPLAIN`, `ANALYZE`로 실행계획 확인 | 동일하게 실행계획 확인 가능 (콘솔/쿼리) |
| **CPU 100%** | 느린 쿼리, **풀스캔** | OS 도구(`top`,`htop`) + **Slow Query Log** | CloudWatch/Cloud Monitoring에서 CPU 그래프 → 느린 쿼리 로그 |
| **Connection Full** | **커넥션 누수**, 풀 미사용 | `SHOW PROCESSLIST`, `Threads_connected` | `max_connections` 초과 알람, 연결 수 그래프 |
| **복제 지연** | 네트워크 문제, 대용량 DML | `SHOW SLAVE STATUS` 또는<br>`pg_last_xact_replay_timestamp()` | **ReplicaLag 지표 자동 제공** |
| **디스크 꽉 참** | 로그 미삭제, 임시파일 | `df -h`, 스토리지 모니터링 | **FreeStorageSpace** / Disk Usage 지표 |

---

## 32-5. 알람(Alert) 설정 예시

| 상황 | 경고 기준 | 행동 |
|------|-----------|------|
| **평균 응답 시간 > 500ms** | 5분 이상 지속 | 쿼리 분석 시작 |
| **Replica Lag > 30초** | 10분 지속 | 복제 트래픽 점검 |
| **CPU 사용률 > 80%** | 10분 지속 | 인덱스, 캐시 점검 |
| **Free Storage < 10%** | **즉시** | 로그 정리, 용량 증설 |

---

## 32-6. On-Prem vs Cloud 모니터링 차이

| 항목 | **On-Prem** | **Cloud (DBaaS)** |
|------|---|---|
| **설치/운영** | 직접 설정 필요 | **자동 설치/패치** |
| **로그 접근** | 직접 파일(`/var/log/...`) 확인 | 콘솔/로그 서비스에서 조회 (Export 필요) |
| **리소스 지표** | OS 명령어(`top`, `vmstat`) | **클라우드 모니터링에서 자동 수집** |
| **복제 모니터링** | 수동 스크립트 필요 | **ReplicaLag 지표 기본 제공** |
| **모니터링 도구** | Prometheus/Grafana 직접 설치 | CloudWatch, Query Insights **자동 제공** |
| **알람 설정** | 직접 구성 | **콘솔에서 클릭 몇 번** |
| **튜닝 자유도** | **높음** (파라미터 직접 수정) | ⚠️ **제한적** (파라미터 그룹만) |

> 🔑 **"내가 다 하는 것" vs "대부분 자동, 하지만 세밀 제어는 제한"**

---

## 32-7. 요약

| 개념 | 의미 | 도구/방법 |
|------|------|-----------|
| **TPS / QPS / Latency** | DB의 **"속도와 양"** | 모니터링 그래프, `SHOW STATUS`, `pg_stat_database` |
| **Slow Query Log** | **느린 쿼리 기록** | MySQL: `/var/log/mysql/slow.log` |
| **pg_stat_activity** | 현재 활동 | PostgreSQL 내부 뷰 |
| **Prometheus + Grafana** | 시각화 | On-Prem 용 |
| **CloudWatch / Query Insights** | 자동 모니터링 | 클라우드용 |

> ✅ **한 줄 정리**
> **TPS/QPS = DB가 얼마나 바쁘게 일하는가**
> **Latency = 얼마나 빨리 일하는가**
> **로그 = 왜 느렸는가의 증거**
> **모니터링 도구 = 그걸 한눈에 보여주는 창**

---

# 33. 종합실습 – 4

> 📌 **주제** : ecommerce 매출 분석 및 정리

## 33-1. 시나리오

> **당신은 E-Commerce 데이터팀 주니어 엔지니어**
> 월간 매출 리포트/AOV, 카테고리별 성과, 재구매·RFM 분석, 재고 이슈 탐지를 만들고, **실행 계획(성능)까지 개선**하는 것

**데이터 특징**

| 항목 | 내용 |
|------|------|
| **채널** | web, mobile, marketplace |
| **주문 상태** | created / paid / shipped / delivered / cancelled / refunded |
| **가격** | **가격이력(SCD2)** 로 관리 (`product_prices`, `valid_from`~`valid_to`) |
| **카테고리** | **트리 구조 (재귀 CTE)** |
| **재고** | 재주문 시점 관리 (`reorder_point`) |
| **리뷰** | 평점 1~5, 효자상품 판별 |
| **쿠폰** | SAVE10 등 |

> 💡 **Day 1~3 총동원입니다** — SCD2(Day3 22장), 재귀 CTE(Day2 14장), Window Function(Day2 15장), 실행계획(Day3 18장), MV(Day2 14장)

## 33-2. 환경설정

```
Schema 생성 : 종합실습4_ecom_schema_postgres.sql
데이터 적재 : 종합실습4_ecom_seed_postgres.sql
```

## 33-3. 실습 문제 11문항

| # | 문제 | 필요한 도구 |
|---|------|------------|
| **Q1** | 지난 한 달간 실제 팔린 **총 금액** (paid+shipped+delivered) | `SUM` + `WHERE IN` |
| **Q2** | **월별** 주문 수, 매출, **주문당 평균 금액(AOV)** | `DATE_TRUNC` + `GROUP BY` |
| **Q3** | 최근 90일 **카테고리 Top10** | `GROUP BY` + `ORDER BY` + `LIMIT` |
| **Q4** | 제품별 **누적매출 `RANK()` Top20** | **Window Function** |
| **Q5** | **RFM 분석** — 고객이 얼마나 최근에, 자주, 많이 샀는지 | `MAX(date)`, `COUNT`, `SUM` |
| **Q6** | **첫 구매 후 30일 내 재구매율** | **CTE + `MIN(order_date)` + 자기 조인** |
| **Q7** | **재고가 임계치보다 낮은** 상품 (곧 품절 위험) | `JOIN` + `WHERE stock < reorder_point` |
| **Q8** | **리뷰 4.5↑ & 50개↑ 효자상품** | `GROUP BY` + **`HAVING`** |
| **Q9** | **쿠폰 사용 영향** — 쿠폰 쓴 주문 vs 안 쓴 주문 평균 금액 비교 | `CASE WHEN` + `AVG` 또는 `FILTER` |
| **Q10** | **상위 1% 고객**의 최근 60일 매출 | **`PERCENT_RANK()` 또는 `NTILE(100)`** |
| **Q11** | **0으로 나눠도 에러 안 나는** 나눗셈 함수 → 안전한 평균 계산 | **`NULLIF(분모, 0)`** 또는 사용자 정의 함수 |

> 💡 **Q11 힌트** : `SUM(amount) / NULLIF(COUNT(*), 0)` — Day 2의 LAG 예시에서 썼던 그 패턴입니다.
> 또는 24장에서 배운 **사용자 정의 함수**로 `fn_safe_div(a, b)`를 만들어도 됩니다.

## 33-4. 실행 계획 비교 & 성능 개선

- **`EXPLAIN ANALYZE`로 병목 파악**
- **인덱스 추가/개선**
- **Join 전략 비교** — Hash Join vs Nested Loop, Bitmap Heap Scan 등
- **Materialized View 활용** — `mv_daily_gmv`로 리포트 질의 가속, **갱신 전략 검토**
- (Option) 엔진별 옵티마이저 차이 정리 — Postgres / MySQL / Oracle / SQL Server

> **`mv_daily_gmv` 과제 상세**
> 매일매일 총 판매금액을 조회할 수 있게 하되, **매번 JOIN해서 SUM하면 느리므로 Materialized View 사용**.
> 데이터가 얼마나 자주 바뀌는지에 맞춰 **갱신 주기를 설계** (오후 3시 기준으로 설정)

## 33-5. 제출물

| 항목 | 내용 |
|------|------|
| **SQL Query 및 결과** | 각 문항별 **쿼리와 실행결과 화면** (Screen Capture) |
| **제출 방법** | **Slack 내 댓글 제출** |
| **제출 기한** | **금일 중** |
| **채점 기준** | ① 요구사항 반영 여부<br>② **Query 내 컬럼 선택** (불필요한 컬럼 확인)<br>③ ⭐ **DB 프로그래밍에 대한 주석처리 여부** |

> ⚠️ **Day 4 채점 기준에 "주석처리"가 추가되었습니다.** 쿼리마다 무엇을 하는지 주석을 다세요.

---

# 🧭 Day 4 전체 흐름 한 장 요약

```
[Day 4의 세 덩어리]

━━━━ ① DB 안에서 코드 돌리기 (24~25장) ━━━━

  Stored Procedure  값 안 돌려줌 / 트랜잭션 O / 작업 절차
  Function          값 돌려줌   / 트랜잭션 X / 계산 도구
                    PG: IMMUTABLE → 함수 기반 인덱스 가능

  Trigger           자동 실행. 우회 불가능이 유일한 강점
                    ✅ 감사 로그, 기본값, 무결성
                    ❌ 외부 API 호출 (트랜잭션 연장·장애 전파)
                    → 트리거는 짧고 결정적으로, 외부 의존성 없이

  ⚠️ 공통 원칙: 자주 바뀌면 앱, 안 바뀌고 공통이면 DB


━━━━ ② DB를 클라우드로 (26~29장) ━━━━

  On-Prem  →  DBaaS  →  Cloud-Native  →  서버리스/분산
   자유↑        운영부담↓                    확장성↑
   비용CAPEX    비용OPEX                    scale-to-zero

  ⚠️ DBaaS라도 스키마·인덱스·쿼리 튜닝은 여전히 우리 책임!

  OLTP (행 지향)          ⟷         OLAP (컬럼 지향)
  정규화·ACID·단건                  비정규화·스타스키마·대량스캔
                                     3대 기술: 파티션프루닝
                                              컬럼프루닝
                                              벡터화실행

  트렌드: NewSQL(3박자) · 시계열 · Vector DB · in-DB ML · Edge
         → 단일 DBMS에서 "목적별 DB 혼용"으로


━━━━ ③ 운영 (30~32장) ━━━━

  보안 5계층   인증 → 인가 → 입력검증 → 암호화 → 감사
               최소 권한 원칙 / 역할 만들고 → 역할에 권한 → 사용자에 역할
               SQL Injection: 파라미터 바인딩 (ORDER BY는 화이트리스트)
               RLS로 멀티테넌시 안전장치

  백업/HA      Full · Incremental · Differential · PITR
               RPO(데이터 손실) vs RTO(다운타임)
               동기복제 RPO=0 (느림) / 비동기 RPO>0 (빠름)

  모니터링     QPS(주문수) · TPS(결제완료수) · Latency(나오는 시간)
               Prometheus+Grafana (On-Prem) / CloudWatch (Cloud)
```

---

## 🎓 시험/면접 대비 핵심 문답

| 질문 | 답 |
|------|-----|
| **SP와 함수의 차이는?** | **값을 돌려주면 함수, 일을 시키면 프로시저**. 함수는 트랜잭션 제어·DML 불가 |
| **PostgreSQL 함수 안정성 3단계는?** | **IMMUTABLE**(항상 같음, 인덱스 가능) / **STABLE**(쿼리 내 불변) / **VOLATILE**(기본값) |
| **함수 기반 인덱스를 걸려면?** | 함수가 **`IMMUTABLE`** 이어야 함 |
| **DEFINER vs INVOKER란?** | DEFINER = **작성자 권한**, INVOKER = 호출자 권한.<br>⚠️ **DEFINER + SQL Injection = 권한 상승 위험** |
| **SQL Server 스칼라 함수가 느린 이유는?** | **행마다 호출**되기 때문. **인라인 테이블 함수(iTVF)** 가 빠름 |
| **Trigger가 잘 맞는 경우는?** | **감사 로그, 기본값/유효성 보강, 무결성** — **어떤 경로로든 반드시 실행**되어야 할 때 |
| **⭐Trigger에서 절대 하면 안 되는 것은?** | **외부 API 호출** → 트랜잭션 연장, 장애 전파.<br>**트리거 → 로그 테이블 적재 → 비동기 소비자** 패턴으로 |
| **Row vs Statement 트리거 차이는?** | 10만 건 INSERT 시 Row는 **10만 번**, Statement는 **1번** 실행 (Transition table 활용) |
| **MySQL 트리거의 제약 2가지는?** | ① **Row 트리거만** 지원 ② **같은 테이블 재수정 금지** (오류 1442) |
| **PostgreSQL에 내장 스케줄러가 있나?** | ❌ **없음** → **`pg_cron`** 확장 또는 외부 스케줄러 |
| **⭐DBaaS를 써도 우리가 해야 하는 것은?** | **스키마/인덱스/쿼리 최적화**, 보안정책 설계, 메이저 버전 업그레이드, 호환성 검증 |
| **RDS vs Aurora 선택 기준은?** | RDS = **엔진 호환성 최우선**, 중소규모 / Aurora = **읽기 부하↑, 고가용성, 빠른 장애 조치** |
| **Cloud DB 선택 4단계는?** | ① **규제/데이터 주권** ② **팀 역량** ③ **워크로드 특성** ④ **TCO** |
| **클라우드에서 간과하기 쉬운 비용은?** | **Egress(데이터 전송) · IOPS · API 호출** |
| **OLTP vs OLAP의 저장 형식 차이는?** | OLTP = **행 지향**(1건 전체 읽기) / OLAP = **컬럼 지향**(한 컬럼 대량 집계) |
| **⭐분석 DB 핵심 기술 3가지는?** | **파티션 프루닝 · 컬럼 프루닝 · 벡터화 실행** |
| **BigQuery에서 `SELECT *`가 왜 치명적인가?** | **스캔 바이트 과금** — 컬럼 수에 비례해 **돈이 나감** |
| **스타 스키마의 두 축은?** | **팩트 테이블**(거래·이벤트, 크고 append-only) + **디멘전 테이블**(작고 SCD2 이력) |
| **NewSQL이 푸는 문제는?** | RDBMS의 **ACID+SQL** + NoSQL의 **수평 확장**을 동시에 |
| **CockroachDB vs TiDB?** | 강한 일관성·기본 SERIALIZABLE → **CockroachDB** / MySQL 호환·HTAP → **TiDB** |
| **RAG를 한 줄로?** | 문서를 **임베딩으로 저장** → 질문 임베딩으로 **유사 문서 검색** → **LLM 컨텍스트 주입** |
| **DB 보안 5계층은?** | **인증 → 인가 → 입력검증 → 암호화 → 감사** |
| **⭐SQL Injection 1차 방어는?** | **파라미터 바인딩(Prepared Statement)** — DB가 SQL과 값의 경계를 분리 |
| **`ORDER BY`에 사용자 입력을 쓰려면?** | 파라미터 바인딩 불가 → **화이트리스트 검증** |
| **ORM은 안전한가?** | 기본적으로 안전하지만, **raw SQL이나 `text()`에 직접 포맷팅하면 취약** |
| **암호화 3계층은?** | **TLS**(전송) / **TDE**(디스크, 컬럼 제어 불가) / **컬럼 암호화**(민감 컬럼만, 인덱스 제약) |
| **RLS는 무엇을 푸나?** | **같은 테이블에서 사용자가 볼 수 있는 행을 제한** → 멀티테넌시 안전장치 |
| **클라우드 KMS에서 가장 위험한 실수는?** | **키 권한을 잃으면 백업 복구 불가** |
| **Full/Incremental/Differential 차이는?** | Full = 전체 / **Incremental = 마지막 백업 이후** / **Differential = 마지막 Full 이후** (복구 간단) |
| **⭐RPO와 RTO의 차이는?** | **RPO = 최대 허용 데이터 손실 시간** / **RTO = 최대 허용 다운타임** |
| **동기 vs 비동기 복제?** | 동기 = **RPO=0**, 성능 저하 / 비동기 = RPO>0, **기본값**, 성능 우수 |
| **PITR이 유용한 상황은?** | **실수로 DELETE한 직전 시점으로 복구** |
| **TPS와 QPS의 차이는?** | **QPS = 초당 쿼리 수**(물어본 횟수) / **TPS = 초당 트랜잭션 수**(완료된 거래) |
| **모니터링 알람 기준 예시는?** | 응답시간 >500ms(5분) / Replica Lag >30초(10분) / CPU >80%(10분) / **Storage <10%(즉시)** |

---

## 🏁 4일 과정 전체 지도

```
Day 1  현실 → 표로 만들기
       ERD → 정규화(1NF~3NF) → PK/FK/UK → DDL
       지키는 장치: ACID · 격리수준 · 제약조건 · WAL

Day 2  표에서 답 꺼내기
       집계(GROUP BY) · 결합(JOIN) · 분해(서브쿼리/CTE) · 유지하며 계산(Window)
       실행 순서: FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY

Day 3  왜 느린가, 왜 충돌하는가
       속도:   인덱스 → 실행계획 → 안티패턴 8 → 파티셔닝
       동시성: MVCC → 격리수준 → Lock → Deadlock
       커지면: 파티셔닝 → Replica → 샤딩

Day 4  어디에 두고, 어떻게 지키고, 어떻게 굴리나
       DB 안 코드: SP · Trigger (자주 바뀌면 앱, 공통이면 DB)
       클라우드:   On-Prem → DBaaS → Serverless / OLTP vs OLAP / 트렌드
       운영:       보안 5계층 · 백업(RPO/RTO) · 모니터링(TPS/QPS/Latency)
```

---

*본 문서는 SK AX의 컨텐츠 자산을 학습 목적으로 정리한 것으로, 무단 사용 및 불법 배포 시 법적 조치를 받을 수 있습니다.*
