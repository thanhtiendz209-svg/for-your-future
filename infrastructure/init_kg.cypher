// ==========================================
// BƯỚC 1: XÓA DỮ LIỆU CŨ (Để bắt đầu sạch)
// ==========================================
MATCH (n) DETACH DELETE n;

// ==========================================
// BƯỚC 2: TẠO CÁC NODES VỚI THUỘC TÍNH MẪU
// ==========================================

// --- 1. Student Domain ---
CREATE (st:Student {student_id: 'ST01', first_name: 'Nguyen', last_name: 'Van A', dob: '2005-01-01', gender: 'Male', email: 'a@email.com', phone: '0123456789', nationality: 'Vietnam', address: 'HCMC', social_links: ['linkedin.com/in/a']})
CREATE (bg:Background {income_level: 'Medium', exact_income: 15000000, currency: 'VND', family_size: 4, parent_occupation: 'Teacher', region_type: 'Urban', financial_hardship: false})
CREATE (ap:AcademicProfile {gpa: 8.5, gpa_scale: 10, gpa_trend: [8.0, 8.2, 8.5], ielts: 7.0, toefl: 0, sat: 0, dgnl: 900, academic_rank: 'Top 10%'})
CREATE (ac:Achievement {achievement_id: 'ACH01', name: 'HSG Quốc Gia', category: 'Academic', level: 'National', rank: 'First', issuing_org: 'MOET', date: '2023-05-01'})
CREATE (sg:SubjectGroup {group_code: 'A00', subjects: ['Toán', 'Lý', 'Hóa'], total_score: 27.5, bonus_points: 1.0})

// --- 2a. Assessment Domain ---
CREATE (ca:CompetencyAssessment {assessment_id: 'CA01', test_name: 'ĐGNL HCM', test_date: '2024-03-01', logic_score: 85, quant_score: 90, verbal_score: 70, total_score: 950, percentile: 95})
CREATE (pt:PersonalityTestResult {test_type: 'MBTI', result_code: 'INTJ', traits: ['Introverted', 'Intuitive', 'Thinking', 'Judging'], description: 'The Architect', confidence_score: 0.9})

// --- 2b. Study Ability Domain ---
CREATE (sa:StudyAbility {study_habits: 'Regular', time_management_score: 8, stress_level: 'Low', learning_style: 'Visual', self_discipline_score: 9})

// --- 3. Career Domain ---
CREATE (cr:Career {career_id: 'CAR01', title: 'Data Scientist', domain: 'IT', description: 'Analyze data', outlook: 'Growing', avg_salary: 2000, work_environment: 'Remote'})
CREATE (c_req:CompetencyRequirement {req_id: 'REQ01', competency_name: 'Logic', required_level: 4, weight: 0.8})
CREATE (jp:JobPosition {position_id: 'JP01', title: 'Junior Data Scientist', min_salary: 1000, max_salary: 2000, currency: 'USD', experience_years: 1, job_type: 'Full-time'})
CREATE (pc:ProfessionalCert {cert_id: 'CERT01', name: 'Google Data Analytics', provider: 'Google', cost: 50, validity_years: 3, recognition_level: 'Global'})
CREATE (sk:Skill {skill_id: 'SK01', name: 'Python', category: 'Hard', proficiency_level: 3})

// --- 4. University Domain ---
CREATE (u:University {uni_id: 'UNI01', name: 'Bách Khoa TP.HCM', type: 'Public', ranking_national: 1, ranking_global: 500, website: 'hcmut.edu.vn', founded_year: 1957})
CREATE (p:Program {program_id: 'PRO01', name: 'Khoa học Máy tính', major_code: 'CS01', degree_level: 'Bachelor', duration_years: 4, language: 'Vietnamese', curriculum_url: 'hcmut.edu.vn/cs'})
CREATE (ptype:ProgramType {type_id: 'PT01', type_name: 'Chính quy'})
CREATE (fa:FinancialAspect {tuition_fee: 30000000, currency: 'VND', scholarship_coverage: 'Partial', other_fees: 5000000})
CREATE (sch:Scholarship {scholarship_id: 'SCH01', name: 'Học bổng Tài năng', type: 'Merit', amount: 10000000, percentage: 50, conditions: 'GPA > 8.5', slots: 10})
CREATE (ad:AdmissionCriteria {criteria_id: 'AD01', method: 'Thi THPT', min_score: 27.0, quota: 100, deadline: '2024-07-01', subject_combinations: ['A00', 'A01']})
CREATE (loc:Location {city: 'HCMC', country: 'Vietnam', region: 'South', cost_of_living_index: 70, campus_type: 'Urban'})

// --- 5. Market & Industry Domain ---
CREATE (mt:MarketTrend {trend_id: 'MT01', name: 'AI & Big Data', sector: 'IT', growth_rate: 0.15, impact_level: 'High', forecast_year: 2025, source: 'Report'})
CREATE (ind:Industry {industry_id: 'IND01', name: 'IT', sector: 'Technology', market_size: 100000000, key_players: ['FPT', 'Viettel']});

// ==========================================
// BƯỚC 3: TẠO CÁC RELATIONSHIPS (MỐI QUAN HỆ)
// ==========================================

