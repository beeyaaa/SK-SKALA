import logging
from typing import List

import httpx

from app.config.settings import settings
from app.model.schemas import UserSummary

logger = logging.getLogger(__name__)


class UserServiceClient:
    """User Service가 소유한 사용자 데이터를 REST API로 조회한다."""

    def __init__(self) -> None:
        self.base_url = settings.user_service_url

    async def get_user(self, user_id: int) -> UserSummary:
        url = f"{self.base_url}/api/users/internal/{user_id}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return UserSummary(**response.json())

    async def get_students(self) -> List[UserSummary]:
        """DB에 등록된 STUDENT 전체를 ID 순으로 조회한다.

        Recommend Service가 users 테이블에 직접 연결하지 않고 User Service의 내부
        API를 이용함으로써 MSA의 데이터 소유 경계를 지킨다.
        """
        url = f"{self.base_url}/api/users/internal/students"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return [UserSummary(**item) for item in response.json()]


user_client = UserServiceClient()
