# ⚡ Day 3 — 스마트 데이터 이해 및 활용

> 💡 **Day 3 한 줄 요약**
> Day 1이 **"어떻게 만드나"**, Day 2가 **"어떻게 꺼내나"** 였다면, Day 3은 **"왜 느린가, 왜 충돌하는가"**.
> 도구는 두 축뿐입니다 — **속도(인덱스·실행계획·튜닝)** 와 **동시성(MVCC·격리수준·Lock)**.

**출처** : AI 서비스를 위한 SW 기초 Full-stack Engineering (AI캠퍼스, 4일) > 4. 스마트 데이터 이해 및 활용 (백정열 / SK AX, 2026.6)
**범위** : 전체 482p 중 **Day 3 = 245~346p** (17~23장 + 참고 섹션)

---

## 📑 Day 3 목차

| # | 장 | 부제 | 핵심 질문 |
|---|---|------|-----------|
| 17 | [인덱스 설계 및 최적화](#17-인덱스-설계-및-최적화) | B-Tree · Hash · GIN · GiST · BRIN · 복합 · 커버링 | 왜 인덱스가 빠른가? |
| 18 | [실행계획 분석](#18-실행계획-분석) | EXPLAIN ANALYZE · 플랜 읽기 · DBMS별 도구 | DB가 실제로 뭘 하는지 보려면? |
| 19 | [SQL 튜닝 & 느린 쿼리 식별](#19-sql-튜닝--느린-쿼리-식별) | 안티패턴 8 · Slow Query · 파티셔닝 | 뭘 고쳐야 빨라지나? |
| 20 | [MVCC & 트랜잭션 격리 수준](#20-mvcc--트랜잭션-격리-수준) | 다중버전 동시성 제어 · Isolation 실습 | 동시에 읽고 써도 왜 안 막히나? |
| 21 | [Lock & Deadlock 관리](#21-lock--deadlock-관리) | Row Lock · Advisory Lock · 감지 · 해소 | 서로 기다리다 멈추면? |
| ★ | [[강사님 보충] 실무 관점의 튜닝](#-강사님-보충-실무-관점의-튜닝--db-내부-동작) | 튜닝 목표 3지표 · 옵티마이저 · 통계 · 파티션 인덱스 · 부하테스트 | 실무에선 뭘 보고 판단하나? |
| 22 | [고급 DB 설계](#22-고급-db-설계) | BCNF·4NF·5NF · 반정규화 · SCD · 샤딩 · MSA | 커지면 어떻게 나누나? |
| ★ | [운영 실무](#-운영-실무-참고) | 백업·VACUUM·Connection Pool·모니터링 | 실제로 굴리려면? |
| 23 | [종합실습 – 3](#23-종합실습--3) | HR DB 느린 쿼리 최적화 (5문항) | 직접 튜닝해보기 |

> 💬 **편집 안내** : 원본의 `[참고] 심화 & 운영 실무`(324~340p)는 [★ 운영 실무](#-운영-실무-참고) 절로 모았습니다. 각 항목이 어느 슬라이드에서 왔는지 표시했습니다.

---

# 17. 인덱스 설계 및 최적화

> 📌 **다루는 것** : B-Tree · Hash · GIN · GiST · BRIN · 복합 인덱스 · 커버링 인덱스

## 17-1. 인덱스는 공짜가 아닙니다 — 트레이드오프

| | 인덱스 없음 | 인덱스 있음 |
|---|---|---|
| **탐색** | Table Full Scan → 전체 행 순차 검사 → **O(N)** | B-Tree 탐색 → **O(log N)** |
| **차이** | | 수백만 행에서 **수십 ms 차이** |

### ⚖️ 핵심 트레이드오프 3가지

| | 내용 |
|---|---|
| ✅ **읽기 성능 향상** | 자주 쓰는 필드 — **WHERE / JOIN / ORDER BY** |
| ❌ **쓰기 비용 증가** | **INSERT/UPDATE/DELETE 시 인덱스 재정렬 비용** |
| ❌ **저장 공간 증가** | 인덱스 자체도 디스크 공간 소모 |

> 🔑 **인덱스를 많이 만들수록 읽기는 빨라지고 쓰기는 느려집니다.**
> 그래서 **"일단 다 걸어두자"가 최악의 전략**입니다.

### 인덱스 설계 원칙 5가지

- **WHERE 조건에 자주 등장하는 컬럼** 우선
- **선택도(Selectivity) 높은 컬럼** — 고유값이 많을수록 좋은 인덱스
- **FK 컬럼에 반드시 인덱스** (JOIN 성능, FOREIGN KEY 체크)
- **쓰기 중심(OLTP) vs 읽기 중심(OLAP)** — 인덱스 전략이 다름
- ⚠️ **미사용 인덱스는 제거** — 쓰기 비용만 증가, 조회 이점 없음

---

## 17-2. 인덱스 종류 비교

| 인덱스 | 구조 | 최적 용도 | 지원 |
|--------|------|-----------|------|
| **B-Tree**<br>*(실제 구현은 주로 **B+Tree**)* | **다진 균형 트리**<br>(Multi-way Balanced Search Tree) | `=`, 범위(`BETWEEN`,`<`,`>`,`<=`,`>=`),<br>전방 일치 `LIKE 'prefix%'`, 정렬(`ORDER BY`,`GROUP BY`) | **기본 인덱스 (모든 DBMS)** |
| **Hash** | 해시 테이블 | **등호(=) 비교만** — ⚠️ 범위 불가 | PostgreSQL, MySQL(제한적) |
| **GIN** | 역인덱스 (Inverted) | **JSONB, 배열, 전문검색(FTS)** | PostgreSQL, MySQL(FTS 한정) |
| **GiST** | 일반화 검색 트리 | **지리정보(PostGIS), 범위 타입, 벡터 유사도** | PostgreSQL(확장) |
| **BRIN** | 블록 범위 최소/최대 | **타임시리즈, 물리적 연속 저장 대용량** | PostgreSQL |
| **Bitmap** | 비트 배열 | **저선택도 컬럼 조합** (AND/OR) | Oracle (DW용) |
| **Clustered** | 데이터 물리 정렬 | 범위 스캔, PK 기반 접근 | SQL Server / MySQL InnoDB |

> 💡 **거의 다 B-Tree입니다.** 나머지는 "B-Tree로 안 되는 특수한 경우"에 씁니다.
> - JSON·배열·전문검색 → **GIN**
> - 지도·좌표 → **GiST**
> - 로그처럼 시간순으로 쌓이는 초대용량 → **BRIN**

---

## 17-3. 실제 성능 차이 — 100만 건 실습

```sql
-- AI 연계 테이블: 사용자 쿼리 로그
CREATE TABLE query_logs (
  id               SERIAL PRIMARY KEY,
  user_id          TEXT,
  user_input       TEXT,
  similarity       FLOAT,
  response_quality TEXT,
  created_at       TIMESTAMP DEFAULT NOW()
);

-- 대량 데이터 생성 (100만 건)
INSERT INTO query_logs (user_id, user_input, similarity, response_quality)
SELECT 'u' || (i % 1000),
       'query_' || i,
       RANDOM(),
       CASE (i%4) WHEN 0 THEN 'excellent' WHEN 1 THEN 'good'
                  WHEN 2 THEN 'fair'      ELSE 'poor' END
FROM GENERATE_SERIES(1, 1000000) i;
```

**Before — 인덱스 없이**
```sql
EXPLAIN ANALYZE SELECT * FROM query_logs WHERE user_id = 'u123';
-- Seq Scan on query_logs (cost=0.00..20000 rows=1000 actual time=120..1850)
```

**인덱스 생성**
```sql
CREATE INDEX idx_query_logs_user    ON query_logs(user_id);
CREATE INDEX idx_query_logs_created ON query_logs(created_at DESC);
```

**After**
```sql
EXPLAIN ANALYZE SELECT * FROM query_logs WHERE user_id = 'u123';
-- Index Scan using idx_query_logs_user (actual time=0.05..0.8 rows=1000)
```

> ✅ **결과 : Seq Scan 1,850ms → Index Scan 0.8ms — 약 2,300배 향상**

---

## 17-4. 인덱스 생성 명령어 6가지

```sql
-- ① 복합 인덱스: 선두 컬럼 원칙 (leftmost prefix rule)
CREATE INDEX idx_orders_cust_date ON orders (customer_id, order_date DESC);

-- ② 커버링 인덱스: SELECT 컬럼이 모두 인덱스에 있으면 테이블 접근 불필요
CREATE INDEX idx_customer_cover ON customers (customer_id) INCLUDE (name, email);
SELECT customer_id, name, email FROM customers WHERE customer_id = 42;
-- → Index Only Scan (가장 빠름)

-- ③ 부분 인덱스 (Partial Index): 특정 조건 행만 인덱싱
CREATE INDEX idx_orders_pending ON orders (created_at)
  WHERE status = 'PENDING';     -- PENDING 5%만 인덱싱 → 크기↓, 속도↑

-- ④ 함수 기반 인덱스
CREATE INDEX idx_users_email_lower ON users (LOWER(email));
-- WHERE LOWER(email) = 'user@example.com' → 인덱스 사용

-- ⑤ CONCURRENTLY: 운영 중 잠금 없이 인덱스 생성
CREATE INDEX CONCURRENTLY idx_products_category ON products (category_id);
```

### ⭐ 선두 컬럼 원칙 (Leftmost Prefix Rule) — 가장 많이 틀리는 부분

`INDEX(customer_id, order_date)` 를 만들었을 때

| 쿼리 | 인덱스 사용? | 이유 |
|------|:---:|---|
| `WHERE customer_id = 5` | ✅ | 선두 컬럼 있음 |
| `WHERE customer_id = 5 AND order_date > '...'` | ✅ | 선두부터 순서대로 |
| `WHERE customer_id = 5 ORDER BY order_date DESC` | ✅ | 선두 + 정렬 |
| **`WHERE order_date > '2024-01-01'`** | ❌ **사용 불가** | **선두 컬럼(customer_id)이 없음** |

> 💡 **전화번호부로 이해하세요.**
> `(성, 이름)` 순으로 정렬된 전화번호부에서
> - "김씨" 찾기 → ✅ 바로 찾음
> - "길동이라는 이름" 찾기 → ❌ 성을 모르면 처음부터 다 뒤져야 함

### 복합 인덱스 컬럼 순서 원칙

```
등호(=) 조건 컬럼 먼저  →  범위(<,>) 조건 나중  →  선택도 높은 컬럼 우선
```

**예시**
```sql
WHERE status = 'A' AND created_at > '2024-01-01'

✅ INDEX(status, created_at)   -- status로 좁히고 → created_at 범위
❌ INDEX(created_at, status)   -- 범위를 넓게 잡고 → status 필터 (비효율)
```

---

## 17-5. 선택도(Selectivity) — 좋은 인덱스의 기준

> ### **선택도 = 고유값 수 ÷ 전체 행 수**

**1에 가까울수록 인덱스 효과가 큽니다.**

| 컬럼 | 선택도 | 평가 |
|------|:---:|---|
| `gender` (M/F) | **0.5** | ❌ **나쁨** — 반은 걸러도 반이 남음 |
| `email` | **≈ 1** | ✅ **좋음** — 하나만 콕 집힘 |

> 💡 **성별에 인덱스를 걸면 왜 소용없나?** 100만 명 중 50만 명이 남자면, 인덱스를 타고 가도 **50만 건을 봐야** 합니다. 그럴 바엔 그냥 Full Scan이 낫습니다.

---

## 17-6. 인덱스 DBMS별 차이

| DBMS | 특징 |
|------|------|
| **PostgreSQL** | **비클러스터형 기본** (힙 저장, 인덱스는 별도 구조)<br>**GIN** : JSONB, 배열, FTS / **GiST** : 지리정보, 범위, 벡터 유사도<br>**BRIN** : 타임시리즈 대용량 (작은 크기, 빠른 빌드)<br>**Hash** : 등호만 / **deduplication** : 동일 페이지 내 중복값 공간 절약 (PG 13+) |
| **MySQL/MariaDB** | **InnoDB: 클러스터형 인덱스 기본** (PK 기준으로 데이터 물리 정렬)<br>⚠️ **PK 없으면 내부 Row ID 자동 생성 → 대체 PK 권장**<br>GIN/GiST 미지원 → FULLTEXT 인덱스로 전문검색 (제한적)<br>Hash : InnoDB는 **어댑티브 해시 인덱스** (자동, 수동 생성 불가) |
| **Oracle** | B-Tree(기본) + **Bitmap**(저선택도 DW용) + Cluster 인덱스 |
| **SQL Server** | **클러스터형(테이블당 1개)** — 데이터 물리 정렬<br>비클러스터형 : 여러 개 가능<br>**Columnstore 인덱스** — OLAP 집계에 최적화 |

---

## 17-7. B-Tree / B+Tree 내부 구조

> 🚨 **[정오] 강사님 정정 사항**
> 원본 자료의 **"균형 **이진** 트리"** 는 오류입니다.
> B-Tree는 **다진 균형 트리(Multi-way Balanced Search Tree)** 이고, **실제 RDB 구현은 대부분 B+Tree** 입니다.

### B-Tree 정리

```
B-Tree (실제 구현은 주로 B+Tree)
├── 구조: 다진 균형 트리 (Multi-way Balanced Search Tree)
├── 효율적인 연산 (인덱스 활용 가능)
│   ├── 단일 값 검색   : =
│   ├── 범위 검색      : BETWEEN, <, >, <=, >=
│   ├── 전방 일치 검색 : LIKE 'prefix%'
│   └── 정렬 연산      : ORDER BY, GROUP BY
└── 위상: 대부분의 RDB에서 사용하는 기본 인덱스 구조
```

> ✅ **"모든 리프 노드가 같은 깊이"** (Balanced) → **O(log N) 탐색 보장** — 이 부분은 그대로 맞습니다.

---

### ⭐ 왜 RDB는 이진 트리가 아니라 B+Tree를 쓰는가 — 이유 2가지

#### ① 디스크 블록(페이지) 단위 입출력

```
DB는 데이터를 1바이트씩 읽지 않습니다.
보통 4KB~16KB 크기의 '페이지(Page) / 블록(Block)' 단위로
디스크 → 메모리로 한 번에 로드합니다.
```

| | **이진 트리** | **B+Tree** |
|---|---|---|
| 노드 하나에 든 키 | **1개** | **수십~수백 개** |
| 페이지 활용 | ❌ **4KB 페이지에 키 1개** → 낭비 | ✅ 페이지를 꽉 채움 |
| 결과 | **디스크 접근을 여러 번 반복** | 한 번 읽으면 많은 키를 얻음 |

> 🔑 **핵심** : 디스크에서 한 번 읽어올 때 **어차피 4KB를 통째로** 가져옵니다.
> 그 안에 키가 1개만 들어있으면 **3,999바이트를 버리는** 셈입니다.

#### ② 낮은 트리 높이 (Fan-out)

> **Fan-out** = 노드 하나가 가질 수 있는 **자식 노드의 개수**

```
B-Tree는 노드 하나에 여러 키를 모아 저장 → Fan-out이 매우 큼

  노드 하나가 자식 100개를 가진다면?
     1단계 :        100개
     2단계 :     10,000개
     3단계 :  1,000,000개
     4단계 : 100,000,000개   ← 단 4단계로 1억 건 커버!
```

| | 이진 트리 | B+Tree (Fan-out 100) |
|---|---|---|
| **1억 건 커버에 필요한 높이** | **약 27단계** | **약 4단계** |
| **디스크 읽기 횟수** | 27번 | **4번** |

> 🔑 **디스크 읽기 횟수는 트리의 높이에 비례합니다.**
> 그래서 **높이를 극단적으로 낮춘 B-Tree 계열**이 RDB에 훨씬 유리합니다.

---

### ⭐ B-Tree vs B+Tree — 무엇이 다른가

**MySQL(InnoDB), PostgreSQL 등 대부분의 주요 RDB는 B-Tree를 개선한 B+Tree를 사용합니다.**

| | **B-Tree** | **B+Tree** (실제 RDB) |
|---|---|---|
| **데이터 저장 위치** | 모든 노드(Root/Branch/Leaf) | ✅ **최하단 리프 노드에만** |
| **중간 노드 역할** | 데이터 + 경로 안내 | **경로 안내만** (더 많은 키 수용 → Fan-out↑) |
| **리프 간 연결** | 없음 | ✅ **연결 리스트(Linked List)로 이어짐** |
| **범위 검색** | 트리를 계속 오르내려야 함 | 🏆 **리프를 옆으로 쭉 훑으면 끝** |

```
        [Root]                       ← 경로 안내만
       /   |   \
  [Branch][Branch][Branch]           ← 경로 안내만
   /  \    /  \    /  \
[Leaf][Leaf][Leaf][Leaf][Leaf]       ← 여기에만 실제 데이터(또는 레코드 포인터)
  ↔     ↔     ↔     ↔     ↔          ← 연결 리스트!
```

> 💡 **`WHERE score BETWEEN 80 AND 90` 이 왜 빠른가**
> ① 트리를 타고 **80이 있는 리프**를 찾고
> ② 거기서부터 **옆으로(→) 쭉 따라가며** 90까지 읽으면 끝
> 매번 루트로 돌아갈 필요가 없습니다. **이게 B+Tree가 범위 검색에 강한 이유**입니다.

---

### ❓ [수강생 질문] 범위 검색 시 포인터 진행 횟수는 B-Tree나 B+Tree나 같지 않나요?

> 💬 **질문** : *"범위 검색을 위해 Linked List로 포인터를 진행하는 횟수는 B+Tree와 B-Tree 둘 다 같지 않나요?"*

> ## **답 : 같지 않습니다. B+Tree가 훨씬 적고 효율적입니다.**

| | **B-Tree** | **B+Tree** |
|---|---|---|
| **데이터 위치** | 부모·자식 노드 모두에 **흩어져 있음** | **최하단 리프에만** |
| **범위 검색 경로** | 트리의 **위아래(상하)를 계속 오르내림** | 시작 위치만 내려간 뒤 **옆으로(수평) 순차 이동** |
| **포인터 이동 / 디스크 접근** | **많음** | **훨씬 적음** |

> 🔑 **현대 RDB가 B+Tree를 기본 인덱스로 채택한 이유가 바로 이 포인터 이동 구조의 차이**입니다.

---

#### 📖 책으로 비유하면 — 관련 내용(범위)을 찾아 읽는 상황

| | **B-Tree** = *목차와 본문이 섞인 책* | **B+Tree** = *본문이 뒤에 순서대로 몰려 있고, 책갈피가 쭉 이어진 책* |
|---|---|---|
| **찾는 법** | 목차 페이지 봤다가 → 본문으로 내려갔다가 →<br>다음 내용 찾으려고 **다시 앞쪽 목차로 올라갔다가** → 내려오고 **반복** | 처음 시작 페이지 찾을 때만 목차를 **딱 한 번** 봄 |
| **그 다음은** | 트리를 **위아래로 계속 왔다 갔다** | 페이지에 붙은 **책갈피(Linked List)만 잡고 옆으로 한 장씩 스윽** |
| **손가락(포인터)** | **바쁘게 움직여야 함** | **옆으로만 넘기면 끝** — 위로 올라갈 필요 전혀 없음 |

---

#### ⭐ 진짜 핵심 — **"포인터 이동에 드는 비용(Cost)"**

> 💬 **추가 질문** : *"C언어 포인터 관점으로 보면, 어차피 원하는 다음 값으로 따라간 거니까 의미 없는 이동은 아니지 않나요?"*
>
> **맞는 말씀입니다.** 다만 **컴퓨터가 치러야 하는 비용**을 생각하면 이야기가 달라집니다.
> **DB에서는 이 비용이 가장 중요한 요소 중 하나입니다.**

##### C언어 메모리(RAM) 포인터 vs 디스크 포인터

| | **RAM 포인터** (`ptr->next`) | **DB 노드 이동** |
|---|---|---|
| **단위** | 바이트 | **디스크 블록/페이지 (보통 16KB)** |
| **속도** | **nanosecond** — 거의 공짜 | **디스크 I/O** |
| **C로 치면** | 그냥 주소 참조 | **`fseek()` + `fread()` 를 새로 호출**하는 것과 같음 |

```c
// C언어 관점으로 옮기면 — DB의 노드 이동 하나하나가 이렇습니다
fseek(fp, block_offset, SEEK_SET);   // 디스크 헤드 이동
fread(buffer, 16384, 1, fp);         // 16KB 블록 읽기
```

##### 🐢 B-Tree — 값 하나 찾을 때마다 디스크를 여러 번

**`20` 다음 값 `30`을 찾으려면**

```
30이 들어 있는 블록을 읽기 위해
  ① 부모 블록을 디스크에서 다시 읽고
  ② 자식 블록을 또 읽어야 함

→ 원하는 값에 도달은 하지만, 그 과정에서 Disk I/O가 2~3번 발생
```

##### 🚀 B+Tree — 이미 읽어온 블록 안에서 다 해결

```
리프 노드 블록 하나(16KB) 안에 데이터 수백 개가 순서대로 연속 저장

   [ 리프 블록 #1 (16KB) ]
   20, 21, 22, 23, ... , 30, ... , 250
    ↑ 20 옆에 21,22,23...30 이 같은 블록 안에 모여 있음

→ 포인터를 넘길 때 디스크를 새로 읽지 않고
  이미 RAM에 올려둔 데이터를 C언어 배열 읽듯 읽음
→ 다음 블록으로 넘어갈 때만 디스크를 1번 읽음
```

---

#### 📊 그래서 실제 속도 차이가 엄청나게 납니다

| | **B-Tree** | **B+Tree** |
|---|---|---|
| **값 하나 넘어갈 때** | **비싼 Disk I/O** 를 치러야 함 | **이미 읽어온 연속 메모리**를 쓱 훑음 |
| **디스크 읽기 빈도** | 값마다 2~3회 | **블록이 끝날 때만 1회** |

> 🔑 **정리**
> **'이동' 자체가 무의미한 건 아닙니다.**
> 다만 **B-Tree는 값 하나마다 expensive한 Disk I/O를 치르고**,
> **B+Tree는 이미 읽어온 연속 메모리 영역을 쓱 지나가기** 때문에 **실제 속도 차이가 엄청나게 벌어집니다.**

---

### 구성 요소

| 구성 요소 | 역할 |
|-----------|------|
| **Root Node** | 트리 시작점 — **경로 안내** |
| **Branch Node** | 탐색 경로를 안내하는 중간 노드 — **경로 안내** |
| **Leaf Node** | **실제 인덱스 키 값 + 테이블 행의 물리 위치**(ctid/ROWID) 저장<br>**리프끼리 연결 리스트** → 범위 탐색 효율적 |

### 인덱스 키 크기의 영향

```
키가 작을수록  →  노드당 더 많은 항목  →  트리 깊이 감소  →  빠름

UUID (16바이트)  vs  BIGINT (8바이트)
    ↑ UUID 인덱스는 더 큰 트리
```

> 💡 **PK를 UUID로 잡으면 인덱스가 커집니다.** 성능이 중요하면 `BIGINT` 대체키를 고려하세요.

### Fill Factor (페이지 채움 비율)

- **기본 90%** — 페이지를 90%만 채우고 **10% 여유 공간** 남김
- **UPDATE가 많은 테이블**은 Fill Factor를 낮추면 **페이지 분할(Split) 감소**

```sql
CREATE INDEX ... WITH (fillfactor = 70);
```

---

## 17-8. 커버링 인덱스 — Index Only Scan 달성

> **SELECT에 필요한 모든 컬럼이 인덱스에 포함** → **테이블 Heap 접근 없이 인덱스만으로 응답**

```sql
-- ❌ 일반 인덱스 (Index Scan: 테이블 접근 필요)
CREATE INDEX idx_email ON users (email);
SELECT id, name FROM users WHERE email = 'a@b.com';
-- → Index Scan using idx_email + Heap Fetch (추가 I/O 발생)

-- ✅ 커버링 인덱스 (Index Only Scan: 테이블 접근 없음!)
CREATE INDEX idx_email_cover ON users (email) INCLUDE (id, name);
SELECT id, name FROM users WHERE email = 'a@b.com';
-- → Index Only Scan (I/O 최소화, 훨씬 빠름)

-- 확인
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, name FROM users WHERE email = 'a@b.com';
-- "Index Only Scan using idx_email_cover on users"
-- "Heap Fetches: 0"     ← 테이블 접근 0번!
```

```
[일반 인덱스]                     [커버링 인덱스]
  인덱스에서 위치 찾고               인덱스 안에 답이 다 있음
        ↓                                ↓
  테이블로 가서 값 읽어옴 (I/O)      끝. 테이블 안 감.
```

| DBMS | 문법 |
|------|------|
| **PostgreSQL** | `INCLUDE` 절 (인덱스 탐색에는 미사용, **반환에만** 포함) |
| **SQL Server** | `INCLUDE` 절 동일 지원 |
| **MySQL** | 커버링 인덱스 = **WHERE + SELECT 컬럼 모두** 인덱스에 포함 |

> ✅ **Checkpoint** : **`Heap Fetches: 0`이 목표**. Visibility Map이 최신이어야 하므로 **VACUUM으로 유지**해야 합니다.

---

## 17-9. 인덱스 관리 — 안 쓰는 인덱스 찾아내기

```sql
-- PostgreSQL: 인덱스 사용률 확인
SELECT
  indexrelname                                  AS index_name,
  relname                                       AS table_name,
  idx_scan                                      AS scan_count,   -- 사용 횟수
  idx_tup_read                                  AS tuples_read,
  idx_tup_fetch                                 AS tuples_fetched,
  pg_size_pretty(pg_relation_size(indexrelid))  AS index_size
FROM   pg_stat_user_indexes
ORDER BY idx_scan ASC       -- 사용 횟수가 적은 것 = 제거 후보
LIMIT 20;

-- 미사용 인덱스 (idx_scan = 0) — 삭제 검토 대상
SELECT indexrelname, relname, pg_size_pretty(pg_relation_size(indexrelid))
FROM   pg_stat_user_indexes
WHERE  idx_scan = 0
  AND  indexrelname NOT LIKE 'pk_%'    -- PK 제외
ORDER BY pg_relation_size(indexrelid) DESC;

-- 인덱스 재구성 (블로트 제거)
REINDEX INDEX CONCURRENTLY idx_orders_cust_date;   -- 운영 중 잠금 없이
REINDEX TABLE CONCURRENTLY orders;

-- MySQL: 인덱스 통계
SELECT TABLE_NAME, INDEX_NAME, CARDINALITY
FROM   information_schema.STATISTICS
WHERE  TABLE_SCHEMA = 'mydb'
ORDER BY CARDINALITY ASC;
```

> 🔑 **`idx_scan = 0` = 한 번도 쓰인 적 없는 인덱스.** 쓰기 비용만 축내고 있으니 **삭제 검토** 대상입니다.

---

# 18. 실행계획 분석

> 📌 **다루는 것** : EXPLAIN ANALYZE · 플랜 읽기 · DBMS별 도구

## 18-1. 실행계획이란?

> **SQL이 느린 이유를 눈으로 보는 창**

- DB 옵티마이저가 SQL을 **실행하기 전에 결정하는 실행 방법**
- *"어떤 순서로 테이블을 읽고, 어떤 인덱스를 쓰며, 어떤 조인 방식을 택했는가"*

### EXPLAIN vs EXPLAIN ANALYZE

| 명령 | 동작 |
|------|------|
| **`EXPLAIN`** | **추정** 실행 계획만 보여줌 (**쿼리 실행 안 함**) |
| **`EXPLAIN ANALYZE`** | **실제 실행 + 측정값** ⚠️ **실제로 실행됨 — DML이면 ROLLBACK 권장** |
| **`EXPLAIN (ANALYZE, BUFFERS)`** | 버퍼 히트 / 디스크 읽기까지 측정 |

### 실행계획을 읽어야 하는 4가지 상황

- 쿼리가 **갑자기 느려졌을 때**
- **인덱스를 만들었는데 안 쓰이는 것 같을 때**
- **JOIN 방식이 이상해 보일 때** (Hash vs Nested Loop)
- **rows 예측값과 actual rows가 크게 다를 때** → **통계 갱신 필요**

> 🛠 **시각화 도구** : [explain.dalibo.com](https://explain.dalibo.com) — PostgreSQL JSON 플랜을 붙여넣으면 트리로 보여줍니다.

---

## 18-2. PostgreSQL EXPLAIN ANALYZE 읽기

```sql
BEGIN;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT s.name, c.title, e.score
FROM   students s
  JOIN enrollments e ON e.student_id = s.id
  JOIN courses     c ON c.id = e.course_id
WHERE  s.major_id = 1;
ROLLBACK;   -- DML이면 롤백
```

**결과 해석**

```
Hash Join  (cost=12.5..45.8 rows=200 width=32)
           (actual time=0.5..2.3 rows=185 loops=1)
  Hash Cond: (e.student_id = s.id)
  Buffers: shared hit=12 read=5
           ↑ shared hit: 메모리에서 읽음 (빠름)
           ↑ read      : 디스크에서 읽음 (느림) → 캐시 히트율 확인
  ->  Seq Scan on enrollments  (cost=0..15 rows=1000)
      ↑ 인덱스 없음! → 인덱스 추가 검토
  ->  Hash
      ->  Index Scan on students  (cost=0.29..8 rows=50)
            Index Cond: (major_id = 1)

Planning Time:  0.2 ms
Execution Time: 2.5 ms      ← 전체 실행 시간
```

### 🔍 체크 포인트 3가지

| 신호 | 의미 | 조치 |
|------|------|------|
| **Seq Scan** on 대형 테이블 | 인덱스 없음 | 인덱스 추가 |
| **예측 `rows` ≠ 실제 `actual rows`** | 통계가 오래됨 | **`ANALYZE`** 실행 |
| **Hash Batches > 1** | 메모리 **Spill** 발생 | **`work_mem`** 증가 검토 |

**추가 활용**
```sql
-- DML 포함 시 ROLLBACK으로 실제 변경 방지
BEGIN;
EXPLAIN ANALYZE UPDATE orders SET status = 'DONE' WHERE id = 1;
ROLLBACK;

-- JSON 포맷 (dalibo.com 붙여넣기용)
EXPLAIN (ANALYZE, FORMAT JSON) SELECT ...;
```

---

## 18-3. MySQL / SQL Server / Oracle 실행계획

```sql
-- MySQL: EXPLAIN (기본)
EXPLAIN FORMAT=JSON
SELECT * FROM orders o
  JOIN customers c ON o.customer_id = c.id
WHERE o.order_date >= '2024-01-01';
```

**MySQL 결과 해석 키워드**

| 항목 | 의미 |
|------|------|
| `"access_type": "range"` | ✅ 범위 인덱스 스캔 (좋음) |
| **`"access_type": "ALL"`** | ❌ **Full Table Scan (나쁨!)** |
| `"rows_examined_per_scan": 45` | 예상 스캔 행 수 |
| `"key": "idx_orders_date"` | 사용된 인덱스 |

```sql
-- MySQL 8.0.18+: 실제 측정
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 1;
-- "-> Index lookup on orders using idx_cust (customer_id=1)
--    (actual time=0.1..0.5 rows=10 loops=1)"

-- SQL Server
SET SHOWPLAN_ALL ON;
SELECT * FROM Orders o JOIN Customers c ON o.CustomerID = c.CustomerID
WHERE o.OrderDate >= '2024-01-01';
SET SHOWPLAN_ALL OFF;

-- Oracle
SET AUTOTRACE ON;
SELECT * FROM orders WHERE order_date >= DATE '2024-01-01';
-- Execution Plan: NESTED LOOPS, INDEX RANGE SCAN 등
```

---

## 18-4. ⭐ 실행계획 주요 노드 타입 해석

| 노드 타입 | 의미 | 평가 | 조치 |
|-----------|------|:---:|------|
| **Seq Scan** | 전체 테이블 순차 스캔 | 보통 **Bad** | **인덱스 추가**<br>*(전체 10% 이상 읽을 땐 의도적으로 쓰기도 함)* |
| **Index Scan** | 인덱스 탐색 + 테이블 랜덤 접근 | **Good** | FK/WHERE 컬럼 인덱스 확인 |
| **Index Only Scan** | **인덱스만으로 처리** (테이블 접근 없음) | 🏆 **Best** | **커버링 인덱스** 설계 |
| **Bitmap Heap Scan** | 비트맵 빌드 후 정렬 접근 | 양호 | 여러 인덱스 조합 시 |
| **Hash Join** | 해시 테이블 빌드 후 대용량 등가 조인 | — | ⚠️ **work_mem 부족 시 Spill 주의** |
| **Nested Loop** | 중첩 반복 조인 | 소규모 + 인덱스면 좋음 | ⚠️ **외부 집합이 커지면 느려짐** |
| **Sort** | 결과 정렬 | ⚠️ **확인 필요** | **ORDER BY 컬럼에 인덱스** 추가 |
| **Materialize** | 임시 결과 | ⚠️ **확인 필요** | 서브쿼리를 **CTE/JOIN으로 검토** |

> 🔑 **목표 순서** : `Seq Scan` → `Index Scan` → **`Index Only Scan`**
> 오른쪽으로 갈수록 빠릅니다.

---

# 19. SQL 튜닝 & 느린 쿼리 식별

> 📌 **다루는 것** : 안티패턴 · Slow Query · pg_stat_statements · 파티셔닝

## 19-1. ⭐ SQL 튜닝 안티패턴 8가지 (암기 대상)

> 💡 강의 자료에 **"8 안티패턴 암기"** 라고 명시되어 있습니다.
> **함수적용 · SELECT\* · 타입불일치 · LIKE%앞 · N+1 · NOT IN · DISTINCT남용 · OFFSET**

| # | 안티패턴 | 문제 | 올바른 방법 | 효과 |
|---|----------|------|-------------|------|
| **1** | **`SELECT *`** | 불필요한 데이터 전송,<br>커버링 인덱스 사용 불가 | `SELECT id, email` | 트래픽 감소<br>Index Only Scan 가능 |
| **2** | **`WHERE YEAR(date)=2026`** | **인덱스 컬럼에 함수 → 인덱스 무력화** | `WHERE date >= '2026-01-01'`<br>`AND date < '2027-01-01'` | 인덱스 Range Scan |
| **3** | **`WHERE LOWER(email)=x`** | 함수로 인덱스 무력화 | `CREATE INDEX ON users(LOWER(email))` | **함수 기반 인덱스** 사용 |
| **4** | **서브쿼리 과다** | N×M 반복 실행 | **JOIN 또는 CTE**로 변경 | 한 번의 스캔 |
| **5** | **`NOT IN` (NULL 포함)** | NULL 있으면 **항상 빈 결과** | **`NOT EXISTS`** | NULL 안전 + 빠름 |
| **6** | **`LIKE '%keyword%'`** | 인덱스 미사용, Full Scan | **pg_trgm GIN** 또는 FTS | 텍스트 검색 인덱스 |
| **7** | **암묵적 타입 변환** | `WHERE int_col='123'` → 인덱스 무력화 | `WHERE int_col=123` | 인덱스 사용 |
| **8** | **`COUNT(*)` 과다 / 대용량 OFFSET** | 전체 스캔 / 선형 증가 | 집계 테이블 별도 관리 / **Cursor 방식** | 조회 성능 |

---

## 19-2. 안티패턴 1~4 (인덱스 관련) — 코드로

```sql
-- 안티패턴 1: 인덱스 컬럼에 함수 적용 → 인덱스 무력화
-- ❌
WHERE YEAR(order_date) = 2024      -- 인덱스 미사용!
WHERE UPPER(email) = 'A@B.COM'     -- 인덱스 미사용!
-- ✅
WHERE order_date >= '2024-01-01' AND order_date < '2025-01-01'
CREATE INDEX idx_email_lower ON users (LOWER(email));   -- 함수 기반 인덱스

-- 안티패턴 2: SELECT * → 불필요한 데이터 + 커버링 인덱스 불가
-- ❌
SELECT * FROM orders WHERE customer_id = 1;
-- ✅
SELECT id, order_date, amount FROM orders WHERE customer_id = 1;

-- 안티패턴 3: 암묵적 타입 변환 → 인덱스 무력화
-- ❌  user_id가 INT인데 문자열로 비교
WHERE user_id = '12345'     -- 전체 타입 변환 발생 → Full Scan
-- ✅
WHERE user_id = 12345

-- 안티패턴 4: LIKE 앞 와일드카드 → 전체 스캔
-- ❌
WHERE name LIKE '%길동%'    -- B-Tree 인덱스 사용 불가
-- ✅  prefix는 인덱스 사용 가능
WHERE name LIKE '홍%'
-- 또는 GIN + pg_trgm으로 중간 검색 가속
CREATE EXTENSION pg_trgm;
CREATE INDEX idx_name_trgm ON users USING GIN (name gin_trgm_ops);
SELECT * FROM users WHERE name LIKE '%길동%';   -- 이제 인덱스 사용!
```

> 💬 **원본 272p의 안티패턴 3 예시에 `-- O` / `-- X` 표기가 뒤바뀌어 있습니다.** 위 코드가 올바른 표기입니다. (`WHERE user_id = '12345'` 가 나쁜 예)

---

## 19-3. 안티패턴 5~8 (쿼리 구조 관련) — 코드로

```sql
-- 안티패턴 5: N+1 문제
-- ❌ 루프 안에서 개별 쿼리 (1 + N번)
for student in students:
    score = db.query("SELECT score FROM e WHERE student_id=%s", student.id)
-- ✅ 한 번의 JOIN으로 처리
SELECT s.id, s.name, e.score
FROM   students s LEFT JOIN enrollments e ON e.student_id = s.id
WHERE  s.id = ANY($1);      -- 배열로 한 번에

-- 안티패턴 6: NOT IN + NULL 함정
-- ❌ 서브쿼리에 NULL 있으면 전체 결과 빈 집합!
WHERE id NOT IN (SELECT student_id FROM enrollments)
-- ✅
WHERE NOT EXISTS (SELECT 1 FROM enrollments e WHERE e.student_id = s.id)

-- 안티패턴 7: DISTINCT 남용 → 중복 원인 파악 없이 제거
-- ❌
SELECT DISTINCT s.name FROM students s JOIN enrollments e ON e.student_id = s.id
-- ✅ EXISTS로 존재 여부 확인 (애초에 중복 없음)
SELECT name FROM students s
WHERE EXISTS (SELECT 1 FROM enrollments e WHERE e.student_id = s.id)

-- 안티패턴 8: 대용량 OFFSET → 선형 증가
-- ❌ 1만 페이지 = 10만 행 스캔 후 버림
SELECT * FROM orders ORDER BY id LIMIT 10 OFFSET 100000;
-- ✅ Cursor 방식 (O(log N))
SELECT * FROM orders WHERE id > :last_id ORDER BY id LIMIT 10;
```

---

## 19-4. 느린 쿼리 식별 — 도구

### MySQL — Slow Query Log

```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;                 -- 1초 이상 쿼리 기록
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';

-- 분석 (상위 10개, 실행 시간 기준)
mysqldumpslow -s t -n 10 /var/log/mysql/slow.log;

-- MySQL 8.0: Performance Schema
SELECT DIGEST_TEXT, COUNT_STAR, AVG_TIMER_WAIT/1e12 AS avg_sec
FROM   performance_schema.events_statements_summary_by_digest
ORDER BY AVG_TIMER_WAIT DESC LIMIT 10;
```

### PostgreSQL — pg_stat_statements ⭐

```sql
-- postgresql.conf: shared_preload_libraries = 'pg_stat_statements'
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 느린 쿼리 TOP-10 (평균 실행 시간 기준)
SELECT
  ROUND(mean_exec_time::NUMERIC, 2)   AS avg_ms,
  calls,
  ROUND(total_exec_time::NUMERIC, 0)  AS total_ms,
  ROUND(shared_blks_hit::NUMERIC
        / NULLIF(shared_blks_hit + shared_blks_read, 0) * 100, 1) AS cache_hit_pct,
  LEFT(query, 100)                    AS query_snippet
FROM   pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 통계 초기화 (튜닝 전후 비교용)
SELECT pg_stat_statements_reset();
```

> 💡 **`total_exec_time`도 함께 보세요.** 0.1초짜리 쿼리가 하루 100만 번 실행되면, 10초짜리 쿼리 하나보다 훨씬 큰 문제입니다.

---

## 19-5. Slow Query 분석 방법론 4단계

| 단계 | 하는 일 |
|------|---------|
| **1단계 — 수집** | **PostgreSQL** : `log_min_duration_statement = 1000` (1초 이상 로깅)<br>**MySQL** : `slow_query_log = ON`, `long_query_time = 1`<br>**pg_stat_statements** : 누적 호출 수, 총 시간, 평균 시간 분석 |
| **2단계 — 병목 특정 & EXPLAIN** | **Seq Scan on 대형 테이블** → 인덱스 추가<br>**actual rows ≠ rows 예측** → **`ANALYZE`** 실행<br>**Hash Batches > 1** → `work_mem` 증가 (per-session) |
| **3단계 — 개선 & 검증** | **인덱스 추가 (`CONCURRENTLY`)** → 실행계획 재확인<br>쿼리 구조 변경 (서브쿼리→CTE/JOIN, DISTINCT 제거)<br>**Before/After 실행 시간 비교 및 기록** |
| **4단계 — 지속 모니터링** | `pg_stat_statements_reset()` 후 일정 기간 모니터링<br>**Cloud** : AWS Performance Insights, GCP Query Insights |

---

## 19-6. 파티셔닝 — Range / Hash / List

> 📖 **파티셔닝** : 큰 테이블을 **작은 조각으로 나눠 저장** (단일 DB 인스턴스 내)

### Range 파티셔닝 (날짜 기준)

```sql
CREATE TABLE sales (
  id        BIGSERIAL,
  sale_date DATE NOT NULL,
  amount    NUMERIC
) PARTITION BY RANGE (sale_date);

CREATE TABLE sales_2023 PARTITION OF sales
  FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE sales_2024 PARTITION OF sales
  FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE sales_2025 PARTITION OF sales
  FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### ⭐ Partition Pruning — 파티셔닝의 핵심 효과

```sql
EXPLAIN SELECT * FROM sales
WHERE sale_date BETWEEN '2024-06-01' AND '2024-06-30';

-- → Seq Scan on sales_2024     ← 이것만 읽음!
--   (sales_2023, sales_2025는 자동 제외)
```

> 🔑 **WHERE에 파티션 키가 있어야 Pruning이 작동합니다.**
> **파티션 키가 WHERE에 없으면 모든 파티션을 스캔 → 효과 없음.**

### Hash / List 파티셔닝

```sql
-- Hash 파티셔닝 (MySQL): 균등 분산
CREATE TABLE orders (order_id INT NOT NULL, customer_id INT NOT NULL, ...)
PARTITION BY HASH(customer_id) PARTITIONS 4;

-- List 파티셔닝 (PostgreSQL): 지역별
CREATE TABLE orders PARTITION BY LIST (region);
CREATE TABLE orders_kr PARTITION OF orders FOR VALUES IN ('KR', 'KO');
CREATE TABLE orders_us PARTITION OF orders FOR VALUES IN ('US', 'CA');
```

### DB별 지원 현황

| 타입 | PostgreSQL | MySQL/MariaDB | Oracle | SQL Server |
|------|:---:|:---:|:---:|:---:|
| **Range** | ○ (10+) | ○ | ○ | ○ (Enterprise+) |
| **List** | ○ | ○ | ○ | ○ (Enterprise+) |
| **Hash** | ○ | ○ | ○ | ○ (Enterprise+) |
| **Composite** | ○ (Range+Hash 등) | ○ | ○ | 제한적 |
| **Partition Pruning** | ○ (자동) | ○ (자동) | ○ (자동) | ○ (자동) |
| **파티션 인덱스** | ○ (Local/Global) | ○ | ○ (Local/Global) | ○ |

### 파티셔닝 운영 관리

| 항목 | 내용 |
|------|------|
| **파티션 인덱스** | 부모 테이블에 인덱스 생성 시 **각 파티션에 자동 생성**<br>`CREATE INDEX ON orders (customer_id)` → 모든 파티션 자동 적용 |
| **신규 파티션** | 범위 파티션은 **다음 기간 파티션을 미리 생성** |
| **오래된 파티션 삭제** | `DROP TABLE orders_2022q1` → **매우 빠름** (개별 파일 삭제)<br>💡 `DELETE`와 비교하면 압도적입니다 |
| **자동 관리** | **`pg_partman`** 확장 (생성·삭제·유지보수) |

### 🔀 파티셔닝 vs 샤딩

| | **파티셔닝** | **샤딩** |
|---|---|---|
| **범위** | **단일 DB 인스턴스 내** 논리 분할 | **여러 DB 인스턴스**에 물리 분산 |
| **JOIN** | ✅ 가능 | ❌ 어려움 |
| **확장** | 수직 | **수평 확장 (Scale-out)** |
| **복잡도** | 간단 | 높음 |

---

## 19-7. SQL 튜닝 실전 체크리스트 4단계

| 단계 | 체크 항목 |
|------|-----------|
| **1단계 — 실행계획 확인** | • `EXPLAIN ANALYZE`로 **Seq Scan 여부** 확인<br>• **actual rows vs rows 예측** 차이 큰 경우 → **`ANALYZE`**<br>• **Hash Batches > 1** → `work_mem` 부족, Spill 발생 |
| **2단계 — 인덱스 최적화** | • **WHERE/JOIN/ORDER BY** 컬럼에 인덱스 추가<br>• **복합 인덱스 순서** : 등호(=) 먼저 → 범위(<,>) 나중<br>• **커버링 인덱스**로 Index Only Scan 유도 |
| **3단계 — 쿼리 개선** | • 함수 적용된 컬럼 → **범위 조건 또는 함수 기반 인덱스**<br>• 서브쿼리 → **JOIN 또는 CTE**<br>• **N+1 문제** → 한 번의 JOIN |
| **4단계 — 아키텍처 개선** | • 대용량 집계 → **Materialized View / 집계 테이블**<br>• 전체 스캔 불가피 → **파티셔닝**으로 스캔 범위 축소<br>• 읽기 부하 → **Replica**(읽기 전용 복제본) 분산 |

> 🔑 **위에서부터 순서대로** 하세요. 아키텍처를 먼저 뜯어고치는 건 최후의 수단입니다.

---

## 19-8. Before / After 성능 비교 (자료의 예시값)

| 쿼리 패턴 | Before | After | 향상 |
|-----------|--------|-------|:---:|
| **인덱스 없는 조회** | Seq Scan (1000ms) | Index Scan (5ms) | **200배** ↑ |
| **함수 적용으로 인덱스 무력화** | `WHERE YEAR(date)=2024` (Seq Scan) | `WHERE date >= '2026-01-01'` (Index) | **100배** ↑ |
| **`SELECT *` 전체 컬럼** | 100컬럼 × 100만행 전송 | 5컬럼만 (커버링 인덱스) | **20배** ↑ |
| **N+1 쿼리** | 1000명 → **1000번 DB 쿼리** | **JOIN 1번** | **1000배** ↑ |
| **대용량 OFFSET** | OFFSET 100만 (1000ms) | Cursor 방식 (3ms) | **333배** ↑ |
| **Hash Join Spill** | work_mem 부족 → 디스크 | work_mem 256MB 증가 | **10배** ↑ |
| **미사용 인덱스 유지** | INSERT 20ms (5개 인덱스 재정렬) | 인덱스 2개 삭제 → 8ms | **2.5배** ↑ |

> ⚠️ 자료에 **"(예시)"** 로 명시된 값입니다. 실제 환경에 따라 달라집니다.
> 💡 **마지막 줄이 중요합니다** — 인덱스를 **지웠더니** 빨라진 사례입니다.

---

# ★ [강사님 보충] 실무 관점의 튜닝 & DB 내부 동작

> 📌 강사님이 별도로 공유해주신 내용입니다. **시험보다 실무에서 훨씬 자주 쓰이는 관점**입니다.

## ⓪ ⭐ 튜닝의 핵심 목표 3가지 — 무엇을 보고 판단할 것인가

> 🚨 **실무 및 성능 튜닝 관점에서는 수 ms 이하 단위의 미세한 플래닝/실행 시간 차이보다는, 아래 지표들을 핵심 튜닝 목표로 삼는 것이 바람직합니다.**

| # | 지표 | 확인할 것 |
|---|------|-----------|
| **1** | **Buffers 지표** | **`shared read`(디스크에서 읽은 블록 수)가 최소화**되고<br>**`shared hit` 비중이 높게 유지**되는가? |
| **2** | **실행계획 구조** | **`Seq Scan` 대신 작성한 `Index Scan` / `Index Only Scan`을 제대로 타는지**,<br>**불필요한 연산들에 의한 오버헤드**가 없는가? |
| **3** | **재현성** | 동일 환경에서 **여러 번 수행했을 때 평균 런타임 수치가 안정적**인가? |

> 🔑 **`Execution Time`이 2.5ms → 2.3ms로 줄었다"는 의미 없는 개선입니다.**
> 측정 노이즈일 수 있습니다. **위 3가지가 실제로 바뀌었는지**를 보세요.

### 💡 3번(재현성)을 실습에서 적용하는 법

```sql
-- 같은 쿼리를 3~5번 돌려서 평균을 보세요
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;   -- 1회차: 캐시 워밍업 (버림)
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;   -- 2회차
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;   -- 3회차  ← 2~3회차 평균으로 비교
```

**왜 필요한가** — 1회차는 캐시가 비어 있어 `read`가 크게 나옵니다. **인덱스 효과인지 캐시 효과인지 구분되지 않습니다.**

---

## ① 옵티마이저의 비용 계산 방식 — 🧭 네비게이션 비유

| 질문 | 답 |
|------|-----|
| **옵티마이저란?** | DB 내부의 **'네비게이션'**.<br>데이터(목적지)를 찾아달라고 명령하면, **여러 길**(인덱스 이용, 전체 스캔 등) 중 **가장 빠르고 저렴한 길**을 찾아줍니다. |
| **비용 계산 방식을 직접 바꿀 수 있나?** | ✅ **네, 가능합니다.**<br>네비 옵션에서 *최단 거리 우선 / 고속도로 우선*을 고르듯,<br>**DB 파라미터**로 *"디스크 읽는 비용을 높게 측정해 줘"*, *"CPU 계산 비용을 낮춰 줘"* 처럼 **가중치를 조절**할 수 있습니다. |
| **모든 DB가 똑같이 계산하나?** | ❌ **아닙니다.**<br>네이버 지도·카카오내비·Tmap이 알고리즘과 예상 시간이 다르듯,<br>**MySQL, Oracle, PostgreSQL 등 DB 브랜드마다 비용 공식과 가중치가 모두 다릅니다.** |

> 💡 **그래서 `cost` 값은 DB 간에 비교하면 안 됩니다.** 같은 DB 안에서 **계획끼리 비교하는 상대 점수**일 뿐입니다.

---

## ② 데이터 통계 정보의 업데이트 방식 — 📚 도서관 비유

| 질문 | 답 |
|------|-----|
| **통계 정보란?** | 옵티마이저(네비게이션)가 길을 잘 찾으려면 **"어느 도로가 막히는지", "어느 구역에 책이 많은지"** 를 알아야 합니다. 이 정보가 **'통계 정보'** 입니다. |
| **책 한 권 넣을 때마다 통계표를 바로 수정하나?** | ❌ **아닙니다.**<br>책이 들어올 때마다 전체 도서 수·장르별 비율을 매번 계산하면 **직원(DB)이 과로로 쓰러집니다.**<br>→ **쓰기 성능 급격히 하락** |

### 그럼 어떻게 갱신되나 — 3가지 방식

| 방식 | 내용 |
|------|------|
| **주기적 갱신** | 책이 어느 정도(예: **전체의 10~20%**) 새로 쌓이면, **밤이나 한가한 시간에 백그라운드 작업자가 비동기로** 갱신 |
| **샘플링** (일부만 살펴보기) | 책 전체를 다 세지 않고, **몇몇 책장만 훑어보고 전체 양을 추측** |
| **수동 갱신** | **대량의 데이터를 한꺼번에 넣은 직후**에는 사람이 직접 *"지금 통계표 다시 작성해!"* 라고 명령 → **`ANALYZE`** |

> 🔑 **이래서 `actual rows`와 예측 `rows`가 벌어지는 겁니다.**
> 통계는 **샘플링 + 주기적 갱신**이라 항상 최신이 아닙니다.
> **대량 INSERT/DELETE 직후에는 반드시 `ANALYZE`** 를 수동으로 돌리세요.

```sql
ANALYZE employees;           -- 특정 테이블
VACUUM ANALYZE employees;    -- Dead tuple 정리 + 통계 갱신 동시에
```

---

## ③ 파티셔닝 구조 — 🗄️ 서류함 비유

| 질문 | 답 |
|------|-----|
| **파티셔닝이란?** | 테이블에 데이터가 몇천만 건 쌓이면 조회가 너무 무거워집니다.<br>그래서 서류철을 **"2024년용 서랍", "2025년용 서랍", "2026년용 서랍"** 으로 **물리적으로 나누어** 보관하는 기술입니다. |
| **하나의 모테이블에 모여 있고 색인만 따로 있나?** | ❌ **아닙니다.**<br>**데이터 자체가 서로 다른 서랍(물리적 파일)에 나누어져** 들어갑니다. |

### 파티션 인덱스 — 로컬 vs 글로벌

| 종류 | 비유 | 동작 |
|------|------|------|
| **로컬 인덱스**<br>(각 서랍 전용 색인표) | 서랍마다 **자기 서랍 안에 뭐가 있는지** 적힌 작은 색인표 | *"2025년 데이터 보여줘"* → **2025년 서랍으로 바로 달려가서 그 안의 색인표만 확인** → 아주 빠름<br>🏆 **보통 이 방식** |
| **글로벌 인덱스**<br>(통합 색인표) | 모든 서랍 내용을 합친 **하나의 큰 색인표** | 가끔 두기도 하지만 **관리하기 까다로움** |

> 💬 **강사님 실무 경험**
> *"저는 **둘 다 사용하는 방식**으로 해서 성능 개선을 해본 적이 있네요.
> 그래서 **부모 테이블에 설정한 인덱스를 그대로 자식들에게도 적용**했습니다."*
>
> → 19-6절의 *"부모 테이블에 인덱스 생성 시 각 파티션에 자동 생성"* 이 바로 이 이야기입니다.

---

## ④ ⭐ 실무에서의 인덱스 설정과 검증

> 💬 강사님 개인 경험 위주의 의견입니다.

### 인덱스란 — 📖 책 뒤의 '찾아보기'

```
색인이 있으면  →  첫 장부터 다 읽을 필요 없이 한 번에 찾아감   (SELECT 속도↑)

하지만 새 내용을 추가하려면
  본문도 쓰고  +  뒤의 '찾아보기' 페이지에도 단어와 쪽수를 일일이 적어야 함
                                              (INSERT/UPDATE 속도↓)
```

### 🚨 실무에서는 EXPLAIN만 보고 인덱스를 결정하나?

> ## **아닙니다.**
> **`EXPLAIN`은 "이 색인표를 사용해서 찾을 예정이다"라는 '계획'만 보여주는 도구**입니다.

### 실제 검증은 어떻게 하나 — 3단계

| 단계 | 방법 |
|------|------|
| **① 조회 검증** | `EXPLAIN`으로 **"이 색인표를 잘 타고 검색하는가?"** 확인 |
| **② 삽입/수정 검증**<br>**(부하 테스트)** 🏆 | ⚠️ **`EXPLAIN`으로는 데이터가 들어갈 때 얼마나 버벅거리는지 알 수 없습니다.**<br>테스트 환경에서 **실제로 초당 몇 천 건의 데이터를 막 넣어보면서**(부하 테스트)<br>**데이터 삽입이 늦어지지 않는지 직접 시계로 측정**합니다.<br>💬 *성능 테스트할 때 제일 많이 사용하는 방법* |
| **③ 최종 결정** | **"찾는 건 엄청 빨라지는데, 데이터를 넣을 때 느려지는 손해가 크지 않은가?"**<br>를 **종합적으로 따져본 뒤** 인덱스를 최종 적용 |

> 🔑 **이게 17-1절 "인덱스 트레이드오프"의 실무 버전입니다.**
> 자료에서 *"읽기↑ / 쓰기↓"* 라고만 배웠던 것을, **실제로 어떻게 재는지**가 여기 있습니다.
>
> ```
> EXPLAIN  →  읽기 쪽만 검증됨   (계획만 보여줌)
> 부하 테스트 →  쓰기 쪽 검증      (실측)
>              ↑ 이게 빠지면 반쪽짜리 검증
> ```

---

# 20. MVCC & 트랜잭션 격리 수준

> 📌 **다루는 것** : 다중버전 동시성 제어 · Isolation Level · DBMS별 실습

## 20-1. MVCC — 왜 읽기가 쓰기를 안 막나

> **MVCC (Multi-Version Concurrency Control)** — 다중 버전 동시성 제어

### 핵심 원리 3가지

| | 내용 |
|---|---|
| **① 새 버전 생성** | 데이터 수정 시 **In-place 덮어쓰기 대신 새 버전 레코드 생성** |
| **② 스냅샷** | 각 트랜잭션은 **시작 시점의 스냅샷(Snapshot)** 을 가짐 |
| **③ 비차단 읽기** | **읽기 작업이 쓰기 작업을 차단하지 않음** → Reader-Writer Lock 경합 감소 |

> 🔑 **이게 Day 1의 격리 수준이 작동하는 원리입니다.**
> "REPEATABLE READ에서 왜 남이 바꿔도 옛날 값이 보이나?" → **내 스냅샷의 버전을 읽기 때문**입니다.

### PostgreSQL MVCC 구현

```
각 행에 시스템 컬럼:
  xmin  = 이 행을 생성한 트랜잭션 ID
  xmax  = 이 행을 삭제/수정한 트랜잭션 ID

UPDATE = 새 버전 INSERT + 구 버전의 xmax 업데이트
         (In-place 수정 없음!)
```

| 개념 | 설명 |
|------|------|
| **Dead tuple** | 더 이상 필요 없는 구버전 → **VACUUM이 주기적으로 회수** |
| ⚠️ **장수 트랜잭션** | Long-running TX는 **VACUUM을 차단** → **Table Bloat 주의** |

### MySQL InnoDB MVCC

| 개념 | 설명 |
|------|------|
| **Undo Log** | 변경 **전** 데이터를 별도 undo 공간에 저장 |
| **Read View** | 트랜잭션 시작 시 스냅샷 생성 |
| **Purge Thread** | 더 이상 필요 없는 undo log 자동 정리 |

> ⚠️ **MVCC의 비용** : 버전 저장 공간 증가 / 장수 TX 시 가비지 증가 / 인덱스 유지 복잡성

---

## 20-2. 격리 수준 실습 — 직접 해보기

```sql
CREATE TABLE bank (id SERIAL, name TEXT, balance INT);
INSERT INTO bank(name, balance) VALUES ('Alice', 1000), ('Bob', 1000);
```

### ① READ COMMITTED (PostgreSQL/Oracle 기본)

| 시각 | 🅰 Session 1 | 🅱 Session 2 |
|:--:|---|---|
| ① | `BEGIN ISOLATION LEVEL READ COMMITTED;`<br>`SELECT balance ... 'Alice';` → **1000** | |
| ② | | `BEGIN;`<br>`UPDATE bank SET balance=800 WHERE name='Alice';`<br>`COMMIT;` |
| ③ | `SELECT balance ... 'Alice';` → **800** ⚠️ | |
| ④ | `COMMIT;` | |

> ➡️ **커밋된 변경사항이 즉시 반영** = **Non-Repeatable Read 발생!**

### ② REPEATABLE READ (MySQL 기본)

| 시각 | 🅰 Session 1 | 🅱 Session 2 |
|:--:|---|---|
| ① | `BEGIN ISOLATION LEVEL REPEATABLE READ;`<br>`SELECT balance ... 'Alice';` → **1000** | |
| ② | | `BEGIN;`<br>`UPDATE bank SET balance=700 WHERE name='Alice';`<br>`COMMIT;` |
| ③ | `SELECT balance ... 'Alice';` → **1000** ✅ | |

> ➡️ **트랜잭션 시작 시점의 스냅샷 유지** = **Non-Repeatable Read 방지**

### ③ SERIALIZABLE — 충돌 시 강제 롤백

| 시각 | 🅰 Session 1 | 🅱 Session 2 |
|:--:|---|---|
| ① | `BEGIN ISOLATION LEVEL SERIALIZABLE;`<br>`SELECT SUM(balance) FROM bank;` → **2000** | |
| ② | | `BEGIN ISOLATION LEVEL SERIALIZABLE;`<br>`UPDATE bank SET balance = balance - 100 WHERE name='Alice';`<br>`COMMIT;` ✅ 성공 |
| ③ | `UPDATE bank SET balance = balance + 100 WHERE name='Bob';`<br>`COMMIT;` | |
| ④ | ❌ **`ERROR: could not serialize access due to concurrent update`** | |

> 🔑 **PostgreSQL SSI**(Serializable Snapshot Isolation)가 **순환 충돌을 감지 → 강제 실패**
> **에러 코드 40001** (Serialization Failure) → ⚠️ **앱에서 재시도 로직 필수**

### 격리 수준 설정 명령

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;               -- 현재 트랜잭션
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;     -- MySQL 세션
ALTER SYSTEM SET default_transaction_isolation = 'read committed';  -- PG 전역
```

---

## 20-3. DBMS별 기본값 및 지원

| 격리수준 | Dirty Read | Non-Rep Read | Phantom Read |
|---|:---:|:---:|:---:|
| **Read Uncommitted** | 허용 | 허용 | 허용 |
| **Read Committed** | 방지 | 허용 | 허용 |
| **Repeatable Read** | 방지 | 방지 | **허용(표준)**<br>*단, InnoDB는 next-key lock으로 실질 차단* |
| **Serializable** | 방지 | 방지 | 방지 |
| **Snapshot** (SQL Server) | 방지 | 방지 | 방지 |

| 격리수준 | PostgreSQL | MySQL/MariaDB | Oracle | SQL Server |
|---|:---:|:---:|:---:|:---:|
| **Read Uncommitted** | RC로 처리 | 지원(비권장) | **미지원** | 지원 |
| **Read Committed** | **기본값** | 지원 | **기본값** | **기본값** |
| **Repeatable Read** | 지원 | **기본값** | **미지원** | 지원 |
| **Serializable** | 지원 | 지원 | 지원 | 지원 |
| **Snapshot** | 해당없음 | 해당없음 | 해당없음 | **지원** |

---

## 20-4. ⭐ 격리 수준별 실무 적용 가이드

| 작업 유형 | 권장 격리 수준 | 이유 | 주의사항 |
|-----------|---------------|------|----------|
| **단순 분석 SELECT** | **Read Committed** | 빠르고 안정적, 최신 데이터 | Non-Repeatable Read 허용 확인 |
| **보고서, 집계** (반복 조회) | **Repeatable Read** | 같은 트랜잭션 내 일관성 보장 | Phantom Read 가능성 |
| **금융 이체, 재고 차감** | **Serializable** | 완벽한 무결성 보장 | ⚠️ **성능 저하, 충돌 재시도 필요** |
| **캐시 워밍업, 읽기 전용** | **Read Committed** | 성능 우선 | 읽기 불일치 허용 여부 확인 |
| **장바구니, 좌석 예약** | **Serializable** 또는<br>**`SELECT FOR UPDATE`** | 동시 접근 충돌 방지 | ⚠️ **Deadlock 가능성 설계 주의** |

---

# 21. Lock & Deadlock 관리

> 📌 **다루는 것** : Row Lock · Advisory Lock · 감지 · 해소 · 모니터링
> 🔑 **왜 Lock이 필요한가** : *"여러 트랜잭션이 동일 데이터를 동시 변경 → 무결성 위반 위험"*

## 21-1. PostgreSQL Lock 계층

| 종류 | 설명 |
|------|------|
| **Row-Level Lock** (Tuple Lock) | 행 단위 충돌 방지 (UPDATE, DELETE) |
| **Table-Level Lock** | ACCESS SHARE, ROW EXCLUSIVE, ACCESS EXCLUSIVE 등 |
| **Advisory Lock** | **사용자 정의 논리 락** (`pg_advisory_xact_lock()`) |

### Row-Level Lock 옵션 3가지 ⭐

| 옵션 | 동작 | 용도 |
|------|------|------|
| **`FOR UPDATE`** | 해당 행 배타적 Lock → 다른 UPDATE/DELETE **차단 대기** | 일반적인 비관적 Lock |
| **`FOR UPDATE NOWAIT`** | 잠겨 있으면 **즉시 ERROR 반환** (대기 없음) | 빠른 실패가 필요할 때 |
| **`FOR UPDATE SKIP LOCKED`** | 잠긴 행을 **건너뛰고 진행** | 🏆 **작업 큐 처리** |

### Lock 유지 시간

- **COMMIT 또는 ROLLBACK 시점에 자동 해제**
- 트랜잭션이 **길수록 Lock 유지 시간 증가 → 충돌 확률 증가**

> 🔑 **트랜잭션을 짧게 유지하는 것이 성능의 핵심**

---

## 21-2. Row Lock 시나리오

| 시각 | 🅰 Session 1 | 🅱 Session 2 |
|:--:|---|---|
| ① | `BEGIN;`<br>`UPDATE items SET stock=stock-1 WHERE id=1;`<br>*(id=1 Lock 획득, COMMIT 안 함)* | |
| ② | | `BEGIN;`<br>`UPDATE items SET stock=stock-1 WHERE id=1;`<br>⏳ **대기(blocking)** |
| ③ | `COMMIT;` | ▶️ **실행 재개** |

```sql
-- FOR UPDATE NOWAIT: 잠겨있으면 즉시 실패
BEGIN;
SELECT * FROM items WHERE id = 1 FOR UPDATE NOWAIT;
-- ERROR: could not obtain lock on row in relation "items"
```

### 🏆 SKIP LOCKED — 작업 큐 패턴 (경쟁 소비자)

> **Worker 여러 개가 중복 없이 작업을 나눠 가져갑니다.**

```sql
WITH picked AS (
  SELECT id FROM job_queue
  WHERE  status = 'READY'
  ORDER BY id
  FOR UPDATE SKIP LOCKED       -- 다른 Worker가 처리 중인 행은 건너뜀
  LIMIT 10
)
UPDATE job_queue SET status = 'RUNNING', started_at = now()
FROM   picked WHERE job_queue.id = picked.id
RETURNING job_queue.*;
```

> ✅ **SKIP LOCKED 활용** : 분산 작업 큐 · 이메일 발송 Queue · 배치 처리 — **필수 패턴**

---

## 21-3. 낙관적 Lock vs 비관적 Lock

| | **낙관적 Lock** (Optimistic) | **비관적 Lock** (Pessimistic) |
|---|---|---|
| **가정** | 충돌이 **드물다** | 충돌이 **빈번하다** |
| **동작** | **버전 컬럼으로 충돌 감지**<br>저장 시 충돌 → **재시도** | **즉시 행 잠금 획득**<br>다른 트랜잭션은 대기 |
| **구현** | `version INT` 또는 `updated_at`<br>`UPDATE ... WHERE version = :old`<br>→ **0행 = 충돌 → 재시도** | `SELECT ... FOR UPDATE`<br>잠금 보유 중 다른 TX 대기<br>COMMIT 시 해제 |
| **적합** | 읽기 많고 갱신 드문 시스템<br>블로그, 설정 변경<br>**긴 사용자 세션** | **은행 이체, 좌석 예매**<br>재고 차감<br>**짧은 트랜잭션 (ms)** |

> 💡 **낙관적 Lock의 핵심 트릭** : `UPDATE ... WHERE version = :내가_읽은_버전`
> **영향받은 행이 0개면** 그 사이에 누가 바꾼 것 → 충돌 감지 → 재시도

---

## 21-4. Deadlock — 서로 기다리다 멈춤

### 발생 구조 (교차 대기)

| 시각 | 🅰 Session 1 | 🅱 Session 2 |
|:--:|---|---|
| ① | `UPDATE items ... WHERE id=1;`<br>✅ **row 1 Lock 획득** | |
| ② | | `UPDATE items ... WHERE id=2;`<br>✅ **row 2 Lock 획득** |
| ③ | `UPDATE items ... WHERE id=2;`<br>⏳ **row 2 대기** (Session 2가 보유) | |
| ④ | | `UPDATE items ... WHERE id=1;`<br>⏳ **row 1 대기** (Session 1이 보유) |
| ⑤ | 💥 **순환 대기 → Deadlock!** | |

```
Session 1  ──보유──▶ row 1 ◀──대기── Session 2
    │                                    ▲
    └────대기──▶ row 2 ──보유────────────┘
```

### 자동 감지

```
ERROR:  deadlock detected
DETAIL: Process 123 waits for ShareLock on transaction 456;
        blocked by process 456.
        Process 456 waits for ShareLock on transaction 123;
        blocked by process 123.
HINT:   See server log for query details.

→ 한 쪽이 자동으로 ROLLBACK됨 → 다른 쪽이 계속 진행
   deadlock_timeout = 1s (기본 감지 대기 시간)
```

> 💡 **DB가 알아서 감지하고 한쪽을 죽입니다.** 문제는 **죽은 쪽을 앱이 재시도해야** 한다는 것입니다.

---

## 21-5. ⭐ Deadlock 해소 4가지 방법

### 해결 1 — 항상 동일 순서로 Lock 획득 (가장 중요)

```sql
BEGIN;
WITH targets AS (
  SELECT id FROM items
  WHERE  id = ANY (ARRAY[1, 2])
  ORDER BY id            -- ← 핵심! 항상 id 오름차순으로 잠금
  FOR UPDATE
)
UPDATE items SET stock = stock - 1
FROM   targets WHERE items.id = targets.id;
COMMIT;
```

> 🔑 **모두가 같은 순서로 잠그면 순환이 생길 수 없습니다.**
> 위 예시에서 두 세션 모두 **1 → 2 순서**로 잠그면, 한쪽이 1을 먼저 잡고 다른 쪽은 1에서 대기하다가 순서대로 진행됩니다.

### 해결 2 — 트랜잭션 짧게 유지

- **비즈니스 로직, HTTP 호출, 파일 I/O는 트랜잭션 밖에서** 수행
- 꼭 필요한 테이블/행만 접근
- 격리 수준 **READ COMMITTED** 유지

### 해결 3 — Advisory Lock (업무 개념 단위 직렬화)

```sql
BEGIN;
SELECT pg_advisory_xact_lock(42);      -- user_id=42에 대한 논리 락
UPDATE users SET balance = balance - 1000 WHERE id = 42;
INSERT INTO payments (user_id, amount) VALUES (42, 1000);
COMMIT;   -- 트랜잭션 종료 시 Advisory Lock 자동 해제
```

> 💡 **"행"이 아니라 "업무 단위"로 잠급니다.** 여러 테이블을 건드리는 작업을 사용자 단위로 직렬화할 때 유용합니다.

### 해결 4 — 재시도 전략 (애플리케이션 레벨)

```python
# Deadlock 에러 코드: 40P01 (PostgreSQL)
try:
    execute_tx()
except psycopg2.errors.DeadlockDetected:      # 40P01
    time.sleep(random.uniform(0.1, 0.5))      # ← Jitter로 재충돌 방지
    retry()
```

> ⚠️ **Jitter(랜덤 대기)가 중요합니다.** 둘 다 정확히 같은 시간 후 재시도하면 **또 충돌**합니다.

---

## 21-6. Deadlock 모니터링

```sql
-- 현재 Lock 대기 중인 세션 전체 보기
SELECT
  bl.pid                      AS waiting_pid,
  wl.pid                      AS blocking_pid,
  bl.query                    AS waiting_query,
  wl.query                    AS blocking_query,
  now() - bl.query_start      AS waiting_for
FROM   pg_catalog.pg_locks l1
  JOIN pg_catalog.pg_stat_activity bl ON bl.pid = l1.pid
  JOIN pg_catalog.pg_locks l2
    ON  l1.locktype = l2.locktype
    AND l1.database IS NOT DISTINCT FROM l2.database
    AND l1.relation IS NOT DISTINCT FROM l2.relation
    AND l1.pid <> l2.pid
  JOIN pg_catalog.pg_stat_activity wl ON wl.pid = l2.pid
WHERE  NOT l1.granted AND l2.granted
ORDER BY waiting_for DESC;

-- 30초 이상 대기 중인 세션
SELECT pid, state, wait_event, now()-query_start AS duration, query
FROM   pg_stat_activity
WHERE  state != 'idle' AND now()-query_start > INTERVAL '30 seconds';

-- 세션 강제 종료
SELECT pg_cancel_backend(pid);      -- 현재 쿼리만 취소 (graceful)
SELECT pg_terminate_backend(pid);   -- 연결 자체 종료 (강제)
```

**postgresql.conf 권장 설정**
```
deadlock_timeout          = 500ms   -- 감지 전 대기 (기본 1s)
log_lock_waits            = on      -- 락 대기 로그 기록
log_min_error_statement   = error   -- 에러 SQL 기록
```

### DBMS별 Deadlock 제어

| DBMS | 자동 감지 | 예방 방법 | 해소 명령 | 모니터링 |
|------|:---:|---|---|---|
| **PostgreSQL** | ○ (`deadlock_timeout`) | 순서 통일, 짧은 TX, **Advisory Lock** | `pg_terminate_backend(pid)` | `pg_locks`, `pg_stat_activity` |
| **MySQL/InnoDB** | ○ | 순서 통일, Row-Level Lock | `KILL <process_id>` | `SHOW ENGINE INNODB STATUS` |
| **Oracle** | ○ | 순서 통일, 짧은 TX | `ALTER SYSTEM KILL SESSION` | `V$LOCK`, `V$SESSION` |
| **SQL Server** | ○ (Deadlock Monitor) | **`DEADLOCK_PRIORITY`** 설정 | `KILL <spid>` | `sys.dm_tran_locks`, XML Deadlock |
| **Cloud/분산** | ○ | 분산 그래프 탐지, 중앙 Lock 서버 | Cloud UI/API | 분산 Lock Graph |

---

# 22. 고급 DB 설계

> 📌 **다루는 것** : BCNF·4NF·5NF · 반정규화 · SCD · 샤딩 · MSA 패턴

## 22-1. BCNF (Boyce-Codd Normal Form)

### 조건

> **모든 결정자(Determinant)가 후보키(Candidate Key)여야 한다**
> 어떤 함수 종속 `X → Y`가 있을 때, **X가 후보키가 아니면 BCNF 위반**

### 위반 예시

```
학습지원(교수, 과목, 강의실)
  - 교수 → 강의실     (교수는 항상 같은 강의실 사용)
  - 그런데 "교수"는 후보키가 아님!
       ↓
  BCNF 위반
```

**해결 — 두 테이블로 분리**
```
교수강의실(교수, 강의실)  +  강의배정(교수, 과목)
```

> 🔧 **판별 순서** : **함수 종속성 분석 → 후보키 파악 → 결정자 검사**

### 3NF vs BCNF

| | **3NF** | **BCNF** |
|---|---|---|
| **우선순위** | **함수 종속 보존** 우선 | **정합성** 우선 |
| **허용** | 비후보 결정자 허용 가능 | **모든 결정자 = 후보키** 엄격 적용 |

> 💡 **실무 : 3NF까지 적용** — JOIN 비용·관리 복잡도를 고려합니다.

---

## 22-2. 정규화 심화 — 4NF / 5NF

| 정규형 | 해결 문제 | 핵심 개념 | 예시 | 실무 적용 |
|--------|-----------|-----------|------|-----------|
| **BCNF** | 비후보키 결정자 | 모든 결정자 = 후보키 | 교수 → 강의실<br>(교수가 후보키가 아님) | **3NF 이후 추가 검토** |
| **4NF** | **다치 종속** | 독립적인 다중값 분리 | 직원 → 자격증,<br>직원 → 외국어 (**서로 독립**) | `직원_자격증` + `직원_외국어`로 분리 |
| **5NF** | **조인 종속** | 분해 후 조인 시 원본을 **정확히 복원** | 프로젝트-직원-역할 **3개 테이블 조합** | 이론적으로 중요하나 **실무에서는 드묾** |

> 💡 **4NF 직관** : 직원이 자격증 2개, 외국어 2개를 가지면 한 테이블에서는 **2×2 = 4행**이 생깁니다. 자격증과 외국어는 **아무 관계가 없는데** 억지로 조합된 겁니다. → 분리.

---

## 22-3. ⭐ 정규화 vs 반정규화 선택

| | **정규화 유지 (OLTP)** | **반정규화 허용 (OLAP)** |
|---|---|---|
| **중심 작업** | **쓰기**(INSERT/UPDATE) 중심 | **읽기**(집계 SELECT) 중심 |
| **최우선** | **데이터 무결성** | **JOIN 비용 감소** |
| **중복** | 제거 | **허용** (⚠️ 동기화 필요) |
| **적합 시나리오** | 은행 계좌 관리<br>주문 처리 시스템<br>사용자 등록·변경 | 대시보드, 보고서<br>분석 쿼리 최적화<br>**AI/ML 피처 테이블** |
| **적용 수준** | **3NF ~ BCNF** | 중복 컬럼·집계 컬럼 추가 |
| **성능 해결** | **인덱스로 해결** | — |
| **안전한 대안** | — | 🏆 **Materialized View** |

> 🔑 **반정규화 전에 먼저 시도할 것**
> ① 인덱스 → ② Materialized View → ③ 그래도 안 되면 반정규화
> **반정규화는 되돌리기 어렵습니다.**

---

## 22-4. SCD (Slowly Changing Dimension) — 이력 관리

> **"고객이 서울에서 부산으로 이사했다. 예전 주소는?"** 이 문제를 푸는 방법입니다.

### Type 1 — 덮어쓰기 (이력 없음)

```sql
UPDATE customers SET city = '부산' WHERE id = 42;
-- ⚠️ 이전 도시 정보 사라짐 → 이력 추적 불가
```

### Type 2 — 이력 보존 (새 행 추가, 기간 관리) ⭐

```sql
CREATE TABLE customer_history (
  id          BIGSERIAL PRIMARY KEY,
  customer_id INT  NOT NULL,
  name        TEXT NOT NULL,
  city        TEXT NOT NULL,
  valid_from  DATE NOT NULL,
  valid_to    DATE,                    -- NULL = 현재 유효
  is_current  BOOLEAN DEFAULT TRUE
);

-- 변경 발생 시: 기존 행 종료 + 새 행 삽입
UPDATE customer_history
SET    valid_to = CURRENT_DATE - 1, is_current = FALSE
WHERE  customer_id = 42 AND is_current = TRUE;

INSERT INTO customer_history (customer_id, name, city, valid_from)
VALUES (42, '홍길동', '부산', CURRENT_DATE);

-- 현재 데이터 조회
SELECT * FROM customer_history WHERE is_current = TRUE AND customer_id = 42;

-- 특정 시점 데이터 조회 (2023-06-01 기준)
SELECT * FROM customer_history
WHERE  customer_id = 42
  AND  valid_from <= '2023-06-01'
  AND (valid_to IS NULL OR valid_to >= '2023-06-01');
```

**결과 이미지**

| customer_id | city | valid_from | valid_to | is_current |
|:--:|---|---|---|:--:|
| 42 | 서울 | 2020-01-01 | 2026-08-11 | FALSE |
| 42 | **부산** | 2026-08-12 | **NULL** | **TRUE** |

> ✅ **다른 타입**
> - **Type 3** : 현재 + 이전 값을 **별도 컬럼**으로 보존 (한 단계 이력만)
> - **Type 6** : Type 1 + 2 + 3 **혼합**

---

## 22-5. 샤딩 (Sharding) — 수평 분할

> **데이터를 여러 DB 인스턴스에 수평으로 분산 저장** (파티셔닝의 확장)

### 샤딩 vs 파티셔닝 (다시)

| | **파티셔닝** | **샤딩** |
|---|---|---|
| 범위 | **단일 DB 인스턴스 내** 논리/물리 분할 | **여러 DB 인스턴스**에 걸쳐 분산 |
| 목적 | 스캔 범위 축소 | **수평 확장 (Scale-out)** |

### 주요 샤딩 전략

| 전략 | 방식 | 특징 |
|------|------|------|
| **Range 샤딩** | 사용자 ID 범위<br>1~1000만 → Shard1 / 1000만+ → Shard2 | ⚠️ **hot spot 가능성** |
| **Hash 샤딩** | `user_id % N` 으로 균등 분산 | 균형적 but **이관(re-sharding) 어려움** |
| **Directory 샤딩** | 샤드 맵 테이블로 관리 | 유연 but **단일 장애점** |
| **Geo 샤딩** | 지역별 분산 (KR → KR 샤드) | 지연시간 감소 |

### 구현 도구

| 도구 | 설명 |
|------|------|
| **Citus** (PostgreSQL) | 분산 쿼리, 자동 샤딩, **SQL 그대로 사용** |
| **Vitess** (MySQL) | YouTube 출신, 오픈소스 MySQL 샤딩 |
| **TiDB** | MySQL 호환 분산 NewSQL (Google Spanner 영감) |

### ⚠️ 샤딩 주의사항

- **Cross-shard JOIN 불가** (앱 레벨에서 처리 필요)
- **분산 트랜잭션 복잡** (2PC 필요)
- **Re-sharding 어려움**

> 🔑 **샤딩 전에 먼저 검토할 것**
> ① **파티셔닝**(단일 DB 내 분할) → ② **Read Replica** → ③ **Cloud DB 자동 확장**
> 이걸로 충분한지 **먼저** 확인하세요. 샤딩은 마지막 수단입니다.

---

## 22-6. CDC (Change Data Capture)

> **DB 변경을 실시간 이벤트로 스트리밍**

| DB | 파이프라인 |
|----|-----------|
| **PostgreSQL** | Logical Decoding + **wal2json** → Kafka |
| **MySQL** | Binlog → **Debezium** → Kafka |

**활용** : 실시간 동기화 · DW 적재 · 마이크로서비스 이벤트 전파

> 💡 **Day 2의 WAL이 여기서 다시 등장합니다.** WAL 로그를 읽어서 이벤트로 흘려보내는 것이 CDC입니다.

---

## 22-7. MSA DB 패턴 — Saga / CQRS / Outbox

### Database per Service 원칙

> **각 마이크로서비스가 독립적인 DB를 소유**

| 장점 | 단점 |
|------|------|
| 서비스별 **독립 배포** | **분산 트랜잭션 복잡** |
| **기술 선택 자유** | **데이터 일관성 유지 어려움** |
| **장애 격리** | |

### ① Saga 패턴 — 분산 트랜잭션

```
주문 → 결제 → 재고 → 배송
 각 서비스: 로컬 트랜잭션 + 이벤트 발행
       ↓ 실패하면
 보상 트랜잭션(Compensating TX) 실행 — "이미 한 것을 되돌린다"
```

| 방식 | 설명 |
|------|------|
| **Choreography** | 이벤트 기반 **자율 조정** (중앙 조정자 없음) |
| **Orchestration** | **중앙 조정자**가 순서 지휘 |

> 💡 **ROLLBACK이 없습니다.** 각 서비스의 DB가 다르니 전체 롤백이 불가능해서, **"취소 작업을 따로 실행"** 하는 방식입니다.

### ② CQRS (Command Query Responsibility Segregation)

```
쓰기(Command)  →  RDBMS (정규화, ACID)
읽기(Query)    →  비정규화 캐시 / Read Replica
```

> 💡 **읽기와 쓰기의 요구사항이 정반대**라서 아예 분리하는 발상입니다. (22-3의 정규화 vs 반정규화와 같은 맥락)

### ③ Outbox 패턴 — 트랜잭션 내 이벤트 발행 보장

```
같은 트랜잭션 안에서:
   메인 로직 실행  +  아웃박스 테이블 INSERT
              ↓ (커밋됨)
   CDC(Debezium) → Kafka → 소비자 서비스
              ↓
   최소 1회 전달 보장 (at-least-once)
```

> 🔑 **왜 필요한가** : "DB에 저장했는데 Kafka 발행이 실패" 하는 상황을 막습니다.
> **DB 저장과 이벤트 기록을 같은 트랜잭션에 묶어놓고**, 발행은 CDC가 나중에 책임집니다.
> (Day 2의 *"Kafka 메시지 전송 전 DB COMMIT 완료"* 주의사항의 정석 해법입니다)

---

# ★ 운영 실무 [참고]

> 📌 원본 `[참고] 심화 & 운영 실무` (324~340p)

## ⓐ PostgreSQL 백업 및 복구

### 논리 백업 (SQL 형태)

```bash
pg_dump -U postgres -d mydb -f backup.sql          # 단순 SQL
pg_dump -U postgres -d mydb -Fc -f backup.dump     # 압축 바이너리 (권장)
pg_dump -U postgres -d mydb -Fd -j 4 -f backup_dir/ # 병렬 (4 코어)

# 전체 클러스터 백업 (전역 객체 포함)
pg_dumpall -U postgres > full_cluster_backup.sql

# 복구
psql -U postgres -d mydb < backup.sql
pg_restore -U postgres -d mydb -j 4 backup.dump    # 병렬 복구
```

### 물리 백업 (PITR용)

```bash
pg_basebackup -U replicator -D /backup/base -Ft -z -P --wal-method=stream
```

**PITR 설정 (postgresql.conf)**
```
wal_level       = replica
archive_mode    = on
archive_command = 'cp %p /backup/wal/%f'

# 복구 목표 시점 지정
restore_command      = 'cp /backup/wal/%f %p'
recovery_target_time = '2024-12-15 14:30:00'
```

**자동 백업 (crontab)**
```bash
0 3 * * * pg_dump -U postgres -Fc -d mydb > /backup/daily-$(date +%F).dump
```

> ✅ **백업 3-2-1 원칙**
> **3 copies / 2 media / 1 offsite** — 그리고 **정기 복원 테스트 필수!**
> ⚠️ **복원해본 적 없는 백업은 백업이 아닙니다.**

---

## ⓑ VACUUM & Table Bloat

### Table Bloat이란

```
Dead tuple이 쌓여 테이블이 실제보다 커지는 현상

UPDATE = 새 버전 삽입 + 구 버전을 Dead tuple로 표시   ← MVCC 때문!
              ↓
Dead tuple이 공간을 차지하고 순차 스캔 속도 저하
```

> 🔑 **20장 MVCC와 직결됩니다.** MVCC가 성능을 주는 대신, **쓰레기를 치우는 일(VACUUM)** 이 필요해집니다.

### VACUUM 종류

| 명령 | 하는 일 | 잠금 |
|------|---------|------|
| **`VACUUM`** | Dead tuple 정리, 공간 **재사용 표시** (⚠️ 테이블 크기는 안 줄어듦) | 없음 |
| **`VACUUM FULL`** | 테이블 **완전 재작성** → **실제 크기 감소** | ⚠️ **배타적 잠금** |
| **`VACUUM FREEZE`** | Transaction ID **Wraparound 방지** | 없음 |
| **`VACUUM ANALYZE`** | Dead tuple 정리 **+ 통계 갱신** 동시에 | 없음 |

```sql
VACUUM orders;              -- 잠금 없음, 공간 미반환
VACUUM ANALYZE orders;      -- Dead tuple + 통계 갱신
VACUUM FULL orders;         -- ⚠️ 배타적 잠금, 공간 반환
VACUUM FREEZE orders;       -- TX ID Wraparound 방지
```

### Bloat 확인

```sql
SELECT
  relname AS table_name,
  pg_size_pretty(pg_total_relation_size(relname::regclass)) AS total_size,
  n_dead_tup  AS dead_tuples,
  n_live_tup  AS live_tuples,
  ROUND(n_dead_tup::NUMERIC / NULLIF(n_live_tup + n_dead_tup, 0) * 100, 1) AS dead_pct,
  last_autovacuum,
  last_autoanalyze
FROM   pg_stat_user_tables
ORDER BY n_dead_tup DESC LIMIT 10;
```

### autovacuum 튜닝

```sql
-- 전역 기본값
-- autovacuum_vacuum_scale_factor  = 0.05   (5% dead → VACUUM)
-- autovacuum_analyze_scale_factor = 0.02   (2% 변경 → ANALYZE)

-- 테이블별 오버라이드 (변경 잦은 테이블은 더 자주)
ALTER TABLE orders SET (
  autovacuum_vacuum_scale_factor  = 0.01,   -- 1% dead tuple 시 실행
  autovacuum_analyze_scale_factor = 0.005   -- 0.5% 변경 시 통계 갱신
);

-- Transaction ID Wraparound 모니터링 (2^31 = 약 21억 트랜잭션)
SELECT relname, age(relfrozenxid) AS xid_age,
       pg_size_pretty(pg_total_relation_size(oid)) AS size
FROM   pg_class WHERE relkind = 'r' AND age(relfrozenxid) > 100000000
ORDER  BY age(relfrozenxid) DESC;
```

> ⚠️ **Table Bloat 주범 : 장수 트랜잭션(Long-running TX)**
> 열려 있는 오래된 트랜잭션은 **VACUUM을 차단**합니다 → `pg_stat_activity` 모니터링 필수

---

## ⓒ Connection Pool — pgBouncer

### 왜 필요한가

```
PostgreSQL 연결당 약 5~10MB 메모리 + 연결 핸드셰이크 비용

1000개 연결 × 5MB = 5GB 메모리
        ↓
max_connections 한계 초과 → 연결 거부
```

### pgBouncer 모드 3가지

| 모드 | 동작 | 평가 |
|------|------|------|
| **Session Mode** | 클라이언트 연결 동안 DB 연결 유지 | 안전하지만 **효율 낮음** |
| **Transaction Mode** | **트랜잭션 단위로 DB 연결 할당/반환** | 🏆 **권장, 가장 효율적** |
| **Statement Mode** | 문장 단위 | ⚠️ PREPARE 불가, 거의 미사용 |

### 설정 (pgbouncer.ini)

```ini
[databases]
skala_db = host=127.0.0.1 port=5432 dbname=skala_db

[pgbouncer]
pool_mode           = transaction   ; 권장
max_client_conn     = 2000          ; 앱 → pgBouncer 최대 연결
default_pool_size   = 20            ; pgBouncer → PostgreSQL 실제 연결
min_pool_size       = 5
reserve_pool_size   = 5
server_idle_timeout = 600           ; 유휴 DB 연결 유지 시간(초)
```

> ✅ **Transaction Mode의 위력**
> **DB 연결 20개로 앱 연결 2000개를 처리** → 연결 오버헤드 대폭 감소

**모니터링**
```bash
psql -p 6432 pgbouncer -c "SHOW POOLS;"
psql -p 6432 pgbouncer -c "SHOW CLIENTS;"
psql -p 6432 pgbouncer -c "SHOW STATS;"
```

**다른 DBMS/클라우드** : ProxySQL (MySQL) · RDS Proxy (AWS) · Cloud SQL Proxy (GCP)

---

## ⓓ DB 모니터링 핵심 쿼리

```sql
-- ① 현재 실행 중인 쿼리 (30초 이상)
SELECT pid, now() - query_start AS duration,
       state, wait_event, LEFT(query, 100) AS query_snippet
FROM   pg_stat_activity
WHERE  state != 'idle' AND now() - query_start > INTERVAL '30 seconds'
ORDER BY duration DESC;

-- ② 연결 수 현황
SELECT state, COUNT(*) AS cnt FROM pg_stat_activity GROUP BY state;

-- ③ 캐시 히트율 (권장: 99% 이상) ⭐
SELECT SUM(blks_hit)::FLOAT
       / NULLIF(SUM(blks_hit) + SUM(blks_read), 0) * 100 AS cache_hit_pct
FROM   pg_stat_database WHERE datname = current_database();

-- ④ 테이블 크기 순위
SELECT relname, pg_size_pretty(pg_total_relation_size(relname::regclass)) AS size
FROM   pg_stat_user_tables
ORDER BY pg_total_relation_size(relname::regclass) DESC LIMIT 10;

-- ⑤ 미사용 인덱스 (idx_scan = 0)
SELECT indexrelname, relname, pg_size_pretty(pg_relation_size(indexrelid))
FROM   pg_stat_user_indexes
WHERE  idx_scan = 0 AND relname NOT LIKE 'pg_%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

> 🔑 **캐시 히트율 99% 미만이면** `shared_buffers`를 늘리거나 쿼리가 불필요하게 많이 읽고 있다는 신호입니다.

---

## ⓔ ⭐ DB 성능 최적화 4단계 접근법

| 단계 | 내용 |
|------|------|
| **1단계 — 설계 최적화**<br>**(영향력 가장 큼)** | • 적절한 **정규화 수준** 결정 (OLTP: 3NF / OLAP: 반정규화)<br>• **PK 선택** — 자연키 vs 대체키(BIGINT/UUID), ⚠️ **UUID는 인덱스 효율↓**<br>• **FK 컬럼에 반드시 인덱스**<br>• **데이터 타입 최적화** — `NUMERIC`(금액), `TIMESTAMPTZ`(시각) |
| **2단계 — 쿼리 최적화** | • `SELECT *` 제거<br>• 서브쿼리 → **CTE/JOIN** 변환<br>• **N+1 문제** 해결<br>• **`EXPLAIN ANALYZE`로 병목 파악** |
| **3단계 — 인덱스 최적화** | • **선택도 높은 컬럼 우선**, 복합 인덱스 컬럼 순서<br>• **커버링/부분/함수 기반** 인덱스<br>• **미사용 인덱스 제거** (`idx_scan = 0`) |
| **4단계 — DB 설정 최적화** | • 메모리 — `shared_buffers`(DB 캐시), `work_mem`(정렬/해시 per-query)<br>• **Connection Pool** (pgBouncer)<br>• **VACUUM/ANALYZE 스케줄** |

> 🔑 **1단계의 영향력이 가장 큽니다.**
> 설계가 잘못되면 인덱스와 설정으로 아무리 발버둥 쳐도 한계가 있습니다.
> **거꾸로 말하면, 이미 운영 중인 시스템은 2~4단계밖에 못 건드립니다.** 그래서 설계가 중요합니다.

---

# 23. 종합실습 – 3

> 📌 **주제** : HR DB 느린 쿼리 최적화 — EXPLAIN Before/After 비교

## 23-1. 배경 및 목표

> **HR 데이터베이스를 사용하는 인사 관리 시스템**
> 최근 **직원 수가 5만 명 이상**으로 늘면서 **검색 속도가 느려지고 보고서 생성 시간이 지연**됨

| 항목 | 내용 |
|------|------|
| **환경** | **종합실습 1 환경 활용** + **HR 스키마 개설** |
| **사전 준비** | `종합실습3_HR DB_PostgreSQL 실습스크립트_환경설정.sql` 실행 |
| **학습 목표** | • 인덱스 없는 **Seq Scan → Index Scan 전환** 체험<br>• **`pg_stat_statements`** 로 실제 느린 쿼리 식별<br>• **EXPLAIN ANALYZE Before/After** 결과 비교 리포트<br>• **Deadlock 시나리오** 실습 및 해소 |

**데이터 확인**
```sql
SELECT COUNT(*) FROM employees;
```

---

## 23-2. 실습 과제 5문항

| # | 과제 | 힌트 (Day 3 어디를 보나) |
|---|------|------------------------|
| **1** | **실행 계획 맛보기**<br>사번이 100인 사람 검색 | 18장 — `EXPLAIN ANALYZE` 기본 읽기 |
| **2** | **인덱스 없는 느린 쿼리 → 튜닝**<br>이메일이 `user1234@corp.com`인 사람 (**`lower(email)` 사용**) | 19장 안티패턴 3 — **함수 기반 인덱스**<br>`CREATE INDEX ON employees(LOWER(email))` |
| **3** | **LIKE 검색 → 튜닝**<br>대상 : `'%gmail.com'` **접미사 검색** | 19장 안티패턴 4 — **앞 와일드카드는 B-Tree 불가**<br>→ `pg_trgm` GIN 인덱스 또는 **역순 문자열 인덱스** 고려 |
| **4** | **정렬 + 필터 결합 → 튜닝**<br>`hire_date >= CURRENT_DATE - INTERVAL '365 days'` 이면서 **재직 중**인 사람을 **연봉순 상위 100명** | 17장 — **복합 인덱스 순서**(등호 먼저 → 범위 나중)<br>18장 — **Sort 노드 제거** |
| **5** | **OR 조건 → 튜닝**<br>부서코드 = 10 **또는** 직무가 3, 4, 5 안에 있는 사람 | 18장 — **Bitmap Heap Scan**<br>💡 `OR`는 `UNION`으로 분리하면 각각 인덱스를 탈 수 있음 |

---

## 23-3. 제출물

| 항목 | 내용 |
|------|------|
| **SQL Query 및 결과** | 각 문항별 **쿼리와 실행결과 화면** (Screen Capture) |
| **리포트** | ✓ **느린 이유** → **개선 방법 도출** → **개선 후 주요 효과**<br>✓ **실행계획 이전/후 결과 정리를 자세히** 할 것<br>✓ **최소 2개 이상 쿼리**를 만들고 **쿼리에 대한 차이점 분석 결과** 작성 |
| **제출 방법** | **Slack 내 댓글 제출** |
| **제출 기한** | **4일차 과정 시작 전** |
| **배점** | **문항당 20점** (5문항 × 20점 = 100점) |
| **채점 기준** | ① **요구사항 반영 여부**<br>② **Query 내 컬럼 선택** (⚠️ **불필요한 컬럼 선택 확인**) |

> 💡 **리포트 작성 팁 — 이 3단 구조로 쓰면 됩니다**
> ```
> ① Before : EXPLAIN ANALYZE 결과 캡처
>            → "Seq Scan on employees, actual time=1850ms"
>            → 왜 느린가? (인덱스 없음 / 함수 적용 / 정렬 발생)
>
> ② 조치   : CREATE INDEX ... (왜 이 인덱스인지 근거)
>
> ③ After  : EXPLAIN ANALYZE 결과 캡처
>            → "Index Scan using idx_..., actual time=0.8ms"
>            → 몇 배 향상, 어떤 노드가 사라졌는지
> ```

---

# 🧭 Day 3 전체 흐름 한 장 요약

```
[Day 3의 두 축]

━━━━━━━━━ 축 1. 속도 ━━━━━━━━━

  왜 느린가?  →  EXPLAIN ANALYZE 로 확인
                 Seq Scan / actual rows≠rows / Hash Batches>1

  무엇으로 고치나?
    ① 인덱스     B-Tree(기본) · GIN(JSON/FTS) · GiST(GIS) · BRIN(시계열)
                 복합 인덱스 = 선두 컬럼 원칙 (앞부터 순서대로!)
                 커버링 인덱스 → Index Only Scan (Heap Fetches: 0)
                 선택도 높은 컬럼일수록 효과 큼
                 ⚠️ 미사용 인덱스(idx_scan=0)는 쓰기 비용만 축냄

    ② 쿼리       안티패턴 8개
                 함수적용 · SELECT* · 타입불일치 · LIKE%앞
                 N+1 · NOT IN · DISTINCT남용 · OFFSET

    ③ 아키텍처   Materialized View · 파티셔닝(Pruning) · Read Replica

  목표: Seq Scan → Index Scan → Index Only Scan


━━━━━━━━━ 축 2. 동시성 ━━━━━━━━━

  MVCC        수정 시 새 버전 생성 + 스냅샷
              → 읽기가 쓰기를 막지 않음
              ⚠️ 대가: Dead tuple → VACUUM 필요 → Table Bloat

  격리 수준    RC(기본) → RR → Serializable
              위로 갈수록 빠르고 위험 / 아래로 갈수록 안전하고 느림

  Lock        FOR UPDATE / NOWAIT / SKIP LOCKED(작업 큐!)
              낙관적(버전 비교) vs 비관적(즉시 잠금)

  Deadlock    순환 대기 → DB가 자동 감지 → 한쪽 ROLLBACK
              해소: ①순서 통일 ②짧은 TX ③Advisory Lock ④재시도+Jitter


━━━━━━━━━ 커지면 나눈다 ━━━━━━━━━

  파티셔닝(단일 DB 내)  →  Read Replica  →  샤딩(여러 DB)
       ↑ 여기서 최대한 버티기            ↑ 마지막 수단

  MSA:  Database per Service
        Saga(보상 트랜잭션) · CQRS(읽기/쓰기 분리) · Outbox(이벤트 보장)


[최적화 우선순위 — 영향력 순]
  1. 설계  (가장 큼, 하지만 운영 중엔 못 바꿈)
  2. 쿼리
  3. 인덱스
  4. DB 설정
```

---

## 🎓 시험/면접 대비 핵심 문답

| 질문 | 답 |
|------|-----|
| **인덱스의 트레이드오프는?** | 읽기 성능↑ / **쓰기 비용↑**(재정렬) / **저장 공간↑** |
| **인덱스 없을 때 vs 있을 때 복잡도는?** | **O(N)** Full Scan vs **O(log N)** B-Tree |
| **선택도(Selectivity)란?** | **고유값 수 / 전체 행 수**. 1에 가까울수록 좋음. gender=0.5(나쁨), email≈1(좋음) |
| **⭐선두 컬럼 원칙이란?** | `INDEX(A,B)`는 **A부터 순서대로** 조건이 있어야 사용 가능. **`WHERE B=...`만 있으면 못 씀** |
| **복합 인덱스 컬럼 순서 원칙은?** | **등호(=) 먼저 → 범위(<,>) 나중 → 선택도 높은 컬럼 우선** |
| **커버링 인덱스란?** | SELECT에 필요한 **모든 컬럼이 인덱스에 포함** → **Index Only Scan** (Heap Fetches: 0) |
| **JSON/배열 검색에 쓰는 인덱스는?** | **GIN** (지리정보는 GiST, 시계열 대용량은 BRIN) |
| **`idx_scan = 0`이 의미하는 것은?** | 한 번도 안 쓰인 인덱스 → **쓰기 비용만 축냄 → 삭제 검토** |
| **EXPLAIN과 EXPLAIN ANALYZE의 차이는?** | EXPLAIN = **추정만** (실행 안 함) / ANALYZE = **실제 실행 + 측정** (DML은 ROLLBACK 권장) |
| **실행계획 노드 중 가장 좋은 것은?** | **Index Only Scan** > Index Scan > Seq Scan |
| **`actual rows`와 `rows`가 크게 다르면?** | **통계가 오래됨 → `ANALYZE` 실행** |
| **Hash Batches > 1이 의미하는 것은?** | **메모리 Spill 발생 → `work_mem` 부족** |
| **⭐안티패턴 8가지는?** | **함수적용 · SELECT\* · 타입불일치 · LIKE%앞 · N+1 · NOT IN · DISTINCT남용 · OFFSET** |
| **`WHERE YEAR(date)=2024`가 왜 문제?** | **인덱스 컬럼에 함수 → 인덱스 무력화**. 범위 조건으로 바꾸거나 함수 기반 인덱스 |
| **`LIKE '%길동%'`을 인덱스로 처리하려면?** | **`pg_trgm` + GIN 인덱스** (앞 와일드카드는 B-Tree 불가) |
| **느린 쿼리를 찾는 도구는?** | PostgreSQL **`pg_stat_statements`** / MySQL **Slow Query Log** |
| **Partition Pruning이란?** | **WHERE에 파티션 키가 있으면 해당 파티션만 스캔**. ⚠️ 파티션 키가 없으면 전체 스캔 |
| **파티셔닝 vs 샤딩?** | 파티셔닝 = **단일 DB 내** 분할(JOIN 가능) / 샤딩 = **여러 DB 인스턴스**(수평 확장, JOIN 어려움) |
| **⭐MVCC란?** | 수정 시 **덮어쓰지 않고 새 버전 생성** + 트랜잭션마다 **스냅샷** → **읽기가 쓰기를 안 막음** |
| **PostgreSQL MVCC의 시스템 컬럼은?** | **`xmin`**(생성 TX ID), **`xmax`**(삭제/수정 TX ID) |
| **MVCC의 대가는?** | **Dead tuple** 발생 → VACUUM 필요 → **Table Bloat** 위험 |
| **Serializable 충돌 시 에러 코드는?** | **40001** (Serialization Failure) → **앱에서 재시도 필요** |
| **`SELECT FOR UPDATE`의 세 옵션은?** | **기본**(대기) / **NOWAIT**(즉시 에러) / **SKIP LOCKED**(건너뜀 — 작업 큐) |
| **낙관적 Lock의 구현 방법은?** | `version` 컬럼 + `UPDATE ... WHERE version=:old` → **0행이면 충돌 → 재시도** |
| **Deadlock은 왜 생기나?** | **서로 다른 순서로 Lock을 잡아서 순환 대기** 발생 |
| **⭐Deadlock 해소 4가지는?** | ① **순서 통일**(가장 중요) ② 짧은 트랜잭션 ③ **Advisory Lock** ④ **재시도 + Jitter** |
| **Deadlock 에러 코드는? (PG)** | **40P01** |
| **BCNF 조건은?** | **모든 결정자가 후보키**여야 함. 실무는 보통 **3NF까지** |
| **4NF가 해결하는 문제는?** | **다치 종속** — 서로 독립적인 다중값(자격증, 외국어)을 분리 |
| **반정규화 전에 먼저 시도할 것은?** | ① 인덱스 → ② **Materialized View** → ③ 그래도 안 되면 반정규화 |
| **SCD Type 2란?** | **이력 보존** — 새 행 추가 + `valid_from`/`valid_to`/`is_current`로 기간 관리 |
| **Outbox 패턴이 푸는 문제는?** | **"DB 저장은 됐는데 이벤트 발행 실패"** → 같은 트랜잭션에 아웃박스 INSERT, CDC가 발행 |
| **Saga 패턴이란?** | 분산 트랜잭션을 **로컬 TX 체인 + 보상 트랜잭션**으로 처리 (전체 ROLLBACK 불가하니까) |
| **VACUUM과 VACUUM FULL의 차이는?** | VACUUM = 잠금 없음, **공간 재사용 표시만** / VACUUM FULL = **배타적 잠금**, **실제 크기 감소** |
| **VACUUM을 막는 것은?** | **장수 트랜잭션(Long-running TX)** → `pg_stat_activity` 모니터링 |
| **pgBouncer 권장 모드는?** | **Transaction Mode** — DB 연결 20개로 앱 연결 2000개 처리 |
| **캐시 히트율 권장 수치는?** | **99% 이상** |
| **백업 3-2-1 원칙은?** | **3 copies / 2 media / 1 offsite** + **정기 복원 테스트 필수** |
| **성능 최적화 4단계 중 영향력이 가장 큰 것은?** | **1단계 설계** (정규화 수준, PK 선택, FK 인덱스, 데이터 타입) |

---

## 🔗 Day 4 예고

| # | 장 | Day 3의 어디서 이어지나 |
|---|---|---|
| 24 | **Stored Procedure & 함수** | "로직을 코드에 둘까 DB에 둘까" — 22장 설계 논의의 연장 |
| 25 | **Trigger & 이벤트 처리** | ⚠️ 남용하면 로직이 DB에 갇힘 |
| 26 | **Cloud DB 개요** | 20~21장 격리·Lock이 분산 환경에서 어떻게 되나 |
| 27 | **서버리스 & 분산 Cloud DB** | 22장 샤딩의 관리형 버전 |
| 28 | **데이터 웨어하우스 & 분석 DB** | 22장 반정규화(OLAP)의 실제 |
| 29 | **현재의 트렌드** | — |
| 30 | **보안 및 권한 관리** | — |
| 31 | **백업·복구 & 고가용성** | ★ 운영 실무 ⓐ의 심화 |
| 32 | **모니터링 및 운영** | ★ 운영 실무 ⓓ의 심화 |
| 33 | **종합실습 – 4** | ecommerce 매출 분석 및 정리 |

---

*본 문서는 SK AX의 컨텐츠 자산을 학습 목적으로 정리한 것으로, 무단 사용 및 불법 배포 시 법적 조치를 받을 수 있습니다.*
