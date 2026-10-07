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
    userId: int
    recommendedCourses: List[CourseResponse]
    basedOnCategory: Optional[CourseCategory] = None
    message: str


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class PackageDraftRequest(BaseModel):
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
    userName: str
    email: str
    enrollmentCount: int
    enrolledCourses: List[AudienceCourse]


class InferredPersona(BaseModel):
    position: str
    level: str
    interests: List[str]
    summary: str


class PackageRecommendationCourse(AudienceCourse):
    learningOrder: int
    reason: str


class CoPurchaseEvidence(BaseModel):
    courseIds: List[int]
    courseNames: List[str]
    coPurchaseCount: int


class AudiencePackageRecommendation(BaseModel):
    id: str
    name: str
    summary: str
    courses: List[PackageRecommendationCourse]
    originalPrice: int
    discountRate: int
    packagePrice: int
    coPurchaseCount: int
    coPurchaseEvidence: List[CoPurchaseEvidence]
    recommendationReason: str


class AudiencePackageResponse(BaseModel):
    mode: Literal["AI", "RULE_BASED"]
    generatedAt: datetime
    user: UserSummary
    persona: InferredPersona
    enrollmentHistory: List[AudienceCourse]
    packages: List[AudiencePackageRecommendation]
