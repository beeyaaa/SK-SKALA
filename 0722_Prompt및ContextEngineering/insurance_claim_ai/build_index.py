from pathlib import Path

from src.pdf_parsers import (
    parse_case_pdf,
    parse_law_pdf,
    parse_terms_pdf,
)
from src.vector_store import build_store


PROJECT_DIR = Path(__file__).resolve().parent
CASE_PDF = PROJECT_DIR / "data/case_law.pdf"
LAW_PDF = PROJECT_DIR / "data/laws.pdf"
TERMS_PDF = (
    PROJECT_DIR / "data/Sample_Automobile_Insurance_Policy_Terms.pdf"
)
VECTOR_DIR = PROJECT_DIR / "vector_db"


def main() -> None:
    if not CASE_PDF.exists():
        raise FileNotFoundError(
            f"판례 PDF를 배치하세요: {CASE_PDF}"
        )
    if not LAW_PDF.exists():
        raise FileNotFoundError(
            f"법률 PDF를 배치하세요: {LAW_PDF}"
        )
    if not TERMS_PDF.exists():
        raise FileNotFoundError(
            f"보험약관 PDF를 배치하세요: {TERMS_PDF}"
        )

    case_documents = parse_case_pdf(CASE_PDF)
    law_documents = parse_law_pdf(LAW_PDF)
    terms_documents, terms_profile = parse_terms_pdf(TERMS_PDF)

    build_store(
        "case_law",
        case_documents,
        VECTOR_DIR / "case_law",
    )
    build_store(
        "statute",
        law_documents,
        VECTOR_DIR / "statute",
    )
    build_store(
        "terms",
        terms_documents,
        VECTOR_DIR / "terms",
    )

    print(f"판례 청크: {len(case_documents)}")
    print(f"법률 청크: {len(law_documents)}")
    print(f"약관 청크: {len(terms_documents)}")
    print(f"약관 버전: {terms_profile['terms_version']}")


if __name__ == "__main__":
    main()
