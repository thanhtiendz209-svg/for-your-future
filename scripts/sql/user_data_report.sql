-- One read-only reporting view; no source-table writes, triggers or scheduled jobs.
-- Dates/times retain the source values (application timestamps are UTC).
CREATE VIEW public."dữ liệu người dùng" AS
SELECT
    u.user_id AS "Mã người dùng",
    u.email AS "Email đăng nhập",
    NULLIF(concat_ws(' ', NULLIF(btrim(p.last_name), ''), NULLIF(btrim(p.first_name), '')), '') AS "Họ và tên",
    p.dob AS "Ngày sinh",
    p.gender AS "Giới tính",
    p.phone AS "Số điện thoại",
    p.current_school AS "Trường đang học",
    p.grade_level AS "Lớp",
    p.target_year AS "Năm xét tuyển",
    bg.hometown_province AS "Tỉnh/thành",
    u.role AS "Vai trò",
    u.is_active AS "Đang hoạt động",
    u.created_at AS "Ngày đăng ký",
    p.updated_at AS "Hồ sơ cập nhật lúc",
    acad.data AS "Học bạ và điểm thi",
    bg.data AS "Tài chính và khu vực ưu tiên",
    health.data AS "Thể lực",
    riasec.data AS "Kết quả RIASEC",
    mbti.data AS "Kết quả MBTI",
    bigfive.data AS "Kết quả Big Five",
    cognitive.data AS "Kết quả năng lực nhận thức"
FROM public.users AS u
LEFT JOIN public.student_profiles AS p ON p.student_id = u.user_id
LEFT JOIN LATERAL (
    SELECT b.hometown_province, jsonb_build_object(
        'hometown_province', b.hometown_province,
        'income_level', b.income_level,
        'max_annual_tuition', b.max_annual_tuition,
        'priority_zone', b.priority_zone,
        'priority_object', b.priority_object,
        'priority_points_calculated', b.priority_points_calculated,
        'financial_hardship', b.financial_hardship,
        'created_at', b.created_at
    ) AS data
    FROM public.student_backgrounds AS b
    WHERE b.student_id = u.user_id
    ORDER BY b.created_at DESC NULLS LAST, b.background_id DESC
    LIMIT 1
) AS bg ON TRUE
LEFT JOIN LATERAL (
    SELECT jsonb_build_object(
        'gpa_grade_10', a.gpa_grade_10,
        'gpa_grade_11', a.gpa_grade_11,
        'gpa_grade_12', a.gpa_grade_12,
        'gpa_overall', a.gpa_overall,
        'gpa_5_semesters', a.gpa_5_semesters,
        'academic_rank', a.academic_rank,
        'conduct_grade_10', a.conduct_grade_10,
        'conduct_grade_11', a.conduct_grade_11,
        'conduct_grade_12', a.conduct_grade_12,
        'ielts_score', a.ielts_score,
        'sat_score', a.sat_score,
        'dgnl_hcm_score', a.dgnl_hcm_score,
        'dgnl_hn_score', a.dgnl_hn_score,
        'tsa_hust_score', a.tsa_hust_score,
        'subject_scores', a.subject_scores,
        'exam_scores', a.exam_scores,
        'certificates', a.certificates,
        'updated_at', a.updated_at
    ) AS data
    FROM public.academic_profiles AS a
    WHERE a.student_id = u.user_id
    ORDER BY a.updated_at DESC NULLS LAST, a.created_at DESC NULLS LAST, a.profile_id DESC
    LIMIT 1
) AS acad ON TRUE
LEFT JOIN LATERAL (
    SELECT jsonb_build_object(
        'height_cm', h.height_cm,
        'weight_kg', h.weight_kg,
        'bmi', h.bmi,
        'eye_degree_left', h.eye_degree_left,
        'eye_degree_right', h.eye_degree_right,
        'max_eye_degree', h.max_eye_degree,
        'color_blindness', h.color_blindness,
        'hearing_status', h.hearing_status,
        'physical_grade', h.physical_grade,
        'has_health_certificate', h.has_health_certificate,
        'created_at', h.created_at
    ) AS data
    FROM public.health_profiles AS h
    WHERE h.student_id = u.user_id
    ORDER BY h.created_at DESC NULLS LAST, h.health_id DESC
    LIMIT 1
) AS health ON TRUE
LEFT JOIN LATERAL (
    SELECT jsonb_build_object(
        'result_id', r.result_id,
        'result_code', r.result_code,
        'scores_detail', r.scores_detail,
        'top_traits', r.top_traits,
        'completed_at', r.completed_at
    ) AS data
    FROM public.personality_results AS r
    WHERE r.student_id = u.user_id AND r.test_type = 'RIASEC'
    ORDER BY r.completed_at DESC NULLS LAST, r.result_id DESC
    LIMIT 1
) AS riasec ON TRUE
LEFT JOIN LATERAL (
    SELECT jsonb_build_object(
        'result_id', r.result_id,
        'result_code', r.result_code,
        'scores_detail', r.scores_detail,
        'top_traits', r.top_traits,
        'completed_at', r.completed_at
    ) AS data
    FROM public.personality_results AS r
    WHERE r.student_id = u.user_id AND r.test_type = 'MBTI'
    ORDER BY r.completed_at DESC NULLS LAST, r.result_id DESC
    LIMIT 1
) AS mbti ON TRUE
LEFT JOIN LATERAL (
    SELECT jsonb_build_object(
        'result_id', r.result_id,
        'result_code', r.result_code,
        'scores_detail', r.scores_detail,
        'top_traits', r.top_traits,
        'completed_at', r.completed_at
    ) AS data
    FROM public.personality_results AS r
    WHERE r.student_id = u.user_id AND r.test_type = 'BIGFIVE'
    ORDER BY r.completed_at DESC NULLS LAST, r.result_id DESC
    LIMIT 1
) AS bigfive ON TRUE
LEFT JOIN LATERAL (
    SELECT jsonb_build_object(
        'assessment_id', c.assessment_id,
        'test_type', c.test_type,
        'total_score', c.total_score,
        'max_scale', c.max_scale,
        'verbal_score', c.verbal_score,
        'quant_score', c.quant_score,
        'logic_score', c.logic_score,
        'data_analysis_score', c.data_analysis_score,
        'completed_at', c.completed_at
    ) AS data
    FROM public.competency_assessments AS c
    WHERE c.student_id = u.user_id AND c.test_type = 'INTERNAL'
    ORDER BY c.completed_at DESC NULLS LAST, c.assessment_id DESC
    LIMIT 1
) AS cognitive ON TRUE;

REVOKE ALL ON public."dữ liệu người dùng" FROM PUBLIC;

COMMENT ON VIEW public."dữ liệu người dùng" IS
'Tổng hợp chỉ đọc, một dòng/tài khoản; hồ sơ và kết quả mới nhất của từng bài test đã lưu trên máy chủ. Không chứa mật khẩu/mã băm mật khẩu, không ghi dữ liệu gốc, không tích hợp với AI. Không phải bản sao lưu lịch sử.';
