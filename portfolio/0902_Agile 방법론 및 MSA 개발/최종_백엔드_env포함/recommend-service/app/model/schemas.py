from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from enum import Enum
from decimal import Decimal
from datetime import datetime


class CourseCategory(str, Enum):
    BACKEND = "BACKEND"
    FRONTEND = "FRONTEND"
    DEVOPS = "DEVOPS"
    DATA_SCIENCE = "DATA_SCIENCE"
    MOBILE = "MOBILE"
    SECURITY = "SECURITY"
    DATABASE = "DATABASE"
    OTHER = "OTHER"


class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: CourseCategory
    price: Decimal
    instructorId: int
    enrollmentCount: int
    status: str
    createdAt: Optional[datetime] = None


class EnrollmentHistoryResponse(BaseModel):
    userId: int
    activeCourseIds: List[int]


class RecommendResponse(BaseModel):
    """기존 사용자 단위 강의 추천 API의 응답 계약."""

    userId: int
    recommendedCourses: List[CourseResponse]
    basedOnCategory: Optional[CourseCategory] = None
    message: str


class PackageDraftRequest(BaseModel):
    """기존 자연어 기반 패키지 초안 API의 요청 계약."""

    persona: str = Field(min_length=5, max_length=500)
    goal: str = Field(min_length=5, max_length=500)
    bundleSize: Optional[Literal[2, 3, 4]] = None
    maxBudget: Optional[int] = Field(default=None, ge=0)


class PackageDraftCourse(BaseModel):
    id: int
    title: str
    category: str
    description: Optional[str] = None
    price: int
    learningOrder: int
    salesCount: int
    reason: str


class PackageDraftResponse(BaseModel):
    mode: Literal["AI", "RULE_BASED"]
    packageName: str
    targetPersona: str
    courses: List[PackageDraftCourse]
    originalPrice: int
    discountRate: int
    packagePrice: int
    coPurchaseCount: int
    recommendationReason: str


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class UserSummary(BaseModel):
    id: int
    email: str
    name: str
    role: str
    createdAt: Optional[datetime] = None


class AudienceCourse(BaseModel):
    id: int
    title: str
    category: str
    price: int
    enrollmentCount: int
    salesCount: int


class AudienceSummary(BaseModel):
    userId: int
    enrollmentCount: int
    enrolledCourses: List[AudienceCourse]


class CoPurchaseEvidence(BaseModel):
    courseIds: List[int]
    courseNames: List[str]
    coPurchaseCount: int


# 전체 수강생 군집화 → 담당자 검토 → 페르소나별 번들 생성에 사용하는 2단계 모델
class PersonaGenerationRequest(BaseModel):
    maxPersonaCount: int = Field(default=5, ge=3, le=5)


class PersonaDraft(BaseModel):
    personaId: str = Field(min_length=1, max_length=50)
    personaKeyword: str = Field(min_length=2, max_length=100)
    memberUserIds: List[int] = Field(min_length=1)
    personaReason: str = Field(min_length=2, max_length=1000)
    interests: List[str] = Field(min_length=1, max_length=5)
    level: str = Field(min_length=1, max_length=30)


class PersonaGenerationResponse(BaseModel):
    personas: List[PersonaDraft] = Field(min_length=3, max_length=5)


class PersonaBundleGenerationRequest(BaseModel):
    personas: List[PersonaDraft] = Field(min_length=3, max_length=5)
    minBundleSize: int = Field(default=3, ge=3, le=6)
    maxBundleSize: int = Field(default=6, ge=3, le=6)


class PersonaBundleCourse(BaseModel):
    courseId: int
    courseName: str
    category: str
    price: int
    salesCount: int
    learningOrder: int
    reason: str


class PersonaBundle(BaseModel):
    bundleId: str
    bundleName: str
    courses: List[PersonaBundleCourse] = Field(min_length=3, max_length=6)
    bundleReason: str
    coPurchaseEvidence: List[CoPurchaseEvidence]
    originalPrice: int
    discountRate: int
    bundlePrice: int


class PersonaWithBundle(PersonaDraft):
    bundle: PersonaBundle


class PersonaBundleResponse(BaseModel):
    personas: List[PersonaWithBundle] = Field(min_length=3, max_length=5)
