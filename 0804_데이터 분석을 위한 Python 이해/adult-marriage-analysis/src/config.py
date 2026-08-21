"""프로젝트 전반에서 공유하는 컬럼 및 타깃 정의."""

ADULT_DATA_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
)
RAW_DATA_FILENAME = "adult.data"

COLS = [
    "age",
    "workclass",
    "fnlwgt",
    "education",
    "education-num",
    "marital-status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
    "native-country",
    "income",
]

INTEGER_COLUMNS = [
    "age",
    "fnlwgt",
    "education-num",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
]

MARRIAGE_MAP = {
    "Never-married": 0,
    "Married-civ-spouse": 1,
    "Married-spouse-absent": 1,
    "Married-AF-spouse": 1,
    "Divorced": 1,
    "Separated": 1,
    "Widowed": 1,
}

TARGET = "ever_married"

NUMERIC_FEATURES = [
    "age",
    "education-num",
    "hours-per-week",
]

SKEWED_NUMERIC_FEATURES = [
    "capital-gain",
    "capital-loss",
]

CATEGORICAL_FEATURES = [
    "workclass",
    "occupation",
]

OPTIONAL_FEATURES = ["income"]

LEAKAGE_OR_EXCLUDED_FEATURES = [
    "marital-status",
    "relationship",
    "fnlwgt",
    "education",
]

SENSITIVE_AUDIT_FEATURES = [
    "race",
    "sex",
    "native-country",
]