// --- Student Relationships ---
MATCH (st:Student {student_id: 'ST01'}), (bg:Background {income_level: 'Medium'}) CREATE (st)-[:HAS]->(bg);
MATCH (st:Student {student_id: 'ST01'}), (bg:Background {income_level: 'Medium'}) CREATE (st)-[:CONSTRAINED_BY]->(bg);
MATCH (st:Student {student_id: 'ST01'}), (ca:CompetencyAssessment {assessment_id: 'CA01'}) CREATE (st)-[:ASSESSED]->(ca);
MATCH (st:Student {student_id: 'ST01'}), (pt:PersonalityTestResult {test_type: 'MBTI'}) CREATE (st)-[:HAS]->(pt);
MATCH (st:Student {student_id: 'ST01'}), (ap:AcademicProfile {gpa: 8.5}) CREATE (st)-[:HAS]->(ap);
MATCH (st:Student {student_id: 'ST01'}), (sa:StudyAbility {learning_style: 'Visual'}) CREATE (st)-[:HAS]->(sa);
MATCH (st:Student {student_id: 'ST01'}), (sch:Scholarship {scholarship_id: 'SCH01'}) CREATE (st)-[:CAN_AFFORD]->(sch);
MATCH (st:Student {student_id: 'ST01'}), (cr:Career {career_id: 'CAR01'}) CREATE (st)-[:PREFERRED {priority: 1}]->(cr);
MATCH (st:Student {student_id: 'ST01'}), (p:Program {program_id: 'PRO01'}) CREATE (st)-[:PREFERRED {priority: 1}]->(p);

// --- Assessment & Study Ability Relationships ---
MATCH (ap:AcademicProfile {gpa: 8.5}), (ac:Achievement {achievement_id: 'ACH01'}) CREATE (ap)-[:SPECIFIES]->(ac);
MATCH (ap:AcademicProfile {gpa: 8.5}), (sg:SubjectGroup {group_code: 'A00'}) CREATE (ap)-[:QUALIFIES]->(sg);
MATCH (ap:AcademicProfile {gpa: 8.5}), (ad:AdmissionCriteria {criteria_id: 'AD01'}) CREATE (ap)-[:MEETS {score_margin: 0.5}]->(ad);
MATCH (ap:AcademicProfile {gpa: 8.5}), (sch:Scholarship {scholarship_id: 'SCH01'}) CREATE (ap)-[:ELIGIBLE_FOR]->(sch);
MATCH (ca:CompetencyAssessment {assessment_id: 'CA01'}), (c_req:CompetencyRequirement {req_id: 'REQ01'}) CREATE (ca)-[:SATISFIES {match_score: 85}]->(c_req);
MATCH (pt:PersonalityTestResult {test_type: 'MBTI'}), (cr:Career {career_id: 'CAR01'}) CREATE (pt)-[:MATCH {match_percentage: 90}]->(cr);

// --- Career Relationships ---
MATCH (cr:Career {career_id: 'CAR01'}), (c_req:CompetencyRequirement {req_id: 'REQ01'}) CREATE (cr)-[:HAS]->(c_req);
MATCH (cr:Career {career_id: 'CAR01'}), (jp:JobPosition {position_id: 'JP01'}) CREATE (cr)-[:DEMANDS]->(jp);
MATCH (cr:Career {career_id: 'CAR01'}), (jp:JobPosition {position_id: 'JP01'}) CREATE (cr)-[:MAPS]->(jp);
MATCH (cr:Career {career_id: 'CAR01'}), (sk:Skill {skill_id: 'SK01'}) CREATE (cr)-[:DEMANDS]->(sk);
MATCH (cr:Career {career_id: 'CAR01'}), (sk:Skill {skill_id: 'SK01'}) CREATE (cr)-[:REQUIRES {proficiency_level: 3}]->(sk);
MATCH (cr:Career {career_id: 'CAR01'}), (pc:ProfessionalCert {cert_id: 'CERT01'}) CREATE (cr)-[:REQUIRES]->(pc);
MATCH (jp:JobPosition {position_id: 'JP01'}), (pc:ProfessionalCert {cert_id: 'CERT01'}) CREATE (jp)-[:REQUIRES]->(pc);

// --- University Relationships ---
MATCH (u:University {uni_id: 'UNI01'}), (p:Program {program_id: 'PRO01'}) CREATE (u)-[:OFFERS]->(p);
MATCH (p:Program {program_id: 'PRO01'}), (cr:Career {career_id: 'CAR01'}) CREATE (p)-[:PREPARES_FOR]->(cr);
MATCH (p:Program {program_id: 'PRO01'}), (sk:Skill {skill_id: 'SK01'}) CREATE (p)-[:TEACHES {course_code: 'CS101'}]->(sk);
MATCH (p:Program {program_id: 'PRO01'}), (ptype:ProgramType {type_id: 'PT01'}) CREATE (p)-[:HAS]->(ptype);
MATCH (p:Program {program_id: 'PRO01'}), (fa:FinancialAspect {tuition_fee: 30000000}) CREATE (p)-[:HAS]->(fa);
MATCH (p:Program {program_id: 'PRO01'}), (ad:AdmissionCriteria {criteria_id: 'AD01'}) CREATE (p)-[:HAS]->(ad);
MATCH (p:Program {program_id: 'PRO01'}), (sch:Scholarship {scholarship_id: 'SCH01'}) CREATE (p)-[:OFFERS]->(sch);
MATCH (p:Program {program_id: 'PRO01'}), (loc:Location {city: 'HCMC'}) CREATE (p)-[:LOCATED_AT]->(loc);
MATCH (u:University {uni_id: 'UNI01'}), (loc:Location {city: 'HCMC'}) CREATE (u)-[:LOCATED_AT]->(loc);
MATCH (ad:AdmissionCriteria {criteria_id: 'AD01'}), (sg:SubjectGroup {group_code: 'A00'}) CREATE (ad)-[:USE]->(sg);

// --- Market & Industry Relationships ---
MATCH (mt:MarketTrend {trend_id: 'MT01'}), (cr:Career {career_id: 'CAR01'}) CREATE (mt)-[:HAS {impact_score: 0.9}]->(cr);
MATCH (ind:Industry {industry_id: 'IND01'}), (cr:Career {career_id: 'CAR01'}) CREATE (ind)-[:NEED]->(cr);
