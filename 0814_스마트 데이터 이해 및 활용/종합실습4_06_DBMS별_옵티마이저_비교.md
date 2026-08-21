# DBMS 엔진별 옵티마이저 비교 (Option)

조사 기준일: 2026-08-14  
비교 대상: PostgreSQL 17/18 문서, MySQL 8.4, Oracle AI Database 26, SQL Server 2025 문서

## 핵심 비교

| 구분 | PostgreSQL | MySQL | Oracle | SQL Server |
|---|---|---|---|---|
| 기본 방식 | 비용 기반 플래너 | 비용 기반 옵티마이저 | 비용 기반 옵티마이저(CBO) | 비용 기반 Query Optimizer |
| 대표 조인 | Nested Loop, Hash, Merge | Nested Loop/BKA, Hash | Nested Loop, Hash, Sort Merge | Nested Loops, Hash, Merge, Adaptive Join |
| 통계 | `ANALYZE`, 컬럼 통계, 확장 통계 | `ANALYZE TABLE`, 히스토그램 | `DBMS_STATS`, 히스토그램, 동적 통계 | 자동 통계, 다중 열 통계, Cardinality Estimator |
| 계획 적응 | prepared statement의 generic/custom plan, Memoize 등 | optimizer switch·hint·히스토그램 중심 | Adaptive Plan과 자동 재최적화 | Adaptive Join, Memory Grant Feedback, PSP/OPPO 등 IQP |
| 계획 확인 | `EXPLAIN (ANALYZE, BUFFERS)` | `EXPLAIN ANALYZE`, JSON/TREE | `DBMS_XPLAN.DISPLAY_CURSOR` | Actual Execution Plan, `SET STATISTICS IO/TIME` |
| 계획 제어 | `enable_*`, 비용 상수; 내장 힌트는 제한적 | `/*+ ... */`, `optimizer_switch`, index hint | 풍부한 `/*+ ... */`, SQL Plan Management | `OPTION (...)`, Query Store hint/plan forcing |

## 엔진별 특징

### PostgreSQL

- 가능한 접근 경로와 조인 순서를 비용으로 비교하고, Nested Loop·Hash·Merge Join 중 예상 비용이 가장 낮은 계획을 선택한다.
- 조인 수가 `geqo_threshold`를 넘으면 탐색 비용을 제한하기 위해 GEQO(유전 알고리즘)를 사용할 수 있다.
- `enable_hashjoin`, `enable_mergejoin`, `enable_nestloop`는 실습에서 계획을 비교할 때 유용하지만, 운영 튜닝의 우선순위는 정확한 통계와 적절한 인덱스다.
- 공식 문서: [Planner/Optimizer](https://www.postgresql.org/docs/17/planner-optimizer.html), [Query Planning 설정](https://www.postgresql.org/docs/current/runtime-config-query.html)

### MySQL 8.4

- InnoDB 통계와 히스토그램을 이용해 접근 경로와 조인 순서를 비용 기반으로 결정한다.
- BKA(Batched Key Access)는 인덱스 접근과 조인 버퍼를 결합한다. 기존 BNL은 Hash Join으로 대체되었다.
- `JOIN_ORDER`, `JOIN_PREFIX`, `JOIN_SUFFIX`, `BKA`, `BNL` 등의 옵티마이저 힌트와 `optimizer_switch`를 제공한다. MySQL 8.4의 `HASH_JOIN`/`NO_HASH_JOIN` 힌트는 문서상 효과가 없으므로 `BNL` 계열 제어를 확인해야 한다.
- 공식 문서: [Optimizer Hints](https://dev.mysql.com/doc/refman/8.4/en/optimizer-hints.html), [Execution Plan](https://dev.mysql.com/doc/refman/8.4/en/execution-plan-information.html), [BKA Join](https://dev.mysql.com/doc/refman/8.4/en/bnl-bka-optimization.html)

### Oracle AI Database 26

- CBO가 각 접근 경로와 조인 계획에 비용을 부여해 가장 낮은 비용을 선택한다.
- Adaptive Plan은 실행 중 관찰한 행 수를 기준으로 Nested Loop와 Hash Join 같은 미리 준비된 하위 계획 중 하나를 활성화할 수 있다.
- 힌트가 매우 풍부하지만 Oracle은 데이터·환경 변화로 힌트가 노후화될 수 있어 SQL Tuning Advisor, SQL Plan Management, SQL Performance Analyzer도 함께 사용할 것을 권장한다.
- 공식 문서: [Query Optimizer Concepts](https://docs.oracle.com/en/database/oracle/oracle-database/26/tgsql/query-optimizer-concepts.html), [Influencing the Optimizer](https://docs.oracle.com/en/database/oracle/oracle-database/26/tgsql/influencing-the-optimizer.html), [Optimizer Access Paths](https://docs.oracle.com/en/database/oracle/oracle-database/26/tgsql/optimizer-access-paths.html)

### SQL Server

- Nested Loops·Merge·Hash Join 외에 실행 시점의 실제 행 수에 따라 Hash와 Nested Loops 중 하나를 고르는 Adaptive Join을 지원한다.
- 실행계획 캐시와 Query Store를 통해 계획 재사용, 회귀 탐지, 계획 강제·힌트 적용을 지원한다.
- Intelligent Query Processing(IQP)은 Adaptive Join, Memory Grant Feedback, Parameter Sensitive Plan 최적화처럼 추정 오차나 매개변수 편향에 대응하는 기능군이다.
- 공식 문서: [Joins](https://learn.microsoft.com/en-us/sql/relational-databases/performance/joins?view=sql-server-ver17), [Query Processing Architecture](https://learn.microsoft.com/en-us/sql/relational-databases/query-processing-architecture-guide?view=sql-server-ver17), [Intelligent Query Processing](https://learn.microsoft.com/en-us/sql/relational-databases/performance/intelligent-query-processing?view=sql-server-ver17)

## 실무 결론

1. 네 엔진 모두 비용 기반이므로 통계가 부정확하면 좋은 SQL과 인덱스가 있어도 잘못된 계획을 선택할 수 있다.
2. NLJ는 작은 외부 입력과 인덱스 탐색, Hash Join은 큰 비정렬 동등 조인, Merge Join은 정렬된 큰 입력에 대체로 유리하다.
3. 힌트나 조인 강제는 재현 실험에는 유용하지만, 운영에서는 데이터 증가와 분포 변화에 취약하므로 마지막 수단으로 사용한다.
4. 실행계획의 예상 행 수와 실제 행 수 차이를 먼저 확인하고, 통계 → 조건식 → 인덱스 → SQL 구조 → 계획 강제 순서로 접근한다.

