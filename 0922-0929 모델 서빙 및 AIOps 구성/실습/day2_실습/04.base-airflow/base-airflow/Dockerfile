# base-airflow 실습 전용 이미지 — 공식 apache/airflow 3.3.1 위에
# ml_serving_pipeline DAG가 쓰는 scikit-learn만 얹는다.
FROM apache/airflow:3.3.1

RUN pip install --no-cache-dir scikit-learn
