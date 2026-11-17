"""
Enrich Neo4j Knowledge Graph with HCM Universities (Self-contained Cypher statements):
- QSK (ĐH Bách khoa ĐHQG TP.HCM)
- UEH (Đại học Kinh tế TP.HCM)
- UIT (Trường ĐH Công nghệ Thông tin - ĐHQG TP.HCM)
- SPK (Trường ĐH Sư phạm Kỹ thuật TP.HCM)
Covers benchmark range 22 - 27 for A01 / A00 admissions.
"""

from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "sitk2023")

STATEMENTS = [
    # 1. Location
    """MERGE (loc:Location {location_id: 'LOC_HCM_CENTRAL'})
       SET loc.campus_name = 'Khu vực TP.HCM',
           loc.city = 'TP.HCM',
           loc.address = 'TP. Hồ Chí Minh',
           loc.region = 'South',
           loc.cost_of_living_index = 80,
           loc.public_transport_score = 85""",

    # 2. Subject Groups
    """MERGE (sg:SubjectGroup {group_code: 'A01'})
       SET sg.group_name = 'Toán, Vật lý, Tiếng Anh', sg.subjects = ['Toán', 'Vật lý', 'Tiếng Anh']""",

    """MERGE (sg:SubjectGroup {group_code: 'A00'})
       SET sg.group_name = 'Toán, Vật lý, Hóa học', sg.subjects = ['Toán', 'Vật lý', 'Hóa học']""",

    """MERGE (sg:SubjectGroup {group_code: 'D01'})
       SET sg.group_name = 'Toán, Ngữ văn, Tiếng Anh', sg.subjects = ['Toán', 'Ngữ văn', 'Tiếng Anh']""",

    # 3. Holland Types
    """MERGE (h:HollandType {code: 'RIA'})
       SET h.name = 'Kỹ thuật - Nghiên cứu - Nghệ thuật',
           h.primary_traits = ['Thực tế', 'Tư duy logic', 'Sáng tạo giải pháp']""",

    """MERGE (h:HollandType {code: 'SEC'})
       SET h.name = 'Xã hội - Quản lý - Nghiệp vụ',
           h.primary_traits = ['Giao tiếp', 'Đàm phán', 'Tổ chức quy trình']""",

    # 4. Careers
    """MERGE (c:Career {career_id: 'CAR_SOFTWARE_ENG'})
       SET c.name = 'Kỹ sư Phần mềm',
           c.title = 'Kỹ sư Phần mềm',
           c.domain = 'Công nghệ Thông tin',
           c.job_growth_rate = 18.0,
           c.entry_salary_avg = 15000000,
           c.senior_salary_avg = 35000000,
           c.avg_salary_entry = 15.0,
           c.avg_salary_mid = 35.0,
           c.hiring_companies = ['FPT', 'VNG', 'Shopee', 'Momo']""",

    """MERGE (c:Career {career_id: 'CAR_DATA_SCIENTIST'})
       SET c.name = 'Kỹ sư Dữ liệu & AI',
           c.title = 'Kỹ sư Dữ liệu & AI',
           c.domain = 'Công nghệ Thông tin',
           c.job_growth_rate = 22.0,
           c.entry_salary_avg = 18000000,
           c.senior_salary_avg = 45000000,
           c.avg_salary_entry = 18.0,
           c.avg_salary_mid = 45.0,
           c.hiring_companies = ['VinAI', 'Zalo', 'Viettel', 'NAB']""",

    """MERGE (c:Career {career_id: 'CAR_INTL_BIZ'})
       SET c.name = 'Chuyên viên Kinh doanh Quốc tế',
           c.title = 'Chuyên viên Kinh doanh Quốc tế',
           c.domain = 'Kinh tế & Thương mại',
           c.job_growth_rate = 15.0,
           c.entry_salary_avg = 14000000,
           c.senior_salary_avg = 32000000,
           c.avg_salary_entry = 14.0,
           c.avg_salary_mid = 32.0,
           c.hiring_companies = ['Unilever', 'P&G', 'DHL', 'Samsung']""",

    # 5. Career - Holland relationships
    """MATCH (h:HollandType {code: 'RIA'}), (c:Career {career_id: 'CAR_SOFTWARE_ENG'})
       MERGE (h)-[:ALIGNED_WITH {weight: 1.0}]->(c)""",

    """MATCH (h:HollandType {code: 'RIA'}), (c:Career {career_id: 'CAR_DATA_SCIENTIST'})
       MERGE (h)-[:ALIGNED_WITH {weight: 1.0}]->(c)""",

    """MATCH (h:HollandType {code: 'SEC'}), (c:Career {career_id: 'CAR_INTL_BIZ'})
       MERGE (h)-[:ALIGNED_WITH {weight: 0.9}]->(c)""",

    # 6. Universities
    """MERGE (u:University {uni_id: 'QSK'})
       SET u.name = 'Trường Đại học Bách khoa - ĐHQG TP.HCM',
           u.type = 'Public',
           u.student_faculty_ratio = 19.0,
           u.has_dormitory = true,
           u.campus_facilities = ['KTX Bách Khoa', 'Trung tâm HPC', 'Thư viện số'],
           u.website = 'https://hcmut.edu.vn'""",

    """MERGE (u:University {uni_id: 'UEH'})
       SET u.name = 'Đại học Kinh tế TP.HCM',
           u.type = 'Public',
           u.student_faculty_ratio = 22.0,
           u.has_dormitory = true,
           u.campus_facilities = ['Cơ sở B Nguyễn Tri Phương', 'Smart Campus', 'Thư viện thông minh'],
           u.website = 'https://ueh.edu.vn'""",

    """MERGE (u:University {uni_id: 'UIT'})
       SET u.name = 'Trường ĐH Công nghệ Thông tin - ĐHQG TP.HCM',
           u.type = 'Public',
           u.student_faculty_ratio = 18.0,
           u.has_dormitory = true,
           u.campus_facilities = ['Khuôn viên ĐHQG Thủ Đức', 'Lab An toàn thông tin', 'KTX ĐHQG'],
           u.website = 'https://uit.edu.vn'""",

    """MERGE (u:University {uni_id: 'SPK'})
       SET u.name = 'Trường ĐH Sư phạm Kỹ thuật TP.HCM',
           u.type = 'Public',
           u.student_faculty_ratio = 20.0,
           u.has_dormitory = true,
           u.campus_facilities = ['Trung tâm thực hành tự động hóa', 'KTX Võ Văn Ngân'],
           u.website = 'https://hcmute.edu.vn'""",

    # Universities LOCATED_AT
    """MATCH (u:University), (loc:Location {location_id: 'LOC_HCM_CENTRAL'})
       WHERE u.uni_id IN ['QSK', 'UEH', 'UIT', 'SPK']
       MERGE (u)-[:LOCATED_AT]->(loc)""",

    # 7. Programs
    # QSK CS
    """MERGE (p:Program {program_id: 'QSK_CS'})
       SET p.name = 'Khoa học Máy tính',
           p.major_code = '7480201',
           p.degree_level = 'Kỹ sư',
           p.educational_credential_awarded = 'Bằng Kỹ sư Khoa học Máy tính',
           p.accreditation = 'AUN-QA, ABET'""",
    """MATCH (p:Program {program_id: 'QSK_CS'}), (u:University {uni_id: 'QSK'}) MERGE (p)-[:OFFERED_BY]->(u)""",
    """MATCH (p:Program {program_id: 'QSK_CS'}), (c:Career {career_id: 'CAR_DATA_SCIENTIST'}) MERGE (p)-[:PREPARES_FOR]->(c)""",

    """MERGE (fa:FinancialAspect {financial_id: 'FA_QSK_CS_2025'})
       SET fa.academic_year = 2025, fa.tuition_fee_annual = 30000000, fa.tuition_subsidy = false, fa.effective_annual_cost = 30000000""",
    """MATCH (p:Program {program_id: 'QSK_CS'}), (fa:FinancialAspect {financial_id: 'FA_QSK_CS_2025'}) MERGE (p)-[:HAS_FINANCIAL]->(fa)""",

    """MERGE (ad:AdmissionCriteria {criteria_id: 'AD_QSK_CS_2025_A01'})
       SET ad.year = 2025, ad.is_latest = true, ad.method = 'Thi THPT', ad.benchmark_score = 26.5, ad.minimum_threshold = 22.0, ad.score_scale = 30.0, ad.gender_requirement = 'Any'""",
    """MATCH (p:Program {program_id: 'QSK_CS'}), (ad:AdmissionCriteria {criteria_id: 'AD_QSK_CS_2025_A01'}) MERGE (p)-[:HAS_CRITERIA]->(ad)""",
    """MATCH (ad:AdmissionCriteria {criteria_id: 'AD_QSK_CS_2025_A01'}), (sg:SubjectGroup {group_code: 'A01'}) MERGE (ad)-[:REQUIRES_GROUP]->(sg)""",

    # UIT SE
    """MERGE (p:Program {program_id: 'UIT_SE'})
       SET p.name = 'Kỹ thuật Phần mềm',
           p.major_code = '7480103',
           p.degree_level = 'Kỹ sư',
           p.educational_credential_awarded = 'Bằng Kỹ sư Kỹ thuật Phần mềm',
           p.accreditation = 'AUN-QA'""",
    """MATCH (p:Program {program_id: 'UIT_SE'}), (u:University {uni_id: 'UIT'}) MERGE (p)-[:OFFERED_BY]->(u)""",
    """MATCH (p:Program {program_id: 'UIT_SE'}), (c:Career {career_id: 'CAR_SOFTWARE_ENG'}) MERGE (p)-[:PREPARES_FOR]->(c)""",

    """MERGE (fa:FinancialAspect {financial_id: 'FA_UIT_SE_2025'})
       SET fa.academic_year = 2025, fa.tuition_fee_annual = 33000000, fa.tuition_subsidy = false, fa.effective_annual_cost = 33000000""",
    """MATCH (p:Program {program_id: 'UIT_SE'}), (fa:FinancialAspect {financial_id: 'FA_UIT_SE_2025'}) MERGE (p)-[:HAS_FINANCIAL]->(fa)""",

    """MERGE (ad:AdmissionCriteria {criteria_id: 'AD_UIT_SE_2025_A01'})
       SET ad.year = 2025, ad.is_latest = true, ad.method = 'Thi THPT', ad.benchmark_score = 25.5, ad.minimum_threshold = 20.0, ad.score_scale = 30.0, ad.gender_requirement = 'Any'""",
    """MATCH (p:Program {program_id: 'UIT_SE'}), (ad:AdmissionCriteria {criteria_id: 'AD_UIT_SE_2025_A01'}) MERGE (p)-[:HAS_CRITERIA]->(ad)""",
    """MATCH (ad:AdmissionCriteria {criteria_id: 'AD_UIT_SE_2025_A01'}), (sg:SubjectGroup {group_code: 'A01'}) MERGE (ad)-[:REQUIRES_GROUP]->(sg)""",

    # UEH IB
    """MERGE (p:Program {program_id: 'UEH_IB'})
       SET p.name = 'Kinh doanh Quốc tế',
           p.major_code = '7340120',
           p.degree_level = 'Cử nhân',
           p.educational_credential_awarded = 'Bằng Cử nhân Kinh doanh Quốc tế',
           p.accreditation = 'FIBAA'""",
    """MATCH (p:Program {program_id: 'UEH_IB'}), (u:University {uni_id: 'UEH'}) MERGE (p)-[:OFFERED_BY]->(u)""",
    """MATCH (p:Program {program_id: 'UEH_IB'}), (c:Career {career_id: 'CAR_INTL_BIZ'}) MERGE (p)-[:PREPARES_FOR]->(c)""",

    """MERGE (fa:FinancialAspect {financial_id: 'FA_UEH_IB_2025'})
       SET fa.academic_year = 2025, fa.tuition_fee_annual = 32000000, fa.tuition_subsidy = false, fa.effective_annual_cost = 32000000""",
    """MATCH (p:Program {program_id: 'UEH_IB'}), (fa:FinancialAspect {financial_id: 'FA_UEH_IB_2025'}) MERGE (p)-[:HAS_FINANCIAL]->(fa)""",

    """MERGE (ad:AdmissionCriteria {criteria_id: 'AD_UEH_IB_2025_A01'})
       SET ad.year = 2025, ad.is_latest = true, ad.method = 'Thi THPT', ad.benchmark_score = 25.0, ad.minimum_threshold = 20.0, ad.score_scale = 30.0, ad.gender_requirement = 'Any'""",
    """MATCH (p:Program {program_id: 'UEH_IB'}), (ad:AdmissionCriteria {criteria_id: 'AD_UEH_IB_2025_A01'}) MERGE (p)-[:HAS_CRITERIA]->(ad)""",
    """MATCH (ad:AdmissionCriteria {criteria_id: 'AD_UEH_IB_2025_A01'}), (sg:SubjectGroup {group_code: 'A01'}) MERGE (ad)-[:REQUIRES_GROUP]->(sg)""",

    # SPK IT
    """MERGE (p:Program {program_id: 'SPK_IT'})
       SET p.name = 'Công nghệ Thông tin',
           p.major_code = '7480201',
           p.degree_level = 'Kỹ sư',
           p.educational_credential_awarded = 'Bằng Kỹ sư Công nghệ Thông tin',
           p.accreditation = 'AUN-QA'""",
    """MATCH (p:Program {program_id: 'SPK_IT'}), (u:University {uni_id: 'SPK'}) MERGE (p)-[:OFFERED_BY]->(u)""",
    """MATCH (p:Program {program_id: 'SPK_IT'}), (c:Career {career_id: 'CAR_SOFTWARE_ENG'}) MERGE (p)-[:PREPARES_FOR]->(c)""",

    """MERGE (fa:FinancialAspect {financial_id: 'FA_SPK_IT_2025'})
       SET fa.academic_year = 2025, fa.tuition_fee_annual = 26000000, fa.tuition_subsidy = false, fa.effective_annual_cost = 26000000""",
    """MATCH (p:Program {program_id: 'SPK_IT'}), (fa:FinancialAspect {financial_id: 'FA_SPK_IT_2025'}) MERGE (p)-[:HAS_FINANCIAL]->(fa)""",

    """MERGE (ad:AdmissionCriteria {criteria_id: 'AD_SPK_IT_2025_A01'})
       SET ad.year = 2025, ad.is_latest = true, ad.method = 'Thi THPT', ad.benchmark_score = 24.5, ad.minimum_threshold = 19.0, ad.score_scale = 30.0, ad.gender_requirement = 'Any'""",
    """MATCH (p:Program {program_id: 'SPK_IT'}), (ad:AdmissionCriteria {criteria_id: 'AD_SPK_IT_2025_A01'}) MERGE (p)-[:HAS_CRITERIA]->(ad)""",
    """MATCH (ad:AdmissionCriteria {criteria_id: 'AD_SPK_IT_2025_A01'}), (sg:SubjectGroup {group_code: 'A01'}) MERGE (ad)-[:REQUIRES_GROUP]->(sg)""",
]

def seed_neo4j():
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    with driver.session() as session:
        for stmt in STATEMENTS:
            session.run(stmt)
        print("Enriched Neo4j Knowledge Graph with HCM universities (QSK, UEH, UIT, SPK) with self-contained statements successfully!")
    driver.close()

if __name__ == "__main__":
    seed_neo4j()
