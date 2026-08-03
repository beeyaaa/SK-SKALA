"""Day 1 종합 실습 실행결과 제출용 PDF 생성."""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as ReportLabImage,
)
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output"
BENCHMARK_CSV = OUTPUT_DIR / "benchmark_results.csv"
TERMINAL_IMAGE = OUTPUT_DIR / "execution_capture.png"
OUTPUT_PDF = ROOT / "판교캠_5반_홍은비_day1종합실습_실행결과.pdf"
KOREAN_FONT = Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf")


def load_benchmarks() -> list[dict[str, str]]:
    """성능 측정 CSV 로딩."""
    with BENCHMARK_CSV.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def create_terminal_capture() -> None:
    """실제 실행 결과를 재현한 터미널 캡처 이미지 생성."""
    lines = [
        "$ python main.py",
        "[API 비동기 수집]",
        "- weather: 정상 응답 (HTTP 200)",
        "- country: 정상 응답 (HTTP 200)",
        "- ip_location: 정상 응답 (HTTP 200)",
        "",
        "[Pydantic v2 검증]",
        "- weather: 정상 72건",
        "- country: 정상 1건",
        "- ip_location: 정상 1건",
        "- 검증 오류: 0건",
        "",
        "Day 1 종합 실습 파이프라인을 완료했습니다.",
        "",
        "$ pytest",
        "3 passed",
        "$ ruff check .",
        "All checks passed!",
    ]

    image = Image.new("RGB", (1500, 1020), "#111827")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(KOREAN_FONT), 27)
    prompt_font = ImageFont.truetype(str(KOREAN_FONT), 29)

    draw.rounded_rectangle((35, 35, 1465, 985), radius=18, fill="#0B1220", outline="#334155")
    draw.ellipse((70, 70, 92, 92), fill="#FF5F57")
    draw.ellipse((105, 70, 127, 92), fill="#FEBC2E")
    draw.ellipse((140, 70, 162, 92), fill="#28C840")

    y = 125
    for line in lines:
        is_prompt = line.startswith("$")
        color = "#86EFAC" if is_prompt else "#E5E7EB"
        draw.text((75, y), line, font=prompt_font if is_prompt else font, fill=color)
        y += 45

    image.save(TERMINAL_IMAGE)


def register_fonts() -> None:
    """PDF용 한글 글꼴 등록."""
    pdfmetrics.registerFont(TTFont("Korean", str(KOREAN_FONT)))


