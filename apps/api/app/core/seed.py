"""
Initialize the admissions catalog and career reference data.
"""

import logging

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.admissions_catalog import insert_catalog, load_catalog
from app.core.models_db import Career, University

logger = logging.getLogger("foryourfuture.seed")


def seed_initial_data(db: Session):
    """Initialize the workbook catalog when the university table is empty."""
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(20261118, 126)"))

    if db.scalar(select(University.uni_id).limit(1)) is not None:
        logger.info("Existing admissions catalog found. Skipping seed.")
        return

    schools, logos = load_catalog()
    _seed_careers(db)
    insert_catalog(db, schools, logos)
    db.commit()
    logger.info("Initialized the admissions catalog with %s schools.", len(schools))


def _seed_careers(db: Session):
    careers_data = [
        Career(
            career_id="car_ai_data",
            title="Kỹ sư Trí tuệ Nhân tạo & Khoa học Dữ liệu",
            name="Kỹ sư Trí tuệ Nhân tạo & Khoa học Dữ liệu",
            domain="Công nghệ Thông tin",
            holland_codes=["RIA", "RIC", "IRC", "IRA", "AIR"],
            description="Nghiên cứu, thiết kế và triển khai các mô hình học máy (Machine Learning), Deep Learning và hệ thống dữ liệu lớn.",
            job_growth_rate=22.5,
            salary_entry=18000000,
            salary_mid=45000000,
            entry_salary_avg=18.0,
            senior_salary_avg=45.0,
            top_companies=["VinAI", "FPT Software", "Viettel", "Zalo", "Google"],
            hiring_companies=["VinAI", "FPT Software", "Viettel", "Zalo", "Google"],
            skills=["Python", "PyTorch", "SQL", "Thuật toán", "Tư duy Logic"],
        ),
        Career(
            career_id="car_software_eng",
            title="Kỹ sư Phần mềm & Hệ thống Thông tin",
            name="Kỹ sư Phần mềm & Hệ thống Thông tin",
            domain="Công nghệ Thông tin",
            holland_codes=["IRC", "RIC", "ICR", "CRI", "RCI", "RIA"],
            description="Phát triển các ứng dụng web, di động, kiến trúc backend phân tán và giải pháp phần mềm doanh nghiệp.",
            job_growth_rate=18.0,
            salary_entry=15000000,
            salary_mid=35000000,
            entry_salary_avg=15.0,
            senior_salary_avg=35.0,
            top_companies=["FPT", "VNG", "One Mount", "VNPT", "Shopee"],
            hiring_companies=["FPT", "VNG", "One Mount", "VNPT", "Shopee"],
            skills=["Java", "Golang", "React", "Docker", "Hệ thống phân tán"],
        ),
        Career(
            career_id="car_finance_invest",
            title="Chuyên viên Phân tích Tài chính & Đầu tư",
            name="Chuyên viên Phân tích Tài chính & Đầu tư",
            domain="Kinh tế & Tài chính",
            holland_codes=["ECS", "ESC", "SEC", "CES", "SCE"],
            description="Phân tích báo cáo tài chính, thẩm định dự án đầu tư và quản trị rủi ro danh mục.",
            job_growth_rate=14.0,
            salary_entry=12000000,
            salary_mid=32000000,
            entry_salary_avg=12.0,
            senior_salary_avg=32.0,
            top_companies=["SSI", "VNDirect", "Vietcombank", "MBBank", "KPMG"],
            hiring_companies=["SSI", "VNDirect", "Vietcombank", "MBBank", "KPMG"],
            skills=["Excel", "Mô hình tài chính", "CFA", "Kế toán", "Đàm phán"],
        ),
        Career(
            career_id="car_cyber_security",
            title="Chuyên viên An ninh Mạng & Điều tra Số",
            name="Chuyên viên An ninh Mạng & Điều tra Số",
            domain="An ninh & Quốc phòng",
            holland_codes=["RCS", "CRS", "SCR", "RCI", "ICR"],
            description="Bảo vệ hệ thống mạng quốc gia, điều tra phòng chống tội phạm công nghệ cao và phòng thủ không gian mạng.",
            job_growth_rate=20.0,
            salary_entry=16000000,
            salary_mid=40000000,
            entry_salary_avg=16.0,
            senior_salary_avg=40.0,
            top_companies=["Bộ Công an", "Ban Cơ yếu Chính phủ", "Viettel Cyber Security", "BKAV"],
            hiring_companies=["Bộ Công an", "Ban Cơ yếu Chính phủ", "Viettel Cyber Security", "BKAV"],
            skills=["An toàn thông tin", "Reverse Engineering", "Mạng máy tính", "Kỷ luật"],
        ),
        Career(
            career_id="car_math_teacher",
            title="Giảng viên & Nhà giáo dục Toán học",
            name="Giảng viên & Nhà giáo dục Toán học",
            domain="Giáo dục & Sư phạm",
            holland_codes=["IAS", "SAI", "ASI", "ISA", "SIA"],
            description="Giảng dạy toán học tại các trường chuyên, THPT, đại học và nghiên cứu khoa học giáo dục.",
            job_growth_rate=10.0,
            salary_entry=9000000,
            salary_mid=22000000,
            entry_salary_avg=9.0,
            senior_salary_avg=22.0,
            top_companies=["Các trường THPT Chuyên", "Trường Đại học Sư phạm", "Hệ thống Vinschool"],
            hiring_companies=["Các trường THPT Chuyên", "Trường Đại học Sư phạm", "Hệ thống Vinschool"],
            skills=["Nghiệp vụ sư phạm", "Toán cao cấp", "Truyền đạt", "Tâm lý học"],
        ),
    ]
    existing_ids = set(db.scalars(select(Career.career_id)))
    db.add_all(career for career in careers_data if career.career_id not in existing_ids)
    db.flush()
