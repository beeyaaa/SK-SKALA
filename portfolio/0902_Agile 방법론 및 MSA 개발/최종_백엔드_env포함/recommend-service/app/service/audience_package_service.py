import asyncio
import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import httpx

from app.client.course_client import course_client
from app.client.enrollment_client import enrollment_client
from app.client.user_client import user_client
from app.config.settings import settings
from app.model.schemas import (
    AudienceCourse,
    AudienceSummary,
    CoPurchaseEvidence,
    CourseResponse,
    PersonaBundle,
    PersonaBundleCourse,
    PersonaBundleGenerationRequest,
    PersonaBundleResponse,
    PersonaDraft,
    PersonaGenerationResponse,
    PersonaWithBundle,
)

logger = logging.getLogger(__name__)


class AudiencePackageService:
    """전체 수강생을 군집화하고, 승인된 페르소나별 번들을 생성한다."""

    DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "mock_sales_data.json"
    MIN_PERSONA_COUNT = 3
    MAX_PERSONA_COUNT = 5
    MAX_AI_PERSONA_ATTEMPTS = 3
    CANDIDATE_COUNT_PER_PERSONA = 18
    # init-db/03_seed_audiences.sql의 패키지 플래너용 데모 수강생 범위
    FALLBACK_AUDIENCE_USER_IDS = range(201, 251)

    CATEGORY_LABELS = {
        "BACKEND": "백엔드", "FRONTEND": "프론트엔드", "DEVOPS": "DevOps",
        "DATA_SCIENCE": "데이터", "DATABASE": "데이터베이스", "SECURITY": "보안",
        "MOBILE": "모바일", "OTHER": "AI",
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
        self.sales_data = self._load_sales_data()
        self.sales_by_course_id = {
            int(item["courseId"]): int(item["salesCount"])
            for item in self.sales_data.get("courseSales", [])
        }
        self.audience_user_ids = list(self.FALLBACK_AUDIENCE_USER_IDS)
        self.co_purchase_by_pair = {
            frozenset(int(course_id) for course_id in item.get("courseIds", [])): int(
                item.get("coPurchaseCount", 0)
            )
            for item in self.sales_data.get("coPurchases", [])
            if len(item.get("courseIds", [])) >= 2
        }

    def _load_sales_data(self) -> Dict[str, Any]:
        try:
            with self.DATA_PATH.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            logger.warning("[PersonaBundle] 목 판매 데이터 로딩 실패: %s", error)
            return {"metadata": {}, "courseSales": [], "coPurchases": []}

    async def get_audiences(self) -> List[AudienceSummary]:
        audiences, _ = await self._load_audience_context()
        return audiences

    async def generate_personas(self, max_persona_count: int = 5) -> PersonaGenerationResponse:
        """1단계: 전체 수강 이력을 3~5개 군집으로 나누고 페르소나 초안을 만든다."""
        max_persona_count = min(
            max(self.MIN_PERSONA_COUNT, max_persona_count),
            self.MAX_PERSONA_COUNT,
        )
        audiences, _ = await self._load_audience_context()
        if not audiences:
            raise ValueError("분석할 수강생이 없습니다.")
        if len(audiences) < self.MIN_PERSONA_COUNT:
            raise ValueError("페르소나 3개를 만들려면 수강생이 최소 3명 필요합니다.")

        raw_personas = None
        validation_feedback = None
        previous_result = None
        for attempt in range(1, self.MAX_AI_PERSONA_ATTEMPTS + 1):
            try:
                ai_result = await self._generate_personas_with_ai(
                    audiences,
                    max_persona_count,
                    validation_feedback=validation_feedback,
                    previous_result=previous_result,
                )
            except (KeyError, TypeError, ValueError) as error:
                validation_feedback = str(error)
                previous_result = None
                logger.warning(
                    "[PersonaBundle] AI 군집 배정 변환 실패 "
                    "(attempt=%d/%d), 재시도합니다: %s",
                    attempt,
                    self.MAX_AI_PERSONA_ATTEMPTS,
                    error,
                )
                continue
            if not ai_result:
                break
            try:
                candidate_personas = ai_result["personas"]
                self._validate_persona_partition(
                    candidate_personas, audiences, max_persona_count
                )
                raw_personas = candidate_personas
                logger.info(
                    "[PersonaBundle] AI 페르소나 검증 통과 (attempt=%d)", attempt
                )
                break
            except (KeyError, TypeError, ValueError) as error:
                validation_feedback = str(error)
                previous_result = ai_result
                logger.warning(
                    "[PersonaBundle] AI 페르소나 검증 실패 "
                    "(attempt=%d/%d), 재시도합니다: %s",
                    attempt,
                    self.MAX_AI_PERSONA_ATTEMPTS,
                    error,
                )

        if raw_personas is None:
            logger.warning("[PersonaBundle] AI 페르소나 생성 실패, 규칙 기반으로 대체합니다.")
            raw_personas = self._build_fallback_personas(audiences, max_persona_count)

        # 다음 단계에서 안정적으로 참조하도록 페르소나 ID는 서버가 부여한다.
        personas = [
            PersonaDraft(personaId=f"P{index:02d}", **raw_persona)
            for index, raw_persona in enumerate(raw_personas, start=1)
        ]
        response = PersonaGenerationResponse(personas=personas)
        logger.info(
            "[PersonaBundle] 페르소나 도출 결과\n%s",
            json.dumps(response.model_dump(), ensure_ascii=False, indent=2),
        )
        return response

    async def generate_persona_bundles(
        self, request: PersonaBundleGenerationRequest
    ) -> PersonaBundleResponse:
        """2단계: 담당자가 검토한 페르소나마다 강의 3~6개의 번들 하나를 만든다."""
        if request.minBundleSize > request.maxBundleSize:
            raise ValueError("최소 번들 강의 수는 최대 번들 강의 수보다 클 수 없습니다.")

        audiences, active_courses = await self._load_audience_context()
        audience_map = {audience.userId: audience for audience in audiences}
        self._validate_approved_personas(request.personas, set(audience_map))
        candidate_map = {
            persona.personaId: self._build_cluster_shortlist(persona, audience_map, active_courses)
            for persona in request.personas
        }
        for persona_id, candidates in candidate_map.items():
            if len(candidates) < request.minBundleSize:
                raise ValueError(f"{persona_id}의 번들을 구성할 강의 후보가 부족합니다.")

        ai_result = await self._generate_bundles_with_ai(request, candidate_map)
        if ai_result:
            try:
                raw_bundles = ai_result["bundles"]
                self._validate_bundle_result(raw_bundles, request, candidate_map)
            except (KeyError, TypeError, ValueError) as error:
                logger.warning("[PersonaBundle] AI 번들 검증 실패, 규칙 기반으로 대체: %s", error)
                raw_bundles = self._build_fallback_bundles(request, candidate_map)
        else:
            raw_bundles = self._build_fallback_bundles(request, candidate_map)

        raw_by_persona = {bundle["personaId"]: bundle for bundle in raw_bundles}
        course_map = {course.id: course for course in active_courses}
        response = PersonaBundleResponse(
            personas=[
                PersonaWithBundle(
                    **persona.model_dump(),
                    bundle=self._to_persona_bundle(
                        persona, raw_by_persona[persona.personaId], course_map
                    ),
                )
                for persona in request.personas
            ]
        )
        logger.info(
            "[PersonaBundle] 커리큘럼 생성 결과\n%s",
            json.dumps(response.model_dump(), ensure_ascii=False, indent=2),
        )
        return response

    async def _load_audience_context(
        self,
    ) -> Tuple[List[AudienceSummary], List[CourseResponse]]:
        # 분석 대상 수강생은 User Service의 실제 DB에서 조회한다. 구버전 User
        # Service에 전체 수강생 API가 없을 때에는 SQL 시드의 데모 ID 범위로 대체한다.
        try:
            students = await user_client.get_students()
            audience_user_ids = [student.id for student in students]
        except httpx.HTTPError as error:
            logger.warning(
                "[PersonaBundle] 전체 수강생 API 조회 실패, 후보 ID별 DB 조회로 대체: %s",
                error,
            )
            # 실제 분석 대상 여부는 구버전 User Service에도 존재하는 단건 조회 API로
            # 확인하므로, 삭제됐거나 STUDENT가 아닌 계정을 포함하지 않는다.
            user_results = await asyncio.gather(
                *(user_client.get_user(user_id) for user_id in self.audience_user_ids),
                return_exceptions=True,
            )
            audience_user_ids = [
                user.id
                for user in user_results
                if not isinstance(user, Exception) and user.role == "STUDENT"
            ]

        if not audience_user_ids:
            return [], []
        courses = await course_client.get_all_courses()
        active_courses = [course for course in courses if course.status == "ACTIVE"]
        course_map = {course.id: course for course in active_courses}
        histories = await asyncio.gather(
            *(
                enrollment_client.get_enrollment_history(user_id)
                for user_id in audience_user_ids
            )
        )

        audiences = []
        for user_id, history in zip(audience_user_ids, histories):
            enrolled_courses = [
                self._to_audience_course(course_map[course_id])
                for course_id in history.activeCourseIds
                if course_id in course_map
            ]
            audiences.append(
                AudienceSummary(
                    userId=user_id,
                    enrollmentCount=len(enrolled_courses),
                    enrolledCourses=enrolled_courses,
                )
            )
        return audiences, active_courses

    async def _generate_personas_with_ai(
        self,
        audiences: Sequence[AudienceSummary],
        max_persona_count: int,
        validation_feedback: Optional[str] = None,
        previous_result: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        audience_count = len(audiences)
        response_schema = {
            "type": "object",
            "properties": {
                "personas": {
                    "type": "array",
                    "minItems": self.MIN_PERSONA_COUNT,
                    "maxItems": max_persona_count,
                    "items": {
                        "type": "object",
                        "properties": {
                            "clusterNumber": {"type": "integer"},
                            "personaKeyword": {"type": "string"},
                            "personaReason": {"type": "string"},
                            "interests": {"type": "array", "items": {"type": "string"},
                                          "minItems": 1, "maxItems": 5},
                            "level": {"type": "string"},
                        },
                        "required": ["clusterNumber", "personaKeyword", "personaReason",
                                     "interests", "level"],
                        "additionalProperties": False,
                    },
                },
                "clusterAssignments": {
                    "type": "array",
                    "minItems": audience_count,
                    "maxItems": audience_count,
                    "items": {"type": "integer"},
                },
            },
            "required": ["personas", "clusterAssignments"],
            "additionalProperties": False,
        }
        expected_user_ids = sorted(audience.userId for audience in audiences)
        audience_by_id = {audience.userId: audience for audience in audiences}
        payload = {
            "minPersonaCount": self.MIN_PERSONA_COUNT,
            "maxPersonaCount": max_persona_count,
            "expectedUserIds": expected_user_ids,
            "students": [
                {"userId": audience.userId, "enrollmentHistory": [
                    {"courseId": course.id, "courseName": course.title, "category": course.category}
                    for course in audience.enrolledCourses
                ]}
                for audience in (audience_by_id[user_id] for user_id in expected_user_ids)
            ],
        }
        if validation_feedback:
            payload["previousValidationError"] = validation_feedback
            payload["invalidPreviousResult"] = previous_result
        result = await self._call_openai_json(
            response_schema, "audience_personas",
            "당신은 온라인 교육 플랫폼의 고객 세분화 분석가입니다. "
            "이 작업의 페르소나는 서로 겹치는 특성 태그가 아니라, 전체 수강생을 나누는 "
            "상호 배타적 군집(partition)입니다. 수강 카테고리·강의 내용·학습 수준을 기준으로 "
            "최소 3개, 최대 maxPersonaCount개의 군집을 만드세요. "
            "personas의 clusterNumber는 1부터 순차적으로 부여하고 중복하지 마세요. "
            "clusterAssignments는 expectedUserIds와 동일한 순서의 배열입니다. "
            "즉 clusterAssignments의 n번째 값은 expectedUserIds의 n번째 수강생이 속할 "
            "clusterNumber 하나입니다. 배열 길이는 expectedUserIds와 정확히 같아야 합니다. "
            "모든 clusterNumber는 clusterAssignments에 최소 한 번 사용하세요. "
            "previousValidationError가 있으면 invalidPreviousResult를 그대로 반복하지 말고, "
            "해당 오류를 제거하여 새로 배정하세요. 근거 없는 개인정보는 추론하지 마세요. "
            "페르소나 키워드는 마케팅 담당자가 이해하기 쉬운 간결한 한국어로 작성하세요.",
            payload, 2200,
        )
        if result is None:
            return None

        persona_definitions = result["personas"]
        assignments = result["clusterAssignments"]
        if len(assignments) != len(expected_user_ids):
            raise ValueError("AI 군집 배정 개수가 수강생 수와 다릅니다.")

        definition_by_number = {
            int(persona["clusterNumber"]): persona for persona in persona_definitions
        }
        if len(definition_by_number) != len(persona_definitions):
            raise ValueError("AI가 중복된 군집 번호를 반환했습니다.")

        members_by_number = {cluster_number: [] for cluster_number in definition_by_number}
        for user_id, cluster_number in zip(expected_user_ids, assignments):
            cluster_number = int(cluster_number)
            if cluster_number not in members_by_number:
                raise ValueError("AI가 정의하지 않은 군집에 수강생을 배정했습니다.")
            members_by_number[cluster_number].append(user_id)
        if any(not members for members in members_by_number.values()):
            raise ValueError("AI가 수강생이 없는 빈 군집을 만들었습니다.")

        personas = []
        for cluster_number in sorted(definition_by_number):
            definition = definition_by_number[cluster_number]
            personas.append({
                "personaKeyword": definition["personaKeyword"],
                "memberUserIds": members_by_number[cluster_number],
                "personaReason": definition["personaReason"],
                "interests": definition["interests"],
                "level": definition["level"],
            })
        return {"personas": personas}

    def _build_fallback_personas(
        self, audiences: Sequence[AudienceSummary], max_persona_count: int
    ) -> List[Dict[str, Any]]:
        groups: Dict[str, List[AudienceSummary]] = {}
        for audience in audiences:
            counts = Counter(
                self._category_code(course.category)
                for course in audience.enrolledCourses
            )
            dominant = counts.most_common(1)[0][0] if counts else "OTHER"
            groups.setdefault(dominant, []).append(audience)

        ranked = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
        retained = {category: list(members) for category, members in ranked[:max_persona_count]}
        for category, members in ranked[max_persona_count:]:
            target = max(retained, key=lambda key: (
                self._category_affinity(category, key), -len(retained[key])
            ))
            retained[target].extend(members)

        # 원본 카테고리가 1~2개뿐이어도 항상 최소 3개의 페르소나를 만든다.
        while len(retained) < self.MIN_PERSONA_COUNT:
            source = max(retained, key=lambda key: len(retained[key]))
            members = retained[source]
            if len(members) < 2:
                raise ValueError("빈 군집 없이 페르소나 3개를 만들 수 없습니다.")
            split_at = (len(members) + 1) // 2
            retained[source] = members[:split_at]
            retained[f"{source}__{len(retained) + 1}"] = members[split_at:]

        personas = []
        for _, members in sorted(retained.items(), key=lambda item: (-len(item[1]), item[0])):
            counts = Counter(
                self._category_code(course.category)
                for member in members
                for course in member.enrolledCourses
            )
            interests = [self._category_label(category) for category, _ in counts.most_common(3)] or ["IT 기초"]
            level = self._infer_group_level(members)
            member_ids = sorted(member.userId for member in members)
            personas.append({
                "personaKeyword": f"{interests[0]} {level} 성장형",
                "memberUserIds": member_ids,
                "personaReason": f"수강생 {len(member_ids)}명이 {', '.join(interests)} 관련 강의를 공통적으로 수강한 {level} 수준의 집단입니다.",
                "interests": interests,
                "level": level,
            })
        return personas

    def _build_cluster_shortlist(
        self, persona: PersonaDraft, audience_map: Dict[int, AudienceSummary],
        courses: Sequence[CourseResponse],
    ) -> List[CourseResponse]:
        members = [audience_map[user_id] for user_id in persona.memberUserIds]
        enrolled_courses = [course for member in members for course in member.enrolledCourses]
        enrolled_ids = {course.id for course in enrolled_courses}
        category_counts = Counter(
            self._category_code(course.category) for course in enrolled_courses
        )
        primary_categories = [category for category, _ in category_counts.most_common(2)]
        terms = {term.lower() for term in re.findall(
            r"[0-9a-zA-Z가-힣.+#]+", f"{persona.personaKeyword} {' '.join(persona.interests)}"
        ) if len(term) >= 2}

        def score(course: CourseResponse) -> int:
            category = course.category.value
            value = self._sales_count(course.id, course)
            if category in primary_categories:
                value += 1800
            if any(category in self.ADJACENT_CATEGORIES.get(primary, []) for primary in primary_categories):
                value += 450
            searchable = f"{course.title} {course.description or ''}".lower()
            return value + sum(90 for term in terms if term in searchable)

        available = [course for course in courses if course.id not in enrolled_ids]
        return sorted(available, key=score, reverse=True)[:self.CANDIDATE_COUNT_PER_PERSONA]

    async def _generate_bundles_with_ai(
        self, request: PersonaBundleGenerationRequest,
        candidate_map: Dict[str, List[CourseResponse]],
    ) -> Optional[Dict[str, Any]]:
        response_schema = {
            "type": "object", "properties": {"bundles": {"type": "array",
                "minItems": len(request.personas), "maxItems": len(request.personas),
                "items": {"type": "object", "properties": {
                    "personaId": {"type": "string"}, "bundleName": {"type": "string"},
                    "bundleReason": {"type": "string"}, "courses": {"type": "array",
                        "minItems": request.minBundleSize, "maxItems": request.maxBundleSize,
                        "items": {"type": "object", "properties": {
                            "courseId": {"type": "integer"}, "reason": {"type": "string"}},
                            "required": ["courseId", "reason"], "additionalProperties": False}}},
                    "required": ["personaId", "bundleName", "bundleReason", "courses"],
                    "additionalProperties": False}}},
            "required": ["bundles"], "additionalProperties": False,
        }
        payload_personas = []
        for persona in request.personas:
            candidates = candidate_map[persona.personaId]
            candidate_ids = {course.id for course in candidates}
            evidence = [item for item in self.sales_data.get("coPurchases", [])
                        if set(map(int, item.get("courseIds", []))).issubset(candidate_ids)]
            evidence.sort(key=lambda item: int(item.get("coPurchaseCount", 0)), reverse=True)
            payload_personas.append({
                **persona.model_dump(),
                "candidateCourses": [{
                    "courseId": course.id, "courseName": course.title,
                    "category": self._category_label(course.category.value),
                    "description": course.description or "", "price": int(course.price),
                    "salesCount": self._sales_count(course.id, course),
                } for course in candidates],
                "coPurchases": evidence[:30],
            })
        return await self._call_openai_json(
            response_schema, "persona_course_bundles",
            "당신은 온라인 교육 플랫폼의 커리큘럼 상품기획자입니다. 담당자가 검토한 각 페르소나마다 "
            "정확히 하나의 번들을 만드세요. 반드시 해당 페르소나의 후보 강의 ID만 사용하고 지정된 "
            "개수 안에서 학습 순서대로 구성하세요. 페르소나 적합성과 학습 흐름을 우선하고 판매량과 "
            "동시 구매 횟수를 근거로 보완하세요. 모든 페르소나 ID를 한 번씩 그대로 반환하세요.",
            {"minBundleSize": request.minBundleSize, "maxBundleSize": request.maxBundleSize,
             "personas": payload_personas}, 3600,
        )

    def _build_fallback_bundles(
        self, request: PersonaBundleGenerationRequest,
        candidate_map: Dict[str, List[CourseResponse]],
    ) -> List[Dict[str, Any]]:
        bundles = []
        for persona in request.personas:
            candidates = candidate_map[persona.personaId]
            preferred = {"입문": 3, "중급": 4, "고급": 5}.get(persona.level, 4)
            bundle_size = min(request.maxBundleSize, max(request.minBundleSize, preferred))
            selected: List[CourseResponse] = []
            remaining = list(candidates)
            while remaining and len(selected) < bundle_size:
                selected_ids = {course.id for course in selected}
                best = max(remaining, key=lambda course: self._sales_count(course.id, course) + sum(
                    self.co_purchase_by_pair.get(frozenset({course.id, selected_id}), 0) * 8
                    for selected_id in selected_ids
                ))
                selected.append(best)
                remaining.remove(best)
            bundles.append({
                "personaId": persona.personaId,
                "bundleName": f"{persona.personaKeyword} 맞춤 커리큘럼",
                "bundleReason": f"{', '.join(persona.interests)} 관심 분야와 {persona.level} 학습 수준을 기준으로 판매량 및 함께 구매된 강의 관계가 높은 순서로 구성했습니다.",
                "courses": [{
                    "courseId": course.id,
                    "reason": f"{persona.personaKeyword}에게 필요한 {self._category_label(course.category.value)} 역량을 단계적으로 확장하는 강의입니다.",
                } for course in selected],
            })
        return bundles

    def _to_persona_bundle(
        self, persona: PersonaDraft, raw_bundle: Dict[str, Any],
        course_map: Dict[int, CourseResponse],
    ) -> PersonaBundle:
        recommendations = raw_bundle["courses"]
        courses = [course_map[item["courseId"]] for item in recommendations]
        course_ids = [course.id for course in courses]
        original_price = sum(int(course.price) for course in courses)
        discount_rate = {3: 15, 4: 20, 5: 25, 6: 30}[len(courses)]
        numeric_id = persona.personaId.removeprefix("P")
        return PersonaBundle(
            bundleId=f"B{int(numeric_id):02d}" if numeric_id.isdigit() else f"bundle-{persona.personaId}",
            bundleName=raw_bundle["bundleName"],
            courses=[PersonaBundleCourse(
                courseId=course.id, courseName=course.title,
                category=self._category_label(course.category.value), price=int(course.price),
                salesCount=self._sales_count(course.id, course), learningOrder=index + 1,
                reason=recommendations[index]["reason"],
            ) for index, course in enumerate(courses)],
            bundleReason=raw_bundle["bundleReason"],
            coPurchaseEvidence=self._co_purchase_evidence(course_ids)[:8],
            originalPrice=original_price, discountRate=discount_rate,
            bundlePrice=round(original_price * (1 - discount_rate / 100)),
        )

    async def _call_openai_json(
        self, schema: Dict[str, Any], schema_name: str, instructions: str,
        payload: Dict[str, Any], max_output_tokens: int,
    ) -> Optional[Dict[str, Any]]:
        api_key = settings.openai_api_key.get_secret_value()
        if not api_key:
            logger.info("[PersonaBundle] API 키가 없어 규칙 기반 결과를 반환합니다.")
            return None
        body = {"model": settings.openai_model, "store": False,
                "reasoning": {"effort": "minimal"}, "instructions": instructions,
                "input": json.dumps(payload, ensure_ascii=False),
                "max_output_tokens": max_output_tokens,
                "text": {"format": {"type": "json_schema", "name": schema_name,
                                    "strict": True, "schema": schema}}}
        try:
            async with httpx.AsyncClient(timeout=settings.openai_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.openai_base_url.rstrip('/')}/responses",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=body,
                )
                response.raise_for_status()
                return json.loads(self._extract_output_text(response.json()))
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            logger.warning("[PersonaBundle] OpenAI 호출 실패, 규칙 기반으로 대체: %s", error)
            return None

    @staticmethod
    def _validate_persona_partition(
        raw_personas: Sequence[Dict[str, Any]], audiences: Sequence[AudienceSummary],
        max_persona_count: int,
    ) -> None:
        if not AudiencePackageService.MIN_PERSONA_COUNT <= len(raw_personas) <= max_persona_count:
            raise ValueError("페르소나는 최소 3개, 요청한 최대 개수 이하여야 합니다.")
        expected_ids = {audience.userId for audience in audiences}
        assigned_ids = [int(user_id) for persona in raw_personas
                        for user_id in persona.get("memberUserIds", [])]
        if len(assigned_ids) != len(set(assigned_ids)):
            raise ValueError("한 수강생이 여러 페르소나에 중복 배정됐습니다.")
        if set(assigned_ids) != expected_ids:
            raise ValueError("모든 분석 대상 수강생이 정확히 한 페르소나에 포함돼야 합니다.")
        for persona in raw_personas:
            if not all(persona.get(key) for key in
                       ("personaKeyword", "personaReason", "interests", "level")):
                raise ValueError("페르소나 설명 필드가 누락됐습니다.")

    @staticmethod
    def _validate_approved_personas(
        personas: Sequence[PersonaDraft], known_user_ids: Set[int]
    ) -> None:
        persona_ids = [persona.personaId for persona in personas]
        if len(persona_ids) != len(set(persona_ids)):
            raise ValueError("페르소나 ID가 중복됐습니다.")
        member_ids = [user_id for persona in personas for user_id in persona.memberUserIds]
        if len(member_ids) != len(set(member_ids)):
            raise ValueError("한 수강생이 여러 페르소나에 중복 포함됐습니다.")
        if not set(member_ids).issubset(known_user_ids):
            raise ValueError("분석 대상에 없는 수강생 ID가 포함됐습니다.")

    @staticmethod
    def _validate_bundle_result(
        raw_bundles: Sequence[Dict[str, Any]], request: PersonaBundleGenerationRequest,
        candidate_map: Dict[str, List[CourseResponse]],
    ) -> None:
        expected = {persona.personaId for persona in request.personas}
        returned = [bundle.get("personaId") for bundle in raw_bundles]
        if len(returned) != len(set(returned)) or set(returned) != expected:
            raise ValueError("모든 페르소나에 정확히 하나의 번들이 필요합니다.")
        for bundle in raw_bundles:
            persona_id = bundle["personaId"]
            course_ids = [item.get("courseId") for item in bundle.get("courses", [])]
            if not request.minBundleSize <= len(course_ids) <= request.maxBundleSize:
                raise ValueError("번들 강의 개수가 요청 범위를 벗어났습니다.")
            if len(course_ids) != len(set(course_ids)):
                raise ValueError("같은 번들에 중복 강의가 포함됐습니다.")
            if not set(course_ids).issubset({course.id for course in candidate_map[persona_id]}):
                raise ValueError("추천 후보에 없는 강의가 포함됐습니다.")
            if not bundle.get("bundleName") or not bundle.get("bundleReason"):
                raise ValueError("번들 이름과 구성 이유가 필요합니다.")

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
            if output_item.get("type") == "message":
                for content in output_item.get("content", []):
                    if content.get("type") == "output_text" and content.get("text"):
                        return content["text"]
        raise ValueError("OpenAI 응답에서 output_text를 찾지 못했습니다.")

    @staticmethod
    def _infer_group_level(members: Sequence[AudienceSummary]) -> str:
        course_count = sum(member.enrollmentCount for member in members)
        average = course_count / max(1, len(members))
        beginner_words = ("기초", "입문", "시작", "개론")
        beginner_count = sum(any(word in course.title for word in beginner_words)
                             for member in members for course in member.enrolledCourses)
        if average <= 2.5 or beginner_count >= max(1, course_count // 2):
            return "입문"
        if average >= 5:
            return "고급"
        return "중급"

    def _category_affinity(self, left: str, right: str) -> int:
        if left == right:
            return 3
        if right in self.ADJACENT_CATEGORIES.get(left, []):
            return 2
        if left in self.ADJACENT_CATEGORIES.get(right, []):
            return 1
        return 0

    def _to_audience_course(self, course: CourseResponse) -> AudienceCourse:
        return AudienceCourse(
            id=course.id, title=course.title,
            category=self._category_label(course.category.value), price=int(course.price),
            enrollmentCount=course.enrollmentCount,
            salesCount=self._sales_count(course.id, course),
        )

    def _sales_count(self, course_id: int, course: CourseResponse) -> int:
        return self.sales_by_course_id.get(course_id, course.enrollmentCount)

    def _category_label(self, category: str) -> str:
        return self.CATEGORY_LABELS.get(category, category)

    def _category_code(self, category: str) -> str:
        return next(
            (code for code, label in self.CATEGORY_LABELS.items() if label == category),
            category,
        )


audience_package_service = AudiencePackageService()
