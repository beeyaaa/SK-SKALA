# 🔗 Day 2 — 스마트 데이터 이해 및 활용

> 💡 **Day 2 한 줄 요약**
> Day 1이 **"데이터를 어떻게 넣을 것인가(설계)"** 였다면, Day 2는 **"흩어진 데이터를 어떻게 합쳐서 의미를 뽑을 것인가(조회)"**.
> 그리고 그 도구는 딱 4가지 — **집계(GROUP BY) · 결합(JOIN) · 분해(서브쿼리/CTE) · 유지하며 계산(Window Function)**.

**출처** : AI 서비스를 위한 SW 기초 Full-stack Engineering (AI캠퍼스, 4일) > 4. 스마트 데이터 이해 및 활용 (백정열 / SK AX, 2026.6)
**범위** : 전체 482p 중 **Day 2 = 117~244p** (9~16장 + 참고 섹션)

---

## 📑 Day 2 목차

| # | 장 | 부제 | 핵심 질문 |
|---|---|------|-----------|
| 9 | **Day 1 복습 & DBMS 생태계** | DDL/DML 정리 · DBMS vs DW vs Data Mining · MSA 연동 | DB는 생태계 안에서 어디에 있나? |
| 10 | [SQL 중급 — 집계 & 그룹화](#10-sql-중급--집계--그룹화) | 집계함수 · GROUP BY · HAVING · ROLLUP · CUBE · FILTER | 여러 행을 어떻게 하나로 요약하나? |
| 11 | [SQL 고급 — JOIN 알고리즘](#11-sql-고급--join-알고리즘) | NL · Hash · Merge · BNL/BKA · DBMS별 엔진 | DB는 JOIN을 **어떻게** 수행하나? |
| 12 | [JOIN 종류 상세](#12-join-종류-상세) | INNER · OUTER · SELF · CROSS · Anti · Semi | 어떤 JOIN을 언제 쓰나? |
| 13 | [서브쿼리 & 집합 연산자](#13-서브쿼리--집합-연산자) | 스칼라·인라인뷰·상관 · EXISTS/IN/ANY/ALL · UNION/INTERSECT/EXCEPT | 쿼리 안에 쿼리를 어떻게 쓰나? |
| 14 | [CTE · View · Materialized View](#14-cte--view--materialized-view) | WITH · 재귀 CTE · 뷰 활용 전략 | 복잡한 쿼리를 어떻게 나누나? |
| 15 | [Window Function](#15-window-function--분석-함수) | ROW_NUMBER · RANK · NTILE · LAG/LEAD · 누적합 · 이동평균 | 행을 **유지하면서** 집계하려면? |
| ★ | [실전 패턴 & 최신 트렌드](#-실전-패턴--최신-트렌드-참고) | LATERAL · UPSERT · JSONB · pgvector · 안티패턴 | 현업에서 실제로 쓰는 것들 |
| 16 | [종합실습 – 2](#16-종합실습--2) | CampusHub — 복합 쿼리 25문항 | 직접 풀어보기 |

> 💬 **편집 안내** : 원본 자료는 9~15장 뒤에 `[참고] JOIN 심화`, `[참고] Window Function 심화` 등이 **따로 몰려 있습니다.** 이 문서에서는 각 참고 내용을 **주제가 맞는 장 안의 "🔖 심화" 절로 이동**시켰습니다. 어느 슬라이드에서 왔는지는 각 절에 표시했습니다.

---

# 9. Day 1 핵심 복습 & DBMS 생태계

> 📌 **다루는 것** : DDL/DML 정리 · DBMS vs DW vs Data Mining · MSA 연동

## 9-1. Day 1 빠른 복습

| 영역 | 핵심 |
|------|------|
| **DB 개요** | 파일 시스템의 한계 → DBMS 등장 / **ACID 4원칙**<br>**WAL** : 로그 먼저 → 데이터 파일 반영 → 장애 복구 보장<br>**Isolation Level** : RC → RR → Serializable<br>이상 현상 : **Dirty · Non-Repeatable · Phantom Read** |
| **관계형 모델** | 테이블 · **PK · FK · UK** · 관계(1:1 / 1:N / N:M)<br>**정규화 1NF ~ BCNF** — 부분종속(2NF), 이행종속(3NF), 비후보키 결정자(BCNF) |
| **ERD** | Entity · Attribute · Relationship / **IE 표기법**(까마귀발) / **개념→논리→물리** 3단계 |
| **DDL** | `CREATE TABLE`·제약조건·데이터 타입 / `ALTER TABLE` / DBMS별 차이<br>PK : `GENERATED ALWAYS AS IDENTITY`(PG) / `AUTO_INCREMENT`(MySQL) |
| **DML** | SELECT 실행 순서 `FROM→WHERE→GROUP→HAVING→SELECT→ORDER`<br>NULL 주의 : `= NULL`(❌) → **`IS NULL`(✅)** / `COALESCE()` / `CASE WHEN` |

---

## 9-2. DBMS vs Data Warehouse vs Data Mining

> 🔑 셋 다 "데이터를 다룬다"지만 **목적·응답시간·갱신방식이 전혀 다릅니다.**

| 구분 | **DBMS** | **Data Warehouse** | **Data Mining** |
|------|----------|--------------------|-----------------|
| **목적** | 일상 **트랜잭션 처리 (OLTP)** | 분석, **의사결정 지원 (OLAP)** | **숨겨진 패턴, 지식 발견** |
| **데이터 특성** | **현재** 데이터, **정규화**, 실시간 | **이력** 데이터, **비정규화**, 주기적 적재 | 대용량 데이터, 통계/ML 모델 |
| **쿼리 유형** | 단순 CRUD, **짧은 트랜잭션** | 복잡한 집계, **다차원 분석** | 분류, 군집, 연관, 예측 분석 |
| **예시 시스템** | MySQL, PostgreSQL, Oracle | **BigQuery, Snowflake, Redshift** | Python ML, Spark MLlib |
| **응답시간** | **ms ~ 초** | **초 ~ 분** | **분 ~ 시간** |
| **갱신방식** | 실시간 INSERT/UPDATE/DELETE | **배치 ETL** (야간 주기적 적재) | 배치/온라인 모델 학습 |

> 💡 **정규화 vs 비정규화가 여기서 갈립니다.** OLTP는 정합성이 중요하니 정규화, OLAP은 조회 속도가 중요하니 **일부러 비정규화**합니다. Day 1의 "무결성 vs 확장성" 저울이 여기서도 반복됩니다.

---

## 9-3. MSA 환경에서 DB 연동 — Kafka / Elasticsearch / Redis

### Kafka 연동 패턴

| 항목 | 내용 |
|------|------|
| **목적** | 비동기 메시징, **이벤트 기반 아키텍처**, 서비스 간 **decoupling** |
| **패턴** | DB 변경사항(**Event Sourcing**)을 Kafka Topic으로 전파 → 다른 마이크로서비스가 구독 |
| ⚠️ **주의** | Kafka 메시지 전송 **전에 DB COMMIT 완료** / 또는 **Kafka Transaction** 기능으로 atomic 처리 |
| **Schema Registry** | Producer/Consumer 간 스키마(**Avro/Protobuf**) 중앙 관리 → **호환성 보장** |

### Elasticsearch 연동

| 항목 | 내용 |
|------|------|
| **목적** | 빠른 검색, 필터링, 로그 분석, **비정형 텍스트 인덱싱** |
| **패턴** | DB → **Logstash/Debezium** → Elasticsearch 동기화 (**CDC 패턴**) |
| ⚠️ **주의** | ES는 **Eventually Consistent** → **실시간 정합성 보장 불가**, RDBMS와 **역할 분리 필요** |

### Redis 연동

| 항목 | 내용 |
|------|------|
| **목적** | 캐시(**Cache-Aside / Write-Through**), 세션 저장, Pub/Sub, Rate Limiting |
| **지표** | **캐시 히트율 목표 90%+** / **Cache Stampede 방지** (Lock 또는 Jitter) |
| ⚠️ **주의** | **데이터 유실** — persistence 설정(**RDB/AOF**) 확인 필수 |

---

# 10. SQL 중급 — 집계 & 그룹화

> 📌 **다루는 것** : 집계함수 · GROUP BY · HAVING · ROLLUP · CUBE · FILTER

## 10-1. 집계 함수 핵심 5가지

| 함수 | 설명 | ⚠️ 함정 |
|------|------|---------|
| **COUNT()** | 행의 개수 반환<br>• `COUNT(*)` : **NULL 포함** 전체<br>• `COUNT(col)` : **NULL 제외**<br>• `COUNT(DISTINCT col)` : 고유값 개수 | `COUNT(*)`와 `COUNT(col)`은 **다른 결과** |
| **SUM() / AVG()** | 합계, 평균<br>**NULL은 자동 제외** | **`AVG(NULL) = NULL`** — **0이 아닙니다!!!** |
| **MIN() / MAX()** | 최소값, 최대값<br>**문자열에도 사용 가능** (알파벳, 유니코드 순) | — |
| **FILTER** (PostgreSQL) | **조건부 집계**<br>`COUNT(*) FILTER (WHERE score >= 80)` | MySQL/Oracle은 미지원 →<br>`SUM(CASE WHEN score>=80 THEN 1 ELSE 0 END)` |

> 🔑 **가장 많이 틀리는 것** : `AVG`가 NULL을 **0으로 취급하지 않고 아예 계산에서 빼버린다**는 점. 10개 행 중 5개가 NULL이면 **5개로만 평균**을 냅니다.

---

## 10-2. GROUP BY / HAVING

```sql
-- GROUP BY: 그룹별 집계
-- SELECT 절에는 그룹 키 또는 집계함수만 사용 가능
SELECT department_id,
       COUNT(*)                AS emp_count,
       ROUND(AVG(salary), 0)   AS avg_salary,
       MAX(salary)             AS max_salary,
       MIN(salary)             AS min_salary
FROM   employees
WHERE  hire_date >= '2020-01-01'    -- 집계 전 행 필터 (WHERE)
GROUP BY department_id
HAVING COUNT(*) >= 3                -- 집계 후 그룹 필터 (HAVING)
   AND AVG(salary) >= 5000
ORDER BY avg_salary DESC;

-- COUNT DISTINCT: 중복 제거 후 개수
SELECT COUNT(DISTINCT customer_id) AS unique_buyers
FROM   orders WHERE amount >= 100;

-- PostgreSQL FILTER 절 (다른 DBMS: CASE WHEN으로 대체)
SELECT
  COUNT(*)                                          AS total,
  COUNT(*) FILTER (WHERE true_label = pred_label)   AS correct,
  ROUND(COUNT(*) FILTER (WHERE true_label = pred_label)::NUMERIC
        / COUNT(*), 3)                              AS accuracy
FROM   prediction_results;
```

> ✅ **Checkpoint — 이 한 줄만 기억하면 됩니다**
> - **`WHERE` = 집계 _전_ 행 필터**
> - **`HAVING` = 집계 _후_ 그룹 필터**

---

## 10-3. ROLLUP / CUBE — 다차원 소계 집계

```sql
-- 샘플 테이블
CREATE TABLE sales_summary (region TEXT, product TEXT, amount INT);
INSERT INTO sales_summary VALUES
  ('East','A',100),('East','B',150),('West','A',200),('West','B',50);
```

### ROLLUP — 계층적 소계 (지역별 → 전체합)

```sql
SELECT region, product, SUM(amount) AS total
FROM   sales_summary
GROUP BY ROLLUP(region, product);
```

| region | product | total | 의미 |
|--------|---------|-------|------|
| East | A | 100 | 상세 |
| East | B | 150 | 상세 |
| East | **NULL** | **250** | ← **East 소계** |
| West | A | 200 | 상세 |
| West | B | 50 | 상세 |
| West | **NULL** | **250** | ← **West 소계** |
| **NULL** | **NULL** | **500** | ← **전체 총계** |

### CUBE — 모든 조합 소계

```sql
SELECT region, product, SUM(amount) AS total
FROM   sales_summary
GROUP BY CUBE(region, product);
```
→ **ROLLUP 결과 + `(NULL, A, 300)`, `(NULL, B, 200)` 추가** (상품별 소계도 나옴)

### GROUPING() — NULL이 "집계용"인지 "실제 NULL"인지 구분

```sql
SELECT CASE WHEN GROUPING(region)=1  THEN '전체' ELSE region  END AS region_label,
       CASE WHEN GROUPING(product)=1 THEN '소계' ELSE product END AS product_label,
       SUM(amount) AS total
FROM   sales_summary
GROUP BY ROLLUP(region, product);
```

> ✅ **Checkpoint**
> - **ROLLUP** : 계층적 요약 (**빠름**)
> - **CUBE** : 모든 조합 (**느림**)
> - 결과의 **NULL = 해당 차원의 총합**

### DBMS별 지원 현황

| DBMS | ROLLUP | CUBE | GROUPING SETS | 특이사항 |
|------|:---:|:---:|:---:|---|
| **PostgreSQL** | ○ | ○ | ○ | `GROUPING()` 제공, **SQL 표준에 가장 근접** |
| **MySQL/MariaDB** | ○ (5.7+) | △ 일부 | ○ (8.0+) | ⚠️ **구버전은 CUBE 미지원 — 버전 확인 필수** |
| **Oracle** | ○ | ○ | ○ | `GROUPING_ID()` 추가 제공, **계층 집계가 강력** |
| **SQL Server** | ○ | ○ | ○ | `GROUPING()`, `GROUPING_ID()` 제공 |

---

## 10-4. 집계 쿼리 성능 최적화 5가지

| # | 포인트 | 내용 |
|---|--------|------|
| **1** | **SELECT에 GROUP BY 키 이외 컬럼 금지** | MySQL `ONLY_FULL_GROUP_BY` — 위반 시 **Error 또는 임의값 반환**<br>→ **GROUP BY에 포함하거나 집계 함수로 감쌀 것** |
| **2** | **OFFSET 페이지네이션의 함정** | `LIMIT 10 OFFSET 990` → DB가 **990개를 읽고 버린 후** 10개 반환 → **O(N)**<br>→ **Cursor/Keyset 방식** : `WHERE id > :last_id ORDER BY id LIMIT 10` |
| **3** | **ORDER BY + 인덱스 활용** | 인덱스 컬럼을 ORDER BY 기준으로 → **Sort 노드 제거** → 성능↑<br>`INDEX(dept_id, salary DESC)` → `GROUP BY dept_id ORDER BY salary DESC`에 최적 |
| **4** | **통계 테이블 전략** (대용량) | 자주 쓰는 집계값을 **별도 테이블에 미리 계산·저장**<br>예: `user_stats(user_id, total_orders, last_order_date)` — **트리거로 갱신**<br>또는 **Materialized View + 주기적 REFRESH** |
| **5** | **AI 서비스 연계** | 임베딩 클러스터별 평균 유사도, 태그 빈도 → GROUP BY로 분석 후 시각화 |

---

## 🔖 심화 [참고] — 집계 & DML

### ⓐ 트랜잭션 제어 — BEGIN / COMMIT / ROLLBACK / SAVEPOINT

```sql
-- 기본 트랜잭션 (PostgreSQL)
BEGIN;
  UPDATE account SET balance = balance - 10000 WHERE id = 'A';
  UPDATE account SET balance = balance + 10000 WHERE id = 'B';
COMMIT;    -- 성공 시 확정

-- 오류 발생 시 롤백
BEGIN;
  UPDATE account SET balance = balance - 10000 WHERE id = 'A';
  -- 만약 여기서 오류 →
ROLLBACK;  -- 전체 취소

-- SAVEPOINT: 중간 저장점 (부분 롤백)
BEGIN;
  INSERT INTO orders(customer_id, amount) VALUES(1, 50000);
  SAVEPOINT after_insert;                  -- 중간 저장
  INSERT INTO order_items(order_id, product_id) VALUES(lastval(), 99);
  -- 여기서 문제 발생 →
  ROLLBACK TO SAVEPOINT after_insert;      -- insert 이후만 취소
  -- COMMIT; 또는 ROLLBACK;
```

| DBMS | 트랜잭션 시작 문법 |
|------|-------------------|
| **PostgreSQL** | `BEGIN;` / `START TRANSACTION;` |
| **MySQL** | `START TRANSACTION;` / `BEGIN;` |
| **Oracle** | ⚠️ **DML 시작 시 자동 트랜잭션** (명시적 BEGIN 없음) |
| **SQL Server** | `BEGIN TRANSACTION;` / `BEGIN TRAN;` |

> 💡 **SAVEPOINT 활용** : 배치 처리 시 **청크 단위 커밋**, 오류 시 마지막 체크포인트로 롤백

### ⓑ DB별 AUTO COMMIT 정책

| DBMS | 기본 AUTO COMMIT | 묵시적 COMMIT 발생 |
|------|------------------|-------------------|
| **PostgreSQL** | **ON** | DDL 실행 (대부분 **트랜잭션 내 허용**) |
| **MySQL (InnoDB)** | **ON** | **DDL 실행** (ALTER/CREATE/DROP/TRUNCATE) → ⚠️ **롤백 불가** |
| **Oracle** | **OFF** (자동 시작) | **DDL 실행 전·후 자동 COMMIT** |
| **SQL Server** | **ON** | DDL은 트랜잭션 내 가능 (**ROLLBACK 가능**) |

### ⓒ 정렬(ORDER BY)과 NULL 처리

| 구분 | PostgreSQL | MySQL | Oracle | SQL Server |
|------|-----------|-------|--------|------------|
| **NULL 정렬 기본** | ASC이면 **NULL 마지막**<br>(NULLS LAST 기본) | ASC이면 **NULL 먼저**<br>DESC이면 NULL 나중 | ASC이면 **NULL 마지막**<br>(NULLS LAST 기본) | ASC에서 **NULL이 가장 앞** |
| **명시적 제어** | `ORDER BY col DESC NULLS LAST` | `ORDER BY ISNULL(col), col DESC` | `ORDER BY col DESC NULLS LAST` | `ORDER BY CASE WHEN col IS NULL THEN 1 ELSE 0 END, col` |
| **결과 제한** | `LIMIT n OFFSET m` | `LIMIT n OFFSET m` | `FETCH FIRST n ROWS ONLY`<br>`OFFSET m ROWS FETCH NEXT n` (12c+) | `SELECT TOP(n)`<br>`OFFSET m ROWS FETCH NEXT n` (표준) |

> ⚠️ **문자열 정렬 함정** : 숫자·날짜·문자열의 정렬 기준이 다릅니다. 문자로 저장하면 **`"10" < "9"`** (사전순)이 됩니다.

### ⓓ 페이지네이션 — OFFSET vs Cursor/Keyset

```sql
-- ❌ OFFSET 방식 (간단하지만 대용량에서 느림)
SELECT * FROM orders ORDER BY id LIMIT 10 OFFSET 9990;
-- 문제: DB가 9990개를 읽고 버린 후 10개만 반환 → O(N)
-- OFFSET이 클수록 더 느려짐 (100만 페이지 = 100만 행 스캔)

-- ✅ Cursor/Keyset 방식 (권장 — 항상 O(log N))
-- 첫 페이지
SELECT * FROM orders ORDER BY id LIMIT 10;
-- 반환된 마지막 row의 id = 1000 (예시)

-- 다음 페이지: 마지막 id 이후부터 바로 탐색
SELECT * FROM orders WHERE id > 1000 ORDER BY id LIMIT 10;
-- → 인덱스로 바로 1001부터 접근 → 항상 빠름

-- 정렬 기준이 고유하지 않을 때: 복합 조건
SELECT * FROM orders
WHERE (created_at, id) > ('2024-03-15', 500)
ORDER BY created_at, id LIMIT 10;
```

| | OFFSET | **Cursor/Keyset** |
|---|--------|-------------------|
| **성능** | O(N) — 페이지가 뒤로 갈수록 느려짐 | **O(log N) — 항상 일정** |
| **임의 페이지 이동** | ✅ 가능 (1→3→2) | ❌ **불가** |
| **적합한 UI** | 페이지 번호 있는 목록 | **무한 스크롤, "다음" 버튼만 있는 UI** |

### ⓔ 집계 함수 DBMS별 상세 비교

| 함수 | PostgreSQL | MySQL/MariaDB | Oracle | SQL Server |
|------|-----------|---------------|--------|------------|
| **COUNT(\*)** | 빠름<br>(MVCC 특성상 약간 느릴 수 있음) | **MyISAM**: 메타데이터로 빠름<br>**InnoDB**: 전체 스캔 | 인덱스 활용 적극적 | 통계 기반 빠름 |
| **COUNT(DISTINCT)** | 일반적으로 빠름 | 추가 정렬/해시 비용 | Hash 집계로 효율적 | Hash 집계 |
| **AVG(NULL)** | NULL 제외 자동 | NULL 제외 자동 | NULL 제외 자동 | NULL 제외 자동 |
| **FILTER 절** | **○** | ✗ (CASE WHEN 대체) | ✗ (CASE WHEN 대체) | ✗ (CASE WHEN 대체) |
| **STDDEV/VARIANCE** | ○ | ○ | ○ | ○ |
| **문자열 집계** | `STRING_AGG(col, sep)` | `GROUP_CONCAT(col)` | `LISTAGG(col, sep)` | `STRING_AGG(col, sep)` |

### ⓕ GROUP BY 실수 — ONLY_FULL_GROUP_BY

| DBMS | 동작 |
|------|------|
| **MySQL** (기본 활성) | SELECT 절에 GROUP BY 키 이외 **비집계 컬럼 포함 시 오류**<br>❌ `SELECT name, dept, COUNT(*) FROM emp GROUP BY dept`<br>✅ `SELECT dept, COUNT(*)` 또는 `GROUP BY dept, name` |
| **PostgreSQL** | GROUP BY 키에 없는 컬럼을 SELECT에 쓰면 **항상 오류** (엄격)<br>💡 **예외** : **기본키를 GROUP BY에 포함**하면 해당 테이블의 모든 컬럼 가능 |
| **Oracle** | SELECT 절 비집계 컬럼이 GROUP BY 키에 있어야 함 (표준 준수)<br>`ANY_VALUE(col)`로 임의값 선택 가능 (비표준) |

> 🔑 **실무 원칙**
> - **"SELECT에 쓸 컬럼 → GROUP BY에도 포함"**
> - **Window Function**은 GROUP BY 없이도 집계값과 개별 행을 함께 출력 가능
> - 복잡한 집계는 **CTE로 단계별 분리** → 실수 방지

### ⓖ AI 서비스 연계 — 벡터 임베딩 통계

> 테이블 : `embedding_store(id, user_id, cluster_id, similarity, tag)`

```sql
-- 1. 사용자별 임베딩 개수 및 평균 유사도
SELECT user_id,
       COUNT(*)                   AS total_embeddings,
       ROUND(AVG(similarity), 3)  AS avg_similarity,
       MAX(similarity)            AS best_match
FROM   embedding_store
GROUP BY user_id ORDER BY avg_similarity DESC;

-- 2. 클러스터별 통계 (k-means 결과 분석)
SELECT cluster_id,
       COUNT(*)                        AS cluster_size,
       ROUND(AVG(similarity), 3)       AS cohesion,
       COUNT(DISTINCT tag)             AS tag_variety,
       STRING_AGG(DISTINCT tag, ', ')  AS top_tags
FROM   embedding_store
GROUP BY cluster_id
HAVING COUNT(*) >= 5
ORDER BY cohesion DESC;

-- 3. 태그별 빈도 (워드클라우드용)
SELECT tag, COUNT(*) AS freq,
       ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 1) AS pct
FROM   embedding_store
GROUP BY tag ORDER BY freq DESC LIMIT 20;
```

> 💡 AI 파이프라인에서 GROUP BY 집계는 **임베딩 클러스터 품질 검증, 태그 빈도 분석**에 핵심적으로 활용됩니다.

---

# 11. SQL 고급 — JOIN 알고리즘

> 📌 **다루는 것** : NL · Hash · Merge · BNL/BKA · DBMS별 엔진 비교
> 🔑 **12장이 "어떤 JOIN을 쓸까"라면, 11장은 "DB가 그 JOIN을 어떻게 실행하는가"입니다.**

## 11-1. JOIN 알고리즘 4종

| 알고리즘 | 동작 방식 | 언제 유리한가 |
|----------|-----------|---------------|
| **Nested Loop Join (NLJ)** | 외부 테이블 **행마다** 내부 테이블 탐색<br>인덱스가 있으면 빠름 | **외부 집합이 작을 때** + **내부에 인덱스 있을 때** |
| **Hash Join (HJ)** | **작은 쪽**으로 해시테이블 생성 → **큰 쪽**으로 프로브 탐색<br>메모리 부족 시 디스크 활용 | **대용량 등가(=) 조인** / **인덱스 없을 때** |
| **Sort-Merge Join (SMJ)** | 양쪽을 **정렬 후 병합**하여 매칭 | **이미 정렬된 대용량** / **스트리밍 데이터**<br>💡 **범위/비등가 조인도 가능** |
| **BNL / BKA** (MySQL) | **Block Nested Loop** : 여러 행을 버퍼에 모아 내부 테이블 탐색<br>**Batched Key Access** : 모은 키를 배치로 인덱스 조회 | `join_buffer_size`로 튜닝 |

> 💡 **한 줄 정리**
> - **작은 것 × 큰 것 + 인덱스** → **Nested Loop**
> - **대형 × 대형** → **Hash**
> - **이미 정렬되어 있음** → **Sort-Merge**

## 11-2. DBMS별 JOIN 엔진 비교

| DBMS | 지원 알고리즘 | 기본 전략 | 특이사항 |
|------|--------------|-----------|----------|
| **PostgreSQL** | NLJ · Hash · Merge **+ 병렬 Hash** | **통계 기반 옵티마이저 자동 선택** | `enable_hashjoin`/`mergejoin`/`nestloop` 스위치 |
| **MySQL 8.0+** | NLJ · BNL · BKA **+ Hash (8.0.18+)** | 인덱스 있으면 **NLJ**, 없으면 **BNL** | `optimizer_switch`로 BNL/BKA/Hash 토글 |
| **SQL Server** | NLJ · Hash · Merge **+ Adaptive Join** | **Adaptive Join** : 실행 중 NL ↔ Hash **자동 전환** | ⚠️ 통계 부정확 시 **tempdb Spill** 주의 |
| **Oracle** | NLJ · Sort-Merge · Hash | 힌트: `USE_NL` / `USE_HASH` / `USE_MERGE` | Adaptive Plan / Stats Feedback |

## 11-3. 실행계획으로 JOIN 알고리즘 확인

```sql
-- PostgreSQL: EXPLAIN ANALYZE로 실제 조인 알고리즘 확인
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT s.name, c.title, e.score
FROM   students s
  JOIN enrollments e ON e.student_id = s.id
  JOIN courses     c ON c.id = e.course_id
WHERE  s.grade = 3;
```

**결과 해석**
```
Hash Join  (cost=12.5..45.8 rows=200 width=32)
           (actual time=0.5..2.3 rows=185 loops=1)
  Hash Cond: (e.student_id = s.id)
  Buffers: shared hit=12 read=5        ← 디스크 읽기 횟수
  ->  Seq Scan on enrollments          ← Full Scan (인덱스 필요?)
  ->  Hash
      ->  Index Scan on students       ← 인덱스 사용
            Index Cond: (grade = 3)
```

```sql
-- MySQL 8.0.18+: EXPLAIN ANALYZE로 Hash Join 확인
EXPLAIN ANALYZE
SELECT * FROM customers c JOIN orders o ON c.id = o.customer_id;
-- "-> Inner hash join (o.customer_id = c.id)"
-- ⚠️ Hash Batches > 1 → work_mem 증가 검토 (메모리 Spill 발생)
```

> ✅ **실행계획 핵심 체크 4가지**
> 1. **조인 알고리즘 타입** (Hash / Nested Loop / Merge)
> 2. **actual rows vs rows(예측)** — 크게 다르면 **통계가 오래된 것**
> 3. **Buffers** — shared hit(캐시) vs read(디스크)
> 4. **Spill 여부** — Hash Batches > 1이면 메모리 부족 신호

## 11-4. JOIN 성능 튜닝 체크리스트

### 공통 원칙

- ✅ **FK 컬럼에 반드시 인덱스!** (`ON DELETE CASCADE` 대상 컬럼 포함)
- ✅ 작은 테이블 × 큰 테이블 + 인덱스 → **Nested Loop**
- ✅ 대형 × 대형 → **Hash**
- ⚠️ **ON 조건 누락 주의** → **카르테시안 곱 (N×M행)** 발생

### DBMS별 튜닝

| DBMS | 튜닝 포인트 |
|------|------------|
| **PostgreSQL** | • 큰 동등 조인 → **`work_mem` 늘리기** / `hash_mem_multiplier` 확인<br>• `enable_parallel_hash=on`, `max_parallel_workers_per_gather` 상향<br>• ⚠️ **Hash Batches > 1 → Spill 발생 → work_mem 부족 신호** |
| **MySQL** | • 인덱스 부재 조인 → BNL/BKA → **`join_buffer_size` 적절히 설정**<br>• 8.0.18+ → Hash Join 후보 → `EXPLAIN ANALYZE`로 확인<br>• ⚠️ **과대 설정 주의 : 스레드 × 조인 수만큼 메모리 할당됨** |
| **SQL Server** | • **tempdb Spill** (Hash/Sort Warning) 감지 → **통계 갱신, MAXDOP 조정**<br>• **Adaptive Join** 활용 (2017+) : 런타임에 NL ↔ Hash 자동 전환 |

---

# 12. JOIN 종류 상세

> 📌 **다루는 것** : INNER · OUTER · SELF · CROSS · Anti-Join · Semi-Join

## 12-1. JOIN의 본질

> 🔑 **두 테이블의 카르테시안 곱(Cartesian Product) + 조건 필터링**
> `A JOIN B ON 조건` → 내부적으로 **A × B 후 조건을 만족하는 행만 반환**

**이걸 이해하면 "ON 조건을 빼먹으면 왜 행이 폭발하는지"가 자동으로 설명됩니다.**

## 12-2. JOIN 종류 6가지

| JOIN | 설명 | 비고 |
|------|------|------|
| **INNER JOIN** | 두 테이블에 **모두 매칭되는 행만** (교집합) | 가장 일반적. **`JOIN`만 쓰면 INNER JOIN** |
| **LEFT OUTER JOIN** | **왼쪽 전체** + 오른쪽 없으면 NULL | "모든 A를 보여주고, B 없으면 NULL로"<br>→ **미수강 학생도 표시** |
| **RIGHT OUTER JOIN** | **오른쪽 전체** + 왼쪽 없으면 NULL | 💡 **LEFT JOIN으로 방향 바꿔 쓰는 것이 실무 관례** (가독성) |
| **FULL OUTER JOIN** | **양쪽 모두 전체 보존** | ⚠️ **MySQL 미지원** → `LEFT JOIN UNION RIGHT JOIN`으로 우회 |
| **SELF JOIN** | 같은 테이블을 2개처럼 조인 | **계층형 데이터** (직원–상사) |
| **CROSS JOIN** | 카르테시안 곱 (N × M행) | ⚠️ **의도적으로만 사용, 실수 주의** |

## 12-3. INNER / LEFT / RIGHT / FULL 실전 코드

```sql
-- 샘플: student(id, name), enroll(student_id, course, grade)

-- INNER JOIN: 수강한 학생만
SELECT s.name, e.course, e.grade
FROM   student s INNER JOIN enroll e ON s.id = e.student_id;
-- → 양쪽에 공통으로 있는 행만

-- LEFT OUTER JOIN: 모든 학생 (수강 없으면 NULL)
SELECT s.name, e.course, e.grade
FROM   student s LEFT JOIN enroll e ON s.id = e.student_id;
-- → 수강 없는 학생도 포함 (course, grade = NULL)

-- RIGHT OUTER JOIN: 모든 수강 기록 (학생 없으면 NULL)
SELECT s.name, e.course
FROM   student s RIGHT JOIN enroll e ON s.id = e.student_id;
-- → 고아 수강(학생 없는 enroll)도 포함

-- FULL OUTER JOIN (MySQL 미지원 → UNION 우회)
SELECT s.name, e.course FROM student s LEFT  JOIN enroll e ON s.id = e.student_id
UNION
SELECT s.name, e.course FROM student s RIGHT JOIN enroll e ON s.id = e.student_id;
-- PostgreSQL/Oracle/SQL Server: FULL OUTER JOIN 직접 지원
```

## 12-4. SELF JOIN / CROSS JOIN / Anti-Join

```sql
-- SELF JOIN: 직원-상사 계층 조회
SELECT e.name AS employee, m.name AS manager
FROM   employees e
  LEFT JOIN employees m ON m.id = e.manager_id
ORDER BY m.name NULLS FIRST, e.name;

-- Anti-Join: 한 번도 수강하지 않은 학생 (3가지 방법)

-- 방법 1: LEFT JOIN + IS NULL (직관적)
SELECT s.name FROM student s
  LEFT JOIN enroll e ON e.student_id = s.id
WHERE e.student_id IS NULL;

-- 방법 2: NOT EXISTS (성능 우수, NULL 안전 — ⭐권장)
SELECT s.name FROM student s
WHERE NOT EXISTS (SELECT 1 FROM enroll e WHERE e.student_id = s.id);

-- 방법 3: NOT IN (⚠️ NULL 함정 주의!)
-- 서브쿼리에 NULL이 있으면 전체 결과가 빈 집합!
SELECT s.name FROM student s WHERE s.id NOT IN (SELECT student_id FROM enroll);

-- CROSS JOIN: 전체 학생 × 전체 강좌 조합 (추천 후보 생성)
SELECT s.id AS student_id, c.id AS course_id
FROM   students s CROSS JOIN courses c
LIMIT 100;   -- ⚠️ 실수 방지: 반드시 LIMIT 또는 의도 확인
```

> ✅ **Checkpoint** : `NOT IN` vs `NOT EXISTS` — **NULL 안전성·성능 모두 `NOT EXISTS`가 우수**. **`NOT EXISTS`를 선호하세요.**

## 12-5. 실무 집계 JOIN

```sql
-- 고객별 주문건수·총액 (LEFT JOIN: 주문 없는 고객도 포함)
SELECT
  c.customer_name,
  COUNT(o.order_id)          AS order_count,
  COALESCE(SUM(o.amount), 0) AS total_spent,
  MAX(o.order_date)          AS last_order_date
FROM   customers c
  LEFT JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name
ORDER BY total_spent DESC;

-- 총액 상위 10명 (CTE 활용)
WITH customer_stats AS (
  SELECT c.customer_name,
         COUNT(o.order_id) AS cnt, SUM(o.amount) AS total
  FROM   customers c LEFT JOIN orders o ON o.customer_id = c.customer_id
  GROUP BY c.customer_id, c.customer_name
)
SELECT customer_name, cnt, total
FROM   customer_stats
ORDER BY total DESC
LIMIT 10;
```

> 💡 **`COUNT(o.order_id)`를 쓰는 이유** : LEFT JOIN에서 주문 없는 고객은 `order_id`가 NULL이라 **`COUNT(col)`은 0**이 됩니다. `COUNT(*)`를 쓰면 **1**이 나와서 틀립니다.

## 12-6. JOIN 주의사항 및 성능 팁

| 항목 | 문제 | 해결책 |
|------|------|--------|
| **ON 조건 누락** | CROSS JOIN 발생 (**N×M 행 폭발**) | 반드시 ON 조건 명시, **EXPLAIN으로 확인** |
| **OUTER JOIN 후 WHERE 필터** | **사실상 INNER JOIN으로 변환**됨 | `WHERE b.col IS NULL`은 **Anti-Join 패턴**으로 의도적 사용 |
| **중복 행 폭발** | 1:N 조인 시 N개만큼 행 증가 | **서브쿼리에서 집계 후 조인**, 또는 DISTINCT |
| **NULL과 조인** | FK가 NULL이면 INNER JOIN에서 제외 | 의도적 포함: **LEFT JOIN + COALESCE** |
| **FK 인덱스 미생성** | JOIN 시 Full Scan 발생 | **FK 컬럼에 반드시 INDEX 생성** |
| **대용량 CROSS JOIN** | 메모리/시간 폭발 | **LIMIT 또는 LATERAL로 제한** |

---

## 🔖 심화 [참고] — JOIN 실전 패턴

### ⓐ ⭐ ON 절 vs WHERE 절 — OUTER JOIN에서의 결정적 차이

> **시나리오** : 모든 학생과 수강 정보를 보되(수강 없으면 NULL), **CS101 과목 성적만** 보고 싶다.

```sql
-- ❌ 잘못된 방법: WHERE 절에서 필터 → 사실상 INNER JOIN
SELECT s.name, e.score
FROM   students s LEFT JOIN enrollments e ON e.student_id = s.id
WHERE  e.course_id = 1;
-- LEFT JOIN 효과 사라짐! 수강 없는 학생 제외됨

-- ✅ 올바른 방법: ON 절에서 조건 추가 → LEFT JOIN 유지
SELECT s.name, e.score
FROM   students s
  LEFT JOIN enrollments e ON e.student_id = s.id AND e.course_id = 1;
-- → 수강 없는 학생: score = NULL로 표시됨
```

| | **ON 절 조건** | **WHERE 절 조건** |
|---|---------------|-------------------|
| **적용 시점** | **조인 과정에서** 적용 | **조인 완료 후** 행 필터 |
| **OUTER JOIN 결과** | **유지됨** (NULL 행 보존) | **NULL 행 제거 → INNER JOIN화** |
| **언제 쓰나** | OUTER JOIN 결과를 유지하면서 특정 조건 필요할 때 | 의도적으로 INNER JOIN처럼 쓰고 싶을 때 |

> 🔑 **핵심** : LEFT JOIN에서 WHERE로 **우측 테이블을 필터링**하면 — **Anti-Join 패턴(`IS NULL`)만 예외로** — 사실상 INNER JOIN이 됩니다.

### ⓑ Semi-Join — 존재 여부만 확인하는 조인

> 오른쪽 테이블의 **존재 여부만 확인**, 오른쪽 컬럼은 반환하지 않음.
> `IN`과 `EXISTS`는 내부적으로 **Semi-Join으로 최적화**됩니다.

```sql
-- EXISTS (⭐권장): 행 하나라도 있으면 TRUE
SELECT s.name FROM students s
WHERE EXISTS (SELECT 1 FROM enrollments e
              WHERE e.student_id = s.id AND e.score >= 90);

-- IN (소량 목록에 적합)
SELECT name FROM students
WHERE major_id IN (SELECT id FROM majors WHERE region = 'Seoul');

-- JOIN으로 구현 (⚠️ DISTINCT 필요 → 중복 발생 가능)
SELECT DISTINCT s.name
FROM   students s JOIN enrollments e ON e.student_id = s.id
WHERE  e.score >= 90;
-- DISTINCT 없으면 90점 이상 과목 수만큼 중복 행 발생

-- Anti Semi-Join: 존재하지 않는 경우
SELECT s.name FROM students s
WHERE NOT EXISTS (SELECT 1 FROM enrollments e WHERE e.student_id = s.id);
```

### ⓒ JOIN 종류별 결과 행 수 예측

> **A(5행) JOIN B(3행), 매칭 2건**인 경우

| JOIN 종류 | 계산 | 결과 행 수 | NULL 포함 컬럼 |
|-----------|------|-----------|----------------|
| **INNER JOIN** | 매칭만 | **2행** | 없음 |
| **LEFT JOIN** | A전체 + B매칭 | **5행** | B컬럼 (3행은 NULL) |
| **RIGHT JOIN** | A매칭 + B전체 | **3행** + 비매칭A | A컬럼 (일부 NULL) |
| **FULL OUTER JOIN** | A전체 + B전체 − 겹침 | **5+3−2 = 6행** | 양쪽 비매칭 컬럼 |
| **CROSS JOIN** | 전체 조합 | **5×3 = 15행** | 없음 |
| **Anti-Join** (NOT EXISTS) | A에서 B매칭 제외 | **5−2 = 3행** | 없음 |

### ⓓ 다중 테이블 JOIN — 5개 테이블 실전 쿼리

```sql
-- 학생-학과-수강-강좌-교수 5개 테이블 JOIN
SELECT
  s.student_no  AS 학번,
  s.name        AS 학생,
  d.name        AS 학과,
  c.code        AS 강좌코드,
  c.title       AS 강좌명,
  p.name        AS 담당교수,
  e.score       AS 점수,
  CASE
    WHEN e.score >= 90 THEN 'A'
    WHEN e.score >= 80 THEN 'B'
    WHEN e.score >= 70 THEN 'C'
    WHEN e.score >= 60 THEN 'D'
    ELSE 'F'
  END           AS 학점
FROM   students s
  JOIN departments d ON d.id = s.department_id
  JOIN enrollments e ON e.student_id = s.id
  JOIN courses     c ON c.id = e.course_id
  JOIN professors  p ON p.id = c.professor_id
WHERE  s.enrolled = TRUE
  AND  e.score IS NOT NULL
ORDER BY s.name, e.score DESC;
```

> ✅ **Checkpoint** : ON 조건 누락 시 CROSS JOIN 발생 주의 — **5개 테이블이면 4개의 ON 조건이 필요**합니다.

### ⓔ JOIN 실수 패턴 5가지 및 방지법

| 실수 | 증상 | 방지법 |
|------|------|--------|
| **ON 조건 누락** | 카르테시안 곱 폭발 | `FROM a JOIN b` → 반드시 `ON a.id = b.a_id`<br>**EXPLAIN에서 actual rows가 예상보다 훨씬 많으면 의심** |
| **OUTER JOIN 후 WHERE로 NULL 필터** | INNER JOIN으로 변환됨 | `AND b.col IS NOT NULL` 조건을 **WHERE 대신 ON 절에** 추가 |
| **중복 행 폭발 (1:N)** | COUNT(*) 결과가 이상하게 큼 | **서브쿼리에서 집계 후 JOIN**, 또는 DISTINCT |
| **NOT IN의 NULL 함정** | 결과가 **항상 빈 집합** | **`NOT IN` → `NOT EXISTS`로 변경** |
| **옵티마이저 오판** | 큰 테이블을 Small Table처럼 JOIN | **`ANALYZE` 실행으로 통계 갱신** / EXPLAIN으로 rows 예측값 확인 |

---

# 13. 서브쿼리 & 집합 연산자

> 📌 **다루는 것** : 스칼라·인라인뷰·상관 서브쿼리 · EXISTS/IN/ANY/ALL · UNION/INTERSECT/EXCEPT

## 13-1. 서브쿼리 4가지 유형 — 위치로 구분

| 유형 | 위치 | 예시 | 특징 |
|------|------|------|------|
| **스칼라 서브쿼리** | **SELECT 절** | `SELECT name, (SELECT COUNT(*) FROM orders o WHERE o.cust_id=c.id) AS order_count FROM customers c` | **단일 값 하나만** 반환<br>⚠️ **행마다 실행 → 성능 주의**, JOIN으로 대체 검토 |
| **인라인 뷰** | **FROM 절** | `SELECT * FROM (SELECT *, ROW_NUMBER() OVER(...) AS rn FROM orders) sub WHERE rn <= 5` | **임시 테이블처럼** 사용<br>**페이지네이션에 자주 사용** |
| **WHERE 절 서브쿼리** | **WHERE 절** | `WHERE salary > (SELECT AVG(salary) FROM employees)` | 단일값: `=` / 다중행: `IN/ANY/ALL/EXISTS`<br>**소량 데이터에 유리** |
| **상관 서브쿼리**<br>(Correlated) | 주로 WHERE | `WHERE salary > (SELECT AVG(salary) FROM employees WHERE dept_id = e.dept_id)` | ⚠️ **바깥 쿼리의 컬럼 참조 → 행마다 독립 실행**<br>**JOIN/CTE로 대체 권장** |

## 13-2. EXISTS / IN / ANY / ALL

```sql
-- IN: 목록 또는 서브쿼리 결과에 포함 여부
SELECT name FROM students
WHERE major_id IN (SELECT id FROM majors WHERE region = 'Seoul');

-- EXISTS: 서브쿼리에 행이 하나라도 존재하면 TRUE (더 효율적)
SELECT name FROM students s
WHERE EXISTS (SELECT 1 FROM enrollments e WHERE e.student_id = s.id);

-- NOT EXISTS (⭐권장): NOT IN보다 안전하고 성능 우수
SELECT name FROM students s
WHERE NOT EXISTS (SELECT 1 FROM enrollments e WHERE e.student_id = s.id);

-- ⚠️ NOT IN의 NULL 함정
-- 서브쿼리에 NULL 하나라도 있으면 전체 결과가 빈 집합!
WHERE id NOT IN (SELECT student_id FROM enrollments)
-- enrollments.student_id에 NULL이 있으면 항상 FALSE → 빈 결과

-- ANY: 하나 이상 조건 만족 (> ANY = > MIN과 동일)
WHERE salary > ANY (SELECT salary FROM employees WHERE dept = 'HR')

-- ALL: 모든 값에 대해 조건 만족 (> ALL = > MAX와 동일)
WHERE salary > ALL (SELECT salary FROM employees WHERE dept = 'HR')
```

> ✅ **Checkpoint**
> - **EXISTS vs IN** : EXISTS는 **행 존재만 확인** (`SELECT 1`) → **대용량에서 IN보다 빠름**
> - **`NOT IN`은 NULL 위험** → `NOT EXISTS` 사용
> - **`> ANY` = `> MIN`**, **`> ALL` = `> MAX`** 로 외우면 편합니다

## 13-3. 집합 연산자 — UNION / INTERSECT / EXCEPT

```sql
-- UNION: 합집합 (중복 제거)
SELECT name FROM students_2024
UNION
SELECT name FROM students_2025;   -- 같은 이름은 1번만 출력

-- UNION ALL: 합집합 (중복 포함, ⭐성능 빠름)
SELECT 'sale'   AS type, product_id, amount FROM sales
UNION ALL
SELECT 'refund' AS type, product_id, amount FROM refunds;

-- INTERSECT: 교집합
SELECT customer_id FROM orders WHERE EXTRACT(YEAR FROM order_date)=2024
INTERSECT
SELECT customer_id FROM orders WHERE EXTRACT(YEAR FROM order_date)=2025;
-- → 2024~2025년 모두 구매한 고객

-- EXCEPT (Oracle: MINUS): 차집합
SELECT student_id FROM enrollments WHERE course='DB'
EXCEPT
SELECT student_id FROM enrollments WHERE course='Algorithm';
-- → DB 수강 but 알고리즘 미수강 학생

-- ⚠️ MySQL INTERSECT/EXCEPT 미지원 → NOT EXISTS 우회
SELECT name FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_name = c.name);
```

> ✅ **Checkpoint** : **`UNION ALL`이 `UNION`보다 빠릅니다** (정렬/비교 불필요). **중복이 없거나 상관없으면 `UNION ALL`을 쓰세요.**

### 집합 연산자 DBMS별 지원 비교

| 연산자 | PostgreSQL | MySQL | Oracle | SQL Server | 비고 |
|--------|:---:|:---:|:---:|:---:|---|
| **UNION ALL** | ○ | ○ | ○ | ○ | 모든 DBMS 지원, 중복 포함 |
| **UNION** | ○ | ○ | ○ | ○ | 중복 제거 (**정렬 비용**) |
| **INTERSECT** | ○ | ○ (8.0.31+) | ○ | ○ | MySQL 이전 버전: **EXISTS로 대체** |
| **EXCEPT** | ○ | ✗ | ▲ (`MINUS`) | ○ | MySQL: `NOT EXISTS` / `LEFT JOIN + IS NULL` |
| **INTERSECT ALL** | ○ | ✗ | ✗ | ✗ | 빈도 기반 교집합 (희귀) |
| **EXCEPT ALL** | ○ | ✗ | ✗ | ✗ | 빈도 기반 차집합 (희귀) |

---

## 🔖 심화 [참고] — 상관 서브쿼리 최적화

> ⚠️ 상관 서브쿼리는 **바깥 쿼리의 행마다 내부 쿼리를 반복 실행** → **행 수 × 내부 쿼리 비용** = 성능 문제

```sql
-- ❌ 느린 방법: 상관 서브쿼리 (N × M)
SELECT e.emp_name, e.salary, e.dept_id
FROM   employees e
WHERE  e.salary > (
  SELECT AVG(salary) FROM employees WHERE dept_id = e.dept_id
);

-- ✅ 빠른 방법 1: CTE로 한 번만 집계
WITH dept_avg AS (
  SELECT dept_id, AVG(salary) AS avg_sal FROM employees GROUP BY dept_id
)
SELECT e.emp_name, e.salary, d.avg_sal
FROM   employees e JOIN dept_avg d ON d.dept_id = e.dept_id
WHERE  e.salary > d.avg_sal;

-- ✅ 빠른 방법 2: Window Function (가장 우아)
--    ⚠️ 단, 한 겹 감싸야 합니다 (아래 정오 참고)
SELECT * FROM (
  SELECT emp_name, salary, dept_id,
         AVG(salary) OVER (PARTITION BY dept_id) AS dept_avg
  FROM   employees
) t
WHERE salary > dept_avg;
-- → 한 번의 스캔으로 집계까지 처리
```

> 🚨 **[정오] 자료 191p 원문은 실행되지 않습니다**
>
> 원문에는 아래처럼 적혀 있으나 **에러가 납니다.**
> ```sql
> WHERE salary > AVG(salary) OVER (PARTITION BY dept_id);   -- ❌
> -- ERROR: window functions are not allowed in WHERE
> ```
> **이유** — 실행 순서가 `WHERE → … → Window 계산 → SELECT` 이므로, **WHERE 시점엔 Window 결과가 아직 없습니다.**
> **해결** — 위 코드처럼 **서브쿼리 또는 CTE로 한 겹 감싸세요.**
> 같은 이유로 **`GROUP BY`, `HAVING`에도 쓸 수 없습니다.** Window를 쓸 수 있는 곳은 **`SELECT` 절과 `ORDER BY` 절뿐**입니다.

> ✅ **Checkpoint** : 상관 서브쿼리는 **가독성은 좋지만 성능이 나쁩니다** → **CTE 또는 Window Function**으로 바꾸세요.

---

# 14. CTE · View · Materialized View

> 📌 **다루는 것** : WITH · 재귀 CTE · 뷰 활용 전략

## 14-1. CTE (Common Table Expression) — WITH 절

```sql
-- 기본 CTE: 복잡한 쿼리를 단계별로 분해
WITH dept_avg AS (
  SELECT dept_id, AVG(salary) AS avg_sal
  FROM   employees
  GROUP BY dept_id
)
SELECT e.emp_name, e.salary, d.avg_sal,
       e.salary - d.avg_sal AS diff
FROM   employees e
  JOIN dept_avg d ON d.dept_id = e.dept_id
WHERE  e.salary > d.avg_sal
ORDER BY diff DESC;
```

**다중 CTE — 여러 단계 분리**

```sql
WITH
-- 1단계: 학과별 평균 성적
major_avg AS (
  SELECT s.major_id, AVG(e.score) AS avg_score
  FROM   students s JOIN enrollments e ON e.student_id = s.id
  GROUP BY s.major_id
),
-- 2단계: 학과 평균보다 높은 학생 필터
top_students AS (
  SELECT s.id, s.name, s.major_id, AVG(e.score) AS my_avg
  FROM   students s JOIN enrollments e ON e.student_id = s.id
  GROUP BY s.id, s.name, s.major_id
  HAVING AVG(e.score) > (SELECT avg_score FROM major_avg m
                         WHERE m.major_id = s.major_id)
)
SELECT t.name, m.avg_score AS major_avg, t.my_avg
FROM   top_students t JOIN major_avg m ON m.major_id = t.major_id
ORDER BY t.my_avg DESC;
```

> ✅ **CTE 장점 3가지** : **가독성 향상** / **재사용 가능** / **재귀 쿼리 지원**
> 💡 **서브쿼리가 복잡하면 CTE로 분해**하세요.

## 14-2. 재귀 CTE — 계층형 데이터 탐색

```sql
-- 조직도: 최상위 관리자부터 하위 직원까지 전체 탐색
WITH RECURSIVE org_tree AS (
  -- 기저 단계(Anchor): 최상위 관리자 (manager_id IS NULL)
  SELECT id, emp_name, manager_id,
         1              AS depth,
         emp_name::TEXT AS path
  FROM   employees
  WHERE  manager_id IS NULL

  UNION ALL

  -- 재귀 단계: 하위 직원 추가
  SELECT e.id, e.emp_name, e.manager_id,
         t.depth + 1,
         t.path || ' > ' || e.emp_name
  FROM   employees e
    JOIN org_tree t ON t.id = e.manager_id
  WHERE  t.depth < 10       -- ⚠️ 무한 재귀 방지! 항상 필요
)
SELECT depth,
       REPEAT('  ', depth - 1) || emp_name AS indented_name,
       path
FROM   org_tree
ORDER BY path;
```

> 🔑 **재귀 CTE의 구조는 항상 이 3덩어리입니다**
> ```
> ① 기저 단계 (Anchor)  : 시작점 — 보통 WHERE parent IS NULL
>    UNION ALL
> ② 재귀 단계           : 자기 자신(CTE)을 JOIN
> ③ 종료 조건           : WHERE depth < N  ← 빼먹으면 무한 루프!
> ```
>
> **활용** : 조직도, **카테고리 트리**(e-commerce), 경로 탐색

## 14-3. View / Materialized View

```sql
-- 일반 View: 조회할 때마다 쿼리 실행 (항상 최신 데이터)
CREATE OR REPLACE VIEW v_student_dashboard AS
SELECT s.id, s.student_no, s.name, m.name AS major_name,
       COUNT(e.id)             AS course_count,
       ROUND(AVG(e.score), 2)  AS avg_score,
       MAX(e.score)            AS best_score,
       SUM(c.credits)          AS total_credits
FROM   students s
  LEFT JOIN majors      m ON m.id = s.major_id
  LEFT JOIN enrollments e ON e.student_id = s.id
  LEFT JOIN courses     c ON c.id = e.course_id
GROUP BY s.id, s.student_no, s.name, m.name;

-- View 조회 (일반 테이블처럼 사용)
SELECT * FROM v_student_dashboard WHERE avg_score >= 85;

-- Materialized View (PostgreSQL): 결과를 디스크에 저장 → 빠른 조회
CREATE MATERIALIZED VIEW mv_monthly_sales AS
SELECT DATE_TRUNC('month', order_date) AS month,
       SUM(amount)                     AS total_sales
FROM   orders
GROUP BY 1;

CREATE INDEX ON mv_monthly_sales (month);   -- ⭐인덱스 생성 가능!

-- 갱신 (자동 아님 → 스케줄러 또는 pg_cron 필요)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_sales;  -- 잠금 없이 갱신
```

> 💡 **View 활용 3가지** : **권한 제어**(민감 컬럼 숨기기) / **복잡한 쿼리 재사용** / **인터페이스 안정화**

## 14-4. ⭐ View vs Materialized View vs CTE 비교

| 구분 | **View** | **Materialized View** | **CTE** |
|------|----------|----------------------|---------|
| **데이터 저장** | 저장 안 함 | **결과를 디스크에 저장** | 저장 안 함 (쿼리 내 임시) |
| **데이터 최신성** | **항상 최신** | **Refresh 시점까지만** | 쿼리 실행 시점 |
| **인덱스 생성** | ❌ 불가 | ✅ **가능 (강력한 장점)** | ❌ 불가 |
| **재사용** | 여러 쿼리에서 재사용 | 여러 쿼리에서 재사용 | **해당 쿼리에서만** |
| **자동 갱신** | 자동 (쿼리 실행할 때마다) | ⚠️ **수동 Refresh 필요** | 자동 |
| **사용 예시** | 권한 제어, 인터페이스 | **대시보드, 집계 캐시** | 복잡한 쿼리 분해 |

---

## 🔖 심화 [참고] — CTE 고급 & PIVOT

### ⓐ CTE MATERIALIZED vs NOT MATERIALIZED (PostgreSQL 12+)

```sql
-- NOT MATERIALIZED (기본): 인라인으로 펼쳐서 최적화 허용
WITH dept_stats AS NOT MATERIALIZED (
  SELECT department_id, COUNT(*) AS cnt, AVG(salary) AS avg_sal
  FROM   employees GROUP BY department_id
)
SELECT e.name, ds.avg_sal
FROM   employees e JOIN dept_stats ds ON ds.department_id = e.department_id
WHERE  e.salary > ds.avg_sal;
-- → 옵티마이저가 CTE를 JOIN 최적화에 포함 가능

-- MATERIALIZED: 결과를 임시 저장 후 재사용 (한 번만 실행)
WITH expensive_calc AS MATERIALIZED (
  SELECT DISTINCT customer_id, COUNT(DISTINCT product_id) AS variety
  FROM   orders WHERE order_date >= '2024-01-01'
)
SELECT c.name, ec.variety
FROM   customers c JOIN expensive_calc ec ON ec.customer_id = c.id
WHERE  ec.variety >= 5;
```

> ✅ **언제 MATERIALIZED를 쓰나?**
> 1. **CTE가 여러 번 참조**될 때
> 2. 내부에 **랜덤 함수** 포함 (`random()`, `now()`)
> 3. **옵티마이저가 잘못된 플랜을 선택**할 때 강제 고정

### ⓑ PIVOT — 행을 열로 변환 (CASE WHEN 방식)

```sql
-- 월별 카테고리별 매출을 행 → 열로 피벗
-- (PostgreSQL/MySQL은 동적 피벗 없음 → CASE WHEN 사용)
SELECT
  product_category,
  SUM(CASE WHEN EXTRACT(MONTH FROM order_date)=1 THEN amount ELSE 0 END) AS jan,
  SUM(CASE WHEN EXTRACT(MONTH FROM order_date)=2 THEN amount ELSE 0 END) AS feb,
  SUM(CASE WHEN EXTRACT(MONTH FROM order_date)=3 THEN amount ELSE 0 END) AS mar,
  SUM(CASE WHEN EXTRACT(MONTH FROM order_date)=4 THEN amount ELSE 0 END) AS apr,
  SUM(CASE WHEN EXTRACT(MONTH FROM order_date)=5 THEN amount ELSE 0 END) AS may,
  SUM(CASE WHEN EXTRACT(MONTH FROM order_date)=6 THEN amount ELSE 0 END) AS jun,
  SUM(amount)                                                            AS h1_total
FROM   orders
WHERE  EXTRACT(YEAR FROM order_date) = 2024
GROUP BY product_category
ORDER BY h1_total DESC;
```

> 💡 **SQL Server/Oracle**은 `PIVOT` 문법을 직접 지원. **PostgreSQL**은 `tablefunc` 확장의 `crosstab()` 활용 가능.

### ⓒ ⭐ 서브쿼리 vs CTE vs Window Function vs JOIN — 선택 기준

| 도구 | 언제 쓰나 |
|------|-----------|
| **서브쿼리** | • 단순하고 **한 번만** 사용되는 조건<br>• 소량 데이터의 `IN` 체크<br>• `EXISTS`로 **존재 여부만** 확인 |
| **CTE** | • 복잡한 쿼리를 **단계별로 분해** → 가독성<br>• 같은 집계 결과를 **여러 곳에서 재사용**<br>• **재귀 쿼리** (조직도, 카테고리 트리)<br>• 서브쿼리가 **3단계 이상 중첩**될 때 |
| **Window Function** | • **원래 행을 유지하면서** 집계값 필요 (순위, 누적, 비교)<br>• **상관 서브쿼리로 느린 경우** (부서 평균보다 높은 사원)<br>• `LAG`/`LEAD`로 **이전/다음 행 값** 필요<br>• `ROWS`/`RANGE` 프레임으로 이동 집계 |
| **JOIN** | • 두 테이블의 데이터를 함께 조회 → **항상 JOIN 우선 고려**<br>• `EXISTS`/`IN`으로 표현한 서브쿼리가 복잡해질 때 |

---

# 15. Window Function – 분석 함수

> 📌 **다루는 것** : ROW_NUMBER · RANK · DENSE_RANK · NTILE · LAG · LEAD · 누적합 · 이동평균

## 15-1. ⭐ GROUP BY와의 핵심 차이

| | **GROUP BY** | **Window Function** |
|---|-------------|---------------------|
| **동작** | 그룹으로 집계 → **원래 행 수가 줄어듦**<br>(**개별 행 정보 소실**) | **집계하면서도 원래 행을 유지**<br>→ **행별 결과 + 집계값 동시 표현** |

```
[GROUP BY]                      [Window Function]
부서A 1000                       홍길동  부서A  1000  → 부서평균 900
부서A  800    →  부서A  900      이순신  부서A   800  → 부서평균 900
부서B  700       부서B  700      강감찬  부서B   700  → 부서평균 700
   (3행 → 2행)                        (3행 그대로 + 집계값)
```

### 기본 문법

```sql
함수명() OVER ([PARTITION BY 컬럼] [ORDER BY 컬럼] [ROWS/RANGE 프레임])
```

| 절 | 역할 |
|----|------|
| **PARTITION BY** | **분석 단위 구분** (부서별, 지역별) → GROUP BY와 유사하지만 **행 유지** |
| **ORDER BY** | 윈도우 내 **정렬 기준** |
| **ROWS/RANGE BETWEEN** | 집계 **범위 프레임** 지정 |

### 함수 4계열

| 계열 | 함수 |
|------|------|
| **순위 함수** | `ROW_NUMBER()` · `RANK()` · `DENSE_RANK()` · `NTILE(n)` |
| **이동/비교 함수** | `LAG(col, n)` · `LEAD(col, n)` · `FIRST_VALUE` · `LAST_VALUE` |
| **집계 Window** | `SUM`/`AVG`/`COUNT`/`MIN`/`MAX` `OVER()` — 누적합, 이동평균 |
| **통계 함수** | `PERCENT_RANK()` · `CUME_DIST()` |

## 15-2. ROW_NUMBER / RANK / DENSE_RANK — ⭐동점 처리의 차이

```sql
CREATE TABLE sales (
  id SERIAL PRIMARY KEY, region VARCHAR(20), month DATE, revenue NUMERIC
);
INSERT INTO sales VALUES
  (DEFAULT,'Seoul','2025-01-01',10000),(DEFAULT,'Seoul','2025-02-01',13000),
  (DEFAULT,'Seoul','2025-03-01',12500),(DEFAULT,'Busan','2025-01-01',9000),
  (DEFAULT,'Busan','2025-02-01',9500);

-- 지역별 매출 순위 (3가지 함수 동시 비교)
SELECT region, month, revenue,
  ROW_NUMBER() OVER (PARTITION BY region ORDER BY revenue DESC) AS row_num,
  RANK()       OVER (PARTITION BY region ORDER BY revenue DESC) AS rank_r,
  DENSE_RANK() OVER (PARTITION BY region ORDER BY revenue DESC) AS d_rank,
  NTILE(3)     OVER (PARTITION BY region ORDER BY revenue DESC) AS tier,
  -- PARTITION 없이 전체 기준 순위
  RANK()       OVER (ORDER BY revenue DESC)                     AS overall_rank
FROM sales;
```

> 🔑 **동일 값이 있을 때의 차이 — 시험 단골**

| 함수 | 결과 | 설명 |
|------|------|------|
| **ROW_NUMBER()** | **1, 2, 3, 4** | 동점 상관없이 **항상 고유 번호** |
| **RANK()** | **1, 2, 2, 4** | 동점자 같은 순위, **다음을 건너뜀** |
| **DENSE_RANK()** | **1, 2, 2, 3** | 동점자 같은 순위, **연속** |
| **NTILE(n)** | — | n개 그룹으로 **균등 분할** (백분위 분석) |

## 15-3. LAG / LEAD — 전월 대비 증감 분석

```sql
SELECT
  region, month, revenue,
  LAG(revenue, 1) OVER (PARTITION BY region ORDER BY month)  AS prev_month_sales,
  revenue - LAG(revenue, 1) OVER (PARTITION BY region ORDER BY month)
                                                             AS mom_diff,
  ROUND(
    (revenue - LAG(revenue,1) OVER (PARTITION BY region ORDER BY month))
    / NULLIF(LAG(revenue,1) OVER (PARTITION BY region ORDER BY month), 0) * 100, 1
  )                                                          AS mom_growth_pct,
  LEAD(revenue, 1) OVER (PARTITION BY region ORDER BY month) AS next_month_sales
FROM sales
ORDER BY region, month;
```

> ✅ **Checkpoint** : **`NULLIF(prev, 0)`** — 이전 값이 0일 때 **0으로 나누기를 방지**하고 NULL을 반환해 오류를 막습니다.

**활용 사례**
- **MoM** (Month-over-Month) 성장률
- **YoY** (Year-over-Year) : `LAG(revenue, 12)` — 12개월 전 대비
- **연속 이벤트 감지** (로그인 연속일 수)
- **대기 시간 계산** (이전 이벤트와의 간격)

## 15-4. 누적합 / 이동평균 — ROWS/RANGE 프레임

```sql
-- 누적합 (Running Total)
SELECT region, month, revenue,
  SUM(revenue) OVER (
    PARTITION BY region
    ORDER BY month
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_revenue
FROM sales;

-- 3개월 이동평균 (Moving Average)
SELECT region, month, revenue,
  ROUND(AVG(revenue) OVER (
    PARTITION BY region
    ORDER BY month
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW   -- 현재 포함 최근 3개월
  ), 0) AS ma_3month
FROM sales;

-- 카테고리별 누적 점유율 (파레토 분석)
SELECT product, sales,
  SUM(sales) OVER (ORDER BY sales DESC ROWS UNBOUNDED PRECEDING) AS cum_sales,
  SUM(sales) OVER ()                                             AS total_sales,
  ROUND(SUM(sales) OVER (ORDER BY sales DESC ROWS UNBOUNDED PRECEDING)
        / SUM(sales) OVER () * 100, 1)                           AS cum_pct
FROM product_sales;
```

> ✅ **ROWS vs RANGE**
> - **ROWS** = **물리적 행 기준** (정확)
> - **RANGE** = **ORDER BY 값 기준** (같은 값은 모두 포함)

## 15-5. Window Function DBMS 지원 비교

| 함수/기능 | PostgreSQL | MySQL | Oracle | SQL Server |
|-----------|:---:|:---:|:---:|:---:|
| **ROW_NUMBER** | ○ | ○ (8.0+) | ○ | ○ (2005+) |
| **RANK / DENSE_RANK** | ○ | ○ (8.0+) | ○ | ○ |
| **NTILE(n)** | ○ | ○ (8.0+) | ○ | ○ |
| **LAG / LEAD** | ○ | ○ (8.0+) | ○ | ○ |
| **FIRST_VALUE / LAST_VALUE** | ○ | ○ (8.0+) | ○ | ○ |
| **ROWS / RANGE BETWEEN** | ○ | ○ (8.0+) | ○ | ○ |
| **FILTER 절** | **○** | ✗ (CASE 대체) | ✗ (CASE 대체) | ✗ (CASE 대체) |
| **통계함수** (PERCENTILE 등) | ○ | 제한적 | ○ | ○ |

> ⚠️ **MySQL은 8.0부터** Window Function을 지원합니다. 5.7 이하 환경이면 쓸 수 없습니다.

---

## 🔖 심화 [참고] — Window Function 실무 패턴

### ⓐ ROWS vs RANGE 프레임 상세

```sql
-- ROWS: 물리적 행 개수 기준
SELECT date, revenue,
  SUM(revenue) OVER (
    ORDER BY date
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW   -- 현재+앞2개 = 3개 행
  ) AS sum_3rows
FROM daily_sales;

-- RANGE: 논리적 값 기준 (ORDER BY 값이 같은 행은 모두 포함)
SELECT date, revenue,
  SUM(revenue) OVER (
    ORDER BY date
    RANGE BETWEEN INTERVAL '2 days' PRECEDING AND CURRENT ROW
  ) AS sum_3days   -- 2일 전 날짜~오늘까지 모든 행
FROM daily_sales;
```

**프레임 경계 키워드 5가지**

| 키워드 | 의미 |
|--------|------|
| `UNBOUNDED PRECEDING` | 파티션의 **첫 행** |
| `N PRECEDING` | N행/N값 **이전** |
| `CURRENT ROW` | **현재 행** |
| `N FOLLOWING` | N행/N값 **이후** |
| `UNBOUNDED FOLLOWING` | 파티션의 **마지막 행** |

> ✅ 정확한 **행 개수** 기반 이동평균 → **ROWS** / **날짜·값 범위** 기반 집계 → **RANGE**

### ⓑ NTILE / PERCENT_RANK / CUME_DIST

```sql
-- NTILE(n): n개 구간으로 균등 분할
SELECT student_id, score,
  NTILE(4)   OVER (ORDER BY score DESC) AS quartile,   -- 4분위
  NTILE(10)  OVER (ORDER BY score DESC) AS decile,     -- 10분위
  NTILE(100) OVER (ORDER BY score DESC) AS percentile  -- 백분위
FROM enrollments WHERE course_id = 1;

-- PERCENT_RANK: 0.0~1.0 백분위 순위  공식: (rank-1)/(total_rows-1)
-- CUME_DIST : 현재 값 이하인 행의 비율 (0~1)
SELECT student_id, score,
  PERCENT_RANK() OVER (ORDER BY score DESC) AS pct_rank,
  CUME_DIST()    OVER (ORDER BY score DESC) AS cume_dist
FROM enrollments WHERE course_id = 1;

-- 활용: 상위 20% 학생 추출
SELECT * FROM (
  SELECT student_id, score,
         PERCENT_RANK() OVER (ORDER BY score DESC) AS pct_rank
  FROM enrollments WHERE course_id = 1
) t
WHERE pct_rank <= 0.20;

-- FIRST_VALUE / LAST_VALUE: 파티션의 첫/마지막 값
SELECT region, month, revenue,
  FIRST_VALUE(revenue) OVER (PARTITION BY region ORDER BY month) AS first_rev,
  LAST_VALUE(revenue)  OVER (PARTITION BY region ORDER BY month
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)    AS last_rev
FROM sales;
```

> ⚠️ **`LAST_VALUE`의 함정** : 프레임을 명시하지 않으면 기본값이 `UNBOUNDED PRECEDING ~ CURRENT ROW`라서 **"마지막 값"이 아니라 "현재 행의 값"이 나옵니다.** 위 예시처럼 **`UNBOUNDED FOLLOWING`까지 명시**해야 합니다.

### ⓒ Gap & Island — 연속 구간 찾기

> 🔑 **원리** : **날짜에서 ROW_NUMBER를 빼면 연속 구간은 같은 값**을 갖는다.
>
> ```
> 날짜        ROW_NUMBER   날짜 - ROW_NUMBER
> 01-01           1            12-31      ┐
> 01-02           2            12-31      ├ 같은 그룹 (연속)
> 01-03           3            12-31      ┘
> 01-07           4            01-03      ┐ 다른 그룹 (끊김)
> 01-08           5            01-03      ┘
> ```

```sql
-- 연속 로그인 날짜 구간 찾기
WITH login_data AS (
  SELECT DISTINCT user_id, login_date
  FROM   user_sessions WHERE user_id = 42
),
grouped AS (
  SELECT user_id, login_date,
         login_date - (ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date)
                       * INTERVAL '1 day') AS grp_key
  FROM   login_data
)
SELECT user_id,
       MIN(login_date) AS streak_start,
       MAX(login_date) AS streak_end,
       COUNT(*)        AS consecutive_days
FROM   grouped
GROUP BY user_id, grp_key
ORDER BY streak_start;

-- Gap 찾기: 활동 없는 날짜 (출석 공백)
SELECT login_date + INTERVAL '1 day' AS gap_start,
       LEAD(login_date) OVER (ORDER BY login_date) - INTERVAL '1 day' AS gap_end
FROM   login_data
WHERE  LEAD(login_date) OVER (ORDER BY login_date) > login_date + INTERVAL '1 day';
```

**활용 사례** : 연속 출석 보너스 / 이상 탐지(비정상적으로 긴 연속 이벤트) / 재고 연속 품절 기간 / 장애 연속 발생 구간

### ⓓ 코호트 분석 — 가입 월별 재구매 유지율

```sql
WITH user_cohorts AS (
  SELECT user_id, DATE_TRUNC('month', created_at) AS cohort_month
  FROM   users
),
monthly_active AS (
  SELECT DISTINCT user_id, DATE_TRUNC('month', order_date) AS active_month
  FROM   orders
),
cohort_matrix AS (
  SELECT
    uc.cohort_month,
    ma.active_month,
    COUNT(DISTINCT uc.user_id) AS active_users,
    EXTRACT(MONTH FROM AGE(ma.active_month, uc.cohort_month)) AS months_after
  FROM   user_cohorts uc
    JOIN monthly_active ma ON ma.user_id = uc.user_id
  GROUP BY 1, 2
),
cohort_size AS (
  SELECT cohort_month, COUNT(*) AS total_users
  FROM   user_cohorts GROUP BY 1
)
SELECT
  cm.cohort_month,
  cm.months_after,
  cm.active_users,
  cs.total_users,
  ROUND(cm.active_users::NUMERIC / cs.total_users * 100, 1) AS retention_rate
FROM   cohort_matrix cm
  JOIN cohort_size cs ON cs.cohort_month = cm.cohort_month
ORDER BY 1, 2;
```

---

# ★ 실전 패턴 & 최신 트렌드 [참고]

## ⓐ LATERAL JOIN — 행별 독립 서브쿼리

> **외부 쿼리의 각 행마다 서브쿼리를 독립 실행** — 일반 서브쿼리는 외부 행을 참조할 수 없지만 LATERAL은 가능합니다.

```sql
-- 각 학생의 성적 상위 3개 과목
SELECT s.name, recent.title, recent.score
FROM   students s
CROSS JOIN LATERAL (
  SELECT c.title, e.score
  FROM   enrollments e JOIN courses c ON c.id = e.course_id
  WHERE  e.student_id = s.id        -- ← 외부 행 참조!
  ORDER BY e.score DESC
  LIMIT 3
) recent;

-- 각 카테고리별 Best-2 상품
SELECT cat.name AS category, top.*
FROM   categories cat
CROSS JOIN LATERAL (
  SELECT p.name, p.price
  FROM   products p
  WHERE  p.category_id = cat.id
  ORDER BY p.price DESC
  LIMIT 2
) top;
```

> ✅ **Checkpoint**
> - LATERAL 없이는 `ROW_NUMBER` + 서브쿼리 조합으로 복잡하게 구현해야 함
> - **PostgreSQL, Hive, BigQuery** 지원 / ⚠️ **MySQL 미지원** → FROM 서브쿼리 + 윈도우함수

## ⓑ UPSERT — 없으면 INSERT, 있으면 UPDATE

```sql
-- PostgreSQL
INSERT INTO user_stats (user_id, login_count, last_login)
VALUES (42, 1, now())
ON CONFLICT (user_id)              -- PK 또는 UNIQUE 충돌 시
DO UPDATE SET
  login_count = user_stats.login_count + EXCLUDED.login_count,
  last_login  = EXCLUDED.last_login;
-- EXCLUDED: 충돌된 새 값을 참조하는 가상 테이블

-- 중복 무시
INSERT INTO log_events (event_id, payload)
VALUES ('ev-001', '{"type":"click"}')
ON CONFLICT (event_id) DO NOTHING;

-- MySQL
INSERT INTO user_stats (user_id, login_count) VALUES (42, 1)
ON DUPLICATE KEY UPDATE login_count = login_count + 1;

-- SQL Server: MERGE 문 (표준 SQL)
MERGE INTO user_stats t
USING (SELECT 42 AS uid, 1 AS cnt) s ON t.user_id = s.uid
WHEN MATCHED     THEN UPDATE SET login_count = t.login_count + s.cnt
WHEN NOT MATCHED THEN INSERT (user_id, login_count) VALUES (s.uid, s.cnt);
```

> 💡 **활용** : 실시간 집계 카운터, **스트리밍 데이터 적재 필수 패턴**

## ⓒ STRING_AGG / ARRAY_AGG / JSON_AGG — 여러 행을 하나로

```sql
-- STRING_AGG: 여러 행을 하나의 문자열로
SELECT s.name,
       STRING_AGG(c.title, ', ' ORDER BY c.title) AS courses_taken
FROM   students s JOIN enrollments e ON e.student_id = s.id
                  JOIN courses     c ON c.id = e.course_id
GROUP BY s.id, s.name;

-- ARRAY_AGG: 배열로 집계 (PostgreSQL)
SELECT major_id,
       ARRAY_AGG(name ORDER BY grade DESC) AS students,
       ARRAY_AGG(DISTINCT grade)           AS grades
FROM   students GROUP BY major_id;

-- JSON_AGG + JSON_BUILD_OBJECT: JSON 배열로 집계 (API 응답용)
SELECT s.name,
  JSON_AGG(
    JSON_BUILD_OBJECT(
      'course', c.title,
      'score',  e.score,
      'grade',  CASE WHEN e.score>=90 THEN 'A'
                     WHEN e.score>=80 THEN 'B' ELSE 'C' END
    ) ORDER BY e.score DESC
  ) AS enrollment_history
FROM   students s
  JOIN enrollments e ON e.student_id = s.id
  JOIN courses     c ON c.id = e.course_id
GROUP BY s.id, s.name;
```

## ⓓ TOP-N Per Group — 3가지 방법 비교

> **각 학과별 성적 상위 3명 추출**

```sql
-- ⭐방법 1: Window Function (가장 추천)
SELECT * FROM (
  SELECT s.name, m.name AS major, e.score,
         ROW_NUMBER() OVER (PARTITION BY s.major_id ORDER BY e.score DESC) AS rn
  FROM   students s
    JOIN majors      m ON m.id = s.major_id
    JOIN enrollments e ON e.student_id = s.id
  WHERE  e.course_id = 1
) ranked
WHERE rn <= 3;

-- 방법 2: LATERAL JOIN (PostgreSQL)
SELECT m.name AS major, top3.name, top3.score
FROM   majors m
CROSS JOIN LATERAL (
  SELECT s.name, e.score
  FROM   students s JOIN enrollments e ON e.student_id = s.id
  WHERE  s.major_id = m.id AND e.course_id = 1
  ORDER BY e.score DESC LIMIT 3
) top3;

-- 방법 3: 상관 서브쿼리 (⚠️느림, 학습용)
SELECT s.name, e.score, s.major_id
FROM   students s JOIN enrollments e ON e.student_id = s.id
WHERE  e.course_id = 1
  AND (SELECT COUNT(*) FROM students s2 JOIN enrollments e2 ON e2.student_id = s2.id
       WHERE s2.major_id = s.major_id AND e2.course_id = 1 AND e2.score > e.score) < 3;
```

## ⓔ JSONB 조작 (PostgreSQL)

```sql
CREATE TABLE products (
  id    BIGSERIAL PRIMARY KEY,
  name  TEXT,
  attrs JSONB   -- {"color":"red","size":"L","price":29900}
);

-- JSONB 조회 연산자
SELECT name,
  attrs->>'color'            AS color,       -- 텍스트로 추출
  attrs->'price'             AS price_json,  -- JSONB로 추출
  (attrs->>'price')::NUMERIC AS price_num,   -- 숫자로 변환
  attrs @> '{"color":"red"}' AS is_red,      -- 포함 여부
  attrs ? 'discount'         AS has_discount -- 키 존재 여부
FROM products;

-- JSONB 업데이트
UPDATE products SET attrs = attrs || '{"discount":0.1}' WHERE id = 1;  -- 키 추가/수정
UPDATE products SET attrs = attrs - 'discount'          WHERE id = 1;  -- 키 삭제

-- GIN 인덱스로 JSONB 전체 검색 가속
CREATE INDEX idx_products_attrs ON products USING GIN (attrs);
SELECT * FROM products WHERE attrs @> '{"color":"red","size":"L"}';  -- 인덱스 사용
```

| 연산자 | 의미 |
|--------|------|
| `->>` | **텍스트**로 추출 |
| `->` | **JSONB**로 추출 |
| `@>` | **포함 여부** (GIN 인덱스 사용 가능) |
| `?` | **키 존재 여부** |
| `\|\|` | 키 **추가/병합** |
| `-` | 키 **삭제** |

## ⓕ 날짜 처리 완전 가이드

```sql
-- 월별/주별/일별 집계
SELECT DATE_TRUNC('month', order_date) AS month,
       COUNT(*) AS orders, SUM(amount) AS revenue
FROM   orders GROUP BY 1 ORDER BY 1;

-- 특정 기간 데이터 (최근 30일)
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
WHERE order_date >= NOW() - INTERVAL '30 days'   -- 시각까지 고려

-- 요일별 집계
SELECT TO_CHAR(order_date, 'Day')        AS weekday,
       EXTRACT(DOW FROM order_date)      AS dow_num,   -- 0=일, 6=토
       COUNT(*) AS cnt
FROM   orders GROUP BY 1, 2 ORDER BY 2;

-- 타임존 변환 (UTC → KST +9)
SELECT order_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Seoul' AS kst_time
FROM orders;

-- 월말일 계산
SELECT DATE_TRUNC('month', NOW()) + INTERVAL '1 month' - INTERVAL '1 day' AS last_day;

-- 두 날짜 사이 영업일 수
SELECT COUNT(*) FILTER (WHERE EXTRACT(DOW FROM d) NOT IN (0, 6)) AS workdays
FROM GENERATE_SERIES('2024-01-01'::DATE, '2024-12-31'::DATE, '1 day') d;
```

## ⓖ 문자열 처리 고급

```sql
-- 이메일 도메인 추출
SELECT email,
       SPLIT_PART(email, '@', 2)      AS domain,
       SUBSTRING(email FROM '@(.+)$') AS domain2
FROM   users;

-- 전화번호 정규화 (하이픈 제거)
SELECT REGEXP_REPLACE(phone, '[^0-9]', '', 'g') AS clean_phone FROM users;

-- 이름 마스킹 (홍길동 → 홍*동)
SELECT name,
  SUBSTRING(name, 1, 1)
    || REPEAT('*', GREATEST(LENGTH(name)-2, 0))
    || CASE WHEN LENGTH(name) >= 2 THEN SUBSTRING(name, LENGTH(name)) ELSE '' END
  AS masked_name
FROM users;

-- 텍스트 유사도 (pg_trgm 확장)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
SELECT a.name, b.name, SIMILARITY(a.name, b.name) AS sim
FROM   products a CROSS JOIN products b
WHERE  a.id < b.id AND SIMILARITY(a.name, b.name) > 0.5;

-- 정규표현식 검색
SELECT name FROM customers WHERE name ~ '^[가-힣]{2,4}$';   -- 2~4자 한글 이름
```

## ⓗ AI 시대의 DB — pgvector 하이브리드 검색 (RAG)

```sql
-- 1. pgvector 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 문서 임베딩 저장 테이블 (OpenAI text-embedding-3-small = 1536차원)
CREATE TABLE knowledge_base (
  id         BIGSERIAL PRIMARY KEY,
  title      TEXT NOT NULL,
  content    TEXT,
  chunk_idx  INT DEFAULT 0,        -- 긴 문서를 청크로 분할
  embedding  VECTOR(1536),
  search_ts  TSVECTOR,             -- 전문 검색 인덱스
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. 인덱스 생성
CREATE INDEX ON knowledge_base USING HNSW (embedding vector_cosine_ops);
CREATE INDEX ON knowledge_base USING GIN  (search_ts);

-- 4. 하이브리드 검색 (벡터 유사도 70% + 키워드 30%)
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

> ✅ **하이브리드 검색** : **의미 기반(벡터 70%) + 정확한 키워드(FTS 30%)** → **RAG 답변 품질 향상**

## ⓘ AI 기반 SQL 도구 현황

| 도구 | 내용 |
|------|------|
| **Chat2DB** (chat2db.ai) | AI 연동 SQL 작성 + **ERD 기반 자동 SQL 생성**<br>ChatGPT/Claude 연동 → 자연어로 쿼리 작성, 오류 자동 수정<br>DBeaver처럼 멀티 DB 지원 |
| **GitHub Copilot for SQL / Tabnine** | IDE에서 SQL 자동완성, 쿼리 패턴 학습 기반 |
| **Cloud AI 도구** | **BigQuery with Gemini** (자연어→SQL, 최적화 제안)<br>**Snowflake Cortex AI** (내장 AI 분석 자동화)<br>**AWS QueryEditor + Bedrock** |
| **pgvector + LLM** | DB 자체가 AI 서비스의 일부 — 임베딩 저장 → 유사도 검색 → **RAG** |

> ⚠️ **AI SQL 도구 주의사항**
> - 생성된 쿼리는 **반드시 `EXPLAIN`으로 성능 검증**
> - **데이터 보안** : 민감 스키마를 AI에 전달 시 **정보 유출 위험**

## ⓙ ⭐ SQL 튜닝 안티패턴 vs 해결책

| 안티패턴 | 문제 | 해결책 |
|----------|------|--------|
| **`SELECT *`** | 불필요한 데이터 전송, 커버링 인덱스 불가 | 필요한 컬럼만 명시 |
| **인덱스 컬럼에 함수 적용** | `WHERE YEAR(date)=2024` → **인덱스 무력화** | `WHERE date >= '2024-01-01' AND date < '2025-01-01'` |
| **N+1 문제** | 루프 내 N번 개별 쿼리 → DB 과부하 | **JOIN 또는 IN 절**로 한 번에 처리 |
| **`NOT IN` (NULL 포함)** | 서브쿼리에 NULL 시 결과 **항상 빈 집합** | **`NOT EXISTS`** 또는 `LEFT JOIN + IS NULL` |
| **`%keyword%` LIKE** | 인덱스 미사용, 전체 스캔 | **전문 검색 인덱스** (GIN + pg_trgm) |
| **대용량 OFFSET** | OFFSET이 클수록 선형 증가 O(N) | **Cursor/Keyset 방식** |
| **암묵적 타입 변환** | `WHERE user_id='123'` (INT 컬럼) → 인덱스 무력화 | 같은 타입으로 비교: `WHERE user_id=123` |
| **DISTINCT 남용** | GROUP BY 없이 중복 제거만 사용 | **중복 원인 파악 후** JOIN/집계 구조 개선 |

---

# 16. 종합실습 – 2

> 📌 **주제** : CampusHub — 복합 쿼리 실습 (JOIN + 서브쿼리 + 윈도우함수)

## 16-1. 학습 목표 및 준비

| 항목 | 내용 |
|------|------|
| **환경** | **종합실습 1 환경 활용** + **신규 DB 개설** |
| **사전 준비** | PostgreSQL 스크립트 실행 — **`postgres_join_lab_large`** |
| **학습 목표** | INNER/OUTER/FULL/SELF/CROSS/ANTI/SEMI JOIN과 집계 실습 |
| **진행 순서** | 스키마 생성 → 샘플데이터 → JOIN 실습(Inner/Left/Right/Full/Workaround) → 확장(Self/Cross) → 실무 집계 → **ON vs WHERE 차이** |
| **심화실습** | GROUP BY, Window Function, CTE |

## 16-2. 데이터 배경

| 테이블 | 구성 |
|--------|------|
| **학사 시스템** : `student`, `enroll` | 수강은 학생당 **0~2건**<br>• `student_id % 3 = 0` → **0건** (약 333명 수강 없음)<br>• `= 1` → **1건** (약 334명)<br>• `= 2` → **2건** (약 333명)<br>⚠️ **고아 수강**(enroll에만 존재) **2건** 포함 (학생 1001, 1010) |
| **캠퍼스 스토어** : `customers`, `orders` | 고객 1명당 **정확히 6건**의 주문 |
| **조직도** : `emp` | **CEO 1명 → 매니저 10명 → 직원 300명**<br>(각 직원은 매니저 10명 중 1명에게 배정) |

> ℹ️ 상위 N행 조회 : **Postgres/MySQL → `LIMIT 5`** / **SQL Server → `TOP(5)`**
>
> 💡 **데이터 설계 의도** : 수강 0건 학생과 고아 수강을 일부러 넣어둔 이유는 **LEFT/RIGHT/FULL JOIN의 차이를 눈으로 확인**하게 하려는 것입니다. INNER JOIN만 쓰면 이 데이터들이 사라집니다.

## 16-3. 실습 과제 25문항

### 기본 (1~10) — JOIN

| # | 과제 |
|---|------|
| **1** | 학생과 수강을 **INNER JOIN**하여 수강 존재 학생의 과목/성적 조회 |
| **2** | **모든 학생 기준**으로 수강을 붙이고, 과목(없으면 NULL)까지 보이기 |
| **3** | **수강이 기준**. 학생이 없으면 학생 정보가 NULL |
| **4** | **학생/수강 모두** 포함 |
| **5** | **한 번도 수강하지 않은** 학생 목록 |
| **6** | **한 과목 이상 수강한** 학생 목록 (중복 제거) |
| **7** | 고객별 **주문건수/총액** |
| **8** | **총액 상위 10명**과 금액 |
| **9** | 모든 직원과 그 **매니저 이름** |
| **10** | "모든 학생 기준"으로 과목 분포 보기 → **LEFT JOIN + 집계** |

### 심화 (11~13) — JOIN 응용

| # | 과제 |
|---|------|
| **11** | **DB 과목을 듣지 않은** 모든 학생 나열 |
| **12** | (가정) 과목별로 매니저가 운영 책임을 갖는다고 가정.<br>`emp`의 매니저(이름 `Mgr_`로 시작)와 과목을 임의 매핑한 테이블 **`course_owner(course, manager_id)`** 를 만든 뒤,<br>**과목별 수강 인원 + 책임 매니저 이름** 리포트 작성 |
| **13** | 학생 × 과목 **전체 조합**을 만들어 "학생별 과목 추천 후보"를 만들되, **샘플 100건만** 조회 |

### 심화 (14~20) — 서브쿼리 & 집합

| # | 과제 |
|---|------|
| **14** | **스칼라 서브쿼리** (SELECT 절) 사용 — 학생 + 소속 학과명 붙이기 |
| **15** | **평균 GPA보다 높은** 학생 (WHERE 서브쿼리) |
| **16** | **자신의 학과 평균 GPA보다 높은** 학생 (**Correlated Subquery**) |
| **17** | 수강(`enroll`) 기록이 **있는** 학생만 |
| **18** | 한 번도 **수강하지 않은** 학생 |
| **19** | HR 학과 학생 일부와의 비교 데모 |
| **20** | **CS 학과 학생 또는 DB 과목을 수강한** 학생 목록 |

### 심화 (21~25) — 집계·재귀·Window Function

| # | 과제 | 요구사항 |
|---|------|----------|
| **21** | **ROLLUP 소계 집계**<br>학과별·GPA 구간별 인원을 소계·총계까지 한 번의 쿼리로 | • GPA를 구간(**3.0 미만 / 3.0~3.5 / 3.5 초과**)으로 분류하는 **파생 컬럼** 추가<br>• **`GROUP BY ROLLUP(major, gpa_tier)`** 로 학과별·전체 소계 동시 조회<br>• **`GROUPING(major)`** 함수로 소계 행에 **'전체'** 라벨<br>• `major, gpa_tier` 순 정렬하되 **소계 행은 하단**에 표시 |
| **22** | **재귀 CTE 조직도**<br>`emp`는 CEO(`manager_id = NULL`) → 매니저(10명) → 개발자(300명) 3단계 | • **`WITH RECURSIVE`** 로 CEO에서 시작하는 조직 트리 탐색<br>• 각 행에 **`depth`(0=CEO), `path`** 컬럼 포함 (예: `'CEO > Mgr_2 > Dev_15'`)<br>• **매니저별 직속 부하 직원 수** 집계 쿼리 별도 작성 (컬럼명 **`direct_reports`**) |
| **23** | **Window Function TOP-N**<br>각 학과별 GPA 상위 3명 추출 (**서브쿼리 방식과 CTE 방식 모두** 작성) | • `ROW_NUMBER() OVER (PARTITION BY major ORDER BY gpa DESC)`<br>• GPA 동일 시 **`student_id` 오름차순**을 2차 기준으로<br>• **`RANK()`와 `DENSE_RANK()`도 함께 계산**해 동점 처리 차이 비교<br>• **`COUNT() OVER(PARTITION BY major)`** 로 `total_in_major` 추가 |
| **24** | **LAG 성적 변화 분석**<br>`enroll`을 `student_id` 기준 정렬, 이전 수강 과목 대비 성적 변화 계산 | • grade를 숫자 점수(**A=4, B=3, C=2, D=1**)로 변환하는 **CASE 식**<br>• `LAG(score) OVER (PARTITION BY student_id ORDER BY course)`<br>• 현재 − 이전을 **`diff`** 컬럼으로, **상승/유지/하락**을 텍스트 표시<br>• 학생별 최고점−최저점 차이(**`score_range`**)를 Window Function으로 |
| **25** | **누적합 & 이동평균**<br>`orders`를 `order_id` 순 정렬하여 계산 (**ROWS BETWEEN 사용**) | • `SUM(amount) OVER (ORDER BY order_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` — **누적합**<br>• `AVG(amount) OVER (ORDER BY order_id ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` — **3개 이동평균**<br>• **`customer_id`별 PARTITION**으로 고객별 누적 구매금액도<br>• **누적합이 전체 합의 50%를 초과하는 첫 `order_id`** 찾기 |

## 16-4. 제출물

| 항목 | 내용 |
|------|------|
| **제출물** | 각 문항별 **쿼리와 실행결과 화면** (쿼리와 결과가 함께 나온 화면 **Screen Capture**) |
| **제출 방법** | **Slack 내 댓글 제출** |
| **제출 기한** | **3일차 과정 시작 전** |
| **배점** | **문항당 4점** (25문항 × 4점 = 100점) |
| **채점 기준** | ① **요구사항 반영 여부**<br>② **Query 내 컬럼 선택** (⚠️ **불필요한 컬럼 선택 확인**) |

> 💡 **채점 기준 ②가 중요합니다.** `SELECT *`로 다 뽑으면 감점입니다. 안티패턴 표의 첫 줄과 같은 이야기입니다.

---

# 🧭 Day 2 전체 흐름 한 장 요약

```
[Day 2의 질문]  흩어진 데이터를 어떻게 합쳐서 의미를 뽑을 것인가?

  도구 1. 집계 (여러 행 → 한 행)
     COUNT/SUM/AVG/MIN/MAX + FILTER
     GROUP BY → HAVING            (WHERE는 집계 전, HAVING은 집계 후)
     ROLLUP(계층 소계) / CUBE(모든 조합) + GROUPING()으로 라벨링

  도구 2. 결합 (여러 테이블 → 한 결과)
     본질 = 카르테시안 곱 + 조건 필터   ← ON 빼먹으면 폭발하는 이유
     ├ 종류: INNER / LEFT / RIGHT / FULL / SELF / CROSS / Anti / Semi
     └ 알고리즘: 작은×큰+인덱스→NL  대형×대형→Hash  정렬됨→Merge
     ⚠️ 최대 함정: OUTER JOIN에서 WHERE로 필터 → INNER JOIN이 되어버림
                   → 조건은 ON 절에

  도구 3. 분해 (복잡한 쿼리 → 단계)
     서브쿼리 : 스칼라(SELECT) / 인라인뷰(FROM) / WHERE / 상관
                상관 서브쿼리는 느림 → CTE 또는 Window로
     CTE      : WITH · 재귀 CTE(Anchor + UNION ALL + 종료조건)
     View     : 저장X·항상최신 │ MV: 저장O·인덱스O·수동refresh
     집합     : UNION(중복제거) / UNION ALL(빠름) / INTERSECT / EXCEPT

  도구 4. 유지하며 계산 (행 보존 + 집계)
     GROUP BY는 행이 줄지만, Window는 행이 그대로
     순위  : ROW_NUMBER(1,2,3,4) RANK(1,2,2,4) DENSE_RANK(1,2,2,3)
     비교  : LAG / LEAD → MoM, YoY, 연속 이벤트
     프레임: ROWS(물리적 행) vs RANGE(값 기준) → 누적합·이동평균
     패턴  : Gap&Island(날짜 − ROW_NUMBER) · 코호트 분석


[모든 도구의 공통 검증 도구]  EXPLAIN ANALYZE
     Seq Scan(인덱스 필요 신호) / Index Scan / Index Only Scan
     actual rows vs rows(예측) 차이 크면 → ANALYZE로 통계 갱신
     Buffers: shared hit(캐시) vs read(디스크)
     Hash Batches > 1 → 메모리 Spill → work_mem 부족
```

---

## 🎓 시험/면접 대비 핵심 문답

| 질문 | 답 |
|------|-----|
| **WHERE와 HAVING의 차이는?** | **WHERE = 집계 전 행 필터**, **HAVING = 집계 후 그룹 필터** |
| **`COUNT(*)`와 `COUNT(col)`의 차이는?** | `COUNT(*)`는 **NULL 포함 전체**, `COUNT(col)`은 **NULL 제외** |
| **`AVG(NULL)`은 0인가?** | ❌ **NULL입니다.** SUM/AVG는 NULL을 **아예 계산에서 제외**합니다 |
| **ROLLUP과 CUBE의 차이는?** | ROLLUP = **계층적 소계**(빠름) / CUBE = **모든 조합 소계**(느림) |
| **결과의 NULL이 소계인지 실제 NULL인지 어떻게 구분?** | **`GROUPING()`** 함수 (Oracle/SQL Server는 `GROUPING_ID()`도) |
| **JOIN의 본질은?** | **카르테시안 곱 + 조건 필터링** — 그래서 ON을 빼먹으면 N×M으로 폭발 |
| **JOIN 알고리즘 3종과 각각의 적합 상황은?** | **NL**(작은×큰+인덱스) / **Hash**(대형×대형 등가조인) / **Sort-Merge**(이미 정렬된 대용량, 비등가도 가능) |
| **MySQL에서 FULL OUTER JOIN을 하려면?** | 미지원 → **`LEFT JOIN UNION RIGHT JOIN`** 우회 |
| **⭐OUTER JOIN에서 ON과 WHERE의 차이는?** | **ON = 조인 과정에서 적용(OUTER 결과 유지)** / **WHERE = 조인 후 필터(NULL 행 제거 → 사실상 INNER JOIN)** |
| **Anti-Join 3가지 방법 중 권장은?** | **`NOT EXISTS`** — NULL 안전성·성능 모두 우수 |
| **`NOT IN`의 함정은?** | 서브쿼리에 **NULL이 하나라도 있으면 결과가 항상 빈 집합** |
| **`EXISTS`와 `IN` 중 대용량에 유리한 것은?** | **`EXISTS`** — 행 존재만 확인(`SELECT 1`)하고 즉시 종료 |
| **`> ANY`와 `> ALL`은 각각 무엇과 같나?** | `> ANY` = **`> MIN`** / `> ALL` = **`> MAX`** |
| **UNION과 UNION ALL 중 빠른 것은?** | **`UNION ALL`** — 중복 제거를 위한 정렬/비교가 없음 |
| **CTE의 장점 3가지는?** | **가독성 향상 / 재사용 가능 / 재귀 쿼리 지원** |
| **재귀 CTE의 3요소는?** | **① 기저 단계(Anchor) → ② `UNION ALL` + 재귀 단계 → ③ 종료 조건**(빼먹으면 무한 루프) |
| **View와 Materialized View의 결정적 차이는?** | MV는 **결과를 디스크에 저장**하므로 **인덱스 생성 가능**, 대신 **수동 REFRESH 필요** |
| **⭐GROUP BY와 Window Function의 차이는?** | GROUP BY는 **행 수가 줄어듦**(개별 행 소실) / Window는 **행을 유지하며** 집계값을 함께 표시 |
| **ROW_NUMBER / RANK / DENSE_RANK 동점 처리는?** | **1,2,3,4** / **1,2,2,4**(건너뜀) / **1,2,2,3**(연속) |
| **ROWS와 RANGE의 차이는?** | **ROWS = 물리적 행 개수** / **RANGE = ORDER BY 값 기준**(같은 값 모두 포함) |
| **`LAST_VALUE`가 이상하게 나오는 이유는?** | 기본 프레임이 `UNBOUNDED PRECEDING ~ CURRENT ROW`라서 → **`UNBOUNDED FOLLOWING`까지 명시** 필요 |
| **Gap & Island의 원리는?** | **날짜 − ROW_NUMBER** → 연속 구간은 같은 값을 가짐 → 그 값으로 GROUP BY |
| **상관 서브쿼리가 느린 이유와 대안은?** | **바깥 행마다 내부 쿼리를 반복 실행** → **CTE** 또는 **Window Function**으로 대체 |
| **LATERAL JOIN이 필요한 이유는?** | 일반 서브쿼리는 외부 행을 참조 못 하지만, **LATERAL은 행마다 독립 실행하며 외부 행 참조 가능** |
| **OFFSET 페이지네이션의 문제와 대안은?** | OFFSET만큼 **읽고 버림 → O(N)** / 대안 : **Cursor/Keyset** (`WHERE id > :last_id`) |
| **인덱스를 무력화하는 대표 패턴 3가지는?** | ① **컬럼에 함수 적용**(`YEAR(date)=2024`) ② **`%keyword%` LIKE** ③ **암묵적 타입 변환**(`user_id='123'`) |
| **N+1 문제란?** | 루프 안에서 개별 쿼리를 N번 반복 → **JOIN 또는 IN 절로 한 번에 처리** |
| **MySQL `ONLY_FULL_GROUP_BY`란?** | SELECT에 GROUP BY 키가 아닌 **비집계 컬럼이 있으면 오류**. 기본 활성 |
| **DBMS / DW / Data Mining의 목적은?** | **OLTP(트랜잭션)** / **OLAP(분석·의사결정)** / **패턴·지식 발견** |
| **MSA에서 Elasticsearch 연동 시 주의점은?** | **Eventually Consistent** → 실시간 정합성 보장 불가, **RDBMS와 역할 분리** |

---

## 🔗 Day 3 예고 — SQL 성능 최적화

> 📌 **다루는 것** : 인덱스 · 실행계획 · 튜닝 · 트랜잭션 · MVCC

### 쿼리 최적화의 기본 원칙 (미리 보기)

| 원칙 | 내용 |
|------|------|
| **`SELECT *` 사용 금지** | 필요한 컬럼만 명시 → 불필요한 데이터 전송 방지, **커버링 인덱스 활용 가능** |
| **WHERE 절 인덱스 컬럼에 함수 사용 금지** | ❌ `WHERE YEAR(order_date)=2024` → **인덱스 무력화**<br>✅ `WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'` |
| **N+1 문제** | 루프 안에서 개별 쿼리 반복 → **한 번의 JOIN으로** 처리 |
| **EXPLAIN 습관화** | 실행계획으로 **Seq Scan vs Index Scan** 확인 / cost, actual rows, Buffers 체크 |
| **통계 최신화** | **`ANALYZE` 주기적 실행** — 통계가 오래되면 옵티마이저가 잘못된 실행계획 선택 |

### EXPLAIN ANALYZE 기초

```sql
-- 실행계획 확인 (쿼리 실행 안 함)
EXPLAIN
SELECT s.name, AVG(e.score)
FROM   students s JOIN enrollments e ON e.student_id = s.id
WHERE  s.major_id = 1
GROUP BY s.id, s.name;

-- 실행계획 + 실제 시간 측정 (쿼리 실행함)
EXPLAIN (ANALYZE, BUFFERS)
SELECT s.name, AVG(e.score) FROM students s
  JOIN enrollments e ON e.student_id = s.id
WHERE s.major_id = 1 GROUP BY s.id, s.name;
```

**결과 해석 키워드**

| 항목 | 의미 |
|------|------|
| **Seq Scan** | 테이블 전체 스캔 → ⚠️ **인덱스 필요 신호** |
| **Index Scan** | 인덱스 사용 |
| **Index Only Scan** | **인덱스만으로 처리 (가장 효율적)** |
| `cost=0.00..45.3` | 예상 비용 |
| `actual time=0.1..2.3` | 실제 ms |
| `rows=10` vs `actual rows=8` | **예상 vs 실제** — 차이 크면 통계 갱신 필요 |
| `Buffers: shared hit=5 read=2` | **캐시 히트 vs 디스크 읽기** |

**Before / After 예시**
```
인덱스 없을 때 : Seq Scan on students (cost=0.00..45.00 rows=1000)
인덱스 추가 후 : Index Scan using idx_students_major on students
                 (cost=0.29..8.30 rows=50)
```

### Day 3 목차

| # | 장 |
|---|---|
| 17 | 인덱스 설계 및 최적화 |
| 18 | 실행계획 분석 |
| 19 | SQL 튜닝 & 느린 쿼리 식별 |
| 20 | MVCC & 트랜잭션 격리 수준 |
| 21 | Lock & Deadlock 관리 |
| 22 | 고급 DB 설계 |
| 23 | 종합 실습 – 3 (HR DB 느린 쿼리 최적화 — EXPLAIN Before/After 비교) |

---

*본 문서는 SK AX의 컨텐츠 자산을 학습 목적으로 정리한 것으로, 무단 사용 및 불법 배포 시 법적 조치를 받을 수 있습니다.*
