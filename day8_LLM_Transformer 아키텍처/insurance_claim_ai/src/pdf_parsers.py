from __future__ import annotations

import hashlib
import re
from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader


CASE_NO_RE = re.compile(
    r"\d{2,4}\s*(?:다|가단|가합|나|도|누)\s*\d+"
    r"(?:\(본소\))?(?:,\s*\d{2,4}\s*(?:다|가단|가합|나|도|누)\s*\d+\(반소\))?"
)
DATE_RE = re.compile(r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.")
COURT_RE = re.compile(
    r"(대법원(?:\s*전원합의체)?|[가-힣]+고등법원|[가-힣]+지방법원)"
)
FAULT_RE = re.compile(r"(\d{1,3})%")
ARTICLE_RE = re.compile(
    r"(?m)^(제\s*\d+\s*조(?:의\s*\d+)?(?:\([^)]*\))?)"
    r"(?:\s*-\s*[^\n]*)?\s*$"
)

LAW_NAMES = (
    "도로교통법 시행규칙",
    "자동차손해배상 보장법",
    "도로교통법",
    "민법",
)
TERM_ARTICLE_RE = re.compile(
    r"(?m)^제\s*(\d+)\s*조\s*\(([^)\n]+)\)\s*$"
)


def _page_texts(pdf_path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(pdf_path))
    return [
        (index, page.extract_text() or "")
        for index, page in enumerate(reader.pages, start=1)
    ]


def _file_hash(pdf_path: Path) -> str:
    return hashlib.sha256(pdf_path.read_bytes()).hexdigest()


def _date(text: str) -> str | None:
    matched = DATE_RE.search(text)
    if not matched:
        return None
    year, month, day = matched.groups()
    return f"{year}-{int(month):02d}-{int(day):02d}"


def _normalize_case_no(value: str | None) -> str:
    return re.sub(r"\s+", "", value or "")


def _first_nonempty(lines: list[str], prefix: str) -> str:
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            same_line = line[len(prefix):].strip()
            if same_line:
                return same_line
        if prefix in line and index + 1 < len(lines):
            following = lines[index + 1].strip()
            if following:
                return following
    return ""


def parse_case_pdf(pdf_path: Path) -> list[Document]:
    documents: list[Document] = []
    file_hash = _file_hash(pdf_path)

    # 제공된 사례집은 3페이지부터 페이지당 판례 1건으로 구성됩니다.
    for page_number, text in _page_texts(pdf_path):
        case_match = CASE_NO_RE.search(text)
        court_match = COURT_RE.search(text)
        if page_number < 3 or not case_match or not court_match:
            continue

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        case_no = _normalize_case_no(case_match.group())
        decision_date = _date(text) or ""
        percentages = FAULT_RE.findall(text)
        accident_type = _first_nonempty(lines, "사고 유형")

        metadata = {
            "document_type": "case_law",
            "case_no": case_no,
            "court": court_match.group(),
            "decision_date": decision_date,
            "accident_type": accident_type,
            "fault_ratio_text": ",".join(percentages[:2]),
            "source_file": pdf_path.name,
            "pdf_page": page_number,
            "file_hash": file_hash,
            "metadata_verified": True,
        }
        documents.append(Document(page_content=text, metadata=metadata))

    return documents


def _detect_law_name(text: str, current: str | None) -> str | None:
    for name in LAW_NAMES:
        if re.search(rf"(?m)^\s*{re.escape(name)}\s*$", text):
            return name
    return current


def _split_articles(text: str) -> list[tuple[str, str]]:
    parts = ARTICLE_RE.split(text)
    results: list[tuple[str, str]] = []
    current_heading: str | None = None

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if ARTICLE_RE.fullmatch(part):
            current_heading = part
        elif current_heading:
            results.append((current_heading, part))
    return results


def _article_fields(heading: str) -> tuple[str, str]:
    article_match = re.search(
        r"제\s*(\d+)\s*조(?:의\s*(\d+))?",
        heading,
    )
    title_match = re.search(r"\(([^)]*)\)", heading)
    if not article_match:
        return heading, ""

    article = f"제{article_match.group(1)}조"
    if article_match.group(2):
        article += f"의{article_match.group(2)}"
    article_title = (
        re.sub(r"\s+", " ", title_match.group(1)).strip()
        if title_match else ""
    )
    return article, article_title


def parse_law_pdf(pdf_path: Path) -> list[Document]:
    documents: list[Document] = []
    current_law: str | None = None
    current_effective_date: str | None = None
    file_hash = _file_hash(pdf_path)

    for page_number, text in _page_texts(pdf_path):
        if page_number < 3:
            continue

        current_law = _detect_law_name(text, current_law)
        page_effective_date = _date(text)
        if page_effective_date:
            current_effective_date = page_effective_date

        for heading, body in _split_articles(text):
            article, article_title = _article_fields(heading)
            content = f"{current_law or ''} {heading}\n{body}".strip()
            metadata = {
                "document_type": "statute",
                "law_name": current_law or "법률명 확인 필요",
                "effective_date": current_effective_date or "",
                "article": article,
                "article_title": article_title,
                "source_file": pdf_path.name,
                "pdf_page": page_number,
                "file_hash": file_hash,
                "metadata_verified": True,
            }
            documents.append(Document(page_content=content, metadata=metadata))

    return documents


def _terms_profile(pdf_path: Path) -> dict:
    pages = _page_texts(pdf_path)
    all_text = "\n".join(text for _, text in pages)
    first_page = pages[0][1] if pages else ""
    summary_page = pages[1][1] if len(pages) > 1 else ""

    version_match = re.search(
        r"약관\s*버전\s+([A-Z0-9.-]+)",
        first_page,
    )
    property_limit_match = re.search(
        r"COV-01.*?(\d+(?:,\d{3})*)\s*억원",
        summary_page,
        re.DOTALL,
    )
    own_limit_match = re.search(
        r"COV-02.*?(\d+(?:,\d{3})*)\s*만원",
        summary_page,
        re.DOTALL,
    )
    deductible_match = re.search(
        r"자기부담금은.*?(\d+)%.*?최소\s*(\d+)\s*만원.*?"
        r"최대\s*(\d+)\s*만원",
        all_text,
        re.DOTALL,
    )
    rounding_match = re.search(
        r"최종\s*합계는\s*(\d+(?:,\d{3})*)\s*원\s*단위",
        all_text,
    )

    required = {
        "version": version_match,
        "property limit": property_limit_match,
        "own damage limit": own_limit_match,
        "deductible": deductible_match,
        "rounding": rounding_match,
    }
    missing = [name for name, matched in required.items() if not matched]
    if missing:
        raise ValueError(
            f"약관 핵심 산식 파싱 실패: {', '.join(missing)}"
        )

    return {
        "product_code": "SMARTDRIVE-STANDARD",
        "product_name": "SmartDrive 자동차보험 - Standard Plan",
        "terms_version": version_match.group(1),
        "property_damage_limit": (
            int(property_limit_match.group(1).replace(",", ""))
            * 100_000_000
        ),
        "own_vehicle_damage_limit": (
            int(own_limit_match.group(1).replace(",", ""))
            * 10_000
        ),
        "deductible_rate": int(deductible_match.group(1)) / 100,
        "minimum_deductible": int(deductible_match.group(2)) * 10_000,
        "maximum_deductible": int(deductible_match.group(3)) * 10_000,
        "subtract_counterparty_recovery": True,
        "final_rounding_unit": int(
            rounding_match.group(1).replace(",", "")
        ),
    }


def parse_terms_pdf(
    pdf_path: Path,
) -> tuple[list[Document], dict]:
    documents: list[Document] = []
    profile = _terms_profile(pdf_path)
    file_hash = _file_hash(pdf_path)

    for page_number, text in _page_texts(pdf_path):
        matches = list(TERM_ARTICLE_RE.finditer(text))
        for index, matched in enumerate(matches):
            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(text)
            )
            article_number, article_title = matched.groups()
            article = f"제{article_number}조"
            content = text[matched.start():end].strip()
            documents.append(Document(
                page_content=content,
                metadata={
                    "document_type": "terms",
                    "product_code": profile["product_code"],
                    "product_name": profile["product_name"],
                    "terms_version": profile["terms_version"],
                    "article": article,
                    "article_title": article_title.strip(),
                    "source_file": pdf_path.name,
                    "pdf_page": page_number,
                    "file_hash": file_hash,
                    "metadata_verified": True,
                },
            ))

    if not documents:
        raise ValueError("약관 조문을 찾지 못했습니다.")
    return documents, profile
