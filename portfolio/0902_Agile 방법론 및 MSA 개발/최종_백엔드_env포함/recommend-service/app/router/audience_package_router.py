import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.config.security import verify_token
from app.model.schemas import (
    AudienceSummary,
    PersonaBundleGenerationRequest,
    PersonaBundleResponse,
    PersonaGenerationRequest,
    PersonaGenerationResponse,
)
from app.service.audience_package_service import audience_package_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recommend", tags=["persona-bundles"])


@router.get("/audiences", response_model=List[AudienceSummary])
async def get_audiences(_token_payload: dict = Depends(verify_token)):
    try:
        return await audience_package_service.get_audiences()
    except Exception as error:
        logger.exception("[AudiencePackageRouter] 수강생 목록 조회 실패")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="수강생과 수강 이력을 불러오지 못했습니다.",
        ) from error


@router.post("/personas/generate", response_model=PersonaGenerationResponse)
async def generate_personas(
    request: PersonaGenerationRequest,
    _token_payload: dict = Depends(verify_token),
):
    try:
        return await audience_package_service.generate_personas(request.maxPersonaCount)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except Exception as error:
        logger.exception("[AudiencePackageRouter] 페르소나 생성 실패")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="전체 수강생의 페르소나 분석을 완료하지 못했습니다.",
        ) from error


@router.post("/persona-bundles/generate", response_model=PersonaBundleResponse)
async def generate_persona_bundles(
    request: PersonaBundleGenerationRequest,
    _token_payload: dict = Depends(verify_token),
):
    try:
        return await audience_package_service.generate_persona_bundles(request)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except Exception as error:
        logger.exception("[AudiencePackageRouter] 페르소나별 번들 생성 실패")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="페르소나별 번들 생성을 완료하지 못했습니다.",
        ) from error
