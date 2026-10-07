import asyncio
import json
import logging
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

import httpx

from app.client.course_client import course_client
from app.client.enrollment_client import enrollment_client
from app.client.user_client import user_client
from app.config.settings import settings
from app.model.schemas import (
    AudienceCourse,
    AudiencePackageRecommendation,
    AudiencePackageResponse,
    AudienceSummary,
    CoPurchaseEvidence,
    CourseResponse,
    InferredPersona,
    PackageRecommendationCourse,
    UserSummary,
)
from app.service.package_draft_service import package_draft_service

logger = logging.getLogger(__name__)


class AudiencePackageService:
    """수강 이력으로 페르소나를 추론하고 사용자별 패키지 3개를 제안한다."""

    CATEGORY_LABELS = {
        "BACKEND": "백엔드",
        "FRONTEND": "프론트엔드",
        "DEVOPS": "DevOps",
        "DATA_SCIENCE": "데이터",
        "DATABASE": "데이터베이스",
        "SECURITY": "보안",
        "MOBILE": "모바일",
        "OTHER": "AI",
    }

    POSITION_LABELS = {
        "BACKEND": "백엔드 개발자",
        "FRONTEND": "프론트엔드 개발자",
        "DEVOPS": "DevOps 엔지니어",
        "DATA_SCIENCE": "데이터 분석가",
        "DATABASE": "데이터 엔지니어",
        "SECURITY": "보안 엔지니어",
        "MOBILE": "모바일 개발자",
        "OTHER": "AI 개발자",
    }

    ADJACENT_CATEGORIES = {
        "BACKEND": ["DATABASE", "DEVOPS", "SECURITY"],
        "FRONTEND": ["MOBILE", "BACKEND", "DEVOPS"],
        "DEVOPS": ["BACKEND", "SECURITY", "DATABASE"],
        "DATA_SCIENCE": ["OTHER", "DATABASE", "DEVOPS"],
        "DATABASE": ["BACKEND", "DATA_SCIENCE", "DEVOPS"],
        "SECURITY": ["BACKEND", "DEVOPS", "DATABASE"],
        "MOBILE": ["FRONTEND", "BACKEND", "DEVOPS"],
        "OTHER": ["DATA_SCIENCE", "DEVOPS", "BACKEND"],
    }

    def __init__(self) -> None:
        self.sales_data = package_draft_service.sales_data
        self.sales_by_course_id = {
            int(item["courseId"]): int(item["salesCount"])
            for item in self.sales_data.get("courseSales", [])
        }
        self.audience_user_ids = [
            int(user_id)
            for user_id in self.sales_data.get("metadata", {}).get("audienceUserIds", [])
        ]

    async def get_audiences(self) -> List[AudienceSummary]:
        if not self.audience_user_ids:
            return []
        students, courses = await asyncio.gather(
            asyncio.gather(*(user_client.get_user(user_id) for user_id in self.audience_user_ids)),
            course_client.get_all_courses(),
        )
        course_map = {course.id: course for course in courses}
        histories = await asyncio.gather(
            *(enrollment_client.get_enrollment_history(student.id) for student in students)
        )

        audiences: List[AudienceSummary] = []
        for student, history in zip(students, histories):
            enrolled_courses = [
                self._to_audience_course(course_map[course_id])
                for course_id in history.activeCourseIds
                if course_id in course_map
            ]
            audiences.append(
                AudienceSummary(
                    userId=student.id,
                    userName=student.name,
                    email=student.email,
                    enrollmentCount=len(enrolled_courses),
                    enrolledCourses=enrolled_courses,
                )
            )
        return audiences

    async def generate_packages(self, user_id: int) -> AudiencePackageResponse:
        user, history, courses = await asyncio.gather(
            user_client.get_user(user_id),
            enrollment_client.get_enrollment_history(user_id),
            course_client.get_all_courses(),
        )
        if user.role != "STUDENT":
            raise ValueError("수강생 계정만 분석할 수 있습니다.")

        active_courses = [course for course in courses if course.status == "ACTIVE"]
        course_map = {course.id: course for course in active_courses}
        enrolled_courses = [
            course_map[course_id]
            for course_id in history.activeCourseIds
            if course_id in course_map
        ]
        enrolled_ids = {course.id for course in enrolled_courses}
        shortlist = self._build_shortlist(active_courses, enrolled_courses, enrolled_ids)

        if len(shortlist) < 6:
            raise ValueError("추천 패키지를 구성할 강의가 부족합니다.")

        ai_result = await self._generate_ai_result(user, enrolled_courses, shortlist)
        if ai_result:
            try:
                self._validate_result(ai_result, {course.id for course in shortlist}, enrolled_ids)
            except ValueError as error:
                logger.warning("[AudiencePackage] AI 결과 검증 실패, 규칙 기반으로 대체: %s", error)
                ai_result = None
        mode = "AI" if ai_result else "RULE_BASED"
        result = ai_result or self._build_fallback_result(user, enrolled_courses, shortlist)

        self._validate_result(result, {course.id for course in shortlist}, enrolled_ids)
        packages = self._build_packages(user.id, result["packages"], course_map)

        return AudiencePackageResponse(
            mode=mode,
            generatedAt=datetime.now(timezone.utc),
            user=user,
            persona=InferredPersona(**result["persona"]),
            enrollmentHistory=[self._to_audience_course(course) for course in enrolled_courses],
            packages=packages,
        )

    def _build_shortlist(
        self,
        courses: List[CourseResponse],
        enrolled_courses: List[CourseResponse],
        enrolled_ids: Set[int],
    ) -> List[CourseResponse]:
        category_counts = Counter(course.category.value for course in enrolled_courses)
        primary_categories = [category for category, _ in category_counts.most_common(2)]
        history_text = " ".join(
            f"{course.title} {course.description or ''}" for course in enrolled_courses
        ).lower()
        history_terms = {
            term
            for term in re.findall(r"[0-9a-zA-Z가-힣.+#]+", history_text)
            if len(term) >= 2
        }

        def score(course: CourseResponse) -> int:
            category = course.category.value
            value = self._sales_count(course.id, course)
            if category in primary_categories:
                value += 1200
            if any(
                category in self.ADJACENT_CATEGORIES.get(primary, [])
                for primary in primary_categories
            ):
                value += 300
            searchable = f"{course.title} {course.description or ''}".lower()
            value += sum(70 for term in history_terms if term in searchable)
            return value

        available = [course for course in courses if course.id not in enrolled_ids]
        ranked = sorted(available, key=score, reverse=True)
        selected = ranked[:24]
        selected_ids = {course.id for course in selected}

        # LLM이 다른 성장 경로도 비교할 수 있도록 각 도메인의 인기 강의를 보강한다.
        for category in self.CATEGORY_LABELS:
            category_courses = sorted(
                [course for course in available if course.category.value == category],
                key=lambda course: self._sales_count(course.id, course),
                reverse=True,
            )[:2]
            for course in category_courses:
                if course.id not in selected_ids:
                    selected.append(course)
                    selected_ids.add(course.id)
        return selected[:32]

    async def _generate_ai_result(
        self,
        user: UserSummary,
        enrolled_courses: List[CourseResponse],
        shortlist: List[CourseResponse],
    ) -> Optional[Dict[str, Any]]:
        api_key = settings.openai_api_key.get_secret_value()
        if not api_key:
            logger.info("[AudiencePackage] API 키가 없어 규칙 기반 결과를 반환합니다.")
            return None

        response_schema = {
            "type": "object",
            "properties": {
                "persona": {
                    "type": "object",
                    "properties": {
                        "position": {"type": "string"},
                        "level": {"type": "string"},
                        "interests": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                            "maxItems": 4,
                        },
                        "summary": {"type": "string"},
                    },
                    "required": ["position", "level", "interests", "summary"],
                    "additionalProperties": False,
                },
                "packages": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "properties": {
                            "packageName": {"type": "string"},
                            "summary": {"type": "string"},
                            "courseRecommendations": {
                                "type": "array",
                                "minItems": 2,
                                "maxItems": 4,
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "courseId": {"type": "integer"},
                                        "reason": {"type": "string"},
                                    },
                                    "required": ["courseId", "reason"],
                                    "additionalProperties": False,
                                },
                            },
                            "recommendationReason": {"type": "string"},
                        },
                        "required": [
                            "packageName",
                            "summary",
                            "courseRecommendations",
                            "recommendationReason",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["persona", "packages"],
            "additionalProperties": False,
        }

        payload = {
            "userName": user.name,
            "enrollmentHistory": [
                {
                    "id": course.id,
                    "title": course.title,
                    "category": self._category_label(course.category.value),
                    "description": course.description or "",
                }
                for course in enrolled_courses
            ],
            "candidateCourses": [
                {
                    "id": course.id,
                    "title": course.title,
                    "category": self._category_label(course.category.value),
                    "description": course.description or "",
                    "price": int(course.price),
                    "salesCount": self._sales_count(course.id, course),
                }
                for course in shortlist
            ],
        }
        body = {
            "model": settings.openai_model,
            "store": False,
            "reasoning": {"effort": "minimal"},
            "instructions": (
                "당신은 온라인 IT 교육 플랫폼의 상품기획 분석가입니다. "
                "사용자의 실제 수강 이력만 근거로 현재 직무, 학습 수준과 관심 분야를 추론하세요. "
                "나이, 성별 등 민감하거나 근거 없는 특성은 추론하지 마세요. "
                "이미 수강한 강의는 제외하고 후보 강의 ID만 사용하여 서로 목적이 다른 패키지 3개를 만드세요. "
                "각 패키지는 학습 순서대로 2~4개 강의를 포함해야 합니다. "
                "판매량도 참고하되 학습 흐름과 사용자의 다음 성장 단계가 우선입니다. "
                "결과는 간결하고 자연스러운 한국어로 작성하세요."
            ),
            "input": json.dumps(payload, ensure_ascii=False),
            "max_output_tokens": 2000,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "audience_course_packages",
                    "strict": True,
                    "schema": response_schema,
                }
            },
        }

        try:
            async with httpx.AsyncClient(timeout=settings.openai_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.openai_base_url.rstrip('/')}/responses",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                response.raise_for_status()
                return json.loads(self._extract_output_text(response.json()))
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            logger.warning("[AudiencePackage] OpenAI 호출 실패, 규칙 기반으로 대체: %s", error)
            return None

    def _build_fallback_result(
        self,
        user: UserSummary,
        enrolled_courses: List[CourseResponse],
        shortlist: List[CourseResponse],
    ) -> Dict[str, Any]:
        category_counts = Counter(course.category.value for course in enrolled_courses)
        primary = category_counts.most_common(1)[0][0] if category_counts else None
        position = self.POSITION_LABELS.get(primary, "IT 분야를 탐색하는 학습자")
        beginner_words = ("기초", "입문", "시작", "개론")
        beginner_count = sum(
            any(word in course.title for word in beginner_words)
            for course in enrolled_courses
        )
        if len(enrolled_courses) <= 2 or beginner_count >= max(1, len(enrolled_courses) // 2):
            level = "입문"
        elif len(enrolled_courses) >= 6:
            level = "고급"
        else:
            level = "중급"

        interests = [
            self._category_label(category)
            for category, _ in category_counts.most_common(3)
        ] or ["IT 기초"]
        history_titles = ", ".join(course.title for course in enrolled_courses[:3])
        summary = (
            f"{user.name}은 현재 {position}로, {level} 수준의 학습자입니다. "
            f"{history_titles} 수강 이력을 바탕으로 다음 성장 단계의 강의를 추천합니다."
            if history_titles
            else f"{user.name}은 아직 수강 이력이 없어 IT 기초 탐색 단계의 학습자로 분류했습니다."
        )

        grouped: List[List[CourseResponse]] = []
        if primary:
            primary_courses = [course for course in shortlist if course.category.value == primary]
            adjacent_courses = [
                course
                for course in shortlist
                if course.category.value in self.ADJACENT_CATEGORIES.get(primary, [])
            ]
            grouped.append(primary_courses[:3])
            grouped.append((primary_courses[3:5] + adjacent_courses[:2])[:3])
            grouped.append(adjacent_courses[2:5] or shortlist[6:9])
        else:
            grouped = [shortlist[0:3], shortlist[3:6], shortlist[6:9]]

        used_signatures = set()
        packages = []
        for index, courses in enumerate(grouped[:3]):
            if len(courses) < 2:
                courses = shortlist[index * 3:index * 3 + 3]
            signature = tuple(course.id for course in courses)
            if signature in used_signatures:
                courses = shortlist[(index + 1) * 3:(index + 2) * 3]
            used_signatures.add(tuple(course.id for course in courses))
            packages.append(
                {
                    "packageName": f"{self._category_label(courses[0].category.value)} 성장 패키지 {index + 1}",
                    "summary": "현재 수강 이력에서 자연스럽게 이어지는 다음 단계 학습 구성입니다.",
                    "courseRecommendations": [
                        {
                            "courseId": course.id,
                            "reason": f"기존 학습을 {course.title} 과정으로 확장하기에 적합합니다.",
                        }
                        for course in courses
                    ],
                    "recommendationReason": (
                        "수강 카테고리, 강의별 판매량과 함께 구매된 강의 조합을 기준으로 구성했습니다."
                    ),
                }
            )

        return {
            "persona": {
                "position": position,
                "level": level,
                "interests": interests,
                "summary": summary,
            },
            "packages": packages,
        }

    def _build_packages(
        self,
        user_id: int,
        raw_packages: List[Dict[str, Any]],
        course_map: Dict[int, CourseResponse],
    ) -> List[AudiencePackageRecommendation]:
        packages = []
        for package_index, raw_package in enumerate(raw_packages):
            recommendations = raw_package["courseRecommendations"]
            courses = [course_map[item["courseId"]] for item in recommendations]
            course_ids = [course.id for course in courses]
            original_price = sum(int(course.price) for course in courses)
            discount_rate = {2: 10, 3: 15, 4: 20}[len(courses)]
            package_price = round(original_price * (1 - discount_rate / 100))
            evidence = self._co_purchase_evidence(course_ids)
            exact_evidence = next(
                (item for item in evidence if set(item.courseIds) == set(course_ids)),
                None,
            )
            co_purchase_count = (
                exact_evidence.coPurchaseCount
                if exact_evidence
                else max((item.coPurchaseCount for item in evidence), default=0)
            )

            packages.append(
                AudiencePackageRecommendation(
                    id=f"user-{user_id}-package-{package_index + 1}",
                    name=raw_package["packageName"],
                    summary=raw_package["summary"],
                    courses=[
                        PackageRecommendationCourse(
                            **self._to_audience_course(course).model_dump(),
                            learningOrder=index + 1,
                            reason=recommendations[index]["reason"],
                        )
                        for index, course in enumerate(courses)
                    ],
                    originalPrice=original_price,
                    discountRate=discount_rate,
                    packagePrice=package_price,
                    coPurchaseCount=co_purchase_count,
                    coPurchaseEvidence=evidence[:8],
                    recommendationReason=raw_package["recommendationReason"],
                )
            )
        return packages

    def _co_purchase_evidence(self, course_ids: List[int]) -> List[CoPurchaseEvidence]:
        selected_ids = set(course_ids)
        evidence = []
        for item in self.sales_data.get("coPurchases", []):
            item_ids = {int(course_id) for course_id in item.get("courseIds", [])}
            if len(item_ids) >= 2 and item_ids.issubset(selected_ids):
                evidence.append(CoPurchaseEvidence(**item))
        return sorted(evidence, key=lambda item: item.coPurchaseCount, reverse=True)

    @staticmethod
    def _extract_output_text(response_data: Dict[str, Any]) -> str:
        for output_item in response_data.get("output", []):
            if output_item.get("type") != "message":
                continue
            for content in output_item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    return content["text"]
        raise ValueError("OpenAI 응답에서 output_text를 찾지 못했습니다.")

    @staticmethod
    def _validate_result(
        result: Dict[str, Any],
        candidate_ids: Set[int],
        enrolled_ids: Set[int],
    ) -> None:
        persona = result.get("persona")
        packages = result.get("packages")
        if not isinstance(persona, dict) or not isinstance(packages, list) or len(packages) != 3:
            raise ValueError("추천 결과의 페르소나 또는 패키지 형식이 올바르지 않습니다.")

        signatures = set()
        for package in packages:
            recommendations = package.get("courseRecommendations", [])
            course_ids = [item.get("courseId") for item in recommendations]
            if not 2 <= len(course_ids) <= 4 or len(course_ids) != len(set(course_ids)):
                raise ValueError("각 패키지는 서로 다른 강의 2~4개로 구성해야 합니다.")
            if not set(course_ids).issubset(candidate_ids) or set(course_ids) & enrolled_ids:
                raise ValueError("추천 후보에 없거나 이미 수강한 강의가 포함됐습니다.")
            signature = tuple(sorted(course_ids))
            if signature in signatures:
                raise ValueError("동일한 강의 구성의 패키지가 중복됐습니다.")
            signatures.add(signature)

    def _to_audience_course(self, course: CourseResponse) -> AudienceCourse:
        return AudienceCourse(
            id=course.id,
            title=course.title,
            category=self._category_label(course.category.value),
            price=int(course.price),
            enrollmentCount=course.enrollmentCount,
            salesCount=self._sales_count(course.id, course),
        )

    def _sales_count(self, course_id: int, course: CourseResponse) -> int:
        return self.sales_by_course_id.get(course_id, course.enrollmentCount)

    def _category_label(self, category: str) -> str:
        return self.CATEGORY_LABELS.get(category, category)


audience_package_service = AudiencePackageService()