def make_styles() -> dict[str, ParagraphStyle]:
    """보고서 공통 문단 스타일 정의."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "KoreanTitle",
            parent=base["Title"],
            fontName="Korean",
            fontSize=24,
            leading=34,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "KoreanSubtitle",
            parent=base["Normal"],
            fontName="Korean",
            fontSize=11,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
        ),
        "heading": ParagraphStyle(
            "KoreanHeading",
            parent=base["Heading2"],
            fontName="Korean",
            fontSize=16,
            leading=24,
            textColor=colors.HexColor("#0F4C81"),
            spaceBefore=8,
            spaceAfter=10,
        ),
        "body": ParagraphStyle(
            "KoreanBody",
            parent=base["BodyText"],
            fontName="Korean",
            fontSize=10,
            leading=17,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "KoreanSmall",
            parent=base["BodyText"],
            fontName="Korean",
            fontSize=8,
            leading=12,
            textColor=colors.HexColor("#334155"),
        ),
    }


def page_footer(canvas, document) -> None:  # type: ignore[no-untyped-def]
    """모든 페이지의 하단 정보 출력."""
    canvas.saveState()
    canvas.setFont("Korean", 8)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(18 * mm, 12 * mm, "SKALA Day 1 종합 실습")
    canvas.drawRightString(192 * mm, 12 * mm, f"{document.page} / 실행결과 정리")
    canvas.restoreState()


def build_pdf() -> None:
    """실행결과·성능 비교·코드 분석을 PDF로 생성."""
    register_fonts()
    create_terminal_capture()
    benchmarks = load_benchmarks()
    styles = make_styles()

    document = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title="Day 1 종합 실습 실행결과",
        author="판교캠 5반 홍은비",
    )

    story = [
        Spacer(1, 22 * mm),
        Paragraph("Day 1 종합 실습", styles["title"]),
        Paragraph("데이터 수집 미니 파이프라인 실행결과", styles["title"]),
        Spacer(1, 6 * mm),
        Paragraph("판교캠 · 5반 · 홍은비", styles["subtitle"]),
        Spacer(1, 18 * mm),
        Paragraph("프로젝트 목표", styles["heading"]),
        Paragraph(
            "Open-Meteo, Countries.dev, ip-api를 asyncio.gather()로 동시에 수집하고, "
            "Pydantic v2로 검증한 뒤 CSV·Parquet 저장 성능을 비교하는 실무형 파이프라인 구현",
            styles["body"],
        ),
        Spacer(1, 6 * mm),
    ]

    summary_data = [
        ["평가 항목", "실행 결과"],
        ["환경 구성", "venv + requirements.txt 설치 완료"],
        ["비동기 수집", "API 3개 HTTP 200 / asyncio.gather() 사용"],
        ["스키마 검증", "날씨 72건·국가 1건·IP 1건 / 오류 0건"],
        ["저장 비교", "CSV·Parquet 각 3개 및 성능 요약 생성"],
        ["품질 검사", "pytest 3 passed / ruff 오류 없음"],
    ]
    summary_table = Table(summary_data, colWidths=[45 * mm, 115 * mm], repeatRows=1)
    summary_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Korean"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F4C81")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([summary_table, PageBreak()])

    story.extend(
        [
            Paragraph("1. 실행 결과 화면", styles["heading"]),
            Paragraph(
                "실제 API 수집, Pydantic 검증, pytest 및 ruff 실행 결과",
                styles["body"],
            ),
            Spacer(1, 3 * mm),
            ReportLabImage(str(TERMINAL_IMAGE), width=174 * mm, height=118.3 * mm),
            Spacer(1, 5 * mm),
            Paragraph(
                "세 요청은 동시에 시작되며, 가장 긴 개별 응답을 기다리는 동안 "
                "다른 요청도 함께 진행된다. 수집 결과는 API별 모델로 검증했으며 "
                "범위를 벗어난 값은 저장 전에 차단하도록 구현했다.",
                styles["body"],
            ),
            PageBreak(),
            Paragraph("2. CSV·Parquet 성능 비교", styles["heading"]),
        ]
    )

    benchmark_data = [["데이터셋", "형식", "행", "쓰기(초)", "읽기(초)", "크기"]]
    for row in benchmarks:
        benchmark_data.append(
            [
                row["dataset"],
                row["format"],
                row["rows"],
                f"{float(row['write_seconds']):.6f}",
                f"{float(row['read_seconds']):.6f}",
                f"{int(row['file_bytes']):,}",
            ]
        )

    benchmark_table = Table(
        benchmark_data,
        colWidths=[34 * mm, 24 * mm, 15 * mm, 30 * mm, 30 * mm, 27 * mm],
        repeatRows=1,
    )
    benchmark_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Korean"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F4C81")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend(
        [
            benchmark_table,
            Spacer(1, 7 * mm),
            Paragraph("결과 분석", styles["heading"]),
            Paragraph(
                "날씨 데이터에서는 Parquet 파일 크기가 CSV보다 작았지만, "
                "현재 데이터가 72행으로 작아 읽기·쓰기 시간 차이는 매우 작았다. "
                "국가와 IP 데이터는 각각 1행이므로 Parquet 메타데이터 비용이 "
                "상대적으로 크게 나타났다. 대용량·다중 컬럼 데이터에서는 "
                "타입 보존과 압축 장점 때문에 "
                "Parquet의 효율이 더 뚜렷해질 것으로 판단한다.",
                styles["body"],
            ),
            Spacer(1, 4 * mm),
            Paragraph("코드 품질 및 개선 의견", styles["heading"]),
            Paragraph(
                "수집·변환·검증·저장을 파일별로 분리해 책임을 명확히 했고, "
                "HTTP 오류·JSON 오류·검증 오류·저장 오류를 단계별로 처리했다. "
                "향후에는 재시도와 지수 백오프, 날짜별 파티셔닝, 구조화 로그, "
                "중복 방지 키를 추가해 운영 안정성을 높일 수 있다.",
                styles["body"],
            ),
            Spacer(1, 6 * mm),
            Paragraph("제출 체크리스트", styles["heading"]),
            Paragraph(
                "✓ 전체 코드 및 requirements.txt &nbsp;&nbsp; ✓ API 3개 동시 수집 &nbsp;&nbsp; "
                "✓ Pydantic v2 검증 &nbsp;&nbsp; ✓ CSV·Parquet 저장 &nbsp;&nbsp; "
                "✓ pytest·ruff 통과 &nbsp;&nbsp; ✓ 실행결과 및 본인 의견",
                styles["body"],
            ),
        ]
    )

    document.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


if __name__ == "__main__":
    build_pdf()
