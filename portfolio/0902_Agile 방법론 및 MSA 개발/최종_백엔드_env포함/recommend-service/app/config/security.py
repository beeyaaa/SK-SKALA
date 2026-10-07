from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config.settings import settings


# direct 모드에서는 브라우저가 Bearer Token 없이 Recommend Service로 접근하므로
# LOCAL_DEV_BYPASS_AUTH를 확인하기 전 HTTPBearer가 먼저 403을 내지 않도록 한다.
security = HTTPBearer(auto_error=False)

_jwks_cache: dict = {}


async def get_jwks() -> dict:
    global _jwks_cache
    if not _jwks_cache:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.jwk_set_uri)
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache


def get_signing_key(token: str, jwks: dict) -> dict:
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 헤더에 kid가 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="일치하는 공개키를 찾을 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    # 로컬 전용 우회. docker-compose.local.yml에서 true를 주입할 때만 동작한다.
    if settings.local_dev_bypass_auth:
        return {
            "sub": "local-dev",
            "scope": "service.read",
            "localDev": True,
        }

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer 토큰이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        jwks = await get_jwks()
        signing_key = get_signing_key(token, jwks)

        return jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=settings.jwt_issuer_uri,
            options={"verify_aud": False},
        )
    except JWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"유효하지 않은 토큰입니다: {str(error)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


async def verify_service_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    payload = await verify_token(credentials)
    scopes = payload.get("scope", "").split()

    if "service.read" not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="서비스 권한이 없습니다",
        )

    return payload
