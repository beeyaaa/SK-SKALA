# 🗄️ Day 1 — 스마트 데이터 이해 및 활용

> 💡 **Day 1 한 줄 요약**
> **현실 세계 → ERD → 테이블 → SQL** 로 내려오는 과정을 한 번에 훑는 날.
> 그리고 그 밑에 깔린 단 하나의 질문 — **"데이터를 어떻게 안 깨지게 지킬 것인가(무결성)"** vs **"어떻게 빠르고 크게 굴릴 것인가(확장성)"**.

**출처** : AI 서비스를 위한 SW 기초 Full-stack Engineering (AI캠퍼스, 4일) > 4. 스마트 데이터 이해 및 활용 (백정열 / SK AX, 2026.6)
**범위** : 전체 482p 중 **Day 1 = 7~116p** (1~8장)

---

## 📑 Day 1 목차

| # | 장 | 부제 | 핵심 질문 |
|---|---|------|-----------|
| 1 | [데이터베이스 개요](#1-데이터베이스-개요) | 필요성 · 발전 과정 · ACID · WAL · Isolation Level | DB는 왜 생겼고, 무엇을 보장하나? |
| 2 | [관계형 모델 핵심 개념](#2-관계형-모델-핵심-개념) | 테이블 · 키(PK/FK/UK) · 관계 · 정규화(1NF~3NF) | 현실을 어떻게 표로 옮기나? |
| 3 | [ERD](#3-3-erd-작성-7단계) | 엔티티 · 속성 · 관계 · IE 표기법 | 설계를 어떻게 그림으로 그리나? |
| 4 | [개념적→논리적→물리적 모델 설계](#4-개념적논리적물리적-모델-설계) | 3단계 설계 흐름 · 약한 엔티티 · N:M | 그림을 어떻게 실제 스키마로? |
| 5 | [스키마 전략 & RDBMS 비교](#5-스키마-전략--rdbms-비교) | 멀티 프로젝트 설계 · MySQL/PostgreSQL/Oracle/Cloud | 어떤 DB를 골라야 하나? |
| 6 | [SQL 기초 — DDL](#6-sql-기초--ddl) | CREATE · ALTER · 데이터 타입 · 제약조건 | 그릇을 어떻게 만드나? |
| 7 | [SQL 기초 — DML](#7-sql-기초--dml) | SELECT · INSERT · UPDATE · DELETE · 함수 | 데이터를 어떻게 넣고 꺼내나? |
| 8 | [종합실습 – 1](#8-종합실습--1) | 학사관리시스템 DB 설계 → 구축 → 조회 | 직접 만들어보기 |

---

# 1. 데이터베이스 개요

> 📌 **다루는 것** : 필요성 · 발전 과정 · ACID · WAL · Isolation Level

## 1-1. DB는 왜 생겼나 — 발전 과정

| 시대 | 대표 기술 | 핵심 특징 | 한계 |
|------|-----------|-----------|------|
| **파일시스템** (1960s) | 운영체제 파일 | 개별 앱마다 독자 파일 | **중복 · 불일치 · 동시접근 불가** |
| **계층형 DB** (1970s) | IBM IMS | 트리구조, 빠른 탐색, **1:N 최적** | **N:M 표현 어려움**, 유연성 부족 |
| **관계형 DBMS** (1970s~) | Oracle, MySQL, PostgreSQL | 관계형 모델, **SQL 표준화** | JOIN 비용, **수평 확장 어려움** |
| **NoSQL** (2000s~) | MongoDB, Redis, Cassandra | 유연한 스키마, **수평 확장** | **강한 일관성 보장 어려움** |
| **분산/Cloud DB** (2010s~) | Spanner, Aurora, CockroachDB | **ACID + 수평 확장** (NewSQL) | 높은 운영 복잡도 |

> 🎯 **강의의 핵심 문장**
> DB 발전은 단순한 저장 방식이 아니라 **데이터 무결성·일관성 vs 확장성 간의 균형 싸움**이다.
>
> 💡 이 문장이 Day 1 전체의 뼈대입니다. 뒤에 나오는 ACID, Isolation Level, 정규화, NoSQL 비교가 전부 **이 저울의 어느 쪽에 서느냐**의 이야기입니다.

---

## 1-2. ACID — 트랜잭션의 4대 원칙

| 속성 | 설명 |
|------|------|
| **A**tomicity (원자성) | 트랜잭션의 모든 작업이 **완전히 수행되거나 전혀 수행되지 않아야** 함<br>💬 송금 = 출금 + 입금 → **둘 다 성공 or 둘 다 취소** |
| **C**onsistency (일관성) | 트랜잭션 수행 **전후에 DB는 일관된 상태**를 유지 |
| **I**solation (격리성) | 트랜잭션이 동시에 실행될 때 **서로 간섭하지 않도록** 보장 |
| **D**urability (지속성) | 트랜잭션이 성공적으로 완료되면 그 결과는 **영구적으로 반영** |

### ⚠️ "ACID 지원"이라는 말의 함정

> ACID는 모든 DBMS에서 **"교과서적으로는 지원"** — **엔진/설정/클라우드 옵션에 따라 실제 보장 수준이 다름**

| DBMS | Isolation | Durability 구현 | 특징 |
|------|-----------|-----------------|------|
| **Oracle** | 다양한 Level, 기본 Read Consistent | Redo/Undo | 엔터프라이즈급 표준 |
| **PostgreSQL** | **Serializable 포함** 다양한 Level | **WAL** | MVCC 기반, 오픈소스 중 가장 "Oracle-like"<br>**SSI**(Serializable Snapshot Isolation) 지원 |
| **MySQL (InnoDB)** | Repeatable Read 기본, Phantom Read 발생 가능 | Double-write Buffer | 완전 지원. **엔진에 따라 차이** |
| **MySQL (MyISAM)** | Locking 기반 | 비지속성 | ⚠️ **Rollback 불가, FK 없음 → 사실상 ACID 미지원**<br>(현재는 InnoDB가 기본) |
| **SQL Server** | Read Uncommitted ~ Serializable | Transaction Log | Isolation Level 세부 튜닝 가능 |
| **Cloud DB**<br>(Aurora, Spanner) | 다지역 트랜잭션 지원 | 분산 **WAL/Consensus** | **Consistency 조정 가능** (Strong / Eventual)<br>→ **CAP Trade-off** 선택<br>Aurora: 스토리지 6방향 복제 |

> 🔑 **핵심 포인트** : DB 선택 시 **ACID 보장 수준과 성능 트레이드오프**를 반드시 확인할 것.

---

## 1-3. WAL (Write-Ahead Logging) — 지속성은 어떻게 구현되나

### 이름이 곧 원리

> **"로그가 먼저(Write-Ahead)"**
> 데이터 파일보다 **로그를 먼저 써야** 장애 시 복구할 수 있다.

**동작 과정**

```
① 클라이언트가 UPDATE 실행
② DB는 데이터 파일을 즉시 고치지 않고, 먼저 WAL 로그에 기록
③ 로그가 디스크에 안전하게 기록되면 → "COMMIT 성공" 응답
④ 실제 데이터 파일 반영은 나중에 배치/버퍼 관리자가 수행 (Checkpoint)
```

**PostgreSQL 예시**

```sql
BEGIN;
  UPDATE account SET balance = balance - 10000 WHERE id = 'A';
  -- 1단계: WAL 버퍼에 변경 내용 기록 (로그 우선 원칙)
  -- 2단계: Shared Buffer(메모리)에 페이지 변경 반영
  -- 3단계: 아직 디스크 데이터 파일에는 미기록 (dirty page)
  UPDATE account SET balance = balance + 10000 WHERE id = 'B';
COMMIT;
-- COMMIT 로그를 WAL에 기록 후 fsync(디스크 동기화)
-- 이후 Checkpoint 시점에 데이터 파일에 반영

-- 장애 복구 시:
--   pg_wal/ 디렉토리의 로그를 순서대로 재실행 (Redo)
--   COMMIT되지 않은 트랜잭션은 Undo 처리
```

**주요 설정 (postgresql.conf)**

| 설정 | 값 | 의미 |
|------|-----|------|
| `wal_level` | `replica` | 복제 레벨 |
| `synchronous_commit` | `on` / `off` | **on: 안전** / **off: 성능↑, 최대 200ms 손실 가능** |
| `checkpoint_timeout` | `5min` | 체크포인트 주기 |

**장점**
- 장애 발생 시 로그 기반으로 **Redo(다시 적용) / Undo(취소)** 가능
- **쓰기 성능 개선** — 순차 기록으로 **랜덤 I/O 최소화**
- PostgreSQL, SQL Server, Oracle, MySQL(InnoDB) 등 **대부분의 DBMS가 사용**

---

## 1-4. Consensus (합의 알고리즘) — 분산 환경의 WAL

> 분산 DB에서는 **여러 노드가 동일한 데이터를 가진 상태**여야 함.
> 네트워크 지연/장애가 발생해도 **모든 노드가 같은 결과(합의)** 를 가지도록 하는 알고리즘.

**대표 알고리즘**

| 알고리즘 | 특징 |
|----------|------|
| **Paxos** | 이론적으로 가장 유명한 분산 합의 알고리즘 |
| **Raft** | **구현이 단순**해 실제 제품에서 널리 활용 (AWS Aurora, etcd, CockroachDB) |
| **Google Spanner** | Paxos + **TrueTime API** (전역 시계 동기화) |

**동작 과정**
```
① 클라이언트가 트랜잭션 요청
② Leader 노드가 로그에 기록          ← 여기서도 WAL!
③ Follower 노드들과 "투표" → 과반수가 동의해야 Commit 확정
④ 모든 노드에 같은 순서의 로그가 쌓임 → Strong Consistency 보장
```

**장단점**

| 장점 | 단점 |
|------|------|
| 분산 환경에서도 **데이터 일관성 유지** | **네트워크 지연이 늘어나면 성능 저하**<br>(특히 글로벌 DB에서 latency 증가) |
| 장애 시 **Leader 재선출** 가능 → 고가용성 | |

### 🔑 WAL vs Consensus 한 줄 비교

| | **WAL** | **Consensus** |
|---|---------|---------------|
| **적용 범위** | **단일 DBMS, 단일 노드** | **분산 DB, 멀티 노드** |
| **목적** | 장애 복구, 트랜잭션 보장 | 분산 노드 간 동일한 상태 유지 |
| **동작 원리** | 로그 먼저 기록 → 데이터 반영 | 여러 노드가 **투표**를 통해 합의 |
| **대표 사례** | PostgreSQL, Oracle, SQL Server | Google Spanner, AWS Aurora, CockroachDB |

> 💡 **외우는 법**
> - **WAL** = "**한 DB 안에서** 장애 대비 안전장치"
> - **Consensus** = "**여러 DB가 흩어져 있어도** 모두 같은 결과를 보장하는 안전장치"

---

## 1-5. Isolation Level — 동시성의 3가지 이상 현상

### 먼저, 무엇이 문제인가

| 현상 | 무슨 일이 일어나나 |
|------|-------------------|
| **Dirty Read** | **커밋 전 값**을 읽음 |
| **Non-Repeatable Read** | 같은 행을 두 번 읽었더니 **값이 달라짐**<br>(다른 트랜잭션이 그 행을 **UPDATE/DELETE**) |
| **Phantom Read** | 같은 조건으로 두 번 조회했더니 **행의 개수가 달라짐**<br>(다른 트랜잭션이 **새 행 INSERT** 또는 범위 내 행 추가/삭제) |

> 🔑 **헷갈리는 포인트**
> - Non-Repeatable Read = **"값"이 변함**
> - Phantom Read = **"개수"가 변함** — 값이 변해서가 아니라 **조건에 맞는 새 행이 생겨서**

### ANSI 격리 수준 — 이상 현상 허용 여부

| 격리 수준 | Dirty Read | Non-Repeatable Read | Phantom Read | DBMS 기본값 |
|-----------|-----------|---------------------|--------------|-------------|
| **READ UNCOMMITTED** | 허용 | 허용 | 허용 | 거의 미사용 |
| **READ COMMITTED** | **차단** | 허용 | 허용 | **PostgreSQL, Oracle, SQL Server** |
| **REPEATABLE READ** | **차단** | **차단** | 원칙적 허용<br>→ InnoDB는 **Gap Lock**으로 방지 | **MySQL (InnoDB)** |
| **SERIALIZABLE** | **차단** | **차단** | **차단** | ⚠️ 성능 저하 주의 (순차 실행과 동등) |

> ⚠️ **표준 정의상 RR은 Phantom을 허용**하지만, **DBMS 구현에 따라 범위 잠금/스냅샷으로 실질적으로 막히는 경우**가 존재합니다. 그래서 "MySQL은 Phantom이 발생한다/안 한다" 양쪽 설명이 다 돌아다니는 겁니다.

### DBMS별 기본값과 구현 차이

| DBMS | 기본값 | 구현 특징 |
|------|--------|-----------|
| **Oracle** | READ COMMITTED | MVCC로 **문장 단위 read consistency** → 같은 SELECT 안에서는 일관된 스냅샷<br>SERIALIZABLE은 스냅샷 기반, 충돌 시 **ORA-08177** 발생 → 재시도 필요 |
| **PostgreSQL** | READ COMMITTED | MVCC. **REPEATABLE READ는 스냅샷 격리(SI) 성격** → 같은 트랜잭션 내 반복 SELECT는 새 행(팬텀)을 보지 않음<br>완전 직렬성은 **SERIALIZABLE(SSI)** → 필요 시 트랜잭션을 롤백해 직렬성 보장 |
| **MySQL (InnoDB)** | **REPEATABLE READ** | MVCC의 consistent read로 **일반 SELECT는 팬텀을 사실상 보지 않음**<br>단, **잠금 읽기**(`SELECT … FOR UPDATE / FOR SHARE`)나 UPDATE/DELETE 범위 조건에선 **next-key lock**(레코드+갭 잠금)으로 팬텀 차단 (경합/대기 증가 가능) |
| **SQL Server** | READ COMMITTED (**락 기반**) | 옵션 `READ_COMMITTED_SNAPSHOT`(행 버전) 켜면 RC에서도 과거 버전 읽기 가능<br>SNAPSHOT 레벨 별도 제공 / SERIALIZABLE은 **범위 잠금**으로 팬텀 차단 |
| **Cloud** | — | **Aurora**: MySQL/PostgreSQL 각 호환 엔진 규칙을 따름<br>**Spanner**: TrueTime/분산 합의로 **외부적 직렬성** 보장 |

### 🔍 Phantom Read 실제 시나리오

```sql
-- 【 Session 1 】
BEGIN;
SELECT COUNT(*) FROM orders WHERE amount >= 100;   -- 결과: 5

-- 【 Session 2 (동시 처리 트랜잭션) 】
BEGIN;
INSERT INTO orders(id, amount) VALUES (999, 150);
COMMIT;

-- 【 다시 Session 1 】
SELECT COUNT(*) FROM orders WHERE amount >= 100;   -- 결과가?
```

| 격리 수준 | 결과 | 이유 |
|-----------|------|------|
| **READ COMMITTED** | **5 → 6** ⚠️ 팬텀 발생 | 매 SELECT마다 최신 스냅샷 |
| **REPEATABLE READ**<br>(InnoDB/PG 스냅샷 구현) | **5 → 5 유지** | 같은 트랜잭션 내 **같은 스냅샷**을 보기 때문 |
| ↳ 단, Session 1이 **잠금 읽기**(`FOR UPDATE`)나 같은 범위를 UPDATE/DELETE로 잡으면 | — | **범위 잠금**으로 Session 2의 INSERT가 대기/차단 → 팬텀 **사전 차단** |
| **SERIALIZABLE** | **팬텀 원천 차단** | 범위/프레디킷 잠금 또는 SSI<br>Session 2의 INSERT는 대기하거나 **충돌로 롤백** |

---

# 2. 관계형 모델 핵심 개념

> 📌 **다루는 것** : 테이블 · 키(PK, FK, UK) · 관계(1:1, 1:N, N:M) · 정규화(1NF~3NF)

## 2-1. 관계형 데이터 모델링이란?

> **현실 세계의 데이터를 관계형 포맷으로 변환하는 과정**
> 📄 출처 : Codd, E. F. (1970). *A Relational Model of Data for Large Shared Data Banks*

**왜 필요한가**
1. 현실 세계의 데이터를 **컴퓨터가 이해할 수 있도록 변환**해야 하고
2. 해당 데이터에 대해 **여러 명이 동시에 통합적으로 작업**할 수 있도록 구성이 필요

**관계(Relation)란?** 통상 **열과 행을 지니는 형태**로 표현 — 대표적 예는 **"표"**

---

## 2-2. 테이블 (Table / Relation)

- **행(Row/Tuple)과 열(Column/Attribute)** 로 구성된 **2차원 구조**
- 각 **행** : 하나의 레코드(데이터 인스턴스)
- 각 **열** : 특정 속성(Attribute), **동일한 데이터 타입**을 가진 값들이 저장

**예시 — 학생 테이블**

| 학번(PK) | 이름 | 학과 | 학년 |
|----------|------|------|------|
| 2024001 | 홍길동 | 컴퓨터공학 | 1 |
| 2024002 | 이순신 | 경영학 | 2 |
| 2024003 | 강감찬 | 컴퓨터공학 | 3 |

---

## 2-3. 키 (Key) — 무결성과 식별성의 장치

| 키 | 정의 | NULL | 중복 | 예시 |
|----|------|------|------|------|
| **PK** (Primary Key)<br>기본 키 | 각 행을 **고유하게 식별**하는 컬럼(또는 컬럼 조합)<br>**자동으로 인덱스 생성** | ❌ 불가 | ❌ 불가 | 학생 테이블의 "학번" |
| **FK** (Foreign Key)<br>외래 키 | **다른 테이블의 PK를 참조**하는 컬럼<br>테이블 간 관계 표현, **참조 무결성** 보장 | — | — | 성적 테이블의 "학번" → 학생 테이블의 "학번(PK)" |
| **UK** (Unique Key)<br>고유 키 | 중복 불가, **PK와 달리 NULL은 허용** | ✅ 허용 | ❌ 불가 | 이메일 주소, 주민등록번호, 직원코드 |

### 🔖 [참고] 외래키 제약 조건 옵션 비교

| 옵션 | 동작 | 사용 시나리오 |
|------|------|---------------|
| **ON DELETE CASCADE** | 부모 삭제 시 **자식도 함께 삭제** | 주문 삭제 시 주문 항목도 자동 삭제 |
| **ON DELETE SET NULL** | 부모 삭제 시 자식의 FK를 **NULL로** | 직원 퇴사 시 담당 고객의 담당자를 NULL로 |
| **ON DELETE RESTRICT** | **자식이 있으면 부모 삭제 차단** | 카테고리 삭제 전 상품 먼저 삭제 필요 |
| **ON DELETE NO ACTION** | RESTRICT와 유사, **제약 체크 시점 차이** | Oracle, SQL Server **기본값** |
| **ON UPDATE CASCADE** | 부모 PK 변경 시 자식 FK도 자동 변경 | 자연키(학번) 변경 전파 (**대체키 사용 권장**) |

---

## 2-4. 관계 (Relationship)

| 관계 | 설명 | 구현 | 예시 |
|------|------|------|------|
| **1:1** (One-to-One) | 한 레코드가 다른 테이블의 **하나의 레코드와만** 연결 | FK + UNIQUE | [학생] ↔ [학생증] |
| **1:N** (One-to-Many) | 한 레코드가 다른 테이블의 **여러 레코드와** 연결<br>**가장 흔한 관계** | 자식 쪽에 FK | [학생] 1명 → [성적] 여러 개 |
| **N:M** (Many-to-Many) | 여러 레코드가 여러 레코드와 연결 | ⚠️ **중간 테이블(교차 엔티티)** 로 구현 | [학생] ↔ [강좌] → **"수강" 테이블 필요** |

---

## 2-5. 정규화 — 실전 예제로 따라가기

> 💡 강의에서 **특수임무 TF팀** 예제로 1NF → 2NF → 3NF를 단계적으로 보여줍니다. 이게 가장 이해가 빠릅니다.

### 🅰 1NF — PK 부여

**상황** : 회사 업무 앱으로 역할별 특수임무 TF팀을 구성·운영
- **사번**으로 특정인을 구분, **전공코드**로 역할 구분
- ⇒ 직원별 역할은 **"사번 + 전공코드"** 로 구분 가능 → **복합 PK**

| 사번(PK) | 직위 | 직위코드 | 전공코드(PK) | 역할상세 | 연락처 | 근무지 | 자격증 | 회사코드 | 회사명 |
|---|---|---|---|---|---|---|---|---|---|
| 20-243679 | 중사 | SG2 | SNIPER | 저격 | 010-XXX | 미국 | 스쿠버 | UDT | 3707 |
| 23-023456 | 병장 | SG0 | MEDIC | 의료 | 010-XXX | 한국 | 응급구조사 | 특수전여단 | 1179 |
| 22-138907 | 하사 | SG1 | DEMOLITION | 폭파 | 010-XXX | 캐나다 | 화공기사 | 특전사령부 | 707 |

> ※ **식별자(PK)가 부여된 상태를 1정규형**이라고도 합니다.

### 🅱 2NF — 부분 종속 분리

**문제 발견** : 직원을 한 명 더 추가해보니, **전공코드로 구분되는 임무상세 정보가 중복**되고 추후 재정의될 수도 있음
→ 전체 목록 관리에서 **분리 후 관리**

**인사정보** (역할상세 제거됨)

| 사번(PK) | 직위 | 직위코드 | 전공코드(PK) | 연락처 | 근무지 | 자격증 | 회사코드 | 회사명 |
|---|---|---|---|---|---|---|---|---|
| 20-243679 | 중사 | SG2 | SNIPER | 010-XXX | 미국 | 스쿠버 | UDT | 3707 |
| 23-023456 | 병장 | SG0 | MEDIC | 010-XXX | 한국 | 응급구조사 | 특수전여단 | 1179 |
| 22-138907 | 하사 | SG1 | DEMOLITION | 010-XXX | 캐나다 | 화공기사 | 특전사령부 | 707 |
| 21-135987 | 중사 | SG2 | SNIPER | 010-XXX | 한국 | 고공강하 | 특수전여단 | 1179 |

**전공정보** (분리됨)

| 전공코드(PK) | 역할상세 |
|---|---|
| SNIPER | 저격 |
| MEDIC | 의료 |
| DEMOLITION | 폭파 |

> ※ 식별자(PK)에 **부분 종속된 내용을 분리한 상태를 제2정규형**이라고 합니다.
> ※ 분리된 테이블에서 기존 테이블로 다시 찾아갈 수 있는 기준 열을 **외래키(FK)** 라고 합니다.

### 🅲 3NF — 이행 종속 분리

**문제 발견** : 식별자는 아니지만 **회사와 직위도 각각 따로 관리 가능**
⚠️ 분리를 안 하면, 회사와 동일 직위의 직원을 추가할 때 **회사·직위가 중복**됨

**최종 4개 테이블로 분리**

```
인사정보(사번 PK, 직위코드, 전공코드 PK, 연락처, 근무지, 자격증, 회사코드)
   ├─FK→ 전공정보(전공코드 PK, 역할상세)
   ├─FK→ 직위정보(직위코드 PK, 직위명)
   └─FK→ 회사정보(회사코드 PK, 회사명)
```

> ※ 식별자(PK)가 아닌데 **부분 종속된 내용을 분리한 상태를 제3정규형**이라고 합니다.

---

## 2-6. 정규화 정리

### 왜 필요한가 — 3가지 이상(Anomaly) 현상

| 이상 현상 | 내용 |
|-----------|------|
| **삽입 이상** (Insertion Anomaly) | 일부 데이터 저장 시 **불필요한 데이터도 저장**해야 함 |
| **삭제 이상** (Deletion Anomaly) | 데이터 삭제 시 **다른 중요 정보도 함께 삭제**됨 |
| **갱신 이상** (Update Anomaly) | 중복 저장된 데이터 중 **일부만 수정** → **불일치** 발생 |

### 정규형 단계별 요약

| 정규형 | 조건 | 제거 대상 | 예시 |
|--------|------|-----------|------|
| **1NF** | 각 컬럼은 **원자값(Atomic Value)** 만 | 반복 그룹, 다중값 속성 | "과목 = DB, 네트워크" → **별도 행으로 분리** |
| **2NF** | 1NF + **부분 함수 종속 제거**<br>(복합키 **전체**에만 종속) | 복합키 **일부**에만 종속된 속성 | (학번+과목코드)에서 **학생이름은 학번에만 종속** → 분리 |
| **3NF** | 2NF + **이행적 종속 제거** | 비-키 속성이 **다른 비-키 속성**에 종속 | 학번 → 학과코드 → **학과명** 이행 종속 제거 |
| **BCNF** | 3NF + **결정자는 반드시 후보키** | 비후보키 결정자 | 모든 함수 종속의 결정자가 후보키여야 함 |

> ⚠️ **과도한 정규화의 함정**
> 정규화 → **테이블이 쪼개짐** → **JOIN 비용 증가** → 성능 저하
> → 성능 고려 시 **반정규화(Denormalization) 전략** 도입
> 실무에서는 보통 **3NF 또는 BCNF까지** 적용합니다.

### SQL로 보는 정규화 전/후

```sql
-- ❌ 비정규화 (1NF 위반: 다중값 컬럼)
CREATE TABLE student_bad (
  student_id INT PRIMARY KEY,
  name       VARCHAR(50),
  subjects   VARCHAR(200)   -- "DB, 네트워크, OS" ← 원자값 아님!
);

-- ✅ 1NF + 2NF + 3NF 적용 후 (분리된 테이블)
CREATE TABLE students (
  id       INT PRIMARY KEY,
  name     VARCHAR(50) NOT NULL,
  major_id INT REFERENCES majors(id)   -- 3NF: 학과명 분리
);

CREATE TABLE majors (
  id   INT PRIMARY KEY,
  code VARCHAR(20) UNIQUE,
  name VARCHAR(100)                    -- major_id → name (이행종속 제거)
);

CREATE TABLE enrollments (             -- 1NF: 과목 분리 + 2NF 교차테이블
  student_id INT REFERENCES students(id),
  course_id  INT REFERENCES courses(id),
  score      DECIMAL(5,2),
  PRIMARY KEY (student_id, course_id)  -- 복합 PK
);
```

> ✅ **Checkpoint** : 정규화는 **설계 단계에서 데이터 중복·이상을 방지하는 핵심 원칙**

---

## 2-7. SQL vs NoSQL

| | **SQL (RDBMS)** | **NoSQL** |
|---|---|---|
| **대상 데이터** | **정형 데이터** — 관계형 모델 설계 후 테이블 사용 | **비정형 데이터** — 문서, 키-값, 그래프, 인메모리, 로그검색 |
| **적합한 경우** | **데이터 일관성**과 온라인 처리<br>**엄격한 ACID** 필요 | **가용성과 성능** 중심<br>일부 중복·불일치를 허용하는 **완화된 ACID** |
| **장점** | 데이터 **무결성·정확성 보장** | 웹 환경의 다양한 정보 검색·저장에 유리<br>서버 추가/삭제, **데이터 분산에 유연** |
| **단점** | **확장(수평)에 제약** | 무결성·정확성을 **보장하지 않음** |
| **쿼리** | 다양하고 복잡한 쿼리, **UPDATE/DELETE/JOIN 가능** | **단순한 쿼리**에 유리, 직접 수정·삭제보다 **입력으로 대체** |
| **스키마** | **고정 스키마** — 테이블 디자인 후 쿼리 작성 | ⚠️ **어떤 쿼리 결과가 필요한지 먼저 정의**한 후, 그 결과를 얻도록 테이블 디자인 |

> 🔑 **설계 순서가 정반대입니다**
> - **SQL** : 데이터의 **관계**에 집중 → 테이블 설계 → 쿼리
> - **NoSQL** : 필요한 **쿼리 결과**를 먼저 정의 → 그에 맞게 저장 구조 설계
>
> **예시 (게시판)** — NoSQL은 "표현되는 데이터와 **정렬되는 특징**"에 집중
> - 게시글은 **작성 시간순 정렬**
> - 게시글 ↔ 내용 : **1:1**
> - 게시글 ↔ 댓글 : **1:N**, 댓글은 게시글 내에서 **시간순 정렬**

---

## 2-8. 관계형 데이터 모델 검증

> 설계된 모델이 실제 요구사항을 충족하는지 확인하는 중요한 단계

| 검증 항목 | 설명 |
|-----------|------|
| **데이터 무결성** | 정확하고 일관된 데이터 저장 및 관리 |
| **정규화** | 데이터 중복 최소화 및 무결성 향상 |
| **성능** | 데이터 액세스 및 처리 속도 |
| **보안** | 데이터 보호 및 무단 접근 방지 |

---

# 3. ERD — Entity, Attribute, Relationship

> 📌 **다루는 것** : 엔티티 · 속성 · 관계 · ERD 작성 방법 · IE 표기법

## 3-0. 실습 환경

| 도구 | 내용 |
|------|------|
| **PostgreSQL** (권장) | 오픈소스 RDBMS, 표준 SQL 호환, JSONB/GIS/Vector 확장 풍부<br>기본 포트 **5432** (**Mac: 5433**)<br>실습 버전: **PostgreSQL 14 or 17** (17 이하 권장) |
| **dbdiagram.io** | **DBML** 문법으로 ERD 빠르게 작성, **SQL 내보내기** 가능 |
| **ERDCloud** (erdcloud.com) | 한국어 UI, 팀 협업 |
| **Lucidchart** | 실시간 협업, 다양한 다이어그램 |
| **DBeaver** | GUI 클라이언트 — 무료, 멀티 DB 지원, ERD 시각화, 쿼리 편집기 |

---

## 3-1. Entity (엔티티, 개체)

> **데이터베이스에서 관리하고자 하는 대상 객체**

| 구분 | 설명 | 예시 |
|------|------|------|
| **유형 엔티티** | 사람, 사물, 장소 | 학생, 교수, 강의실 |
| **무형 엔티티** | 개념, 사건, 행위 | 수강신청, 주문 |
| **엔티티 집합** (Entity Set) | 동일한 특성을 가진 엔티티들의 모임 | 모든 학생들의 집합 = "학생" 엔티티 집합 |

### 강한 엔티티 vs 약한 엔티티

| | **강한 엔티티** (Strong) | **약한 엔티티** (Weak) |
|---|---|---|
| **PK** | **독자적인 PK 존재**, 혼자서도 식별 가능 | **독자적 PK 없음**, 다른 강한 엔티티에 의존해야 식별 가능 |
| **예시** | 학생(학번), 강좌(강좌코드), 교수(교수번호) | **OrderItem** — `OrderID + ItemNo` 복합키 (Order 없이 존재 불가) |
| **ERD 표현** | 사각형 | **이중 사각형**, 식별 관계는 **굵은 선** |
| **삭제** | — | 부모 삭제 시 **자식도 삭제** (`ON DELETE CASCADE`) |

---

## 3-2. Attribute (속성)

> **엔티티가 가지는 고유한 특성이나 성질**
> 예: 학생 엔티티의 속성 = 학번, 이름, 이메일, 학과, 학년, 입학일

| 종류 | 설명 | 예시 |
|------|------|------|
| **단순 속성** (Simple) | 더 이상 나눌 수 없는 **원자값** | 전화번호, 성별, 생년월일 |
| **복합 속성** (Composite) | **여러 단순 속성**으로 구성 | 주소 = 시 + 구 + 동 + 상세주소 |
| **단일값 속성** (Single-valued) | 하나의 값만 가짐 | 주민등록번호 → 한 사람당 하나 |
| **다중값 속성** (Multi-valued) | 여러 값을 가질 수 있음<br>→ ⚠️ **별도 테이블로 분리 (1NF)** | 이메일 주소 여러 개, 취미 여러 개 |
| **유도 속성** (Derived) | 다른 속성으로부터 **계산 가능**<br>→ **DB에 직접 저장 불필요** | 나이 = 현재연도 − 출생연도 |
| **기본키 속성** (Key) | 엔티티를 고유하게 식별<br>→ ERD에서 **밑줄**로 표시 | 학번 |

---

## 3-3. ERD 작성 7단계

| # | 단계 | 하는 일 | 예시 |
|---|------|---------|------|
| **1** | **요구사항 수집** | 시스템에서 관리해야 할 정보, 업무 흐름 파악 | 학생 관리 시스템 → 학생, 강의, 교수, 과제 |
| **2** | **엔티티 도출** | 관리대상의 주요 객체 추출 → 엔티티로 정의 (**주로 명사**) | Student, Course, Professor |
| **3** | **속성 정의** | 각 엔티티가 가져야 할 특징 정리 | 학생 → 학번, 이름, 전공 / 강의 → 강의코드, 강의명 |
| **4** | **관계 설정** | 엔티티 간 연관성 파악, 관계 정의 | 학생-강의는 '수강한다', 교수-강의는 '담당한다' |
| **5** | **카디널리티 명시** | 관계의 수(1:1, 1:N, N:M)를 명확히 표시 | 한 학생이 여러 강의 수강 + 한 강의를 여러 학생이 수강 → **N:M** |
| **6** | **ERD 도구 시각화** | 도형으로 표현 — **사각형=엔티티, 타원=속성, 마름모=관계** | Lucidchart, GitMind, Aquerytool, DBdiagram |
| **7** | **검토 및 수정** | 팀원과 함께 검토, 데이터 무결성 및 요구사항 반영 확인 | — |

---

## 3-4. IE 표기법 (까마귀발, Crow's Foot)

**카디널리티 기호**

| 기호 | 의미 |
|------|------|
| `│` | **하나** (One) |
| 까마귀발 (`<`) | **여럿** (Many) |
| `○` | **없거나 하나** (Zero or One) |
| `∥` | **반드시 하나** (One and Only One) |

**관계선 종류** — 이게 실무에서 자주 헷갈립니다

| 선 | 관계 | FK 위치 | 의미 |
|----|------|---------|------|
| **실선** | **식별 관계** (Identifying) | FK가 **자식의 PK 일부** | **부모 없이 자식 존재 불가** (약한 엔티티) |
| **점선** | **비식별 관계** (Non-identifying) | FK가 자식의 **일반 컬럼** | **부모 없이도 자식 존재 가능** |

---

## 3-5. DBML로 ERD 작성 (dbdiagram.io)

> SQL 없이 빠르게 ERD 작성 → **SQL DDL 자동 생성**

```dbml
// dbdiagram.io (DBML - Database Markup Language)

Table students {
  id         bigint       [pk, increment, note: 'PK']
  student_no varchar(20)  [unique, not null, note: '학번']
  name       varchar(100) [not null]
  email      varchar(200) [unique, not null]
  major_id   int          [ref: > majors.id, note: 'FK → 학과']
  grade      smallint     [not null, note: '1~4학년']
  created_at timestamp    [default: 'now()']
}

Table majors {
  id   int          [pk, increment]
  code varchar(20)  [unique, not null]
  name varchar(100) [not null]
}

Table enrollments {              // N:M 교차 테이블
  student_id  bigint  [ref: > students.id]
  course_id   int     [ref: > courses.id]
  score       decimal(5,2)
  enrolled_at date    [not null]
  Indexes {
    (student_id, course_id) [pk]   // 복합 PK
  }
}
```

**관계 방향 기호**

| 기호 | 의미 |
|------|------|
| `>` | 다대일 (Many-to-One) |
| `<` | 일대다 (One-to-Many) |
| `-` | 일대일 (One-to-One) |
| `<>` | 다대다 (Many-to-Many) |

> ✅ **Checkpoint** : 왼쪽에 DBML 코드 작성 → 오른쪽에 ERD 자동 생성 → **PNG/SQL 내보내기** 가능

---

# 4. 개념적→논리적→물리적 모델 설계

> 📌 **다루는 것** : 3단계 설계 흐름 · 약한 엔티티 · N:M 관계 설계

## 4-1. 3단계 설계 흐름

| | **개념적 모델링** | **논리적 모델링** | **물리적 모델링** |
|---|---|---|---|
| **목적** | 비즈니스 요구사항을 **추상화** | 개념 모델 → **논리 구조로 변환** | 특정 DBMS 환경에 **최적화** |
| **DBMS 의존성** | **독립적** | **독립적** | **의존적** |
| **주요 활동** | • 엔터티 식별 (**명사 추출**)<br>• 관계 정의 (1:N, N:M)<br>• ERD 작성 (이해관계자와 소통)<br>• 복합 속성 처리<br>• 약/강 엔터티 구분 | • **엔터티 → 테이블 매핑**<br>• **PK/FK 설정**<br>• **정규화 (1NF~BCNF)** 적용<br>• 반정규화 전략 검토<br>• 상속 관계 모델링<br>  (Single Table vs Class Table) | (아래 7가지 항목) |
| **산출물** | **ERD 다이어그램** | **논리 ERD, 데이터 사전** | 물리 스키마 (DDL) |

---

## 4-2. 물리적 모델링 핵심 7항목

| # | 항목 | 내용 |
|---|------|------|
| **1~2** | **데이터 타입 결정** | DBMS별 최적 타입 선택<br>✓ **금액: `NUMERIC(10,2)`** — 부동소수점 오류 방지<br>✓ **시간: `TIMESTAMPTZ`** (타임존 포함) — 글로벌 서비스 필수<br>✓ 문자열: `VARCHAR(n)` vs `TEXT` — PostgreSQL은 TEXT 제한 없음 |
| **3** | **인덱스 설계** | **WHERE / JOIN / ORDER BY** 컬럼에 인덱스 추가<br>**B-Tree**(기본), **Hash**(등호만), **GIN**(JSONB/배열), **GiST**(GIS) |
| **4** | **파티셔닝** | 대용량 데이터를 **연도/지역별로 분할 저장** |
| **5** | **클러스터형 vs 비클러스터형 인덱스** | 데이터 **물리적 배치 방식** |
| **6** | **저장 공간 최적화** | 압축, 컬럼 기반 저장(Columnstore), 아카이빙 전략 |
| **7** | **트랜잭션 로드 테스트** | 동시 사용자를 고려한 **Lock 전략** (낙관적/비관적) |

---

## 4-3. 낙관적 Lock vs 비관적 Lock

| | **낙관적 Lock** (Optimistic) | **비관적 Lock** (Pessimistic) |
|---|---|---|
| **전제** | 데이터 저장 시 **충돌이 드물다**고 가정 | 충돌이 잦다고 가정 |
| **동작** | 트랜잭션 **종료 시 버전 비교**로 충돌 감지 | 트랜잭션 **시작 시 Lock 획득**, 다른 트랜잭션 접근 차단 |
| **적합 상황** | • **읽기 위주** 작업<br>• 갱신 빈도 낮음<br>• **긴 트랜잭션** (사용자 세션) | • **고충돌 환경**<br>• **쓰기 집약적** 시스템<br>• **짧은 트랜잭션** (ms 단위) |
| **예시** | 블로그 댓글 수정 | **은행 이체, 좌석 예매** |
| **구현** | `updated_at` 또는 `version` 컬럼으로 충돌 감지 | `SELECT ... FOR UPDATE`<br>`SELECT ... FOR UPDATE NOWAIT` |

---

## 4-4. 약한 엔티티 설계

> **자기 혼자서는 고유하게 식별(구분)할 수 없는 엔터티**
> 반드시 다른 **강한 엔터티에 의존해서 존재**하는 데이터 구조

**설계 원칙**
- 독자적 PK 없음 → **강한 엔티티의 PK + 자신의 부분키**로 **복합 PK** 구성
- **`ON DELETE CASCADE` 필수** — 부모 삭제 시 자식도 삭제
- 이름이나 코드만으로는 유일하지 않으므로 혼자서는 구분 불가
- ⚠️ 복합키(PK+FK) 시 **성능/가독성** 고려

**대표 예시**

| 강한 엔티티 | 약한 엔티티 | 복합 PK | 이유 |
|-------------|-------------|---------|------|
| **Order** (주문번호, 고객명) | **OrderItem** (상품명, 수량) | `(OrderID, ItemNo)` | 주문 없이 주문항목이 존재할 수 없음 |
| **Employee** | **Dependent** (부양가족) | `(EmployeeID, DependentName)` | 직원 없이 부양가족 정보가 존재할 수 없음 |

**DDL 예시**

```sql
CREATE TABLE Dependent (
  EmployeeID    INT,
  DependentName VARCHAR(50),
  BirthDate     DATE,
  PRIMARY KEY (EmployeeID, DependentName),
  FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID)
    ON DELETE CASCADE                    -- Cascading Delete
);
```

> 💡 **설계 시 고려사항** : **Cascading Delete** — 강한 엔터티 삭제 시 약한 엔터티를 연쇄 삭제할지 여부를 결정해야 합니다.

---

## 4-5. N:M (다대다) 관계 설계

> ⚠️ **다대다는 DB에서 직접 구현이 불가능합니다.** 반드시 **조인(교차) 테이블**이 필요합니다.

**기본 구조**

```
Student ────< Enrollment >──── Course
PK: StudentID   StudentID(FK)   PK: CourseID
                CourseID(FK)
                EnrollmentDate  ← 교차 테이블에 추가 속성 가능!
```

**설계 전략**

| 선택지 | 내용 | 평가 |
|--------|------|------|
| **자동 증가 ID** (surrogate key) | 단순화 | but **의미 없는 키** |
| **복합 키** `(StudentID, CourseID)` | 두 FK를 묶어 PK로 | ✅ **데이터 무결성 강화**, 중복 방지 |

**성능 최적화**

| 전략 | 내용 |
|------|------|
| **인덱스 전략** | **어떤 컬럼으로 WHERE 조건을 거느냐**에 따라 **양방향 인덱스**를 만들어두는 전략<br>`INDEX(student_id, course_id)` + `INDEX(course_id, student_id)`<br>→ **Non-Clustered Index** 권장 |
| **파티셔닝** | 대량 데이터 시 **학기별로 Enrollment 테이블 분할** |

**DDL 예시 — 약한 엔티티 + N:M 교차 테이블**

```sql
-- 약한 엔티티: OrderItem (Order 없이 존재 불가)
CREATE TABLE order_items (
  order_id   INT REFERENCES orders(id) ON DELETE CASCADE,
  item_no    SMALLINT NOT NULL,             -- 부분키 (약한 엔티티)
  product_id INT REFERENCES products(id),
  quantity   INT NOT NULL CHECK (quantity > 0),
  unit_price NUMERIC(10,2) NOT NULL,
  PRIMARY KEY (order_id, item_no)           -- 복합 PK
);

-- N:M 교차 테이블: 학생-강좌 수강신청
CREATE TABLE enrollments (
  student_id  BIGINT REFERENCES students(id) ON DELETE CASCADE,
  course_id   INT    REFERENCES courses(id)  ON DELETE CASCADE,
  enrolled_at DATE   NOT NULL DEFAULT CURRENT_DATE,
  score       NUMERIC(5,2) CHECK (score BETWEEN 0 AND 100),
  PRIMARY KEY (student_id, course_id)        -- 복합 PK로 중복 방지
);

-- 양방향 조회 최적화 인덱스
CREATE INDEX idx_enroll_course ON enrollments (course_id, student_id);
```

> ✅ **Checkpoint** : WHERE 조건이 어느 컬럼을 자주 쓰느냐에 따라 Index를 별도로 조정 (단, **Non-Clustered Index 권장**)

---

# 5. 스키마 전략 & RDBMS 비교

> 📌 **다루는 것** : 멀티 프로젝트 설계 · MySQL · PostgreSQL · Oracle · Cloud DB

## 5-1. 스키마 기반 멀티 프로젝트 설계 전략

> **스키마** = 테이블/뷰/함수 등 DB 객체를 그룹화하는 **논리적 네임스페이스**

### 멀티 테넌시 3가지 패턴

| 패턴 | 구조 | 보안 | 운영 비용 |
|------|------|------|-----------|
| **Silo Model** | 테넌트별 **완전 독립 DB 인스턴스** | **최강** | **최대** |
| **Pool Model** | **단일 DB + `tenant_id` 컬럼**으로 구분 | 약함 (데이터 혼재) | **운영 단순** |
| **Bridge Model** ⭐<br>*(PostgreSQL 권장)* | **단일 DB 인스턴스 + 테넌트별 스키마 분리** | 중간~강 | 중간 |

### Bridge Model 구조 예시

```
maindb/
  ├─ global/      (공통: users, products, exchange_rates)
  ├─ prj_alpha/   (프로젝트 A: orders, promotions)
  └─ prj_beta/    (프로젝트 B: inventory, suppliers)
```

**주요 장점**
- **물리적 자원 효율성** (단일 인스턴스), **스키마 단위 접근 제어**, 버전 관리
- **성능 최적화** — 프로젝트별 독립적인 인덱스/파티셔닝 전략 적용
- **Vector DB 연계 시** 프로젝트별 임베딩 저장 스키마 분리 설계 가능

---

## 5-2. 주요 RDBMS 비교표

| DBMS | 라이선스 | 기본 격리 | JSON 지원 | 주요 강점 | 활용 시나리오 |
|------|----------|-----------|-----------|-----------|---------------|
| **MySQL/MariaDB** | 오픈소스 | **Repeatable Read** | JSON (8.0+) | 빠름, **배우기 쉬움** | 웹서비스, 스타트업 |
| **PostgreSQL** | 오픈소스 | Read Committed | **JSONB (강력)** | **SQL 표준, GIS, AI/ML** | 분석, 금융, AI 서비스 |
| **Oracle** | 상용 | Read Committed | 21c+ 지원 | **고가용성, 안정성** | 은행, 대기업 ERP |
| **SQL Server** | 상용 | Read Committed | JSON 함수 | **MS 생태계, BI** | ERP, CRM, PowerBI |
| **AWS Aurora** | 관리형(유료) | Read Committed | MySQL/PG 호환 | **MySQL 대비 3~5배 빠름** | 글로벌 서비스 |
| **GCP Cloud SQL** | 관리형(유료) | PG/MySQL 기본 | PG/MySQL 호환 | **BigQuery 연계** | ML 파이프라인 |

---

## 5-3. DBMS별 상세

### MySQL / MariaDB

| 구분 | 내용 |
|------|------|
| **특징** | 경량 & 빠른 성능 → 웹 서비스 초기에 많이 사용<br>**LAMP 스택**의 핵심 DB (Linux, Apache, MySQL, PHP/Python)<br>**InnoDB** 스토리지 엔진 → 트랜잭션, FK, MVCC 지원<br>MariaDB는 MySQL의 **오픈소스 분기(Fork)**, 커뮤니티 중심 개발 |
| **활용** | 쇼핑몰, 블로그, 스타트업 웹서비스<br>MariaDB는 MySQL 호환 + 추가 기능을 빨리 반영 (JSON, Window Functions) |
| **장점** | **배우기 쉽고 설치/운영 부담이 적음**<br>전 세계 웹사이트 기본 (WordPress, Drupal) |
| **단점** | 복잡한 대규모 시스템에서 **성능/확장성 한계** (수천 TPS 이상)<br>고급 기능 부족 (분산 트랜잭션, 고급 보안) |

### PostgreSQL

| 구분 | 내용 |
|------|------|
| **특징** | **"가장 진보한 오픈소스 RDBMS"**<br>표준 SQL 호환성 우수, **ANSI SQL:2016까지** 잘 반영<br>확장성: **JSONB, PostGIS(GIS), 사용자 정의 함수/자료형**<br>**MVCC** 기반으로 동시성 처리에 강함 |
| **활용** | 일부 기업들이 Postgres 기반으로 **전환 중**<br>**GIS 기반 서비스** (배달앱 경로, 위치 서비스)<br>금융/핀테크 도입 확대 |
| **장점** | 복잡한 쿼리, 데이터 분석, GIS, **JSON 같은 반정형 데이터** 처리에 유리<br>오픈소스인데도 **엔터프라이즈급 기능** 제공 |
| **단점** | ⚠️ **운영 난이도가 있음** (튜닝, 학습 곡선이 높음)<br>DB 관리 경험이 부족하면 관리가 까다로움 |

### Oracle

| 구분 | 내용 |
|------|------|
| **특징** | 대기업 시장을 장악한 전통 강자<br>**RAC** (Real Application Clusters) — 여러 서버가 동시에 DB 공유 → 고가용성/확장성<br>고급 기능: 보안, 성능 최적화, 분산 트랜잭션, **Data Guard**(재해복구) |
| **활용** | 은행 계좌 관리, 글로벌 제조/ERP, 대규모 엔터프라이즈 |
| **장점** | 금융·공공기관·글로벌 기업에서 **신뢰도 검증 완료**<br>매우 안정적, **복잡한 트랜잭션에 적합** |
| **단점** | ⚠️ **비용이 매우 비쌈** (라이선스, 유지보수)<br>오픈소스/클라우드 대체제에 비해 폐쇄적 |

### Microsoft SQL Server

| 구분 | 내용 |
|------|------|
| **특징** | **MS 생태계와 밀접 통합** (.NET, Visual Studio, Windows Server)<br>**OLAP** — BI, 데이터 분석 강점<br>**SSIS/SSAS/SSRS** → 데이터 통합·분석·리포팅 |
| **활용** | 기업 내 ERP/CRM, 금융 리포트, **BI + PowerBI** 경영 데이터 분석 |
| **장점** | MS 환경(Windows, Active Directory, PowerBI)과 **완벽 연계**<br>엔터프라이즈 환경에서 쉽고 빠른 분석/리포팅 |
| **단점** | ⚠️ **Windows 종속적** (최근 Linux 지원 확대 중)<br>오픈소스 대비 자유도 낮음 |

### Cloud Database (관리형 RDBMS)

| 서비스 | 특징 |
|--------|------|
| **AWS RDS** | MySQL, PostgreSQL, Oracle, SQL Server 등 다양한 엔진<br>장점: **자동 백업, 장애 복구, 운영 편리성**<br>⚠️ 단점: **직접 서버 제어 불가** (루트 접근 제한) |
| **Amazon Aurora** | MySQL/Postgres 호환 + AWS 자체 최적화<br>**MySQL 대비 3~5배 빠름** (스토리지 분산 구조)<br>활용: 글로벌 서비스 확장, 빠른 읽기 성능 |
| **GCP Cloud SQL** | Google 관리형 DB, 자동 백업/확장<br>**BigQuery, Dataflow와 연계 쉬움**<br>활용: 데이터 분석, ML 파이프라인 |
| **Azure Database** | SQL Server 기반, MS 생태계와 긴밀 연동<br>**Active Directory, PowerBI, Office365** 통합<br>활용: MS 기반 ERP/CRM SaaS |

### 🎯 한 줄 요약

| DBMS | 한 줄 |
|------|-------|
| **MySQL/MariaDB** | 웹서비스 스타트업 기본 DB — **빠르고 배우기 쉽다** |
| **PostgreSQL** | 최신 오픈소스 RDBMS 대표주자 — **JSON + GIS 처리 강력** |
| **Oracle** | 금융/대기업 시스템 — 고성능·안정성, 단 **비용 부담 큼** |
| **SQL Server** | MS 기업 환경 최적화 — **BI/데이터 분석 강점** |
| **Cloud DB** | 관리형 DBMS — **운영 부담 줄이고 글로벌 확장에 최적** |

---

## 5-4. [참고] ANSI SQL — 표준과 현실

### 배경

- SQL은 1970년대 **IBM**에서 처음 만들어졌고, 이후 **ANSI → ISO**가 공식 표준으로 제정
- **ANSI SQL** = 모든 DBMS가 따라야 하는 **공통 규격(표준 문법)**
- 표준 이름 : **ISO/IEC 9075:2016** (= ANSI SQL:2016)

| 기관 | 범위 |
|------|------|
| **ANSI** (American National Standards Institute) | 미국 표준화 기관 — 미국 표준 버전 SQL |
| **ISO/IEC** | 국제 표준화 기관 — 전 세계 공통 버전 SQL |

> 💡 **왜 중요한가** : 여러 RDBMS를 다루는 개발자라면 **ANSI SQL 문법으로 작성해야 이식성(Portability)** 이 좋습니다.
> - **ANSI SQL** : `SELECT`, `JOIN`, `GROUP BY`, `HAVING`, `CASE WHEN` 같은 기본 문법
> - **Non-ANSI** : `LIMIT`(MySQL) vs `TOP`(SQL Server) — DB마다 다른 것

### SQL 표준의 역사

| 버전 | 연도 | 주요 특징 |
|------|------|-----------|
| SQL-86 | 1986 | 최초 ANSI 표준 제정 |
| SQL-89 | 1989 | 소폭 개정 |
| **SQL-92** | 1992 | **대부분 DBMS의 기본 표준** (SELECT, JOIN 등) |
| SQL:1999 | 1999 | 객체지향 확장(UDT), 트리거, **RECURSIVE WITH** |
| SQL:2003 | 2003 | XML 지원, **윈도우 함수** (OVER, RANK, ROW_NUMBER) |
| SQL:2008 | 2008 | MERGE, TRUNCATE, FETCH FIRST n ROWS |
| SQL:2011 | 2011 | **Temporal Table** (시간 기반 이력 관리) |
| **SQL:2016** | 2016 | **JSON 표준 함수**, Polymorphic Table Function |
| SQL:2023 | 2023 | 최신 판 (표준 JSON Schema, 함수 확장) |

### SQL:2016 주요 추가 내용

> SQL:2016은 현대 DB의 방향인 **JSON & 비정형 데이터 지원**에 집중

| 기능 | 설명 | PostgreSQL | MySQL | Oracle | SQL Server |
|------|------|:---:|:---:|:---:|:---:|
| **JSON 지원**<br>`JSON_VALUE()`, `JSON_QUERY()`, `JSON_OBJECT()` | 표준화된 JSON 함수 | △ 부분<br>(jsonb + 함수) | △ 부분<br>(JSON_EXTRACT, 비표준명) | ○ 21c부터<br>표준 함수 | △ 부분<br>(OPENJSON, 비표준명) |
| **Polymorphic Table Function** | 윈도우 함수처럼 동적으로 테이블 구조 변형 | — | — | — | — |
| **Row Pattern Recognition**<br>`MATCH_RECOGNIZE` | 시계열 데이터 패턴 탐지 | ✗ | ✗ | **○ (12c+)** | ✗ |
| **LATERAL JOIN 개선** | 하위쿼리와 상호 참조 가능 | — | — | — | — |
| **Temporal Table** | 시간 이력 관리 강화 | ○<br>(SYSTEM VERSIONING) | ○ (8.0.2+) | ○ | ○ |
| **MERGE** | UPSERT | ○ | ○ | ○ | ○ |

---

## 5-5. ⭐ ANSI SQL vs 주요 DBMS 문법 비교 (통합표)

> 💬 강의 자료에서 4장에 걸쳐 나뉘어 있는 표를 **하나로 통합**했습니다. 실무에서 가장 자주 찾게 되는 부분입니다.

| 구문 / 기능 | **ANSI SQL (표준)** | **MySQL/MariaDB** | **PostgreSQL** | **Oracle** | **SQL Server** |
|---|---|---|---|---|---|
| **상위 N행 조회** | `FETCH FIRST n ROWS ONLY` | `LIMIT n` | `FETCH FIRST n ROWS ONLY`<br>(또는 `LIMIT n`) | `FETCH FIRST n ROWS ONLY` (12c+) | `TOP n` |
| **LIMIT + OFFSET** | `OFFSET n ROWS FETCH FIRST m ROWS ONLY` | `LIMIT m OFFSET n` | 둘 다 지원 | (12c+) | `OFFSET n ROWS FETCH NEXT m ROWS ONLY` (2012+) |
| **NULL 치환** | `COALESCE(e1, e2)` | 동일 | 동일 | **`NVL()`** (비표준) | **`ISNULL()`** (비표준) |
| **문자열 연결** | `CONCAT(a,b)` 또는 `a \|\| b` | `CONCAT()` | `\|\|` | `\|\|` | `+` / `CONCAT()` |
| **현재 시각** | `CURRENT_TIMESTAMP` | `NOW()` | `NOW()` / `CURRENT_TIMESTAMP` | `SYSTIMESTAMP` | `SYSUTCDATETIME()` / `GETDATE()` |
| **자동 증가** | `GENERATED ALWAYS AS IDENTITY` | `AUTO_INCREMENT` | `GENERATED ... AS IDENTITY` 또는 `SERIAL` | `IDENTITY` (12c~) 또는 `SEQUENCE` | `IDENTITY(1,1)` |
| **조건문** | `CASE WHEN ... THEN ... ELSE ... END` | 동일 | 동일 | 동일 | 동일 |
| **문자 길이** | `CHAR_LENGTH(str)` | `CHAR_LENGTH()` | `CHAR_LENGTH()` | `LENGTH()` | `LEN()` |
| **날짜 차이** | 표준 없음 → `ts1 - ts2` | `DATEDIFF()` (비표준) | `AGE()` 또는 뺄셈 | `MONTHS_BETWEEN()` | `DATEDIFF()` (비표준) |
| **논리값(Boolean)** | `BOOLEAN` | `TINYINT(1)` | **진짜 `BOOLEAN`** | ⚠️ **없음** (`NUMBER(1)`로 대체) | `BIT` |
| **대소문자 변경** | `UPPER()`, `LOWER()` | 동일 | 동일 | 동일 | 동일 |
| **부분 문자열** | `SUBSTRING(str FROM pos FOR len)` | `SUBSTRING(str, pos, len)` | `SUBSTRING(str FROM pos FOR len)` | `SUBSTR(str, pos, len)` | `SUBSTRING(str, pos, len)` |
| **MERGE (UPSERT)** | `MERGE INTO ... USING ...` | `INSERT ... ON DUPLICATE KEY UPDATE` (비표준) | `INSERT ... ON CONFLICT ... DO UPDATE` | 표준 `MERGE` | `MERGE` |
| **JSON 접근** | `JSON_VALUE()` | `JSON_EXTRACT()` | `attrs->>'key'`,<br>`jsonb_extract_path_text()` | `JSON_VALUE()` (21c~) | `JSON_VALUE()` / `OPENJSON()` |
| **윈도우 함수** | `OVER(PARTITION BY ... ORDER BY ...)` | 동일 | 동일 | 동일 | 동일 |
| **RECURSIVE CTE** | `WITH RECURSIVE ...` | 동일 | 동일 | (11gR2+) | (2005+) |
| **문자열 검색** | `LIKE '%abc%'` | 동일 | 동일 | 동일 | 동일 |
| **트랜잭션** | `BEGIN`, `COMMIT`, `ROLLBACK` | 동일 | 동일 | 동일 | 동일 |
| **TRUNCATE** | `TRUNCATE TABLE t;` | 동일 | 동일 | 동일 | 동일 |
| **TEMP TABLE** | `CREATE TEMPORARY TABLE` | 동일 | 동일 | `GLOBAL TEMPORARY TABLE` | `#temp`(로컬), `##temp`(전역) |

### 🔑 이식성 전략

| 구분 | 내용 |
|------|------|
| **완전 표준** | `SELECT`, `JOIN`, `GROUP BY`, `HAVING`, `CASE`, `COALESCE`, `FETCH FIRST n ROWS ONLY` |
| **DB 전용 문법** ⚠️ | MySQL: `LIMIT`, `IFNULL` / SQL Server: `TOP`, `ISNULL` / Oracle: `NVL`, `ROWNUM` / PostgreSQL: `SERIAL` |
| **추천 전략** | **ANSI SQL 기반으로 작성**하고, **LIMIT/OFFSET · NULL 처리 · 날짜함수 · JSON 함수만** DB별로 분기 |

**실무 판단 기준**
- 이식성이 중요한 프로젝트면 → **ANSI SQL + 호환 함수로 통일**
- 보고서/배치 등 **DB가 고정**이면 → 해당 DB 고유함수 써도 OK
- **ORM**(JPA, SQLAlchemy)은 내부적으로 이런 차이를 **자동 흡수**
- ⚠️ **쿼리 튜닝할 땐 DB 전용 함수/힌트를 써야 함** (성능용)

---

# 6. SQL 기초 — DDL

> 📌 **다루는 것** : CREATE DATABASE · CREATE TABLE · ALTER · 데이터 타입 · 제약조건

## 6-1. CREATE DATABASE — "컨테이너" 만들기

> ⚠️ **벤더마다 "데이터베이스"의 의미/단위가 조금씩 다릅니다.** 이걸 모르면 처음부터 헤맵니다.

| DBMS | 계층 구조 | 주의할 점 |
|------|-----------|-----------|
| **MySQL/MariaDB** | 서버 → 여러 **database(=schema)** → 테이블 | **문자셋/콜레이션을 꼭 지정!** |
| **PostgreSQL** | 서버(cluster) → 여러 **database** → 각 DB 안에 여러 **schema** → 테이블 | **인코딩/로케일**을 함께 정할 것 |
| **SQL Server** | 인스턴스 → 여러 **database** → 각 DB 안에 **schema**(기본: `dbo`) | 한국어/UTF-8은 **콜레이션 지정** |
| **Oracle** | "데이터베이스"는 **인스턴스/스토리지 단위**(DBA가 생성) | 개발자는 보통 **사용자 = 스키마**를 만들어 씀 |

```sql
-- MySQL / MariaDB
CREATE DATABASE skala_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;   -- 한국어/이모지 지원

-- PostgreSQL (권장)
CREATE DATABASE skala_db
  WITH ENCODING   = 'UTF8'
       LC_COLLATE = 'en_US.UTF-8'
       LC_CTYPE   = 'en_US.UTF-8'
       TEMPLATE   = template0;

-- PostgreSQL 스키마 생성 및 검색 경로 설정
\c skala_db
CREATE SCHEMA app;               -- 애플리케이션 스키마
CREATE SCHEMA audit;             -- 감사 로그 스키마
SET search_path = app, public;   -- 기본 스키마 순서

-- SQL Server
CREATE DATABASE SkalaDB
  COLLATE Korean_100_CI_AS_SC_UTF8;

-- Oracle (DBA 수행, 사용자 = 스키마 개념)
CREATE USER skala_user IDENTIFIED BY "StrongPW1!"
  DEFAULT TABLESPACE users QUOTA UNLIMITED ON users;
GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE TO skala_user;
```

> ✅ **Checkpoint**
> **UTF-8 및 한국어 콜레이션 설정을 처음부터 올바르게** 하세요.
> ⚠️ **나중에 바꾸면 모든 데이터를 재변환**해야 합니다.

---

## 6-2. CREATE TABLE — 같은 테이블, 4가지 문법

> **동일한 `products` 테이블**을 각 DBMS 문법/관례에 맞게 만든 예시
> `id`(정수 식별자) / `name`(문자) / `price`(금액, 소수 고정) / `attrs`(JSON) / `created_at`(생성 시각)

**MySQL / MariaDB (InnoDB 전제)**
```sql
CREATE TABLE products (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(200) NOT NULL,
  price      DECIMAL(10,2) NOT NULL CHECK (price >= 0),  -- MySQL 8.0.16+ / MariaDB 10.2+
  attrs      JSON NULL,          -- MariaDB는 내부적으로 LONGTEXT + JSON 함수
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB
  DEFAULT CHARSET = utf8mb4;
```
> ⚠️ `CHECK`는 **MySQL 8.0.16 미만에선 파싱만 하고 무시**되던 역사가 있음 (버전 확인 필수)
> ⚠️ MariaDB의 JSON은 물리적으로 **LONGTEXT** → 인덱싱 시 **가상컬럼 + 인덱스** 패턴 사용

**PostgreSQL**
```sql
CREATE TABLE products (
  id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- SERIAL 대신 최신 표준
  name       VARCHAR(200) NOT NULL,
  price      NUMERIC(10,2) NOT NULL CHECK (price >= 0),
  attrs      JSONB,                          -- 강력한 JSONB 연산/인덱스
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- JSONB 특정 키 인덱싱 예시
CREATE INDEX idx_products_attrs_color
  ON products ((attrs->>'color'));
```

**SQL Server**
```sql
CREATE TABLE dbo.Products (
  Id        BIGINT IDENTITY(1,1) PRIMARY KEY,
  Name      NVARCHAR(200) NOT NULL,
  Price     DECIMAL(10,2) NOT NULL
            CONSTRAINT CK_Products_Price CHECK (Price >= 0),
  Attrs     NVARCHAR(MAX) NULL,   -- JSON 전용 타입 없음 → JSON_VALUE/OPENJSON 사용
  CreatedAt DATETIME2 NOT NULL
            CONSTRAINT DF_Products_CreatedAt DEFAULT SYSUTCDATETIME()
);
```

**Oracle**
```sql
CREATE TABLE products (
  id         NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,  -- 12c+
  name       VARCHAR2(200 CHAR) NOT NULL,        -- CHAR semantics 권장
  price      NUMBER(10,2) NOT NULL,
  attrs      CLOB,                               -- 12c~: IS JSON 제약, 21c~: JSON 타입
  created_at TIMESTAMP WITH TIME ZONE DEFAULT SYSTIMESTAMP NOT NULL,
  CONSTRAINT ck_products_price CHECK (price >= 0)
);

-- 12c 이상에서 JSON 유효성
ALTER TABLE products ADD CONSTRAINT ck_products_attrs_json
  CHECK (attrs IS JSON);
```

---

## 6-3. 데이터 타입 차이 핵심 정리

| 분류 | MySQL/MariaDB | PostgreSQL | SQL Server | Oracle |
|------|---------------|------------|------------|--------|
| **정수/식별자** | `INT AUTO_INCREMENT` | `GENERATED ... AS IDENTITY`(표준)<br>또는 `SERIAL` | `BIGINT IDENTITY(1,1)` | `IDENTITY`(12c+)<br>또는 `SEQUENCE+TRIGGER`(구버전) |
| **문자열** | `VARCHAR(n)`,<br>`TEXT/MEDIUMTEXT/LONGTEXT` | `VARCHAR(n)`, **`TEXT`**<br>(사이즈 제한 없음, 실무에서 TEXT 많이 사용) | `VARCHAR`/**`NVARCHAR`**(유니코드)<br>대용량 `NVARCHAR(MAX)` | `VARCHAR2(n BYTE\|CHAR)`<br>대용량 `CLOB` |
| **이진** | `BLOB` 계열 | **`BYTEA`**<br>대용량은 Large Object API | `VARBINARY`<br>대용량 `VARBINARY(MAX)` | `BLOB` |
| **날짜/시간** | `DATETIME`, `TIMESTAMP`<br>(⚠️ **타임존 없음**) | `TIMESTAMP [WITH TIME ZONE]`<br>= **`TIMESTAMPTZ`**, `now()` | **`DATETIME2` 권장**<br>`GETDATE()`(로컬)<br>`SYSUTCDATETIME()`(UTC) | `TIMESTAMP [WITH TIME ZONE]`<br>`SYSTIMESTAMP` |
| **불리언** | `BOOLEAN` = `TINYINT(1)` 동의어 | **진짜 `BOOLEAN`** | `BIT` | ⚠️ **SQL 레벨엔 없음**<br>→ `NUMBER(1)` + `CHECK` |
| **JSON** | 8+: `JSON`(네이티브)<br>MariaDB: 표기는 JSON, 실제는 **LONGTEXT** | **`JSONB`**(인덱싱/연산 강력)<br>`JSON`(원문 보존) | ⚠️ 전용 타입 없음<br>(`NVARCHAR` 저장) + `OPENJSON`, `JSON_VALUE` | 12c~ `IS JSON`로 유효성<br>21c~ 전용 `JSON` 타입 |
| **ENUM / ARRAY** | `ENUM` 있음<br>(⚠️ 확장성/이식성 주의) | **`ENUM`, `ARRAY` 모두 강력 지원** | ❌ 직접 지원 X | ❌ 직접 지원 X |

> 💡 **ENUM 대안 — 참조 테이블 + FK 모델링 (권장)**
> ```sql
> -- 상태값을 따로 테이블로
> CREATE TABLE status_types (
>   status_code VARCHAR2(20) PRIMARY KEY,
>   description VARCHAR2(100)
> );
> INSERT INTO status_types VALUES ('ACTIVE',  '활성 사용자');
> INSERT INTO status_types VALUES ('BLOCKED', '차단됨');
> INSERT INTO status_types VALUES ('PENDING', '승인 대기');
>
> CREATE TABLE users (
>   id          NUMBER PRIMARY KEY,
>   email       VARCHAR2(200) NOT NULL,
>   status_code VARCHAR2(20) NOT NULL,
>   CONSTRAINT fk_users_status FOREIGN KEY (status_code)
>     REFERENCES status_types(status_code)
> );
> ```

---

## 6-4. 제약조건 — 무결성의 4대장

| 제약 | 특징 / 추가 옵션 |
|------|------------------|
| **NOT NULL** | 빈 값 금지 |
| **DEFAULT** | 값 없으면 이걸로 (`DEFAULT CURRENT_TIMESTAMP`, `DEFAULT 0`)<br>⚠️ **함수 이름은 벤더별로 다름** (SQL Server: `GETDATE()`/`SYSUTCDATETIME()`) |
| **CHECK** | 수학/논리식으로 값 제한<br>MySQL 8.0.16+ / MariaDB 10.2+ / PostgreSQL / SQL Server / Oracle에서 사용<br>⚠️ **성능상 과도한 복잡식은 지양, 핵심 규칙만!** |
| **FOREIGN KEY** | **참조 무결성** — 자식 → 부모(PK/UNIQUE) 참조<br>삭제/수정 동작을 `ON DELETE`/`ON UPDATE`로 정의 |

**FK의 DBMS별 지원 차이**

| DBMS | 지원 범위 |
|------|-----------|
| **PostgreSQL** | `ON DELETE/UPDATE` CASCADE/SET NULL/RESTRICT 지원, **DEFERRABLE 가능** |
| **MySQL/MariaDB (InnoDB)** | `ON DELETE/UPDATE` 지원 (⚠️ 버전/엔진 주의) |
| **SQL Server** | `ON DELETE/UPDATE` 지원, **DEFERRABLE 없음** |
| **Oracle** | ⚠️ **`ON DELETE`만 지원 (`ON UPDATE` 미지원)**, DEFERRABLE 가능 |

> 💡 **실무 팁** : **FK 컬럼에 인덱스를 고려**할 것 (조인/삭제 성능). 일부 DB는 자동 생성이 안 됩니다.

---

## 6-5. 이식성(Portable SQL) 팁 & 자주 겪는 일

**이식성 팁**

| 항목 | 내용 |
|------|------|
| **타입은 표준/보편형으로** | `INTEGER`, `NUMERIC(p,s)`, `VARCHAR(n)`, `TIMESTAMP` 중심 |
| **예약어/식별자 따옴표 지양** | 벤더별 따옴표가 다름 (`"`, `` ` ``, `[]`) → **스네이크케이스 소문자 권장** |
| **DEFAULT 함수명** | 통일 불가 → **마이그레이션 스크립트에서 분기** |
| **CHECK/ENUM 남용 금지** | 규칙이 바뀌면 스키마 변경 불가 → **많으면 Lookup 테이블 + FK로** |
| **JSON** | 스키마-리스지만, **접근 경로가 자주 쓰이면 가상컬럼/인덱스로 최적화** |

**⚠️ 자주 겪는 일 (실전 함정)**

| 함정 | 내용 |
|------|------|
| **MySQL 구버전 CHECK 무시** | 8.0.16 미만이면 **동작 안 함** |
| **Oracle의 `ON UPDATE` FK 미지원** | 모델 설계로 해결 (애플리케이션에서 업데이트 금지 등) |
| **대용량 텍스트의 DEFAULT** | MySQL `TEXT`/`BLOB`엔 **DEFAULT 불가** |
| **타임존 혼선** | 서버/클라이언트 TZ가 다르면 → `TIMESTAMP WITH TIME ZONE`(PG/Oracle) 또는 **UTC 고정**(SQL Server `SYSUTCDATETIME`) 전략 |
| **문자셋/정렬** | 문자열을 어떻게 비교하고 정렬할지 **프로젝트 초기에 통일** |

**✅ 스키마 리뷰 체크리스트**

- [ ] **PK는 단일/숫자/불변**인가? (자연키 대신 **대체키 권장**)
- [ ] **FK에 필요한 인덱스**가 있는가?
- [ ] **금액/수량은 `DECIMAL`/`NUMERIC`** 으로 스케일을 고정했는가?
- [ ] **시간 컬럼은 기본값/타임존 정책**이 일관적인가?
- [ ] **JSON 컬럼은 꼭 필요한가?** 자주 쓰는 키에 인덱스 계획이 있는가?
- [ ] **CHECK/ENUM이 변경 가능성**을 과도하게 제한하진 않는가?

---

## 6-6. ALTER TABLE — 운영 중 스키마 변경

```sql
-- 컬럼 추가 (일반적으로 안전)
ALTER TABLE students ADD COLUMN phone VARCHAR(20);
ALTER TABLE students ADD COLUMN birth_date DATE;

-- 컬럼 타입 변경 (⚠️ 대용량 테이블에서는 전체 재작성 발생)
ALTER TABLE students ALTER COLUMN phone TYPE VARCHAR(30);   -- PostgreSQL

-- NOT NULL 추가 (기존 NULL 없는 경우만)
ALTER TABLE students ALTER COLUMN phone SET NOT NULL;

-- 제약조건 추가
ALTER TABLE students
  ADD CONSTRAINT chk_email_format CHECK (email LIKE '%@%');

-- 컬럼 삭제 (⚠️ 신중히 — CASCADE: 의존 뷰/인덱스 함께 삭제)
ALTER TABLE students DROP COLUMN IF EXISTS phone CASCADE;

-- 인덱스 생성 (운영 중 잠금 없이)
CREATE INDEX CONCURRENTLY idx_students_grade ON students (grade);
-- CONCURRENTLY: PostgreSQL에서 테이블 잠금 없이 인덱스 생성 (운영 환경 권장)
```

### TRUNCATE vs DELETE

| | **TRUNCATE** | **DELETE** |
|---|---|---|
| **속도** | **빠름** | 느림 |
| **커밋** | **자동 커밋** | **롤백 가능** |
| **트리거** | **미실행** | **실행** |
| **WHERE** | ❌ 불가 | ✅ 가능 |

> ✅ **Checkpoint — 운영 중 DDL 변경 (대용량 테이블)**
> - MySQL: **`pt-online-schema-change`**
> - PostgreSQL: **`pg_repack`**

---

# 7. SQL 기초 — DML

> 📌 **다루는 것** : SELECT · INSERT · UPDATE · DELETE · 함수 · CASE WHEN

## 7-1. INSERT / UPDATE / DELETE

```sql
-- INSERT (단건)
INSERT INTO students (student_no, name, email, major_id, grade)
VALUES ('2025001', '홍길동', 'hong@skala.ai', 1, 1);

-- INSERT (다건)
INSERT INTO courses (code, title, credits) VALUES
  ('CS101', '데이터베이스', 3),
  ('CS102', '알고리즘',     3),
  ('CS103', '운영체제',     3);

-- UPDATE (⚠️ WHERE 필수! 없으면 전체 행 수정)
UPDATE students
   SET grade      = grade + 1,
       updated_at = now()
 WHERE enrolled = TRUE
   AND grade < 4;

-- DELETE (⚠️ WHERE 필수! 없으면 전체 행 삭제)
DELETE FROM enrollments
 WHERE student_id IN (
   SELECT id FROM students WHERE enrolled = FALSE
 );
```

> ⚠️ **주의 사항**
> - **MySQL** : 기본 `autocommit ON` → **즉시 커밋됨** (되돌릴 수 없음!)
> - **PostgreSQL** : `BEGIN;` 없이 DML → **자동 커밋**
> - **대용량 DELETE는 `LIMIT` + 루프로 나눠서 처리** 권장

---

## 7-2. SELECT — ⭐ 논리적 실행 순서

> 🔑 **작성 순서와 실행 순서가 다릅니다.** 이걸 모르면 "왜 WHERE에서 별칭을 못 쓰지?"에서 막힙니다.

```
FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
                                             ↑
                                    별칭(alias)은 여기서 만들어짐
```

| 순서 | 절 | 하는 일 |
|:---:|---|---|
| 1 | `FROM` | 테이블 지정 |
| 2 | `JOIN` | 테이블 결합 |
| 3 | `WHERE` | **행 필터** (집계 **전**) |
| 4 | `GROUP BY` | 그룹화 |
| 5 | `HAVING` | **그룹 필터** (집계 **후**) |
| 6 | `SELECT` | **컬럼 선택 + 별칭 부여** |
| 7 | `ORDER BY` | 정렬 (**여기서만 SELECT 별칭 사용 가능**) |
| 8 | `LIMIT` | 개수 제한 |

**실전 예시**

```sql
SELECT
  s.student_no,
  s.name,
  m.name                              AS major_name,
  UPPER(s.email)                      AS email_upper,
  EXTRACT(YEAR FROM s.created_at)     AS join_year,
  COALESCE(s.phone, '미등록')          AS phone_display,
  CASE s.grade
    WHEN 1 THEN '신입생'
    WHEN 4 THEN '졸업반'
    ELSE s.grade || '학년'
  END                                 AS grade_label
FROM  students s
  JOIN majors m ON m.id = s.major_id       -- 2. JOIN 처리
WHERE s.enrolled = TRUE                    -- 3. 행 필터 (집계 전)
  AND s.grade BETWEEN 1 AND 4
ORDER BY s.grade DESC, s.name ASC          -- ORDER BY에서만 별칭 사용 가능
LIMIT 20 OFFSET 0;                         -- 페이지네이션
```

> ⚠️ **핵심 함정**
> **`WHERE`절에서 `SELECT`절의 별칭(alias)을 사용할 수 없습니다.**
> 이유: **`SELECT`는 `WHERE`보다 나중에 처리**되기 때문. `WHERE` 시점엔 별칭이 아직 존재하지 않습니다.

---

## 7-3. 자주 쓰는 함수

```sql
-- 문자열 함수
SELECT UPPER('hello'),                       -- HELLO
       LOWER('WORLD'),                       -- world
       LENGTH('abc'),                        -- 3
       SUBSTRING('apple' FROM 1 FOR 3),      -- app (표준 SQL)
       TRIM('  hi  '),                       -- hi
       REPLACE('hello world', 'world', 'DB'),-- hello DB
       CONCAT('SK', 'ALA', '4기');           -- SKALA4기

-- 날짜/시간 함수 (PostgreSQL)
SELECT CURRENT_DATE,                         -- 오늘 날짜
       CURRENT_TIMESTAMP,                    -- 현재 일시 + 타임존
       EXTRACT(YEAR FROM now()),             -- 연도 추출
       DATE_TRUNC('month', now()),           -- 월의 첫날
       now() - INTERVAL '30 days',           -- 30일 전
       TO_CHAR(now(), 'YYYY-MM-DD');         -- 포맷팅

-- NULL 처리
SELECT COALESCE(NULL, NULL, '세 번째'),       -- 세 번째 (첫 비-NULL)
       NULLIF(10, 10),                       -- NULL (같으면 NULL)
       NULLIF(10, 20),                       -- 10   (다르면 첫 번째)
       CASE WHEN val IS NULL THEN 0 ELSE val END;
```

> ⚠️ **NULL 처리 함수 이식성**
> - **`COALESCE`** → **SQL 표준 (모든 DBMS)** ✅ 이걸 쓰세요
> - `NVL` → **Oracle 전용**
> - `ISNULL` → **SQL Server 전용**

---

## 7-4. WHERE 절 — 조건 패턴과 NULL 함정

| 분류 | 패턴 |
|------|------|
| **비교 연산자** | `=` `<>` `!=` `<` `>` `<=` `>=`<br>`WHERE grade = 3` / `WHERE grade <> 3` / `WHERE score > 80` |
| **범위/목록** | `WHERE grade BETWEEN 2 AND 4` (**inclusive** — 2와 4 포함)<br>`WHERE major_id IN (1, 3, 5)` / `WHERE major_id NOT IN (2, 4)` |
| **LIKE 패턴** | `WHERE name LIKE '김%'` → ✅ **인덱스 사용 가능** (prefix)<br>`WHERE name LIKE '%길%'` → ❌ **인덱스 미사용!** 대용량 시 **전문검색 인덱스** 필요 |
| **NULL 처리** | ⚠️ **`= NULL` 안 됨. `IS NULL` 사용**<br>`WHERE major_id IS NULL` / `WHERE major_id IS NOT NULL` |
| **AND/OR/NOT 우선순위** | **`NOT` > `AND` > `OR`** → **괄호로 명확하게 표현** |

> ⚠️ **NULL의 3가지 함정 — 가장 많이 틀리는 부분**
> ```
> NULL = NULL      → UNKNOWN (TRUE가 아님!) → WHERE로 필터되지 않음
> NULL + 5         → NULL   (계산에 NULL이 섞이면 결과도 NULL)
> COALESCE(NULL,0) → 0      (그래서 COALESCE로 방어)
> ```
> **NULL은 "값이 없음"이지 "0"이나 "빈 문자열"이 아닙니다.** 비교 대상이 아니라 **상태**입니다.

---

# 8. 종합실습 – 1

> 📌 **주제** : 학사관리시스템 DB 설계 → 구축 → 조회

## 8-1. 학습 목표

- PostgreSQL 환경 구성 및 연결
- 학사 관리 시스템 **ERD 설계**
- **DDL** 작성으로 테이블 생성
- **DML**로 샘플 데이터 입력 및 조회
- **WHERE / 함수 / CASE WHEN** 활용 쿼리 작성

## 8-2. 실습 단계

| # | 단계 | 내용 |
|---|------|------|
| 1 | **환경 구성** | PostgreSQL 접속 확인 (**psql** 또는 **DBeaver**) |
| 2 | **DB 생성** | `CREATE DATABASE` / `CREATE SCHEMA` 실행 |
| 3 | **ERD 설계** | 학사관리시스템 ERD |
| 4 | **DDL** | `CREATE TABLE` — **제약조건 포함** |
| 5 | **DML** | `INSERT INTO` — 테이블 데이터 **최소 10건 이상** |
| 6 | **기초 조회** | `SELECT` + `WHERE` + `ORDER BY` |
| 7 | **함수 활용** | `COALESCE` / `CASE WHEN` / 날짜 함수 |
| 8 | **JOIN** | **수강신청 교차 테이블** JOIN 조회 |

> ℹ️ 과정 기간 내 활용할 DB를 구성합니다 (**추후 DB Docker 예정**).

## 8-3. 환경 구성 — PostgreSQL 설치 (macOS 터미널)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
*(Homebrew 설치 — 이미 설치되어 있다면 skip)*

```bash
brew install postgresql@17
```

```bash
brew services start postgresql@17
```

```bash
psql postgres
```
*(접속 후 `postgres=#` 프롬프트 확인)*

```sql
-- 비밀번호 지정 (필수!)
ALTER USER (계정명) WITH PASSWORD '원하는비밀번호';
```

```
\q
```
*(psql 접속 종료)*

```bash
psql postgres -U (pc명 or 계정) -W
```
*(설정한 비밀번호로 접속)*

> ℹ️ **Docker 내 DB 설치는 이후 과정에서 진행 예정**

## 8-4. 제출물 (당일 제출 원칙)

| 산출물 | 요구사항 |
|--------|----------|
| **ERD** — 학사관리시스템 | ▪ **ERD 내 범례 추가할 것** (설명문)<br>▪ **각 연결관계가 잘 보이도록 할 것** (⚠️ **선 겹침 금지**) |
| **리포트** — PDF 제출 | ▪ 학사관리시스템 **요구사항** (설계 방향)<br>▪ **PostgreSQL 접속 결과 화면**<br>▪ **문항별 실습 결과** (SQL문 + 결과 화면 필수)<br>⚠️ **항목 누락 당 감점** |

---

# 🧭 Day 1 전체 흐름 한 장 요약

```
[근본 질문]  데이터 무결성·일관성  ⟷  확장성   ← DB 발전사 전체가 이 저울

  ├─ 무결성을 지키는 장치들
  │    ACID            원자성/일관성/격리성/지속성
  │      └ Durability → WAL (로그가 먼저!)  → 분산에선 Consensus (투표로 합의)
  │      └ Isolation  → 격리 수준 4단계
  │            RC(기본, PG·Oracle) / RR(기본, MySQL) / Serializable
  │            막는 것: Dirty Read → Non-Repeatable Read → Phantom Read
  │                                      (값 변함)         (개수 변함)
  │    제약조건        NOT NULL / DEFAULT / CHECK / FOREIGN KEY
  │    정규화          1NF(원자값) → 2NF(부분종속) → 3NF(이행종속) → BCNF
  │                     └ 막는 것: 삽입·삭제·갱신 이상
  │
  └─ 확장성을 얻는 대가
       NoSQL / 분산 DB → 일관성 일부 포기
       반정규화        → 중복 허용하고 JOIN 비용 절감


[설계 파이프라인]
  현실 세계
    ↓ 명사 추출, 관계 정의
  개념적 모델  (DBMS 독립)  → 산출물: ERD
    ↓ 테이블 매핑, PK/FK, 정규화
  논리적 모델  (DBMS 독립)  → 산출물: 논리 ERD, 데이터 사전
    ↓ 타입 결정, 인덱스, 파티셔닝, Lock 전략
  물리적 모델  (DBMS 의존)  → 산출물: DDL
    ↓
  CREATE DATABASE → CREATE SCHEMA → CREATE TABLE → INSERT → SELECT


[특수 케이스 2개 — 시험에 잘 나옴]
  약한 엔티티  독자 PK 없음 → 부모PK + 부분키 = 복합 PK + ON DELETE CASCADE
               예) OrderItem(OrderID, ItemNo), Dependent(EmpID, Name)
  N:M 관계     직접 구현 불가 → 교차 테이블 필수 + 복합 PK + 양방향 인덱스
               예) Student ─< Enrollment >─ Course
```

---

## 🎓 시험/면접 대비 핵심 문답

| 질문 | 답 |
|------|-----|
| **DB 발전사를 한 문장으로?** | 저장 방식의 변화가 아니라 **무결성·일관성 vs 확장성의 균형 싸움** |
| **ACID 4가지는?** | **A**tomicity(원자성) / **C**onsistency(일관성) / **I**solation(격리성) / **D**urability(지속성) |
| **MyISAM은 ACID를 지원하나?** | ❌ **Rollback 불가, FK 없음 → 사실상 미지원.** InnoDB만 완전 지원 |
| **WAL을 한 문장으로?** | **데이터 파일보다 로그를 먼저 써야** 장애 시 복구할 수 있다 — Durability의 구현 원리 |
| **WAL의 성능상 이점은?** | **순차 기록**으로 **랜덤 I/O를 최소화** |
| **WAL vs Consensus?** | WAL = **한 DB 안**의 안전장치 / Consensus = **여러 DB 노드**가 같은 결과를 보장하는 장치 |
| **대표 Consensus 알고리즘은?** | **Paxos**(이론), **Raft**(구현 단순, Aurora·etcd·CockroachDB), **Spanner**(Paxos + TrueTime) |
| **Non-Repeatable Read vs Phantom Read?** | 전자는 **"값"이 변함**, 후자는 **"개수"가 변함** (조건에 맞는 새 행이 생겨서) |
| **PostgreSQL / MySQL의 기본 격리 수준은?** | PostgreSQL·Oracle·SQL Server = **READ COMMITTED** / MySQL(InnoDB) = **REPEATABLE READ** |
| **표준상 RR은 Phantom을 막나?** | **원칙적으로 허용**하지만, InnoDB는 **Gap Lock/next-key lock**, PG는 **스냅샷**으로 실질적으로 막음 |
| **PK와 UK의 차이는?** | 둘 다 중복 불가. **PK는 NULL 불가 + 자동 인덱스**, **UK는 NULL 허용** |
| **ON DELETE CASCADE와 RESTRICT?** | CASCADE = 부모 삭제 시 **자식도 삭제** / RESTRICT = 자식이 있으면 **부모 삭제 차단** |
| **1NF / 2NF / 3NF를 한 줄씩?** | 1NF = **원자값**만 / 2NF = **부분 함수 종속** 제거 / 3NF = **이행적 종속** 제거 |
| **정규화의 부작용은?** | 테이블이 쪼개져 **JOIN 비용 증가** → 성능 고려 시 **반정규화** 도입 |
| **정규화가 막는 3가지 이상은?** | **삽입 이상 / 삭제 이상 / 갱신 이상** |
| **약한 엔티티란?** | 독자 PK가 없어 **부모 PK + 자신의 부분키로 복합 PK**를 구성하는 엔티티. `ON DELETE CASCADE` 필수 |
| **N:M은 왜 직접 구현이 안 되나?** | 관계형 모델에서 표현 불가 → 반드시 **교차(조인) 테이블** 필요. 교차 테이블엔 **추가 속성**도 넣을 수 있음 |
| **IE 표기법의 실선/점선 차이는?** | **실선 = 식별 관계**(FK가 자식 PK 일부, 부모 없이 존재 불가) / **점선 = 비식별 관계**(FK가 일반 컬럼) |
| **낙관적 vs 비관적 Lock?** | 낙관적 = **충돌 드물다 가정**, 종료 시 버전 비교 (읽기 위주) / 비관적 = **시작 시 Lock 획득** (은행 이체, 좌석 예매) |
| **멀티 테넌시 3패턴은?** | **Silo**(완전 독립 DB) / **Pool**(단일 DB + tenant_id) / **Bridge**(단일 DB + 스키마 분리, **PostgreSQL 권장**) |
| **금액 컬럼의 올바른 타입은?** | **`NUMERIC`/`DECIMAL`** — 부동소수점 오류 방지. `FLOAT` 쓰면 안 됨 |
| **글로벌 서비스의 시간 타입은?** | **`TIMESTAMPTZ`** (타임존 포함) 또는 **UTC 고정** |
| **NULL 치환 함수 중 표준은?** | **`COALESCE`** (모든 DBMS). `NVL`은 Oracle, `ISNULL`은 SQL Server 전용 |
| **SELECT의 논리적 실행 순서는?** | `FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT` |
| **WHERE에서 별칭을 못 쓰는 이유는?** | **`SELECT`가 `WHERE`보다 나중에 처리**되어, WHERE 시점엔 별칭이 아직 없음. **`ORDER BY`에서만 가능** |
| **`LIKE '%길%'`의 문제는?** | **인덱스를 못 씀**(prefix가 아니라서). 대용량이면 **전문검색 인덱스** 필요 |
| **`= NULL`이 안 되는 이유는?** | `NULL = NULL`은 **TRUE가 아니라 UNKNOWN** → 필터되지 않음. **`IS NULL`** 사용 |
| **TRUNCATE vs DELETE?** | TRUNCATE = 빠름·자동 커밋·트리거 미실행·WHERE 불가 / DELETE = 느림·**롤백 가능**·트리거 실행·WHERE 가능 |
| **운영 중 대용량 DDL 변경 도구는?** | MySQL **`pt-online-schema-change`** / PostgreSQL **`pg_repack`**<br>인덱스는 PG의 **`CREATE INDEX CONCURRENTLY`** |

---

## 🔗 Day 2 예고

Day 1에서 만든 학사관리 DB를 그대로 이어서 씁니다.

| Day 2 주제 | Day 1의 어느 부분에서 이어지나 |
|-----------|------------------------------|
| **9. Day 1 핵심 복습 & DBMS 생태계** | DDL/DML 정리 · DBMS vs DW vs Data Mining · MSA 연동(Kafka/Elasticsearch/Redis) |
| **10. SQL 중급 — 집계 & 그룹화** | 7장 SELECT의 `GROUP BY`/`HAVING` 심화 |
| **11~12. JOIN 알고리즘 & 종류** | 4장 N:M 교차 테이블을 실제로 조회 |
| **13. 서브쿼리 & 집합 연산자** | 7장 DML 확장 |
| **14. CTE · View · Materialized View** | — |
| **15. Window Function** | SQL:2003에서 도입된 `OVER(PARTITION BY ...)` |
| **16. 종합실습 – 2** | **종합실습 1 환경을 그대로 활용** (CampusHub 복합 쿼리) |

---

*본 문서는 SK AX의 컨텐츠 자산을 학습 목적으로 정리한 것으로, 무단 사용 및 불법 배포 시 법적 조치를 받을 수 있습니다.*
