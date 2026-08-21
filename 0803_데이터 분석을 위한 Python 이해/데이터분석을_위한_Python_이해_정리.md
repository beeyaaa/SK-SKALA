# 🐍 데이터 분석을 위한 Python 이해

> 📘 **출처** · `2) 데이터분석 및 AIOps_1. 데이터 분석을 위한 Python 이해_백정열.pdf` (320p)
> 🏫 SK AX / SKALA — AI의 서비스화 · 데이터분석 및 AIOps
> 🗓️ Day 1 (1~7장) + Day 2 (8~14장) 2일 과정

---

## 📑 목차

### Day 1
| # | 챕터 | 핵심 키워드 |
|---|---|---|
| 0 | [Python Summary](#0-python-summary) | 사전 복습 (변수·자료형·함수·클래스·예외) |
| 1 | [실행 구조와 개발 환경](#1-실행-구조와-개발-환경) | 인터프리터 · AST · 바이트코드 · PVM · venv |
| 2 | [자료구조와 컴프리헨션](#2-자료구조와-제어문-연산자-반복문-및-컴프리헨션) | list · dict · set · deque · Counter · 컴프리헨션 · 제너레이터 |
| — | [Practice 1](#-practice-1--자료구조--컴프리헨션) | 리스트+딕셔너리 필터링 / 심화 집계 |
| 3 | [함수 · 파일 · 예외 처리](#3-함수--파일--예외-처리) | functools · 데코레이터 · pathlib · CSV/JSON/Parquet · logging · .env |
| 4 | [타입 힌트와 데이터 모델링](#4-타입-힌트와-데이터-모델링) | 타입 힌트 · Union/Optional/Literal · Pydantic v2 · mypy |
| — | [Practice 2](#-practice-2--파일-io--예외-처리--pydantic) | 파일 I/O · 예외 · Pydantic 검증 파이프라인 |
| 5 | [코드 품질과 기초 테스트](#5-코드-품질과-기초-테스트) | Ruff · pytest · coverage · pre-commit · VS Code 디버거 |
| 6 | [비동기와 병렬 처리 입문](#6-비동기와-병렬-처리-입문) | asyncio · httpx · GIL · multiprocessing · cProfile |
| 7 | [Day 1 종합 실습](#-day-1-종합-실습--데이터-수집-미니-파이프라인) | 데이터 수집 미니 파이프라인 |

### Day 2
| # | 챕터 | 핵심 키워드 |
|---|---|---|
| 8 | [Pandas 2.x 실전](#8-pandas-2x-실전) | DataFrame · EDA · 결측치/이상치 · groupby · pivot · merge · CoW |
| 9 | [Polars + DuckDB](#9-polars--duckdb) | Lazy API · scan_csv · DuckDB SQL · Arrow |
| — | [Practice 3](#-practice-3--pandas--polars--duckdb-비교) | 세 도구 성능 비교 |
| 10 | [데이터 시각화](#10-데이터-시각화) | Matplotlib · Seaborn · Plotly Express · Altair |
| 11 | [기초 통계와 ML 파이프라인 연결](#11-기초-통계와-ml-파이프라인-연결) | 기술통계 · 가설검정 · CRISP-DM · sklearn Pipeline |
| — | [Practice 4](#-practice-4--시각화--통계검정--sklearn-pipeline) | 시각화 4종 · 통계 검정 · Pipeline |
| 12 | [분석 자동화와 파이프라인 설계](#12-분석-자동화와-파이프라인-설계) | schedule · Jinja2 · LLM API · ETL 원칙 |
| 13 | [분석 코드 구조화와 공유](#13-분석-코드-구조화와-공유) | Jupyter vs .py · 프로젝트 구조 · 모듈화 · GitHub |
| 14 | [Day 2 종합 실습](#-day-2-종합-실습--end2end-데이터-분석-프로젝트) | End2End 데이터 분석 프로젝트 |

---

# 0. Python Summary

> 💡 본 과정 시작 전 사전 복습 파트. 문법 자체보다 **"어디에 쓰이는가"** 를 짚고 넘어가는 구간입니다.

### Python이란

간결하고 가독성이 높은 문법을 가진 **인터프리터 기반** 프로그래밍 언어.

**특징**
- 문법이 쉽고 간결 → 초보자도 배우기 쉬움
- 인터프리터 언어 → 코드를 한 줄씩 실행하며 테스트 가능
- 다양한 라이브러리 → 데이터 분석 · AI · 웹 개발
- OOP 지원 / 멀티 패러다임(절차적·객체지향·함수형)
- 플랫폼 독립적 (Windows / Mac / Linux)

**활용 분야**

| 분야 | 대표 도구 |
|---|---|
| 웹 개발 | Django, Flask |
| 데이터 분석 | Pandas, NumPy, Matplotlib |
| AI/ML | TensorFlow, PyTorch, Scikit-Learn |
| 자동화 | 업무 자동화, 웹 스크래핑 |
| 게임 | Pygame |
| 네트워크 | socket 모듈 |

### ⚠️ Python이 약한 영역

> 🚫 **"인터프리터 + GIL"** 이 곧 한계가 되는 지점들

- **OS 및 저수준 시스템 프로그래밍** — 메모리 관리·하드웨어 직접 제어가 어려움
- **모바일 앱 네이티브 개발** (iOS/Android)
- **고성능 게임 개발** — CPU 사용량 ↑
- **실시간 시스템 및 하드웨어 제어** — GC로 인한 지연 가능성
- **블록체인 / 대형 Enterprise(ERP) 시스템**
- **multithreading 기반 고성능 애플리케이션** — 멀티프로세스는 가능하나 멀티스레딩 성능은 낮음

### 문법 요약 체크리스트

- [x] 변수 할당은 `=`, 정수는 메모리가 허용하는 한 **크기 제한 없음**
- [x] 실수 ↔ 정수 연산 시 **형 변환(정수→실수)** 발생
- [x] 연산자: `+ - * /` / 몫 `//` / 나머지 `%` / 제곱 `**`
- [x] 문자열은 **불변(immutable)**, 리스트는 **가변(mutable)**
- [x] 문자열 인덱싱은 0부터 — `aa[:5]`, `bb[3:]`
- [x] 리스트끼리 `+` 는 이어붙이기, `insert/append/remove/sort` 사용
- [x] 튜플은 소괄호 `()`, 값 변경 불가 → **변경되면 안 되는 데이터**에 사용
- [x] dict는 `{key: value}` — 키 중복 불가, 값 중복 가능, **3.7+ 삽입 순서 보장**
- [x] set은 중복 불가·순서 없음 — 인덱스 접근 불가, 집합 연산에 사용
- [x] Bool 거짓값: `0`, 빈 리스트/튜플/사전, `None`
- [x] 파일: `open()` / `close()`, 모드 `r` `w` `a`, `read()` `readline()` `readlines()`
- [x] 클래스 = 붕어빵 틀, 인스턴스 = 붕어빵

---

# 1. 실행 구조와 개발 환경

> 🎯 **왜 배우나** — 패키지 설치 오류 해결, 성능 최적화의 출발점, 에러 메시지 독해력, 후속 과목(LangChain·RAG·AI Agent) 연결

## 1-1. Python이 데이터 분석 표준 언어인 이유

| 이유 | 내용 |
|---|---|
| 인터프리터 언어 | 한 줄씩 즉시 실행, REPL 대화형 탐색이 분석에 최적 |
| 방대한 생태계 | NumPy · Pandas · scikit-learn · Polars · DuckDB 전부 `pip` |
| 2026 AI/ML 표준 | TensorFlow · PyTorch · LangChain · RAG 파이프라인까지 Python 중심 |
| 읽기 쉬운 문법 | 들여쓰기 기반 블록 구조 — 비전공자도 읽을 수 있음 |

## 1-2. 실행 구조 — 소스코드에서 결과까지

```
소스코드(.py) → 파서(Parser) → AST → 바이트코드(.pyc) → PVM 실행 → 결과
```

> 💡 **핵심** — CPython은 소스를 직접 기계어로 변환하지 않고 **바이트코드를 거친다.** 그래서 이식성과 재사용성이 확보되며, `__pycache__`가 생성된다.

**즉, Python은 순수 인터프리터가 아니라 "컴파일 + 인터프리트" 하이브리드 방식.**

### AST (Abstract Syntax Tree)

코드의 의미/구조를 컴퓨터가 이해하기 쉽게 **문법적 핵심 요소만 남겨 추상화한 트리 자료구조.**

| 용도 | 설명 |
|---|---|
| 코드 분석 및 이해 | 컴파일러·인터프리터가 코드 의미 분석 및 오류 검증 |
| 코드 변환 및 최적화 | 트리 형태로 조작 → 최적화, 다른 버전 문법으로 변환 |
| 개발도구 활용 | 린터(문법 오류) · 포매터(스타일 통일) · 트랜스파일러(문법 변환) |

```python
import ast, dis

# AST 분석
tree = ast.parse('x = a + b')
print(ast.dump(tree, indent=2))

# 바이트코드 분석
def add(x, y): return x + y
dis.dis(add)
# LOAD_FAST 0 (x)
# LOAD_FAST 1 (y)
# BINARY_OP 0 (+)
# RETURN_VALUE
```

> 📌 `dis` 모듈로 **컴프리헨션이 for 루프보다 빠른 이유**를 바이트코드 수준에서 확인할 수 있다.

### 바이트코드 & PVM

**바이트코드**
- 파싱 후 생성되는 중간 표현(Intermediate Representation)
- `.pyc` 파일에 저장 → 재사용으로 실행 속도 향상
- 추상화된 명령어라 **OS 독립적**

```bash
python -m py_compile hello.py
# → __pycache__/hello.cpython-311.pyc 생성
```

**PVM (Python Virtual Machine)**
- 바이트코드를 하나씩 읽어 해석·실행하는 엔진
- **스택 기반** 가상 머신
- 바이트코드 = `opcode + 인자(argument)` 구조

## 1-3. 메모리 모델

| 구분 | 내용 |
|---|---|
| **Stack** | 함수 호출, 지역 변수 |
| **Heap** | 객체, 클래스 인스턴스, 리스트 |
| **자동 해제** | Reference Counting + Garbage Collector |

**Python 객체 구조** — 모든 값은 객체이며 메타정보를 포함
- `type` (자료형 정보)
- `refcount` (참조 수)
- `value` (데이터 값)

## 1-4. macOS + VS Code 개발 환경 구성

> ⚙️ 이 환경이 **2일간 모든 실습의 기반**입니다.

```bash
# 1. Python 3.11 설치 확인 (Homebrew)
brew install python@3.11
python3.11 --version

# 2. 프로젝트 폴더 생성 + venv
mkdir data-project && cd data-project
python3.11 -m venv .venv
source .venv/bin/activate     # 프롬프트가 (.venv) 로 변경되는지 확인

# 3. 분석 패키지 설치
pip install -r requirements.txt
```

> ⚠️ `.venv/` 는 **.gitignore에 추가**, `requirements.txt` 는 **반드시 커밋**

---

# 2. 자료구조와 제어문, 연산자, 반복문 및 컴프리헨션

## 2-1. 제어문

```python
if condition1:
    ...
elif condition2:
    ...
else:
    ...
```

- 조건식은 bool 평가 가능 객체로 자동 변환
- `None`, `0`, `""`, `[]`, `{}` 는 모두 **False**
- 삼항 연산: `status = "성인" if age >= 18 else "미성년자"`

### 🔍 Short-circuit Evaluation (단락 평가)

| 연산자 | 동작 |
|---|---|
| `and` | 왼쪽이 False ⇒ 전체 False (오른쪽 **생략**) |
| `or` | 왼쪽이 True ⇒ 전체 True (오른쪽 **생략**) |

```python
def left():  print("left");  return False
def right(): print("right"); return True

print(left() and right())   # 'right' 출력 안 됨 — 호출조차 안 됨
```

**실전 활용**
```python
if user and user.is_active:      # user가 None이면 AttributeError 방지
if cheap_check() and expensive_check():   # 싼 검사를 앞에 → 성능 최적화
value = config.get("key") or "default"    # None 방지 / 디폴트값
```

> ⚠️ **주의** — `and`/`or` 는 bool이 아니라 **원래 값**을 반환한다.
> `[] or [1]` → `[1]` / `[] and [1]` → `[]`

## 2-2. 연산자

- `a == b` 는 **값** 비교, `a is b` 는 **객체 ID** 비교
- 정수는 내부적으로 immutable → 연산 시 **새 객체 생성**

```python
a = 10; b = a
print(a is b)   # True
a += 1
print(a is b)   # False (새 객체)
```

## 2-3. 반복문

```python
for 변수 in iterable:   # list, tuple, str, range, zip, enumerate
    ...
while 조건:
    ...
```

- `break` / `continue` / **`else`** (break 없이 정상 종료 시 실행)
- `range(start, stop, step)`, `enumerate(iterable)`

```python
for i in range(5):
    if i == 3: break
    print(i)
else:
    print("정상 종료")   # break 없이 끝나야 실행
```

## 2-4. 컴프리헨션

```python
# 리스트
squares = [x*x for x in range(10) if x % 2 == 0]
pairs   = [(x, y) for x in range(1, 3) for y in range(3, 5)]
result  = ["짝수" if i % 2 == 0 else "홀수" for i in range(1, 6)]

# 딕셔너리
squares      = {i: i**2 for i in range(1, 6)}
even_squares = {i: i**2 for i in range(1, 6) if i % 2 == 0}
person       = {k: v for k, v in zip(keys, values)}

# 집합
unique_squares = {num**2 for num in numbers}
```

## 2-5. 기본 자료구조 정리

| 자료형 | 순서 | 중복 | 가변 | 특징 | 접근 |
|---|:---:|:---:|:---:|---|:---:|
| **list** | O | O | O | 동적 배열, 인덱싱/슬라이싱 | O(1) |
| **tuple** | O | O | X | 해시 가능 → dict 키·set 요소 / 메모리 절약 | O(1) |
| **set** | X | X | O | 해시 테이블, 합집합 `\|` 교집합 `&` 차집합 `-` | O(1) |
| **dict** | O* | 키X | O | 해시 테이블, 3.7+ 삽입순서 보장 | O(1) |
| **deque** | O | O | O | 양방향 삽입/삭제 O(1) | O(n) |
| **defaultdict** | O* | 키X | O | 없는 키 접근 시 기본값 자동 생성 | O(1) |
| **Counter** | O | O | O | 빈도 계산 특화 | O(1) |

> ℹ️ O(1)은 평균이며, 해시 충돌·리사이징 시 최악의 경우 O(n)까지 갈 수 있음

### 💥 [Why?] 리스트 앞쪽 삽입/삭제가 O(n)인 이유

리스트는 **동적 배열(Dynamic Array)** 이므로 끝에서의 조작은 빠르지만 앞에서 조작하면 전체를 밀어야 함.

```python
my_list.append(4)      # O(1) — 끝에 추가
my_list.pop()          # O(1) — 끝 제거
my_list.insert(0, 0)   # O(n) — 맨 앞 삽입
my_list.pop(0)         # O(n) — 맨 앞 제거
```

→ 그래서 **deque**를 쓴다.

```python
from collections import deque
dq = deque([1, 2, 3])
dq.append(4)      # O(1)
dq.appendleft(0)  # O(1)
dq.pop()          # O(1)
dq.popleft()      # O(1)
```

> 🧠 **deque의 실체** — 단순 Doubly Linked List가 아니라 **"linked list of arrays"**.
> 고정 크기 배열 블록들이 양방향으로 연결된 C 구현체 → cache-friendly 하면서도 O(1) 보장.

## 2-6. collections & 고급 자료구조

```python
from collections import Counter, defaultdict, deque, OrderedDict

# Counter — 빈도 계산 (통계, NLP)
cnt = Counter(['a','b','a','c','b','a'])
cnt.most_common(2)      # [('a', 3), ('b', 2)]

# defaultdict — 그룹핑/카운팅
dd = defaultdict(list)
dd['a'].append(1)       # KeyError 없이 자동 생성 → {'a': [1]}

word_count = defaultdict(int)
word_count["apple"] += 1
```

```python
import heapq      # 우선순위 큐 — 다익스트라, 작업 스케줄링
heapq.heappush(heap, 5)
heapq.heappop(heap)          # 가장 작은 값
heapq.heappush(max_heap, -5) # 최대 힙은 부호 반전

import bisect     # 정렬된 리스트 관리 (이진 탐색)
bisect.bisect_left(numbers, 6)   # 들어갈 위치
bisect.insort(numbers, 6)        # 삽입 후 자동 정렬
```

**O(log N)** — 데이터가 커져도 연산 횟수가 크게 증가하지 않는 효율적 알고리즘 (이진 탐색)

## 2-7. zip() / zip_longest()

```python
zipped = zip(names, ages)                  # 짧은 쪽 기준으로 잘림
person = dict(zip(keys, values))           # dict 생성
names, ages = zip(*pairs)                  # 언패킹

from itertools import zip_longest
zip_longest(a, b, fillvalue="없음")         # 긴 쪽 기준 + 빈 값 채우기
```

| | zip() | zip_longest() |
|---|---|---|
| 기준 | 가장 **짧은** 반복자 | 가장 **긴** 반복자 |
| 남는 값 | 버림 | `fillvalue`로 채움 |

## 2-8. 슬라이싱 & 포맷팅

```python
text = "Hello, Python!"
text[0:5]    # 'Hello'    (끝 인덱스 미포함)
text[:5]     # 'Hello'
text[7:]     # 'Python!'
text[::2]    # 'Hlo yhn'  (2칸씩)
text[::-1]   # '!nohtyP ,olleH' (뒤집기)
```

```python
# % 연산자 → format() → f-string (가장 현대적)
print(f"이름: {name}, 나이: {age}")
print(f"5 + 3 = {a + b}")        # 연산 가능
print(f"파이 값: {pi:.2f}")       # 소수점 지정
print(f"[{text:>10}]")           # 오른쪽 정렬
print(f"[{text:<10}]")           # 왼쪽 정렬
print(f"[{text:^10}]")           # 가운데 정렬
```

## 2-9. 제너레이터 — 대용량 메모리 효율 처리

> 🔑 **CSV 수백만 행 스트리밍 처리의 핵심**

```python
def read_rows(path):
    with open(path) as f:
        next(f)                       # 헤더 스킵
        for line in f:
            yield line.strip().split(',')

for row in read_rows('large.csv'):    # 한 번에 한 행씩
    process(row)

total = sum(float(r[2]) for r in read_rows('f.csv'))   # generator expression
```

**메모리 비교**
```python
lst = [x**2 for x in range(10_000_000)]   # 400MB+
gen = (x**2 for x in range(10_000_000))   # ~120 byte
```

| | List | Generator |
|---|---|---|
| 메모리 | 전체 사용 | 필요 시 생성 (lazy) |
| 문법 | `[x*x for x in ...]` | `(x*x for x in ...)` |

## 2-10. dataclass · TypedDict

```python
from dataclasses import dataclass, field
from typing import TypedDict, Optional

@dataclass                      # __init__·__repr__·__eq__ 자동 생성
class SalesRecord:
    date: str
    region: str
    amount: float
    tags: list = field(default_factory=list)

class Row(TypedDict):           # dict에 타입 힌트 추가
    region: str
    sales: float
    category: Optional[str]
```

## 🎯 자료구조가 데이터 분석 코드의 기반인 이유

| 관점 | 내용 |
|---|---|
| **DataFrame은 dict의 확장** | Pandas 내부는 `dict[컬럼명 → numpy 배열]`. dict를 알면 Pandas 동작 원리가 보인다 |
| **컴프리헨션 = 빠른 전처리** | 필터링·변환을 한 줄로. 간단한 변환은 `apply`보다 빠를 때도 있음 |
| **Counter로 value_counts 대체** | Pandas 없이도 빈도 집계 가능 → 의존성 최소화 |
| **제너레이터 = 스트리밍 파이프라인** | 수백만 행을 한꺼번에 올리지 않고 행 단위 처리 → 메모리 한계 극복 |

---

## 🧪 Practice 1 — 자료구조 · 컴프리헨션

### 기본 실습: 리스트 + 딕셔너리 기반 데이터 필터링기

```python
employees = [
    {"name": "Alice",   "department": "Engineering", "age": 30, "salary": 85000},
    {"name": "Bob",     "department": "Marketing",   "age": 25, "salary": 60000},
    {"name": "Charlie", "department": "Engineering", "age": 35, "salary": 95000},
    {"name": "David",   "department": "HR",          "age": 45, "salary": 70000},
    {"name": "Eve",     "department": "Engineering", "age": 28, "salary": 78000},
]
```

| # | 시나리오 |
|---|---|
| 1 | 부서가 "Engineering"이고 salary ≥ 80000인 직원 **이름만** 리스트로 출력 |
| 2 | 30세 이상 직원의 이름·부서를 **튜플 리스트**로 출력 |
| 3 | salary **내림차순 정렬** 후 상위 3명의 이름·급여 출력 |
| 4 | **부서별 평균 급여** 출력 |

<details>
<summary>💡 예시 답안</summary>

```python
# 1
eng_high_salary = [emp["name"] for emp in employees
                   if emp["department"] == "Engineering" and emp["salary"] >= 80000]
# ['Alice', 'Charlie']

# 2
over_30 = [(emp["name"], emp["department"]) for emp in employees if emp["age"] >= 30]
# [('Alice', 'Engineering'), ('Charlie', 'Engineering'), ('David', 'HR')]

# 3
sorted_by_salary = sorted(employees, key=lambda x: x["salary"], reverse=True)
top3 = [(emp["name"], emp["salary"]) for emp in sorted_by_salary[:3]]
# [('Charlie', 95000), ('Alice', 85000), ('Eve', 78000)]
```
</details>

### 심화 실습: 자료구조 집계 · 컴프리헨션 · 제너레이터

> 📂 `Python_Practice1_Data.json` (Sales) 활용

1. **리스트/딕셔너리 컴프리헨션** — `amount ≥ 1000` 필터링 + 지역별 총매출 dict 계산
2. **Counter + defaultdict** — 지역별 거래 건수(Counter), 카테고리별 amount 리스트(defaultdict)
3. **제너레이터 메모리 비교** — `amount > 1000` 행만 yield, 리스트 버전과 `sys.getsizeof` 비교
4. **종합** — month·category 기준 그룹핑 총매출 dict 완성

**✅ Checkpoint / ❌ 감점**

| Checkpoint | 감점 대상 |
|---|---|
| `region_total` 값 정확 (assert 통과) | 컴프리헨션 대신 for 루프만 사용 **(-2)** |
| `Counter.most_common()` 순서 정확 | defaultdict 대신 `if key not in dict` 패턴 **(-1)** |
| generator `sys.getsizeof` < list 확인 | 제너레이터를 list로 변환해 비교 **(-2)** |
| top3 금액 내림차순 정렬 정확 | Counter 대신 직접 루프 카운팅 **(-1)** |

### 📋 공통 평가 기준 (총 100점)

> 제출 형식: `캠퍼스명_반_이름.py`

| 항목 | 배점 | 내용 |
|---|:---:|---|
| Code의 Comm. | 20 | 프로그램 전체 설명·변경내역(머리말), 함수/기능 설명(중간) |
| 코드 간결성 | 35 | 불필요한 반복 지양 |
| 오류/예외 처리 | 35 | 간단한 코드라도 예외 처리 반영 |
| 납기 | 10 | 1시간 내 제출 완료 |

---

# 3. 함수 · 파일 · 예외 처리

## 3-1. 함수 기초

```python
def 함수이름(매개변수):
    return 결과

def introduce(name, age=20):     # 기본값 인자는 반드시 뒤쪽에
    print(f"이름: {name}, 나이: {age}")
```

> ⚠️ `def wrong(age=20, name)` → 오류. **기본값 있는 인자는 항상 마지막**

## 3-2. 가변 인자 — *args, **kwargs

```python
def mix_example(a, b, *args, **kwargs):
    print(f"a: {a}, b: {b}")
    print(f"args: {args}")      # 튜플
    print(f"kwargs: {kwargs}")  # 딕셔너리

mix_example(1, 2, 3, 4, 5, name="철수", age=30)
# a: 1, b: 2 / args: (3, 4, 5) / kwargs: {'name': '철수', 'age': 30}
```

> 📌 **순서 고정** — 일반 인자 → `*args` → `**kwargs`

## 3-3. 일급 객체 · 람다 · 고차함수 · 클로저

**Python의 함수는 일급 객체(First-class Object)** — 변수 할당, 인자 전달, 리턴값 사용 가능

```python
f = add                          # 변수에 할당
def operate(func, x, y): return func(x, y)   # 인자로 전달

add = lambda x, y: x + y         # 람다
students.sort(key=lambda x: x[1])
list(map(lambda x: x**2, numbers))
list(filter(lambda x: x % 2 == 0, numbers))
reduce(lambda x, y: x + y, numbers)
```

**클로저(Closure)** — 함수가 자신이 선언된 환경을 기억하는 구조

```python
def multiplier(factor):
    def multiply(x):
        return x * factor      # 외부 변수 factor를 기억
    return multiply

double = multiplier(2)
double(10)   # 20
```

**functools.partial** — 인자를 고정해 새 함수 생성

```python
from functools import partial
double2 = partial(scale, factor=2)
list(map(double2, [1,2,3,4]))   # [2,4,6,8]
```

## 3-4. 제너레이터와 yield

```python
def countdown(n):
    while n > 0:
        yield n         # 중단 상태를 저장하고 다음 호출 시 이어서 실행
        n -= 1
```

## 3-5. 모듈과 표준 라이브러리

```python
import math
from math import sqrt, pi
import numpy as np           # 별칭
from math import *           # 권장하지 않음
```

주요 표준 라이브러리: `math` · `time` · `re` · `csv` · `json` · `os` · `pathlib` · `logging` · `collections` · `itertools` · `functools`

## 3-6. 파일 I/O

```python
# 기본
with open("example.txt", "r") as file:     # 자동 닫힘 (컨텍스트 매니저)
    content = file.read()

file.readline()    # 한 줄
file.readlines()   # 전체 줄을 리스트로
```

**CSV**
```python
import csv
with open("data.csv", "r", encoding="utf-8") as f:
    for row in csv.reader(f):
        print(row)

with open("new.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["이름", "나이", "도시"])
```

**JSON**
```python
import json
json.dump(data, file, ensure_ascii=False, indent=4)   # 저장 (한글 깨짐 방지 필수!)
data = json.load(file)                                # 로딩
```

**실전 패턴 — pathlib + Parquet**
```python
from pathlib import Path
import json, csv, pandas as pd

data_dir = Path('data')                        # macOS 경로 처리 표준

with open(data_dir/'sales.csv') as f:
    rows = list(csv.DictReader(f))             # 헤더를 키로 읽기

df = pd.read_parquet(data_dir/'sales.parquet') # 컬럼형 포맷, CSV보다 10× 빠름
df.to_parquet(data_dir/'out.parquet')
```

## 3-7. 데코레이터

> 함수를 인자로 받아 새로운 함수로 반환하고, 기존 함수를 **수정 없이 확장**하는 방법

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("함수 실행 전")
        result = func(*args, **kwargs)
        print("함수 실행 후")
        return result
    return wrapper

@my_decorator
def add(a, b):
    return a + b
```

**실용 예제 — @timer / @require_login**
```python
import time
def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"실행 시간: {time.time() - start:.4f}초")
        return result
    return wrapper
```

### 데코레이터 체이닝

```python
@decorator1
@decorator2
def say_hello():
    print("안녕하세요!")
```

> 📦 **택배박스 비유** — decorator1(택배박스) 열고 → decorator2(물건포장) 열고 → say_hello(물건 확인) → decorator2 닫고 → decorator1 닫기

### ⚠️ functools.wraps의 필요성

데코레이터를 쓰면 원래 함수의 `__name__`, `__doc__` 이 **wrapper로 바뀌어 사라진다.**

```python
import functools

def decorator(func):
    @functools.wraps(func)     # ← 원래 함수 메타데이터 보존
    def wrapper():
        return func()
    return wrapper

print(say_hello.__name__)   # say_hello (유지됨)
```

### 🤔 왜 데코레이터와 클로저를 배우나?

| 영역 | 활용 |
|---|---|
| **FastAPI** | `@app.get("/items/{id}")` — 라우팅 구조 자체가 데코레이터 기반 |
| **LLM** | 입력 클렌징·토큰화·전처리를 `@clean_input` 등으로 모듈화 |
| **RAG** | `retriever(collection)` 클로저로 vector store 상태 유지 (FAISS, Chroma, pgvector) |
| **AI Agent** | 각 Step(검색·추론·요약)마다 `@log_agent_action` 으로 추적/로깅 |

**분석 파이프라인 실전 데코레이터**
```python
from functools import wraps, lru_cache

@timer                          # 실행 시간 측정
@retry                          # 실패 시 재시도 (API 수집 필수)
@lru_cache(maxsize=128)         # 동일 입력 결과 캐싱
def expensive_stats(key): ...
```

## 3-8. 예외 처리

```python
try:
    num = int(input("숫자를 입력하세요: "))
    result = 10 / num
except ValueError:
    print("숫자만 입력해주세요!")
except ZeroDivisionError:
    print("0으로 나눌 수 없습니다!")
except Exception as e:          # 모든 예외
    print("예외 발생:", e)
finally:
    print("프로그램 종료")        # 항상 실행
```

**사용자 정의 예외**
```python
class CustomError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return f"CustomError: {self.message}"

raise ValueError("나이는 0 이상이어야 합니다.")
```

**파이프라인 안정성 패턴**
```python
class DataValidationError(ValueError):
    def __init__(self, col, val):
        super().__init__(f'{col}={val} 검증 실패')

def safe_load(path):
    try:
        df = pd.read_parquet(path)
        if df.empty: raise DataValidationError('rows', '0')
        return df
    except FileNotFoundError:
        logger.error(f'파일 없음: {path}'); return None
    except DataValidationError as e:
        logger.warning(str(e)); return None
    finally:
        logger.info(f'로딩 시도: {path}')    # 파일/연결 반드시 닫기
```

## 3-9. logging

> 🚫 **print()의 한계** — 출력 레벨 구분 불가, 로그 관리 안 됨, 실 서비스 부적절

| 레벨 | 의미 |
|---|---|
| `DEBUG` | 상세 정보 (디버깅용) |
| `INFO` | 정상 동작 정보 |
| `WARNING` | 경고, 문제가 될 수 있는 상황 |
| `ERROR` | 오류 발생 (실행은 계속) |
| `CRITICAL` | 치명적 오류 (서비스 중단 가능성) |

**실무 요구사항** — 콘솔엔 INFO 이상, 파일엔 DEBUG까지, 매일 분리 저장, 에러는 별도 파일

```
                    [Logger]
                   /        \
      [ConsoleHandler]    [FileHandler(app.log)]   → DEBUG 이상 저장
        INFO 이상 출력      [FileHandler(error.log)] → ERROR 이상만 저장
```

```python
import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger('pipeline')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()                  # 콘솔: INFO 이상
ch.setLevel(logging.INFO)

fh = TimedRotatingFileHandler(                # 파일: 날짜별 회전
    'logs/pipeline.log', when='midnight',
    backupCount=7, encoding='utf-8')
fh.setLevel(logging.DEBUG)

fmt = logging.Formatter('%(asctime)s|%(levelname)s|%(message)s')
```

## 3-10. .env 환경변수

| 이유 | 내용 |
|---|---|
| **보안** | DB 비밀번호·API 키 하드코딩 금지 (GitHub 노출 사고) |
| **이식성** | 운영/개발/로컬 환경별 설정을 손쉽게 전환 |
| **재현성** | `.env.example`만 공유하면 동일 환경 구성 가능 |

```bash
# .env
DEBUG=True
DB_HOST=localhost
DB_USER=myuser
DB_PASS=mypassword
```

```python
from dotenv import load_dotenv    # pip install python-dotenv
import os

load_dotenv()
api_key = os.getenv('API_KEY')
env = os.getenv('ENV', 'development')   # 기본값 지정
```

> 🔒 **.gitignore 필수 항목** — `.env`, `.env.local`, `.env.production`
> 보안 강화: dotenv-vault 암호화 / GitHub Actions Secrets / `.env.dev`·`.env.prod` 분리

---

# 4. 타입 힌트와 데이터 모델링

## 4-1. 기본 타입 힌트

> 💡 런타임에는 **영향 없음.** 에디터 자동완성과 정적 검사 도구의 오류 탐지에 도움.

```python
def add(x: int, y: int) -> int:
    return x + y

def compute_avg(values: list[float]) -> float: ...
def lookup(d: dict[str, Any], key: str, default: float = 0.0) -> float: ...

# 3.10+ 문법
def parse(val: str | int | None) -> str: ...
```

## 4-2. Optional · Union · Any · Literal

| 표기 | 의미 |
|---|---|
| `Optional[X]` | `Union[X, None]` 과 동일 — **결측치 표현** |
| `Union[X, Y]` | 여러 타입 중 하나 (3.10+: `X \| Y`) |
| `Any` | 모든 타입 허용 — **비추천** (타입 체크 포기와 동일) |
| `Literal["a","b"]` | 정해진 값만 허용 — enum 대안 |
| `Callable[[Arg], Ret]` | 함수 시그니처 지정 |

```python
def fill_strategy(method: Literal['mean','median','drop']) -> None: ...
turn("up")   # ❌ mypy 오류

def apply_fn(data: list[float], fn: Callable[[float], float]) -> list[float]:
    return [fn(x) for x in data]
```

## 4-3. Generic · Protocol

**Generic** — 타입을 파라미터처럼 (Java/C++ 템플릿 개념)
```python
from typing import TypeVar, Generic, List
T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self): self._items: List[T] = []
    def push(self, item: T) -> None: self._items.append(item)
    def pop(self) -> T: return self._items.pop()

s_int = Stack[int]()   # 정수 전용 Stack
```
→ 재사용성 + 정적 타입 안전성 + IDE 자동완성 품질 향상

**Protocol** — 상속 없이 인터페이스 기반 타입 체크 (Duck Typing 정적 검사)
```python
from typing import Protocol

class SupportsWrite(Protocol):
    def write(self, s: str) -> None: ...

class FileLike:                    # Protocol 상속 안 해도 OK
    def write(self, s: str) -> None: print(f"Writing: {s}")

write_hello(FileLike())            # write()가 있으므로 통과
```

## 4-4. mypy — 정적 타입 검사

```bash
pip install mypy
mypy test.py
mypy src/
mypy --config-file mypy.ini
```

```ini
[mypy]
python_version = 3.11
strict = True                      # 가장 강력한 검사
disallow_untyped_defs = True       # 모든 함수에 타입 힌트 강제
ignore_missing_imports = True
```

> 🔍 VS Code **Pylance** 로 저장할 때마다 실시간 검사 → 데이터 분석 코드의 **컬럼 타입 오류·결측치 처리 누락을 사전 차단**

## 4-5. Pydantic v2 — 데이터 검증과 직렬화

```python
from pydantic import BaseModel, Field
from typing import Optional

class SalesRecord(BaseModel):
    date: str
    region: str
    amount: float = Field(gt=0, description='양수')
    category: Optional[str] = None

r = SalesRecord(**{'date':'2024', 'region':'서울', 'amount':1500})
r.model_dump()                     # 객체 → dict/JSON

try:
    SalesRecord(date='', region='서울', amount=-100)
except ValidationError as e:
    print(e)                       # 어느 필드가 왜 틀렸는지 상세 출력
```

| 기능 | 설명 |
|---|---|
| `BaseModel` | 스키마 정의 + 자동 검증 |
| `Field` | `gt/lt/ge/le/regex/description` 제약 |
| `model_validate()` | dict → 객체 |
| `model_dump()` | 객체 → dict/JSON |
| `model_json_schema()` | OpenAPI 스키마 자동 생성 |

**분석 파이프라인 검증 패턴**
```python
valid, errors = [], []
with open('sales.csv') as f:
    for i, row in enumerate(csv.DictReader(f)):
        try:
            valid.append(Record(**row))
        except ValidationError as e:
            errors.append({'row': i, 'error': str(e)})

print(f'유효: {len(valid)}건, 오류: {len(errors)}건')
```

## 🎯 타입 시스템이 데이터 분석 코드를 바꾸는 이유

- **컬럼명 오타 사전 차단** — `amount` vs `Amount`, 수백만 행 처리 후 발견보다 낫다
- **팀 협업 계약서** — 함수 시그니처에 타입이 있으면 잘못된 인자를 전달하기 어려움
- **IDE 자동완성 품질 향상** — Pylance가 정확한 자동완성과 오류 하이라이팅 제공
- **후속 과목 직접 연결** — FastAPI·SpringBoot 연동 시 Pydantic BaseModel이 JSON 스키마 역할

---

## 🧪 Practice 2 — 파일 I/O · 예외 처리 · Pydantic

> 📂 `Python_Practice1_Data.json` 활용

| # | 과제 |
|---|---|
| 1 | **예외 처리 + 파일 읽기** — `safe_load_csv()`: 파일 없으면 `None` 반환 + `logger.error`, 성공 시 dict 리스트 반환 + `logger.info`, `finally`에서 '로딩 종료' 출력 |
| 2 | **Pydantic v2 스키마** — `SalesRecord`: month·region 비어있으면 안 됨 / amount > 0 / category 선택 |
| 3 | **검증 파이프라인** — raw_data 순회, 성공→`valid`, 실패→`errors({row, error})` |
| 4 | **결과 저장 + 재로딩** — valid는 CSV, errors는 JSON으로 저장 후 다시 읽어 건수 검증 |

**✅ Checkpoint / ❌ 감점**

| Checkpoint | 감점 대상 |
|---|---|
| `safe_load_csv` 동작 + assert None 통과 | try-except 없이 파일 읽기 **(-3)** |
| ValidationError 발생 시 오류 내용 출력 | finally 블록 누락 **(-1)** |
| valid 4건 / errors 3건 assert 통과 | ValidationError 대신 Exception **(-1)** |
| 재로딩 후 `len(reloaded)==4` 통과 | `model_dump()` 대신 dict 직접 구성 **(-1)** |
| | `json.dump ensure_ascii=False` 미설정 (한글 깨짐) **(-1)** |

---

# 5. 코드 품질과 기초 테스트

## 5-1. 디버깅

```python
# print → logging
logging.basicConfig(level=logging.DEBUG)
logging.debug("디버깅 메시지")

# traceback
import traceback
traceback.print_exc()          # 전체 오류 정보

# pdb
import pdb
pdb.set_trace()                # 여기서 실행 정지

# assert
assert b != 0, "b는 0이 될 수 없습니다!"
```

린터: `flake8` / `pylint`

## 5-2. 프로젝트 디렉토리 구조

```
my_project/
├── src/                        # 핵심 로직
│   └── mymodule/
│       ├── __init__.py
│       └── core.py
├── tests/                      # 테스트
│   └── test_core.py
├── .github/workflows/ci.yml    # GitHub Actions
├── .flake8                     # 스타일 검사 설정
├── .pre-commit-config.yaml     # Git pre-commit 설정
├── pyproject.toml              # black·mypy 공통 설정
├── requirements.txt
└── README.md
```

## 5-3. pytest — 테스트 자동화

**기본 동작 규칙**

| 항목 | 규칙 |
|---|---|
| 파일 이름 | `test_*.py` 또는 `*_test.py` |
| 함수 이름 | `test_` 로 시작 |
| 탐색 범위 | 실행 위치 기준 하위 재귀 전체 |
| 예외 | `conftest.py` 는 hook용으로 자동 탐지 |

```bash
pytest                              # 전체
pytest tests/                       # 특정 디렉토리
pytest tests/test_core.py           # 특정 파일
pytest tests/test_core.py::test_add # 특정 함수
pytest -v                           # 상세
pytest -x                           # 첫 실패 시 중단
```

**pytest.ini** (프로젝트 루트에 배치 → 자동 탐지)
```ini
[pytest]
minversion = 6.0
addopts = -ra -q --tb=short
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
```

**분석 함수 단위 테스트**
```python
import pytest, pandas as pd
from src.clean import clean_nulls

@pytest.fixture                       # 공통 데이터·설정 공유
def sample_df():
    return pd.DataFrame({'a':[1,None,3],'b':['x','y',None]})

def test_clean_removes_nulls(sample_df):
    result = clean_nulls(sample_df, cols=['a'])
    assert result['a'].isna().sum() == 0
```

> `parametrize` 로 여러 입력 케이스를 한 번에 검증 가능

**pytest-cov — 커버리지**
```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=term-missing

# Name              Stmts Miss Cover Missing
# src/clean.py         25    3   88%  42-44, 67
# TOTAL                63    3   95%
```
> 🎯 **커버리지 80% 이상 목표.** MLOps 과목 CI 파이프라인의 필수 지표.

## 5-4. black — 코드 포매터

> 🖤 **Black의 철학** — "당신의 스타일은 중요하지 않다. 일관성이 더 중요하다."

```bash
pip install black
black .                          # 하위 모든 .py 자동 정리
black src/mymodule/core.py       # 특정 파일
black --check src/               # 검사만 (CI에서 유용)
```

| 항목 | 규칙 |
|---|---|
| 들여쓰기 | 공백 4칸 (PEP8 동일) |
| 줄 길이 | **88자** (PEP8의 79자보다 완화) |
| 괄호 감싸기 | 인자가 길면 자동 줄바꿈 |
| 문자열 | `'` 또는 `"` 중 하나로 통일 |
| 연산자 공백 | 앞뒤 공백 유지 (`a + b`) |

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py310']
```

**장점** 자동화 · 일관성 · 빠름 · pre-commit/CI 통합 용이
**주의** 커스터마이징 제한 · flake8과 충돌 가능 · 기존 코드에 적용 시 diff 대량 발생

### 📖 [참고] PEP8

- **PEP** = "Python 개선 제안서" — 새 기능·스타일·정책을 제안하는 공식 문서
- **PEP 8** = 8번째 제안서 (스타일 가이드 버전 8이 아님!), 2001년 발표
- 목적: *"코드는 작성하는 사람보다 읽는 사람이 더 많다"*
- 관련: PEP 7(C 코드 스타일) · PEP 484(타입 힌트) · PEP 572(할당 표현식 `:=`)

## 5-5. pre-commit — 자동 검사 Hook

> 🛡️ 코드 품질을 **"Git 단계에서"** 지키기 위한 자동 방어

```bash
pip install pre-commit
pre-commit install              # .git/hooks/pre-commit 자동 생성
pre-commit run --all-files      # 전체 파일 검사
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-yaml
      - id: debug-statements    # print() 남아있으면 커밋 차단
```

→ 오류가 나면 **커밋이 차단**되고, 수정 후 다시 add/commit

## 5-6. Ruff — 2026 Python 린팅·포매팅 표준

> ⚡ **flake8 + black + isort를 하나로 대체.** Rust로 작성되어 기존 도구 대비 **10–100× 빠름**

```bash
pip install ruff
ruff check .              # 린팅
ruff check --fix .        # 자동 수정
ruff format .             # 포매팅
```

```toml
[tool.ruff]
line-length = 88
select = ['E','F','I','UP']   # 에러·경고·임포트·업그레이드
ignore = ['E501']

[tool.ruff.format]
quote-style = 'double'
indent-style = 'space'
```

## 5-7. 환경 재현 & CI

```bash
pip freeze > requirements.txt        # 버전 고정
pip install -r requirements.txt      # 동일 환경 1분 내 재현
```
> 🚫 **.gitignore 필수** — `.venv/` `.env` `__pycache__/` `*.pyc` `.coverage`

```yaml
# .github/workflows/ci.yml
name: CI - Lint & Test
on: [push, pull_request]
jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: { python-version: '3.10' }
      - run: pip install -r requirements.txt
      - run: black --check .
      - run: flake8 .
      - run: mypy src/
      - run: pytest
```

**실전 흐름**
```
코드 작성(src/, tests/) → pre-commit hook 자동 실행(black·flake8·mypy)
  → pytest 로컬 테스트 → GitHub Push → Actions로 품질 검사·테스트 자동 실행
```

**VS Code 연동**
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "python.analysis.typeCheckingMode": "basic"
}
```
- **F9** 중단점 → **F5** 실행 → 변수 인스펙터로 DataFrame 실시간 확인 → *print 디버깅 탈출*
- Python Test Explorer 확장으로 사이드바에서 테스트 실행

## 🎯 코드 품질 도구가 데이터 분석 팀에 필요한 이유

- **분석 코드도 팀이 공유한다** — GitHub에 올리는 순간 팀 자산
- **재현 가능한 분석 = 신뢰** — 6개월 뒤 같은 결과가 나오는 분석이 좋은 분석
- **MLOps CI/CD 기반** — DevOps·MLOps 과목에서 지금 설정을 그대로 사용
- **디버거 > print()** — 중단점으로 컬럼·타입·값 즉시 확인

---

# 6. 비동기와 병렬 처리 입문

## 6-1. 동시성 vs 병렬성

| 구분 | 동시성 (Concurrency) | 병렬성 (Parallelism) |
|---|---|---|
| **도구** | asyncio + httpx | multiprocessing |
| **실행 방식** | 한 스레드, 대기 중 다른 작업 실행 | 여러 프로세스, 진짜 동시 실행 |
| **적합한 작업** | **I/O bound** — API 호출, 파일 읽기 | **CPU bound** — 수치 계산, 이미지 처리 |
| **GIL 영향** | 영향 없음 (대기 중 전환) | GIL 우회 (별도 프로세스) |
| **분석 적용** | 공공 API 대량 수집, 비동기 DB 쿼리 | 대용량 파일 병렬 전처리, 모델 훈련 |

## 6-2. GIL (Global Interpreter Lock)

> 🔒 CPython 인터프리터에서 **하나의 스레드만 실행되도록 강제하는 락**

- **CPU-bound** 작업에서 병렬성 저하 → threading 효과 없음
- **I/O-bound** 작업에서는 대기 중 GIL이 해제되므로 threading 효과적
- **NumPy** 등은 C 확장에서 GIL을 해제하고 병렬 연산 (BLAS)
- Python 3.13+ 에서 GIL 옵션 제거 실험 진행 중

```python
threads = [threading.Thread(target=cpu_task) for _ in range(4)]
# 4개 스레드를 만들지만 GIL 때문에 실질적으로는 하나씩 처리됨
```

## 6-3. threading vs multiprocessing

```python
# threading — 메모리 공유, 생성 빠름 / GIL로 CPU-bound에 비효율
import threading
t = threading.Thread(target=worker, args=(i,))
t.start(); t.join()

lock = threading.Lock()          # 동기화
with lock:
    shared += 1
```

```python
# multiprocessing — 별도 메모리 공간 → GIL 회피, CPU-bound에 유리
from multiprocessing import Process, Pool, Queue

with Pool(processes=4) as pool:
    result = pool.map(square, [1, 2, 3, 4])   # [1, 4, 9, 16]

q = Queue()                      # 프로세스 간 통신
```

**실전 — ProcessPoolExecutor로 대용량 파일 병렬 처리**
```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

n_cores = mp.cpu_count()                      # macOS M1: 8코어
chunks = split_chunks(all_data, n_cores)      # N등분

with ProcessPoolExecutor(max_workers=n_cores) as exe:
    results = list(exe.map(process_chunk, chunks))
# 8코어: 이론상 8× 속도 향상
```
> ⚠️ **주의** — 프로세스 간 데이터 전달 비용 고려

**응용**
- FastAPI `BackgroundTasks` 로 백그라운드 처리
- PyTorch `DataLoader(num_workers=4)` → 다중 프로세스 전처리로 GPU idle 방지 (pre-fetching)

## 6-4. asyncio + httpx — 비동기 API 수집

```python
import asyncio, httpx

async def fetch(client, url):
    try:
        r = await client.get(url, timeout=10)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

async def fetch_all(urls):
    async with httpx.AsyncClient() as c:
        tasks = [fetch(c, u) for u in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

urls = [f'https://api.example.com/data/{i}' for i in range(100)]
results = asyncio.run(fetch_all(urls))
# 순차: ~100초 → 비동기: ~2초
```

| 요소 | 역할 |
|---|---|
| `async def` / `await` | 비동기 함수 정의와 호출 |
| `asyncio.gather()` | 여러 태스크 동시 실행 |
| `httpx.AsyncClient` | 비동기 HTTP 클라이언트 |
| `return_exceptions=True` | 일부 실패 허용 |
| `asyncio.run()` | 이벤트 루프 시작 |

## 6-5. 성능 측정 도구

```python
import timeit, cProfile, sys

# timeit — 반복 측정으로 정확도 향상
t = timeit.timeit("''.join(my_list)", setup="my_list=['a']*1000", number=10000)

# cProfile — 함수별 호출 횟수·시간 분석
cProfile.run('heavy_analysis(df)', sort='cumtime')

# sys.getsizeof — 객체 메모리 크기 (shallow)
print(sys.getsizeof(list(range(10000))))   # ~87KB
print(sys.getsizeof(x for x in range(10000)))  # ~104B
```
> `memory_profiler` 로 라인별 메모리 추적(`@profile`) 가능

## 🎯 왜 필요한가

- **API 수집 속도 100× 향상** — 공공 API 100개 순차 100초 → asyncio 약 2초
- **대용량 전처리 병렬화** — 수십 GB CSV를 코어 수만큼 분할
- **병목 찾기 → 올바른 최적화** — 느낌이 아니라 cProfile로 먼저 측정
- **후속 과목 기반** — LangChain·RAG·AI Agent는 전부 async 기반 코드

---

## 🏆 Day 1 종합 실습 — 데이터 수집 미니 파이프라인

### 사용 API

| API | 엔드포인트 |
|---|---|
| **Open-Meteo** (서울 3일 시간대별 기온·강수확률) | `api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780&hourly=temperature_2m,precipitation_probability&forecast_days=3&timezone=Asia/Seoul` |
| **Countries.dev** (한국 국가 정보) | `countries.dev/alpha/KOR` |
| **ip-api** (IP 기반 지역 정보) | `ip-api.com/json/8.8.8.8` |

### 실습 단계

1. **환경 준비** — venv 생성·활성화, `requirements.txt` 로 패키지 관리
2. **비동기 수집** — `asyncio` + `httpx`, `asyncio.gather()` 로 3개 API 동시 수집
3. **스키마 검증** — 필요한 필드 추출 후 **Pydantic v2** 모델로 타입·범위 검증
4. **저장 및 성능 비교** — CSV와 Parquet 두 형식으로 저장, 읽기/쓰기 시간 측정·비교
5. **테스트 및 Git 커밋** — pytest 스키마 검증 테스트, ruff 코드 스타일 검사

### 채점 기준 (100점)

| 항목 | 배점 | 내용 |
|---|:---:|---|
| 환경 구성 + 비동기 수집 | 35 | venv 활성화 상태 설치 완료 / 3개 API 모두 `gather()` 동시 수집 |
| 스키마 검증 + 저장 비교 | 45 | Pydantic v2 모델 정의·예외 처리 / CSV·Parquet 저장 + 성능 측정 출력 |
| 테스트·커밋 | 10 | pytest 1건 이상 통과, ruff 오류 없음, Git 커밋 이력 존재 |
| 완성도 | 10 | 주석 누락 시 감점 |

### 제출물

- **코드** — 폴더 포함 전체 코드, `캠퍼스명_반_이름_실습명.zip` (예: `서울_1반_홍길동_day1종합실습.zip`)
- **실행결과 정리 (PDF)** — 실행결과 화면 캡처 + 코드 분석에 대한 본인 의견(개선 사항, 코드 품질 측면)
- **제출 기한** — 1차: Day 1 종료 전 / 2차: Day 2 시작 1시간 전 (초과 시 감점)

---

# 8. Pandas 2.x 실전

## 8-1. Pandas 기본 개념

| 개념 | 설명 |
|---|---|
| **DataFrame** | 2D 레이블 표. 엑셀 시트를 코드로. 컬럼마다 다른 타입 가능. 내부는 NumPy 배열 |
| **Series** | 1D 레이블 배열. DataFrame의 한 컬럼. 인덱스 기반 정렬·조인이 강점 |

**Pandas 2.x 핵심 변경** — Copy-on-Write 기본 활성화 / ArrowDtype 지원 / nullable 정수·문자열

> 📌 **언제 Pandas?** 수백만 행 이하 EDA·탐색 / 시각화 라이브러리 연동 / Jupyter 탐색 위주

## 8-2. 기초 EDA

```python
df = pd.read_csv('sales.csv')

df.shape                      # (행수, 열수)
df.info()                     # 타입·결측·메모리
df.describe()                 # 수치 기술통계
df.describe(include='all')    # 범주형 포함
df.head() / df.tail() / df.sample()

# 타입 변환
df['date']   = pd.to_datetime(df['date'])
df['region'] = df['region'].astype('category')

# 선택
df['amount']                  # Series
df[['region','amount']]       # DataFrame
df.loc[df['amount'] > 1000]   # 조건 필터
```

## 8-3. 결측치 · 이상치

```python
# 결측치 파악
df.isna().sum()
df.isna().sum() / len(df) * 100          # 비율

# 처리 전략
df['amount'].fillna(df['amount'].median())        # 수치 → 중앙값
df['category'].fillna(df['category'].mode()[0])   # 범주형 → 최빈값
df.dropna(subset=['date','amount'])               # 특정 컬럼만

# IQR 이상치 탐지
Q1 = df['amount'].quantile(0.25)
Q3 = df['amount'].quantile(0.75)
IQR = Q3 - Q1
lo, hi = Q1 - 1.5*IQR, Q3 + 1.5*IQR
df_clean = df[df['amount'].between(lo, hi)]
```
> ℹ️ 결측 메커니즘 **MCAR / MAR / MNAR** 이해가 처리 전략의 전제

## 8-4. groupby · pivot_table · merge

```python
# named aggregation — 결과 컬럼명 직접 지정
monthly = df.groupby('month').agg(
    revenue=('amount','sum'),
    cnt=('amount','count'),
    avg=('amount','mean')
).reset_index()

# pivot_table — 엑셀 피벗과 동일
pivot = df.pivot_table(values='amount', index='region',
                       columns='category', aggfunc='sum', fill_value=0)

# merge — SQL JOIN (inner/left/right/outer)
result = pd.merge(df_sales, df_cust, on='customer_id', how='left')
```
> 🔑 **merge는 컬럼 기준, join은 인덱스 기준**

## 8-5. ⚠️ Copy-on-Write (CoW)

> Pandas 2.0부터 기본 활성화. **뷰(View)를 수정하면 경고/오류** → 명시적 `copy()` 또는 `assign()` 필요

```python
# ❌ ChainedAssignmentError
df_seoul = df[df['region'] == '서울']
df_seoul['amount'] = df_seoul['amount'] * 1.1

# ✅ 방법 1: .copy() 명시
df_seoul = df[df['region'] == '서울'].copy()
df_seoul['amount'] *= 1.1

# ✅ 방법 2: .loc 직접 수정
df.loc[df['region'] == '서울', 'amount'] *= 1.1
```
> 💡 `assign()` + `query()` 체이닝 패턴이 가장 안전하고 가독성도 좋다

## 8-6. apply vs 벡터화

```python
# 느림 — apply (Python 루프)
df['upper'] = df['name'].apply(lambda x: x.upper())     # ~3.2s

# 빠름 — 벡터화 (C 레벨)
df['upper'] = df['name'].str.upper()                    # ~0.08s → 40× 빠름

# dt 접근자
df['date'] = pd.to_datetime(df['date'])
df['year']    = df['date'].dt.year
df['weekday'] = df['date'].dt.day_name()
```

---

# 9. Polars + DuckDB

## 9-1. 왜 Polars와 DuckDB인가 — 2026 표준

| Pandas의 한계 | Polars — Rust + Arrow |
|---|---|
| 싱글스레드 | 멀티스레드 자동 활용 |
| 수백만 행 이상에서 속도 저하 | Lazy API로 쿼리 최적화 |
| 메모리 사용량이 원본의 5–10× | Pandas 대비 **5–20× 빠름** |
| CoW 전까지 복사 많음 | Apache Arrow 기반 |

**DuckDB** — CSV·Parquet 파일을 로딩 없이 SQL로 분석. 서버 없음. **로컬 DWH급 성능.**

## 9-2. Polars — Eager vs Lazy

```python
import polars as pl

# Eager — 즉시 실행 (탐색·소규모)
df = pl.read_csv('sales.csv')
result = df.filter(pl.col('amount') > 0)

# Lazy — 실행 계획 최적화 후 collect()
result = (
    pl.scan_csv('large.csv', schema_overrides={'amount': pl.Float64})
      .filter(pl.col('region') == '서울')
      .filter(pl.col('amount') > 0)
      .group_by('category')
      .agg([pl.col('amount').sum().alias('total'),
            pl.count().alias('cnt')])
      .sort('total', descending=True)
      .collect()          # ← 여기서 실제 실행
)
```
> ⚡ **Lazy 장점** — predicate pushdown / projection pushdown 으로 불필요한 읽기 제거

## 9-3. Polars 문법 — Pandas 대응표

| Polars | Pandas |
|---|---|
| `pl.col('x')` | `df['x']` |
| `.filter(...)` | `df[mask]` |
| `.select([...])` | 컬럼 선택 |
| `.with_columns(...)` | `.assign(...)` |
| `.group_by().agg()` | `.groupby().agg()` |

```python
df.filter(pl.col('amount') > 0).select(['region','amount'])
df.with_columns((pl.col('amount') * 1.1).alias('adjusted'))
df.with_columns(pl.col('region').str.to_uppercase(),
                pl.col('date').str.to_date('%Y-%m-%d'))

df_pd = df.to_pandas()      # 상호 변환
df_pl = pl.from_pandas(df_pd)
```

## 9-4. DuckDB — 파일에 직접 SQL

```python
import duckdb

result = duckdb.sql("""
    SELECT region, SUM(amount) AS total, AVG(amount) AS avg, COUNT(*) AS cnt
    FROM 'data/*.csv'                 -- 와일드카드 지원
    WHERE year = 2024 AND amount > 0
    GROUP BY region
    ORDER BY total DESC""").df()      -- .df() → Pandas / .pl() → Polars

# 여러 파일 JOIN
duckdb.sql("""
    SELECT s.*, c.tier
    FROM 'sales.parquet' s
    JOIN 'customers.csv' c ON s.cid = c.id""").show()
```
> JOIN · GROUP BY · WINDOW 함수 모두 지원. `CREATE TABLE AS SELECT` 로 영구 저장.

## 9-5. Apache Arrow — 제로카피 생태계

- **Arrow** = 컬럼형 인메모리 포맷. 모든 도구가 중간 포맷으로 쓰면 **직렬화 비용 0**
- Polars ↔ DuckDB ↔ PyArrow ↔ Pandas 간 제로카피 변환
- **Parquet** — 컬럼형 저장으로 필요한 컬럼만 읽음. CSV 대비 **10× 빠른 읽기, 5× 작은 파일**

> 🔄 **권장 흐름** — 원본 CSV 수집 → Parquet 변환 저장 → DuckDB/Polars로 분석 → 최종 검토는 Pandas

---

## 🧪 Practice 3 — Pandas · Polars · DuckDB 비교

> 📂 `sales_100k.csv`

| # | 과제 |
|---|---|
| 1 | **Pandas EDA** — 로딩 후 기본 EDA, IQR 방법으로 이상치 제거 |
| 2 | **Pandas groupby** — region·category별 총매출·평균·건수를 **named aggregation**으로 계산, 총매출 내림차순 정렬 |
| 3 | **Polars Lazy API** — 동일 집계를 `scan_csv → filter → group_by → agg → sort → collect` 체인으로 |
| 4 | **DuckDB SQL + 성능 비교** — 동일 집계를 SQL로 작성, `timeit`으로 세 도구 실행 시간 비교 |

**❌ 감점 대상 (각 -20)**

- IQR 공식 오류 — `Q1 - 1.5*IQR` / `Q3 + 1.5*IQR` 범위 잘못 적용
- named aggregation 미사용 — `agg({'amount': 'sum'})` 방식으로 컬럼명 미지정
- Polars Eager 사용 — `scan_csv` 대신 `read_csv` 로 Lazy API 미적용
- `collect()` 누락 — LazyFrame 상태로 제출
- `timeit` 반복 횟수 미통일 — 세 도구의 `number` 값이 달라 공정 비교 불가

---

# 10. 데이터 시각화

## 10-1. 왜 시각화인가

> 📊 **Anscombe의 사중주** — 평균·분산·상관계수가 **동일한** 4개 데이터셋이 시각화하면 완전히 다른 패턴.
> **수치만으로 하는 분석은 위험하다.**

| 관점 | 내용 |
|---|---|
| EDA의 첫 번째 도구 | 히스토그램·박스플롯(분포), 산점도(상관), 히트맵(결측 패턴) |
| 의사결정자 설득 | 수치 표보다 인터랙티브 차트 한 장 |
| 모델 평가 | Confusion Matrix · 학습 곡선 · Feature Importance |
| 알고리즘 디버깅 | 시간복잡도·메모리 변화 시각화로 병목 파악 |

## 10-2. Matplotlib — 시각화의 어머니

**핵심 구조**

| 항목 | 설명 |
|---|---|
| **Figure** | 전체 그림판(캔버스). 여러 Axes를 담고 크기·해상도·배경색 관리 |
| **Axes** | 실제 데이터가 그려지는 개별 그래프. x축·y축·tick·label·title 포함. *복수형이 아니라 "축들이 모여있는 공간"이라는 단수형 객체* |

**자주 쓰는 플롯**

| 함수 | 용도 |
|---|---|
| `plot()` | 선 그래프 (시계열, 함수) |
| `scatter()` | 산점도 (두 변수 관계) |
| `bar()` / `barh()` | 막대 그래프 (범주형 비교) |
| `hist()` | 히스토그램 (분포) |
| `boxplot()` | 박스 플롯 (사분위수, 이상치) |
| `imshow()` | 이미지·행렬 데이터 |

```python
fig, axes = plt.subplots(1, 2, figsize=(12,5))

axes[0].plot(months, revenue, color='steelblue', lw=2, marker='o', label='매출')
axes[0].set_title('월별 매출 추이')
axes[0].set_xlabel('월'); axes[0].set_ylabel('원')
axes[0].legend(); axes[0].grid(alpha=0.3)

axes[1].bar(regions, values, color='teal', alpha=0.8)
axes[1].set_title('지역별 매출')

plt.tight_layout()
plt.savefig('report.png', dpi=150, bbox_inches='tight')   # 고해상도 저장
```

**2×2 서브플롯**
```python
fig, axes = plt.subplots(2, 2)
axes[0, 0].plot([1,2,3], [4,5,6])
axes[0, 1].bar([1,2,3], [4,5,6])
axes[1, 0].scatter([1,2,3], [4,5,6])
axes[1, 1].hist([1,2,3,4,5,6], bins=3)
plt.tight_layout()
```

## 10-3. Seaborn — 통계 시각화 특화

> Matplotlib 기반의 **high-level 인터페이스.** `hue`·`size`·`style` 로 다차원 정보 인코딩.

```python
import seaborn as sns
tips = sns.load_dataset('tips')

sns.histplot(data=tips, x='total_bill', bins=10, kde=True)
sns.boxplot(data=tips, x='day', y='total_bill', hue='sex')
sns.barplot(x='day', y='total_bill', data=tips, palette='Set2')
sns.scatterplot(data=tips, x='total_bill', y='tip', hue='time')

sns.set_style('whitegrid')   # darkgrid, whitegrid, dark, white, ticks
```

**다변량 분석 2종**

```python
# pairplot — 모든 숫자형 변수 쌍의 산점도 + 분포를 한 번에 (EDA 초기 필수)
sns.pairplot(iris, hue='species', markers=["o", "s", "D"])

# heatmap — 상관계수 행렬, 혼동 행렬 시각화에 탁월
corr = iris.drop(columns='species').corr()
sns.heatmap(corr, annot=True, cmap='coolwarm', linewidths=.5)
```

> 서브플롯 사용 시 `ax=axes[0,0]` 로 Matplotlib Axes에 그린다.

## 10-4. Plotly Express — 인터랙티브

```python
import plotly.express as px

fig = px.scatter(df, x='gdp', y='happiness',
                 color='region', size='population',
                 hover_name='country', title='GDP vs 행복지수')

fig2 = px.bar(monthly_df, x='month', y='revenue',
              color='category', facet_col='region')     # 그룹별 분할 서브플롯

fig.write_html('analysis.html')     # HTML 파일 하나로 공유 (줌·필터·호버 그대로)
```

## 10-5. Altair — 선언형

> Grammar of Graphics 기반. `mark_*` + `encode()` 체이닝. **EDA 빠른 프로토타이핑에 최적.**

```python
import altair as alt

chart = (alt.Chart(df)
    .mark_point()
    .encode(x='gdp:Q', y='happiness:Q', color='region:N',
            tooltip=['country','gdp','happiness'])
    .interactive())
chart.save('chart.html')
```

## 🎯 시각화 도구 선택 가이드

| 상황 | 도구 |
|---|---|
| 학술 논문·보고서 품질, 픽셀 수준 제어 | **Matplotlib** |
| 분포·상관·그룹 비교 (통계) | **Seaborn** |
| 인터랙티브 대시보드, 비전공자 발표 | **Plotly** |
| 탐색 단계에서 수십 개 차트를 빠르게 | **Altair** |
| 웹 공유 | **Streamlit** (소개 수준) |

---

# 11. 기초 통계와 ML 파이프라인 연결

## 11-1. 기술통계

| 범주 | 지표 |
|---|---|
| **중심 경향** | 평균 · 중앙값 · 최빈값 |
| **산포도** | 분산 · 표준편차 · IQR · 범위 |
| **분포 모양** | 왜도(skewness, 0=대칭) · 첨도(kurtosis, 0=정규) |
| **관계** | 상관계수 (-1 ~ +1, 선형 관계 강도) |

```python
df.describe()
df['amount'].skew()
df['amount'].kurt()

corr = df[['amount','visits','age']].corr()

# 정규분포 검정
from scipy import stats
_, p = stats.shapiro(df['amount'].dropna())
print(f'정규분포 검정 p값: {p:.4f}')
```

## 11-2. 가설 검정

> 귀무가설(H0) vs 대립가설(H1), 유의수준 **α = 0.05**
> **p < 0.05 → H0 기각 (통계적으로 유의)**

```python
# t-test — 두 그룹 평균 차이
group_a = df[df['group']=='A']['amount']
group_b = df[df['group']=='B']['amount']
t, p = stats.ttest_ind(group_a, group_b)

if p < 0.05:
    print('통계적으로 유의미한 차이 있음')
else:
    print('차이 없음 (우연일 수 있음)')

# 카이제곱 — 범주형 변수 독립성
from scipy.stats import chi2_contingency
ct = pd.crosstab(df['region'], df['purchased'])
chi2, p, dof, expected = chi2_contingency(ct)
```

## 11-3. CRISP-DM — 실무 데이터 분석 방법론

```
업무 이해 → 데이터 이해 → 데이터 준비 → 모델링 → 평가 → 배포
 문제 정의    EDA 탐색      전처리·피처     알고리즘   성능 측정  서비스 적용
```

> 💡 **기술 중심이 아닌 문제 해결 중심** — 좋은 분석은 올바른 문제 정의에서 시작한다.
> 데이터 준비가 전체의 **80~90%** 를 차지한다.

## 11-4. sklearn Pipeline

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
import joblib

preproc = ColumnTransformer([
    ('num', StandardScaler(), num_cols),
    ('cat', OneHotEncoder(),  cat_cols)])

model = Pipeline([
    ('prep', preproc),
    ('reg',  Ridge(alpha=1.0))])

model.fit(X_train, y_train)
print(f'R2: {model.score(X_test, y_test):.3f}')

joblib.dump(model, 'model.pkl')       # 파이프라인 전체 직렬화
loaded = joblib.load('model.pkl')
```

## 🎯 통계와 ML 파이프라인이 연결되는 이유

- **통계 없이 ML은 블랙박스** — 평균·분산·상관계수를 모르면 피처 선택, 이상치 처리, 결과 해석 불가능
- **CRISP-DM — 기술보다 프로세스** — 알고리즘이 아니라 올바른 문제 정의에서 시작
- **후속 과목 직접 연결** — Feature Engineering·머신러닝에서 sklearn Pipeline을 그대로 사용
- **재현 가능한 모델 관리** — joblib으로 Pipeline 전체 저장 → 배포 환경에서 동일한 전처리+예측 보장 (**MLOps의 기본**)

---

## 🧪 Practice 4 — 시각화 · 통계검정 · sklearn Pipeline

> 📂 `sales_100k.csv` — **실습 3 연계**

| # | 과제 |
|---|---|
| 1 | **EDA 시각화 4종** — `fig, axes = plt.subplots(2,2)` 로 히스토그램+KDE / 박스플롯 / 월별 라인 / 상관 히트맵 |
| 2 | **통계 검정** — 서울 vs 부산 평균 매출 t-test, 지역×카테고리 독립성 카이제곱 |
| 3 | **sklearn Pipeline** — ColumnTransformer + Pipeline 완성 후 훈련·평가·저장·재로딩 |
| 4 | **Plotly 인터랙티브 차트** — 지역·카테고리별 총매출 막대 차트를 HTML로 저장 |

**❌ 감점 대상 (각 -20)**

- 서브플롯 미사용 — 차트 4개를 개별 `plt.show()` 로 따로 출력
- **p-value 해석 누락** — 수치만 출력하고 유의미 여부(p < 0.05) 판단 코드·주석 없음
- Pipeline 미사용 — 전처리와 모델을 개별 단계로 분리 실행
- 모델 저장 누락 — `joblib.dump()` 없이 학습만
- Plotly 차트 파일 미저장 — `fig.show()` 만 하고 `.write_html()` 미호출

---

# 12. 분석 자동화와 파이프라인 설계

## 12-1. 왜 자동화하는가

| 관점 | 내용 |
|---|---|
| **반복 분석의 현실** | 매주 같은 매출 리포트 수작업 → 자동화하면 수십 분이 0분 |
| **데이터 최신성** | 어제 시황·뉴스가 반영된 리포트가 오늘 오전 5시에 이미 완성돼 있어야 한다 *(증권가 애널리스트)* |
| **오류 감소** | 수작업 복붙 오류 제거, 동일 코드가 동일 결과 → 신뢰성 |
| **확장성** | 리포트 10개를 만들든 100개를 만들든 코드는 동일 |

## 12-2. schedule + cron

```python
import schedule, time, logging

def run_daily_report():
    try:
        df = load_and_clean('sales.csv')
        stats = compute_stats(df)
        render_report(stats)
        logging.info('리포트 완료')
    except Exception as e:
        logging.error(f'실패: {e}')

schedule.every().day.at('08:00').do(run_daily_report)
schedule.every().monday.at('09:00').do(weekly_summary)
schedule.every(1).hours.do(check_new_data)

while True:
    schedule.run_pending()
    time.sleep(60)
```
> OS 레벨 스케줄은 macOS **launchd** 또는 **cron** 사용. 외부 스크립트는 `subprocess` 로 연동.

## 12-3. Jinja2 — 리포트 자동 생성

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from datetime import datetime

env  = Environment(loader=FileSystemLoader('templates'))
tmpl = env.get_template('report.html')

html = tmpl.render(
    title='월간 판매 분석',
    generated=datetime.now().strftime('%Y-%m-%d'),
    summary=stats.to_dict(),
    chart_html=fig.to_html(full_html=False),
    top5=df.nlargest(5,'amount').to_dict('records')
)

out = Path('output/report.html')
out.write_text(html, encoding='utf-8')

import webbrowser
webbrowser.open(str(out.resolve()))
```
> 문법: `{{ 변수 }}` · `{% for %}` · `{% if %}` — `pdfkit` 연동으로 PDF 변환 가능

## 12-4. LLM API 활용 개요

> 🤖 벤더 무관 **HTTP POST 기반** 구조. 요청 = 메시지 배열 + 모델 파라미터, 응답 = content 배열.
> **토큰 기반 과금** (입력 + 출력 토큰 합산)

```python
import httpx, os, asyncio

async def call_llm(text: str) -> str:
    async with httpx.AsyncClient() as c:
        r = await c.post(
            'https://api.{vendor}.com/v1/messages',
            headers={'Authorization': f'Bearer {os.getenv("API_KEY")}'},
            json={'model': 'model-name',
                  'max_tokens': 500,
                  'messages': [{'role':'user','content':text}]},
            timeout=30)
        return r.json()['content'][0]['text']

# 활용: 이상치 자동 설명
result = asyncio.run(call_llm(f'다음 데이터 이상치 설명: {outliers}'))
```

## 12-5. ETL 파이프라인 설계 원칙

> ✅ **좋은 파이프라인** = 각 단계 분리 + 오류 기록 + 재현 가능 + 테스트 가능

```python
def run_pipeline(config: dict) -> dict:
    logger.info(f'파이프라인 시작: {config}')

    # E: Extract — 수집 (API / DB / 파일)
    raw = extract(config['source'])
    logger.info(f'수집 완료: {len(raw)}건')

    # V: Validate — 검증 (Pydantic)
    validated, errors = validate(raw, schema=SalesRecord)
    if errors:
        logger.warning(f'검증 오류: {len(errors)}건')
    ...
```
→ 각 단계를 독립적으로 pytest로 테스트 가능하고, **실패 시 어느 단계인지 즉시 파악**

---

# 13. 분석 코드 구조화와 공유

## 13-1. Jupyter vs .py — 언제 무엇을?

| Jupyter (.ipynb) | Python (.py) |
|---|---|
| EDA·데이터 탐색 단계 | 반복 실행 자동화 스크립트 |
| 시각화가 중심인 분석 | Git 버전 관리 + pytest 테스트 |
| 한 번 실행으로 끝나는 분석 | 팀 협업·코드 리뷰 대상 |
| 보고서 변환 (nbconvert) | CI/CD 파이프라인 통합 |
| 교육·튜토리얼 자료 | 라이브러리(`src/`) 코드 |

## 13-2. 분석 프로젝트 폴더 구조

> 🔑 **6개월 뒤 동료(또는 미래의 나)가 README만 읽고 바로 실행할 수 있어야 좋은 구조**

```
data-project/
├── data/
│   ├── raw/           # 원본 데이터 (절대 수정 금지)
│   ├── processed/     # 전처리 완료 데이터
│   └── external/      # 외부 참조 데이터
├── notebooks/         # EDA·실험용 Jupyter 노트북
│   ├── 01_eda.ipynb
│   └── 02_feature_exploration.ipynb
├── src/               # 재사용 가능한 Python 모듈
│   ├── __init__.py
│   ├── clean.py       # 전처리 함수
│   └── viz.py         # 시각화 함수
├── tests/
├── requirements.txt
└── README.md
```

## 13-3. 모듈화

```python
# src/clean.py
from typing import Optional
import pandas as pd

def clean_nulls(df: pd.DataFrame,
                cols: Optional[list] = None,
                strategy: str = 'median') -> pd.DataFrame:
    cols = cols or df.select_dtypes('number').columns.tolist()
    if strategy == 'median':
        return df.fillna(df[cols].median())
    elif strategy == 'drop':
        return df.dropna(subset=cols)
    return df
```

```python
# notebooks/01_eda.ipynb 에서 사용
import sys
sys.path.insert(0, '..')
from src.clean import clean_nulls
from src.viz import plot_distribution
```

## 13-4. README + GitHub 공유

```markdown
## 프로젝트 개요
## 개발 환경 설정
git clone <url> && cd data-project
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## 실행 방법
pytest tests/
python src/run_pipeline.py
```

```bash
jupyter nbconvert --to html notebooks/01_eda.ipynb    # 노트북 공유용 변환
```
> 배지(badge)로 테스트 통과·커버리지 표시, `.github/workflows/test.yml` 로 pytest 자동화

## 🎯 분석 코드 구조화의 핵심 원칙

| 원칙 | 내용 |
|---|---|
| **탐색과 재사용 분리** | 노트북은 탐색·실험용, 검증된 함수는 `src/`로 이동. **두 역할을 섞지 말 것** |
| **재현성 = 신뢰성** | `requirements.txt` + `.env` 예시 + README 실행 가이드. 이 셋이면 누구나 동일 결과 재현 |
| **데이터는 git에 올리지 않는다** | `data/raw/`는 `.gitignore`. 대신 데이터 출처(URL·스크립트)를 README에 기록 |
| **점진적 개선** | 처음부터 완벽할 필요 없음. 분석이 반복되면 함수화, 함수가 쌓이면 모듈화 |

---

## 🏆 Day 2 종합 실습 — End2End 데이터 분석 프로젝트

### 사용 데이터셋 (팀별 택 1)

| 데이터셋 | 링크 |
|---|---|
| **NYC Yellow Taxi** | `d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-05.parquet` |
| **Stack Overflow Survey 2024** | `github.com/StackExchange/Survey` · 공식: `survey.stackoverflow.co` |
| **Adult Census Income** | `archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data` (32561 × 15) |

```python
cols = ["age","workclass","fnlwgt","education","education-num",
        "marital-status","occupation","relationship","race","sex",
        "capital-gain","capital-loss","hours-per-week","native-country","income"]
df = pd.read_csv(url, header=None, names=cols, na_values=" ?", skipinitialspace=True)
```

### 실습 내용

1. **데이터 준비** — Pandas와 Polars **양쪽으로 로딩하여 비교**, 결측치·중복 처리 및 기본 EDA
2. **시각화** — Seaborn 정적 차트, Plotly 인터랙티브 차트 각 1개 이상 (분포·상관관계·그룹 비교 중 택일)
3. **통계 분석** — 기술통계(평균·표준편차·분위수), 상관계수, `scipy.stats.ttest_ind` t-test 및 **p-value 해석**
4. **ML Pipeline** — `sklearn.pipeline.Pipeline` 으로 전처리 + 모델 학습, 평가 지표 출력, joblib 저장
5. **자동화·발표** — 분석 결과를 `report.md` 로 자동 생성 + 팀별 발표 (5분)

### 채점 기준 (100점)

| 항목 | 배점 | 내용 |
|---|:---:|---|
| 데이터 준비 + 시각화 | 35 | Pandas·Polars 모두 사용, 결측치 처리·EDA 출력 / Seaborn·Plotly 각 1개 이상, 제목·축 레이블 포함 |
| 통계분석 + ML Pipeline | 45 | 기술통계·상관계수, t-test 결과 및 p-value 해석 / Pipeline 객체 구성, 평가 지표(정확도·F1 등), 모델 파일 저장 |
| 자동화 + 발표 | 20 | `report.md` 자동 생성 / 팀 발표 5분 |
| 완성도 | 10 | 주석 누락 시 감점 |

### 제출물

- **코드** — `캠퍼스명_반_이름_실습명.zip` (예: `서울_1반_홍길동_day2종합실습.zip`), GitHub 연동 후 폴더 구조 그대로
- **실행결과 정리 (PDF)** — 실행결과 캡처 + 코드 분석에 대한 본인 의견
- **제출 기한** — 과정 종료 시까지 (~21:00 엄수), 초과 시 감점

---

> 🎓 **수고하셨습니다.**
>
> ⚠️ 본 문서는 SK AX의 컨텐츠 자산으로, 무단 사용 및 불법 배포 시 법적 조치를 받을 수 있습니다.
