from app.modules.graphrag.lookup_fallback import build_lookup_fallback


def test_lookup_fallback_reports_only_valid_points_for_a_program():
    data = {
        "specific_program_analysis": [
            {
                "program_name": "Tài chính – Ngân hàng",
                "university_name": "Trường Đại học Mẫu",
                "admission_criteria": [
                    {"year": 2026, "method": "Thi THPT", "score": 25.75},
                    {"year": 2025, "method": "V-SAT", "score": 300.0},
                    {"year": 2026, "method": "Thi THPT", "score": 25.75},
                    {"year": None, "method": "Thi THPT", "score": 29},
                    {"year": 5, "method": "Thi THPT", "score": 28},
                    {"year": 2026, "method": "  ", "score": 27},
                    {"year": 2026, "method": "Học bạ", "score": float("nan")},
                    {"year": 2026, "method": "Học bạ", "score": True},
                    {"year": None, "method": None, "score": None},
                ],
                "sample_jobs": [{"title": "Chuyên viên tín dụng"}, {"title": None}],
            },
            {"program_name": "Tên thiếu trường", "university_name": None},
        ],
    }

    result = build_lookup_fallback(data, university_requested=True, major_requested=True)

    assert "**Tài chính – Ngân hàng** tại **Trường Đại học Mẫu**" in result
    assert result.count("Năm 2026 · Thi THPT · 25,75 điểm") == 1
    assert "Năm 2025 · V-SAT · 300 điểm" in result
    assert "liên quan đến chương trình gồm Chuyên viên tín dụng" in result
    for missing in ("29 điểm", "28 điểm", "27 điểm", "Học bạ", "Tên thiếu trường"):
        assert missing not in result


def test_lookup_fallback_does_not_confuse_generic_career_data_with_verified_programs():
    data = {
        "target_university": {"name": "Trường Đại học Mẫu", "has_dormitory": True},
        "specific_program_analysis": [
            {"program_name": "Tài chính – Ngân hàng", "university_name": "Một trường khác"},
        ],
        "career_insight": {
            "title": "Tài chính",
            "training_universities": [{"program": "Kinh tế", "university": "Một trường khác"}],
            "positions": [{"title": "Chuyên viên tài chính", "salary_min": 20_000_000}],
        },
    }

    result = build_lookup_fallback(data, university_requested=True, major_requested=True)

    assert "chưa xác nhận được ngành bạn hỏi tại **Trường Đại học Mẫu**" in result
    assert "Tham khảo việc làm chung trong lĩnh vực **Tài chính**, gồm Chuyên viên tài chính." in result
    for missing in ("Một trường khác", "Kinh tế", "ký túc xá", "20.000.000", "Chương trình tra được"):
        assert missing not in result


def test_lookup_fallback_links_to_existing_filter_when_no_records_are_available():
    result = build_lookup_fallback({}, university_requested=False, major_requested=False)

    assert "chưa đủ để xác nhận thông tin bạn hỏi" in result
    assert "[Bộ lọc tuyển sinh](https://foryourfuture.vercel.app/#huong-nghiep)" in result
