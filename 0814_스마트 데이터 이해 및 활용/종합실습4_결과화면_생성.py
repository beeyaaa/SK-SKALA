#!/usr/bin/env python3
"""Q1~Q10 튜닝 전/후 SQL과 실제 psql 결과를 PNG 화면으로 만든다."""

from __future__ import annotations

import os
import re
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "실행결과"
SCREEN_DIR = RESULT_DIR / "화면"

FONT_KR = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FONT_MONO = "/System/Library/Fonts/Menlo.ttc"


def question_sections(path: Path) -> dict[int, str]:
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"(?m)^-- Q(\d+)\.", text))
    sections: dict[int, str] = {}
    for index, match in enumerate(matches):
        number = int(match.group(1))
        if number > 10:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[number] = text[match.start():end]
    return sections


def result_statement(section: str) -> str:
    sql_only = "\n".join(
        line for line in section.splitlines()
        if not line.lstrip().startswith("--")
    )
    statements = [statement.strip() for statement in sql_only.split(";") if statement.strip()]
    if len(statements) < 2 or not statements[0].upper().startswith("EXPLAIN"):
        raise ValueError("EXPLAIN 다음의 결과 SELECT를 찾지 못했습니다.")
    return statements[1] + ";"


def execution_times(path: Path) -> list[float]:
    text = path.read_text(encoding="utf-8")
    return [float(value) for value in re.findall(r"Execution Time: ([0-9.]+) ms", text)]


def run_psql(sql: str) -> str:
    command = [
        "psql", "-X", "-v", "ON_ERROR_STOP=1", "-P", "pager=off",
        "-h", os.environ.get("PGHOST", "127.0.0.1"),
        "-p", os.environ.get("PGPORT", "5432"),
        "-d", os.environ.get("PGDATABASE", "practice4"),
        "-c", sql,
    ]
    completed = subprocess.run(command, check=True, text=True, capture_output=True)
    return completed.stdout.strip()


def wrap_sql(sql: str, width: int = 112) -> list[str]:
    lines: list[str] = []
    for raw_line in sql.splitlines():
        indent = len(raw_line) - len(raw_line.lstrip())
        subsequent = " " * min(indent + 2, 20)
        lines.extend(textwrap.wrap(
            raw_line.rstrip(), width=width,
            subsequent_indent=subsequent,
            replace_whitespace=False,
            drop_whitespace=False,
        ) or [""])
    return lines


def render_screen(number: int, phase: str, sql: str, result: str, elapsed_ms: float) -> Path:
    title_font = ImageFont.truetype(FONT_KR, 34)
    label_font = ImageFont.truetype(FONT_KR, 23)
    body_font = ImageFont.truetype(FONT_MONO, 19)
    result_font = ImageFont.truetype(FONT_KR, 19)

    sql_lines = wrap_sql(sql)
    result_lines = result.splitlines()
    line_height = 27
    width = 1760
    header_height = 94
    section_gap = 52
    height = max(760, header_height + (len(sql_lines) + len(result_lines)) * line_height + section_gap + 250)

    background = "#0d1117"
    panel = "#161b22"
    border = "#30363d"
    accent = "#f59e0b" if phase == "튜닝전" else "#58a6ff"
    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, width, header_height), fill=panel)
    draw.text((42, 24), f"Q{number:02d} {phase} — SQL Query 및 실행 결과", font=title_font, fill="#f0f6fc")
    timing = f"EXPLAIN ANALYZE  {elapsed_ms:.3f} ms"
    timing_width = draw.textbbox((0, 0), timing, font=label_font)[2]
    draw.text((width - timing_width - 42, 33), timing, font=label_font, fill=accent)

    x = 42
    y = header_height + 28
    draw.text((x, y), "SQL", font=label_font, fill=accent)
    y += 38
    sql_top = y
    sql_bottom = y + len(sql_lines) * line_height + 24
    draw.rounded_rectangle((28, sql_top - 14, width - 28, sql_bottom), radius=12, fill=panel, outline=border, width=2)
    for line in sql_lines:
        draw.text((x, y), line, font=body_font, fill="#c9d1d9")
        y += line_height

    y = sql_bottom + 28
    draw.text((x, y), "RESULT", font=label_font, fill=accent)
    y += 38
    result_top = y
    result_bottom = y + len(result_lines) * line_height + 24
    draw.rounded_rectangle((28, result_top - 14, width - 28, result_bottom), radius=12, fill=panel, outline=border, width=2)
    for line in result_lines:
        draw.text((x, y), line, font=result_font, fill="#d2e7d6")
        y += line_height

    draw.text((42, height - 46), "PostgreSQL 17.10 · 실매출 상태: paid/shipped/delivered · 2026-08-14", font=label_font, fill="#8b949e")

    SCREEN_DIR.mkdir(parents=True, exist_ok=True)
    output = SCREEN_DIR / f"Q{number:02d}_{phase}.png"
    image.save(output, optimize=True)
    return output


def main() -> None:
    variants = [
        (
            "튜닝전",
            ROOT / "종합실습4_01_튜닝전_쿼리.sql",
            RESULT_DIR / "종합실습4_튜닝전_실행결과.txt",
        ),
        (
            "튜닝후",
            ROOT / "종합실습4_03_튜닝후_쿼리.sql",
            RESULT_DIR / "종합실습4_튜닝후_실행결과.txt",
        ),
    ]
    generated: list[Path] = []
    results_by_phase: dict[str, dict[int, str]] = {}
    for phase, sql_path, result_path in variants:
        sections = question_sections(sql_path)
        times = execution_times(result_path)
        phase_results: dict[int, str] = {}
        if len(times) < 10:
            raise ValueError(f"{result_path.name}: 실행시간 10개를 찾지 못했습니다.")
        for number in range(1, 11):
            statement = result_statement(sections[number])
            result = run_psql(statement)
            phase_results[number] = result
            generated.append(render_screen(number, phase, statement, result, times[number - 1]))
        results_by_phase[phase] = phase_results

    mismatches = [
        number for number in range(1, 11)
        if results_by_phase["튜닝전"][number] != results_by_phase["튜닝후"][number]
    ]
    if mismatches:
        raise ValueError(f"튜닝 전후 결과 불일치: {mismatches}")
    print(f"generated={len(generated)} result_equivalence=passed directory={SCREEN_DIR}")


if __name__ == "__main__":
    main()
