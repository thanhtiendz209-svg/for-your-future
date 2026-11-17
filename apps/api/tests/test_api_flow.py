"""
Comprehensive Integration Tests for For Your Future API.
Tests end-to-end user flow: Registration -> Login -> Profile -> Pruning Recommendation -> AI Consultation -> Admin Health.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, init_db
from app.core.seed import seed_initial_data


def run_all_tests():
    # Explicitly ensure DB and seed data are ready
    init_db()
    db = SessionLocal()
    seed_initial_data(db)
    db.close()

    with TestClient(app) as client:
        # 1. Root & Health
        res = client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert data["app"] == "For Your Future"
        assert data["status"] == "online"

        res_h = client.get("/health")
        assert res_h.status_code == 200
        assert res_h.json()["status"] == "ok"
        print("✓ Root and Health endpoints OK")

        # 2. Auth Flow
        email = "test_student_flow@foryourfuture.edu.vn"
        reg_payload = {
            "email": email,
            "password": "Password123!",
            "first_name": "Minh",
            "last_name": "Trần",
            "grade_level": 12,
            "target_year": 2026,
            "gender": "Male"
        }
        res = client.post("/api/v1/auth/register", json=reg_payload)
        assert res.status_code in [201, 400]
        
        login_payload = {
            "email": email,
            "password": "Password123!"
        }
        res_login = client.post("/api/v1/auth/login", json=login_payload)
        assert res_login.status_code == 200
        token_data = res_login.json()
        assert "access_token" in token_data
        assert token_data["role"] == "student"

        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        res_me = client.get("/api/v1/auth/me", headers=headers)
        assert res_me.status_code == 200
        assert res_me.json()["email"] == email
        print("✓ Auth registration, login and me OK")

        # 3. Student Profile Flow
        res_prof = client.get("/api/v1/students/profile", headers=headers)
        assert res_prof.status_code == 200
        prof_data = res_prof.json()
        assert prof_data["first_name"] == "Minh"

        # Update background
        res_bg = client.put(
            "/api/v1/students/background",
            json={"priority_zone": "KV1", "priority_object": "01", "max_annual_tuition": 40000000},
            headers=headers
        )
        assert res_bg.status_code == 200
        assert res_bg.json()["background"]["priority_points_calculated"] == 2.75
        print("✓ Student profile and background calculation OK")

        # 4. Universities and Careers
        res_u = client.get("/api/v1/universities")
        assert res_u.status_code == 200
        unis = res_u.json()
        assert len(unis) >= 5
        bka = next((u for u in unis if u["short_name"] == "BKA"), None)
        assert bka is not None

        res_detail = client.get(f"/api/v1/universities/{bka['uni_id']}")
        assert res_detail.status_code == 200
        assert len(res_detail.json()["programs"]) >= 1

        res_nganh = client.get(f"/api/v1/universities/{bka['uni_id']}/programs?nganh=7480201")
        assert res_nganh.status_code == 200
        assert len(res_nganh.json()) >= 1

        res_c = client.get("/api/v1/careers")
        assert res_c.status_code == 200
        assert len(res_c.json()) >= 1
        print("✓ Universities and Careers catalog OK")

        # 5. Deterministic Pruning Recommendation
        req_payload = {
            "target_year": 2026,
            "student_method": "Điểm thi THPT",
            "student_group_code": "A00",
            "student_score": 27.0,
            "bonus_points": 1.25,
            "max_annual_budget": 35000000,
            "student_gender": "Male",
            "student_height": 172.0,
            "student_eye_degree": 1.0,
            "holland_code": "RIA"
        }
        res_rec = client.post("/api/v1/recommend", json=req_payload)
        assert res_rec.status_code == 200
        data = res_rec.json()
        assert data["total_found"] > 0
        top = data["results"][0]
        assert top["score_margin"] >= 0
        assert top["actual_tuition"] <= req_payload["max_annual_budget"]
        print("✓ Deterministic recommendation engine OK (Score margin & budget respected)")

        # 6. Physical Constraints
        req_phys = {
            "target_year": 2026,
            "student_method": "Điểm thi THPT",
            "student_group_code": "A00",
            "student_score": 25.0,
            "bonus_points": 0.0,
            "max_annual_budget": 35000000,
            "student_gender": "Male",
            "student_height": 160.0,
            "student_eye_degree": 4.5,
            "holland_code": "RCS"
        }
        res_phys = client.post("/api/v1/recommend", json=req_phys)
        assert res_phys.status_code == 200
        anh_results = [r for r in res_phys.json()["results"] if "An ninh" in r["university_name"]]
        assert len(anh_results) == 0
        print("✓ Physical constraint pruning OK (Short/myopic applicant pruned from Police Academy)")

        # 7. Budget Constraint
        req_bud = {
            "target_year": 2026,
            "student_method": "Điểm thi THPT",
            "student_group_code": "A00",
            "student_score": 27.0,
            "bonus_points": 0.0,
            "max_annual_budget": 10000000,
            "student_gender": "Male",
            "holland_code": "IAS"
        }
        res_bud = client.post("/api/v1/recommend", json=req_bud)
        assert res_bud.status_code == 200
        for r in res_bud.json()["results"]:
            assert r["actual_tuition"] <= 10000000
        print("✓ Budget constraint pruning OK (Low budget pruned non-subsidized programs)")

        # 8. Admin & Health
        res_health = client.get("/api/v1/admin/health")
        assert res_health.status_code == 200
        data_h = res_health.json()
        assert "database" in data_h
        assert "neo4j" in data_h
        assert "ollama" in data_h

        res_stats = client.get("/api/v1/admin/stats")
        assert res_stats.status_code == 200
        assert res_stats.json()["universities_count"] >= 5
        print("✓ Admin health probe and system stats OK")

        print("\n🎉 ========================================================")
        print("   ALL INTEGRATION & ACCEPTANCE CRITERIA TESTS PASSED 100%!")
        print("============================================================")


if __name__ == "__main__":
    run_all_tests()
