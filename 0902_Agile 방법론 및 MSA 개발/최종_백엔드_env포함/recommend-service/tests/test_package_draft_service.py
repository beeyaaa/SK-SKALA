import unittest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from pydantic import SecretStr

from app.client.course_client import course_client
from app.config.settings import settings
from app.model.schemas import CourseCategory, CourseResponse, PackageDraftRequest
from app.service.package_draft_service import package_draft_service


class PackageDraftServiceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.courses = [
            CourseResponse(
                id=1,
                title="Spring Boot 기초",
                description="Spring Boot와 REST API 입문",
                category=CourseCategory.BACKEND,
                price=Decimal("89000"),
                instructorId=4,
                enrollmentCount=10,
                status="ACTIVE",
            ),
            CourseResponse(
                id=2,
                title="Spring Boot MSA",
                description="Spring 기반 MSA 프로젝트",
                category=CourseCategory.BACKEND,
                price=Decimal("129000"),
                instructorId=4,
                enrollmentCount=8,
                status="ACTIVE",
            ),
            CourseResponse(
                id=3,
                title="Vue.js 기초",
                description="Vue 프론트엔드 입문",
                category=CourseCategory.FRONTEND,
                price=Decimal("79000"),
                instructorId=4,
                enrollmentCount=5,
                status="ACTIVE",
            ),
        ]

    async def test_rule_based_fallback_uses_real_course_ids_and_server_price(self):
        request = PackageDraftRequest(
            persona="MSA 프로젝트에 투입되는 신입 백엔드 개발자",
            goal="Spring Boot부터 MSA까지 단계적으로 학습",
            bundleSize=2,
            maxBudget=250000,
        )

        with (
            patch.object(
                course_client,
                "get_all_courses",
                AsyncMock(return_value=self.courses),
            ),
            patch.object(settings, "openai_api_key", SecretStr("")),
        ):
            result = await package_draft_service.generate_package_draft(request)

        self.assertEqual(result.mode, "RULE_BASED")
        self.assertEqual([course.id for course in result.courses], [1, 2])
        self.assertEqual(result.originalPrice, 218000)
        self.assertEqual(result.discountRate, 10)
        self.assertEqual(result.packagePrice, 196200)
        self.assertEqual(result.coPurchaseCount, 145)

    async def test_bundle_size_is_selected_from_persona_level(self):
        request = PackageDraftRequest(
            persona="처음 프로젝트에 투입되는 신입 백엔드 개발자",
            goal="Spring Boot와 MSA의 기초를 단계적으로 학습",
        )

        with (
            patch.object(
                course_client,
                "get_all_courses",
                AsyncMock(return_value=self.courses),
            ),
            patch.object(settings, "openai_api_key", SecretStr("")),
        ):
            result = await package_draft_service.generate_package_draft(request)

        self.assertEqual(result.mode, "RULE_BASED")
        self.assertEqual(len(result.courses), 2)

    def test_ai_validation_rejects_invented_course_id(self):
        candidates = [
            {
                "courseIds": [1, 2],
                "courses": self.courses[:2],
            }
        ]
        invalid_result = {
            "candidateIndex": 0,
            "orderedCourseIds": [1, 999],
            "courseReasons": [
                {"courseId": 1, "reason": "기초 학습"},
                {"courseId": 999, "reason": "존재하지 않는 강의"},
            ],
        }

        with self.assertRaises(ValueError):
            package_draft_service._validate_ai_result(
                invalid_result,
                candidates,
            )


if __name__ == "__main__":
    unittest.main()
