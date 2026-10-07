import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.config.security import verify_token
from app.model.schemas import PackageDraftRequest, PackageDraftResponse
from app.service.package_draft_service import package_draft_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recommend", tags=["package-draft"])


@router.post("/package-draft", response_model=PackageDraftResponse)
async def generate_package_draft(
    request: PackageDraftRequest,
    _token_payload: dict = Depends(verify_token),
):
    """실제 강의 정보, 목 판매 데이터와 OpenAI를 이용해 상품기획 초안을 생성한다."""
    try:
        return await package_draft_service.generate_package_draft(request)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except Exception as error:
        logger.exception("[PackageDraftRouter] 패키지 초안 생성 실패")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="패키지 초안 생성 서비스를 일시적으로 사용할 수 없습니다.",
        ) from error

