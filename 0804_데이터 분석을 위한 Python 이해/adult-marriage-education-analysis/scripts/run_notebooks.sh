#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"
venv_python="${project_root}/../.venv/bin/python"

if [[ ! -x "${venv_python}" ]]; then
  echo "가상환경 Python을 찾을 수 없습니다: ${venv_python}" >&2
  exit 1
fi

export JUPYTER_PATH="${project_root}/.jupyter${JUPYTER_PATH:+:${JUPYTER_PATH}}"
export JUPYTER_RUNTIME_DIR="${project_root}/data/.jupyter/runtime"
export JUPYTER_CONFIG_DIR="${project_root}/data/.jupyter/config"
export IPYTHONDIR="${project_root}/data/.ipython"
export MPLCONFIGDIR="${project_root}/data/.matplotlib"

mkdir -p "${JUPYTER_RUNTIME_DIR}" "${JUPYTER_CONFIG_DIR}" "${IPYTHONDIR}" "${MPLCONFIGDIR}"
cd "${project_root}"

for notebook in notebooks/01_data_quality.ipynb \
                notebooks/02_target_and_features.ipynb \
                notebooks/03_eda_hypothesis.ipynb \
                notebooks/04_feature_engineering.ipynb; do
  echo "실행 중: ${notebook}"
  "${venv_python}" -m jupyter nbconvert \
    --execute --to notebook --inplace "${notebook}" \
    --ExecutePreprocessor.kernel_name=adult-marriage-education \
    --ExecutePreprocessor.timeout=300
done

echo "완료: 01~04 노트북을 순서대로 실행했습니다."
