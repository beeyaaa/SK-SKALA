import json
import logging
import re
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from app.client.course_client import course_client
from app.config.settings import settings
from app.model.schemas import (
    CourseResponse,
    PackageDraftCourse,
    PackageDraftRequest,
    PackageDraftResponse,
)

logger = logging.getLogger(__name__)


class PackageDraftService:
    """실제 강의와 목 판매 데이터를 결합해 패키지 상품기획 초안을 만든다."""

    DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "mock_sales_data.json"

    def __init__(self) -> None:
        self.sales_data = self._load_sales_data()

    def _load_sales_data(self) -> Dict[str, Any]:
        try:
            with self.DATA_PATH.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            logger.warning("[PackageDraft] 목 판매 데이터 로딩 실패: %s", error)
            return {"metadata": {}, "courseSales": [], "coPurchases": []}

    async def generate_package_draft(
        self, request: PackageDraftRequest
    ) -> PackageDraftResponse:
        all_courses = await course_client.get_all_courses()
        active_courses = [course for course in all_courses if course.status == "ACTIVE"]

        if len(active_courses) < 2:
            raise ValueError("패키지 생성에는 판매 중인 강의가 최소 2개 필요합니다.")

        candidates = self._build_candidates(active_courses, request)
        if not candidates:
            raise ValueError("예산 조건에 맞는 강의 패키지가 없습니다.")

        ai_result = await self._generate_ai_result(request, candidates)
        mode = "AI" if ai_result else "RULE_BASED"
        selected_index = (
            ai_result["candidateIndex"]
            if ai_result
            else self._select_rule_based_candidate_index(request, candidates)
        )
        selected = candidates[selected_index]

        ordered_ids = (
            ai_result["orderedCourseIds"]
            if ai_result
            else selected["courseIds"]
        )
        course_by_id = {course.id: course for course in selected["courses"]}
        reason_by_id = (
            {
                item["courseId"]: item["reason"]
                for item in ai_result["courseReasons"]
                if item["courseId"] in course_by_id
            }
            if ai_result
            else {}
        )

        draft_courses = [
            PackageDraftCourse(
                id=course_id,
                title=course_by_id[course_id].title,
                category=course_by_id[course_id].category.value,
                description=course_by_id[course_id].description,
                price=int(course_by_id[course_id].price),
                learningOrder=index + 1,
                salesCount=self._get_sales_count(course_id, course_by_id[course_id]),
                reason=reason_by_id.get(
                    course_id,
                    self._fallback_course_reason(course_by_id[course_id], index),
                ),
            )
            for index, course_id in enumerate(ordered_ids)
        ]

        if ai_result:
            package_name = ai_result["packageName"]
            recommendation_reason = ai_result["recommendationReason"]
        else:
            package_name = self._fallback_package_name(selected["courses"])
            recommendation_reason = (
                f"과거 판매 기록에서 해당 조합이 {selected['coPurchaseCount']}회 함께 구매되었고, "
                f"강의별 판매량과 입력한 학습 목표의 연관성을 기준으로 선정했습니다."
            )

        return PackageDraftResponse(
            mode=mode,
            packageName=package_name,
            targetPersona=request.persona,
            courses=draft_courses,
            originalPrice=selected["originalPrice"],
            discountRate=selected["discountRate"],
            packagePrice=selected["packagePrice"],
            coPurchaseCount=selected["coPurchaseCount"],
            recommendationReason=recommendation_reason,
        )

    def _build_candidates(
        self,
        courses: List[CourseResponse],
        request: PackageDraftRequest,
    ) -> List[Dict[str, Any]]:
        prompt = f"{request.persona} {request.goal}".lower()
        if len(courses) > 24:
            courses = sorted(
                courses,
                key=lambda course: (
                    self._get_relevance_score(course, prompt) * 10
                    + self._get_sales_count(course.id, course)
                ),
                reverse=True,
            )[:24]
        co_purchase_map = {
            frozenset(item.get("courseIds", [])): int(item.get("coPurchaseCount", 0))
            for item in self.sales_data.get("coPurchases", [])
        }
        max_size = min(4, len(courses))
        bundle_sizes = (
            [request.bundleSize]
            if request.bundleSize
            else list(range(2, max_size + 1))
        )
        candidates: List[Dict[str, Any]] = []

        for bundle_size in bundle_sizes:
            discount_rate = {2: 10, 3: 15, 4: 20}[bundle_size]
            size_candidates: List[Dict[str, Any]] = []

            for course_group in combinations(courses, bundle_size):
                course_ids = [course.id for course in course_group]
                original_price = sum(int(course.price) for course in course_group)
                package_price = round(original_price * (1 - discount_rate / 100))

                if request.maxBudget and package_price > request.maxBudget:
                    continue

                co_purchase_count = co_purchase_map.get(frozenset(course_ids), 0)
                total_sales_count = sum(
                    self._get_sales_count(course.id, course) for course in course_group
                )
                relevance_score = sum(
                    self._get_relevance_score(course, prompt) for course in course_group
                )

                size_candidates.append(
                    {
                        "courses": list(course_group),
                        "courseIds": course_ids,
                        "originalPrice": original_price,
                        "discountRate": discount_rate,
                        "packagePrice": package_price,
                        "coPurchaseCount": co_purchase_count,
                        "totalSalesCount": total_sales_count,
                        "score": co_purchase_count * 3 + total_sales_count + relevance_score,
                    }
                )

            size_candidates.sort(key=lambda item: item["score"], reverse=True)
            candidates.extend(size_candidates[:2])

        return candidates

    @staticmethod
    def _select_rule_based_candidate_index(
        request: PackageDraftRequest,
        candidates: List[Dict[str, Any]],
    ) -> int:
        if request.bundleSize:
            preferred_size = request.bundleSize
        else:
            prompt = f"{request.persona} {request.goal}".lower()
            if any(keyword in prompt for keyword in ["신입", "초보", "입문", "기초"]):
                preferred_size = 2
            elif any(keyword in prompt for keyword in ["고급", "시니어", "아키텍트", "리드"]):
                preferred_size = 4
            elif any(keyword in prompt for keyword in ["중급", "경력", "실무", "프로젝트"]):
                preferred_size = 3
            else:
                preferred_size = 3

        available_sizes = sorted({len(candidate["courseIds"]) for candidate in candidates})
        selected_size = min(
            available_sizes,
            key=lambda size: (abs(size - preferred_size), -size),
        )
        matching_indices = [
            index
            for index, candidate in enumerate(candidates)
            if len(candidate["courseIds"]) == selected_size
        ]
        return max(matching_indices, key=lambda index: candidates[index]["score"])

    def _get_sales_count(self, course_id: int, course: CourseResponse) -> int:
        matched = next(
            (
                item
                for item in self.sales_data.get("courseSales", [])
                if item.get("courseId") == course_id
            ),
            None,
        )
        return int(matched.get("salesCount", 0)) if matched else course.enrollmentCount

    @staticmethod
    def _get_relevance_score(course: CourseResponse, prompt: str) -> int:
        searchable = f"{course.title} {course.description or ''} {course.category.value}".lower()
        terms = {
            term
            for term in re.findall(r"[0-9a-zA-Z가-힣.+#]+", prompt)
            if len(term) >= 2
        }
        score = sum(12 for term in terms if term in searchable)

        category_aliases = {
            "백엔드": "BACKEND",
            "프론트엔드": "FRONTEND",
            "데브옵스": "DEVOPS",
            "데이터": "DATA_SCIENCE",
            "데이터베이스": "DATABASE",
            "db": "DATABASE",
            "보안": "SECURITY",
            "모바일": "MOBILE",
            "ai": "OTHER",
            "인공지능": "OTHER",
            "머신러닝": "OTHER",
        }
        for keyword, category in category_aliases.items():
            if keyword in prompt and course.category.value == category:
                score += 35
        return score

    async def _generate_ai_result(
        self,
        request: PackageDraftRequest,
        candidates: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        api_key = settings.openai_api_key.get_secret_value()
        if not api_key:
            logger.info("[PackageDraft] OPENAI_API_KEY가 없어 규칙 기반 결과를 반환합니다.")
            return None

        candidate_payload = [
            {
                "candidateIndex": index,
                "courses": [
                    {
                        "id": course.id,
                        "title": course.title,
                        "description": course.description or "",
                        "category": course.category.value,
                        "price": int(course.price),
                        "salesCount": self._get_sales_count(course.id, course),
                    }
                    for course in candidate["courses"]
                ],
                "coPurchaseCount": candidate["coPurchaseCount"],
                "originalPrice": candidate["originalPrice"],
                "discountRate": candidate["discountRate"],
                "packagePrice": candidate["packagePrice"],
            }
            for index, candidate in enumerate(candidates)
        ]

        response_schema = {
            "type": "object",
            "properties": {
                "candidateIndex": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": len(candidates) - 1,
                },
                "packageName": {"type": "string"},
                "orderedCourseIds": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 4,
                },
                "courseReasons": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "courseId": {"type": "integer"},
                            "reason": {"type": "string"},
                        },
                        "required": ["courseId", "reason"],
                        "additionalProperties": False,
                    },
                    "minItems": 2,
                    "maxItems": 4,
                },
                "recommendationReason": {"type": "string"},
            },
            "required": [
                "candidateIndex",
                "packageName",
                "orderedCourseIds",
                "courseReasons",
                "recommendationReason",
            ],
            "additionalProperties": False,
        }

        body = {
            "model": settings.openai_model,
            "store": False,
            "instructions": (
                "당신은 온라인 IT 교육 플랫폼의 상품기획 보조자입니다. "
                "제공된 후보 중 수강생 페르소나와 학습 목표에 가장 자연스러운 후보 하나만 "
                "선택하세요. 수강생 수준에 따라 2개에서 4개 사이의 적절한 강의 수를 판단하고, "
                "제공된 강의 ID만 사용하세요. 강의 내용은 만들지 말고, "
                "학습 순서와 간결한 한국어 추천 근거를 작성하세요. 가격과 할인율은 변경하지 마세요."
            ),
            "input": json.dumps(
                {
                    "persona": request.persona,
                    "goal": request.goal,
                    "candidates": candidate_payload,
                },
                ensure_ascii=False,
            ),
            "max_output_tokens": 1000,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "course_package_draft",
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
                parsed = json.loads(self._extract_output_text(response.json()))
                self._validate_ai_result(parsed, candidates)
                return parsed
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            logger.warning("[PackageDraft] OpenAI 호출 실패, 규칙 기반으로 대체: %s", error)
            return None

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
    def _validate_ai_result(
        result: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> None:
        candidate_index = result.get("candidateIndex")
        if not isinstance(candidate_index, int) or not 0 <= candidate_index < len(candidates):
            raise ValueError("AI가 유효하지 않은 후보 번호를 반환했습니다.")

        selected_ids = candidates[candidate_index]["courseIds"]
        bundle_size = len(selected_ids)
        ordered_ids = result.get("orderedCourseIds", [])
        if len(ordered_ids) != bundle_size or set(ordered_ids) != set(selected_ids):
            raise ValueError("AI가 후보에 없는 강의 ID를 반환했습니다.")

        reason_ids = [item.get("courseId") for item in result.get("courseReasons", [])]
        if len(reason_ids) != bundle_size or set(reason_ids) != set(selected_ids):
            raise ValueError("AI 추천 이유의 강의 ID가 후보와 일치하지 않습니다.")

    @staticmethod
    def _fallback_course_reason(course: CourseResponse, index: int) -> str:
        if index == 0:
            return f"{course.title}의 핵심 개념으로 학습 기반을 마련하기 위한 강의입니다."
        return f"앞선 강의에서 익힌 내용을 {course.title} 학습으로 확장하기 위한 강의입니다."

    @staticmethod
    def _fallback_package_name(courses: List[CourseResponse]) -> str:
        titles = " ".join(course.title.lower() for course in courses)
        if "vue" in titles and "spring" in titles:
            return "풀스택 프로젝트 입문 패키지"
        if "msa" in titles:
            return "Spring MSA 프로젝트 패키지"
        return "프로젝트 맞춤 IT 역량 패키지"


package_draft_service = PackageDraftService()
