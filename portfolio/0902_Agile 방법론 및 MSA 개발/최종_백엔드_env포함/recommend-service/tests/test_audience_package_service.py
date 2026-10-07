import unittest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from pydantic import SecretStr

from app.client.course_client import course_client
from app.client.enrollment_client import enrollment_client
from app.client.user_client import user_client
from app.config.settings import settings
from app.model.schemas import (
    CourseCategory,
    CourseResponse,
    EnrollmentHistoryResponse,
    PersonaBundleGenerationRequest,
    UserSummary,
)
from app.service.audience_package_service import audience_package_service


class AudiencePackageServiceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user_ids = list(range(201, 207))
        self.users = {
            user_id: UserSummary(
                id=user_id,
                email=f"user{user_id}@lecture.local",
                name=f"user{user_id}",
                role="STUDENT",
            )
            for user_id in self.user_ids
        }
        categories = [
            CourseCategory.FRONTEND,
            CourseCategory.BACKEND,
            CourseCategory.DEVOPS,
        ]
        self.courses = [
            CourseResponse(
                id=index,
                title=f"{category.value} 실무 과정 {index}",
                description=f"{category.value} 기술을 단계적으로 학습합니다.",
                category=category,
                price=Decimal("50000"),
                instructorId=100,
                enrollmentCount=100 + index,
                status="ACTIVE",
            )
            for index, category in enumerate(
                (categories * 12), start=1
            )
        ]
        self.histories = {
            201: EnrollmentHistoryResponse(userId=201, activeCourseIds=[1, 4]),
            202: EnrollmentHistoryResponse(userId=202, activeCourseIds=[7, 10]),
            203: EnrollmentHistoryResponse(userId=203, activeCourseIds=[2, 5]),
            204: EnrollmentHistoryResponse(userId=204, activeCourseIds=[8, 11]),
            205: EnrollmentHistoryResponse(userId=205, activeCourseIds=[3, 6]),
            206: EnrollmentHistoryResponse(userId=206, activeCourseIds=[9, 12]),
        }

    def _dependencies(self):
        return (
            patch.object(audience_package_service, "audience_user_ids", self.user_ids),
            patch.object(
                user_client,
                "get_students",
                AsyncMock(return_value=list(self.users.values())),
            ),
            patch.object(
                enrollment_client,
                "get_enrollment_history",
                AsyncMock(side_effect=lambda user_id: self.histories[user_id]),
            ),
            patch.object(
                course_client,
                "get_all_courses",
                AsyncMock(return_value=self.courses),
            ),
            patch.object(settings, "openai_api_key", SecretStr("")),
        )

    async def test_generates_personas_as_a_complete_partition(self):
        patches = self._dependencies()
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            result = await audience_package_service.generate_personas(3)

        self.assertLessEqual(len(result.personas), 3)
        self.assertGreaterEqual(len(result.personas), 3)
        member_ids = [
            user_id
            for persona in result.personas
            for user_id in persona.memberUserIds
        ]
        self.assertEqual(set(member_ids), set(self.user_ids))
        self.assertEqual(len(member_ids), len(set(member_ids)))

    async def test_generates_one_bundle_for_each_approved_persona(self):
        patches = self._dependencies()
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            personas = await audience_package_service.generate_personas(3)
            result = await audience_package_service.generate_persona_bundles(
                PersonaBundleGenerationRequest(
                    personas=personas.personas,
                    minBundleSize=3,
                    maxBundleSize=6,
                )
            )

        self.assertEqual(len(result.personas), len(personas.personas))
        self.assertEqual(
            {item.personaId for item in result.personas},
            {item.personaId for item in personas.personas},
        )
        for item in result.personas:
            self.assertGreaterEqual(len(item.bundle.courses), 3)
            self.assertLessEqual(len(item.bundle.courses), 6)
            course_ids = [course.courseId for course in item.bundle.courses]
            self.assertEqual(len(course_ids), len(set(course_ids)))


if __name__ == "__main__":
    unittest.main()
