"""
Enumerations and Constants for the GraphRAG Career Guidance System.
Aligned with Ministry of Education & Training regulations, Schema.org, and CTDL standards.
"""

from enum import Enum


class StandardizedTestType(str, Enum):
    V_ACT = "V-ACT"   # ĐGNL ĐHQG-HCM (Thang 1200)
    HSA = "HSA"       # ĐGNL ĐHQG-HN (Thang 150)
    TSA = "TSA"       # ĐGTD ĐH Bách Khoa Hà Nội (Thang 100)
    INTERNAL = "INTERNAL_APTITUDE" # Bài test tư duy nhanh trên web


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class GenderRequirement(str, Enum):
    ANY = "Any"
    MALE = "Male"
    FEMALE = "Female"


class PriorityZone(str, Enum):
    KV1 = "KV1"
    KV2_NT = "KV2-NT"
    KV2 = "KV2"
    KV3 = "KV3"


class AcademicRank(str, Enum):
    EXCELLENT = "Xuất sắc"
    GOOD = "Giỏi"
    FAIR = "Khá"
    AVERAGE = "Trung bình"


class AdmissionMethod(str, Enum):
    THPT = "Thi THPT"
    DGNL = "ĐGNL"
    HOC_BA = "Học bạ"
    TUYEN_THANG = "Tuyển thẳng"
    KET_HOP = "Kết hợp"
    TAI_NANG = "Xét tuyển tài năng"
    DANH_GIA_TU_DUY = "Đánh giá tư duy"


class VerificationStatus(str, Enum):
    PENDING = "Pending"
    VERIFIED = "Verified"
    REJECTED = "Rejected"


class UniversityType(str, Enum):
    PUBLIC = "Public"
    PRIVATE = "Private"
    INTERNATIONAL = "International"


class DegreeLevel(str, Enum):
    BACHELOR = "Bachelor"
    ENGINEER = "Engineer"
    MASTER = "Master"


class ProgramLanguage(str, Enum):
    VIETNAMESE = "Vietnamese"
    ENGLISH = "English"
    BILINGUAL = "Bilingual"


class Region(str, Enum):
    NORTH = "North"
    CENTRAL = "Central"
    SOUTH = "South"


class IncomeLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RegionType(str, Enum):
    URBAN = "Urban"
    SUBURBAN = "Suburban"
    RURAL = "Rural"


class TestType(str, Enum):
    RIASEC = "RIASEC"
    MBTI = "MBTI"
    BIGFIVE = "BIGFIVE"


class GrowthOutlook(str, Enum):
    HIGH = "High"
    MODERATE = "Moderate"
    STABLE = "Stable"
    DECLINING = "Declining"


class WorkEnvironment(str, Enum):
    OFFICE = "Office"
    REMOTE = "Remote"
    FIELD = "Field"
    LAB = "Lab"
    HYBRID = "Hybrid"


class SkillCategory(str, Enum):
    HARD = "Hard"
    SOFT = "Soft"
    TOOL = "Tool"
    LANGUAGE = "Language"


class ExperienceLevel(str, Enum):
    INTERN = "Intern"
    FRESHER = "Fresher"
    JUNIOR = "Junior"
    MID = "Mid"
    SENIOR = "Senior"


class JobType(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"


class CertRecognitionLevel(str, Enum):
    NATIONAL = "National"
    REGIONAL = "Regional"
    GLOBAL = "Global"


class ScholarshipType(str, Enum):
    MERIT = "Merit"
    FINANCIAL_NEED = "Financial_Need"
    CORPORATE = "Corporate"
    EXCHANGE = "Exchange"
