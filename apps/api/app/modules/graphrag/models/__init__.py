"""
GraphRAG Career Guidance System - Unified Python Domain Models.
Exports all Enums, Node entities, Edge entities, and API Contracts.
"""

from .enums import (
    Gender,
    GenderRequirement,
    PriorityZone,
    AcademicRank,
    AdmissionMethod,
    UniversityType,
    DegreeLevel,
    ProgramLanguage,
    Region,
    IncomeLevel,
    RegionType,
    TestType,
    GrowthOutlook,
    WorkEnvironment,
    SkillCategory,
    ExperienceLevel,
    JobType,
    CertRecognitionLevel,
    ScholarshipType,
    StandardizedTestType,
    VerificationStatus,
)

from .student import (
    StudentProfile,
    HealthProfile,
    StudentBackground,
    AcademicProfile,
    InternationalCertificate,
    CompetencyAssessment,
    PersonalityTestResult,
    Achievement,
)

from .career import (
    Career,
    Skill,
    JobPosition,
    ProfessionalCert,
    CompetencyRequirement,
    Industry,
    MarketTrend,
)

from .university import (
    HollandType,
    SubjectGroup,
    Location,
    FinancialAspect,
    AdmissionCriteria,
    Scholarship,
    ProgramType,
    Program,
    University,
)

from .recommendation import (
    RecommendationRequest,
    RecommendationResultItem,
    RecommendationResponse,
    AIConsultStreamRequest,
    ChatPromptRequest,
    PortfolioRecommendationResponse,
    ScoredProgramItem,
)

from .constants import (
    IELTS_TO_SCORE,
    calculate_combined_score,
)

from .query_builder import CypherQueryBuilder

__all__ = [
    # Enums
    "Gender",
    "GenderRequirement",
    "PriorityZone",
    "AcademicRank",
    "AdmissionMethod",
    "UniversityType",
    "DegreeLevel",
    "ProgramLanguage",
    "Region",
    "IncomeLevel",
    "RegionType",
    "TestType",
    "GrowthOutlook",
    "WorkEnvironment",
    "SkillCategory",
    "ExperienceLevel",
    "JobType",
    "CertRecognitionLevel",
    "ScholarshipType",
    "StandardizedTestType",
    "VerificationStatus",
    # Student Domain
    "StudentProfile",
    "HealthProfile",
    "StudentBackground",
    "AcademicProfile",
    "InternationalCertificate",
    "CompetencyAssessment",
    "PersonalityTestResult",
    "Achievement",
    # Career Domain
    "Career",
    "Skill",
    "JobPosition",
    "ProfessionalCert",
    "CompetencyRequirement",
    "Industry",
    "MarketTrend",
    # University Domain
    "HollandType",
    "SubjectGroup",
    "Location",
    "FinancialAspect",
    "AdmissionCriteria",
    "Scholarship",
    "ProgramType",
    "Program",
    "University",
    # Recommendation & API
    "RecommendationRequest",
    "RecommendationResultItem",
    "RecommendationResponse",
    "AIConsultStreamRequest",
    # Constants & Helpers
    "IELTS_TO_SCORE",
    "calculate_combined_score",
    "CypherQueryBuilder",
]
