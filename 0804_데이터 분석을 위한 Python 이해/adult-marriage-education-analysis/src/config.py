"""프로젝트 공통 컬럼과 Target 정의."""

COLS = [
    "age", "workclass", "fnlwgt", "education", "education-num",
    "marital-status", "occupation", "relationship", "race", "sex",
    "capital-gain", "capital-loss", "hours-per-week", "native-country",
    "income",
]

INTEGER_COLUMNS = [
    "age", "fnlwgt", "education-num", "capital-gain", "capital-loss",
    "hours-per-week",
]

EVER_MARRIED_STATUSES = {
    "Married-civ-spouse",
    "Married-spouse-absent",
    "Married-AF-spouse",
    "Divorced",
    "Separated",
    "Widowed",
}

NEVER_MARRIED_STATUS = "Never-married"

TARGET = "ever_married"
HYPOTHESIS_FEATURE = "education-num"

NUMERIC_MODEL_FEATURES = [
    "age", "education-num", "hours-per-week", "capital-gain", "capital-loss",
]

CATEGORICAL_MODEL_FEATURES = ["workclass", "occupation", "income"]

# 04 Feature Engineering에서 최종 전처리기에 전달하는 컬럼입니다.
# capital-gain/loss는 0이 많고 오른쪽 꼬리가 길어 log1p 파생값으로 대체합니다.
ENGINEERED_NUMERIC_FEATURES = [
    "age", "education-num", "hours-per-week",
    "capital-gain-log", "capital-loss-log", "capital-net-signed-log",
]

ENGINEERED_CATEGORICAL_FEATURES = [
    "workclass", "occupation", "income", "age-group", "hours-group",
]

EXCLUDED_FEATURES = {
    "marital-status": "Target 생성에 사용한 원본 컬럼",
    "relationship": "Husband, Wife, Own-child 등이 혼인 상태를 직접 암시",
    "education": "education-num과 같은 학력 정보를 중복 표현",
    "fnlwgt": "개인 특성이 아닌 Census 표본 가중치",
}

SENSITIVE_AUDIT_FEATURES = ["race", "sex", "native-country"]
