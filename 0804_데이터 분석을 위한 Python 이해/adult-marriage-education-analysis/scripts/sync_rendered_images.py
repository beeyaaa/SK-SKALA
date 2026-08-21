"""검증된 최신 PNG를 실행된 노트북의 해당 이미지 출력 셀에 동기화한다."""

from __future__ import annotations

import base64
from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]

IMAGE_CELLS = {
    "notebooks/02_target_and_features.ipynb": {
        "display(Image(filename=str(target_chart_path)))": "reports/figures/02_target_definition.png",
    },
    "notebooks/03_eda_hypothesis.ipynb": {
        "display(Image(filename=str(education_chart_path)))": "reports/figures/03_education_by_marriage.png",
        "display(Image(filename=str(multicollinearity_chart_path)))": "reports/figures/03_multicollinearity.png",
    },
}


def main() -> None:
    for notebook_name, replacements in IMAGE_CELLS.items():
        notebook_path = ROOT / notebook_name
        notebook = nbformat.read(notebook_path, as_version=4)
        replaced = 0
        for cell in notebook.cells:
            if cell.cell_type != "code":
                continue
            for marker, image_name in replacements.items():
                if marker not in cell.source:
                    continue
                image_bytes = (ROOT / image_name).read_bytes()
                encoded = base64.b64encode(image_bytes).decode("ascii")
                cell.outputs = [
                    nbformat.v4.new_output(
                        "display_data",
                        data={
                            "image/png": encoded,
                            "text/plain": "<IPython.core.display.Image object>",
                        },
                        metadata={},
                    )
                ]
                replaced += 1
        if replaced != len(replacements):
            raise RuntimeError(
                f"{notebook_name}: 이미지 출력 셀 {len(replacements)}개 중 {replaced}개만 찾았습니다."
            )
        nbformat.write(notebook, notebook_path)
        print(f"{notebook_path}: {replaced}개 이미지 동기화")


if __name__ == "__main__":
    main()
