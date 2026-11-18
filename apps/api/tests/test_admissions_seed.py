import json
from pathlib import Path

from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from app.core.admissions_catalog import catalog_rows, insert_catalog, load_catalog
from app.core.models_db import (
    AdmissionCriteria,
    Base,
    ChatMessage,
    ChatSession,
    PersonalityResult,
    Program,
    StudentProfile,
    University,
    User,
)
from app.core.seed import seed_initial_data
from scripts.sync_workbook_database import apply_sync, plan_sync, write_backup


def make_engine():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(engine)
    return engine


def counts(db):
    return tuple(db.scalar(select(func.count()).select_from(model)) for model in (
        University, Program, AdmissionCriteria,
    ))


def assert_workbook_catalog(db):
    assert counts(db) == (126, 3478, 11428)
    assert db.get(University, "uni-002").short_name == "NEU"
    assert db.get(University, "uni-068").short_name == "HCMUT"
    assert db.get(Program, "QSK-CS") is None
    assert db.get(University, "uni-hnue") is None
    assert db.get(Program, "SPH-TOAN") is None


def test_api_catalog_matches_workbook_exports():
    public_data = Path(__file__).resolve().parents[2] / "web/public/data"
    schools, logos = load_catalog()
    assert schools == json.loads((public_data / "school_details.json").read_bytes())
    assert logos == {
        school["id"]: school.get("logo")
        for school in json.loads((public_data / "universities.json").read_bytes())
    }


def test_seed_from_empty_database_is_idempotent():
    with Session(make_engine()) as db:
        seed_initial_data(db)
        assert_workbook_catalog(db)
        assert db.scalar(select(func.count()).select_from(User)) == 0
        seed_initial_data(db)
        assert_workbook_catalog(db)


def test_seed_preserves_existing_workbook_catalog():
    with Session(make_engine()) as db:
        schools, logos = load_catalog()
        insert_catalog(db, schools, logos)
        db.get(University, "uni-001").has_dormitory = True
        db.add(User(user_id="existing", email="existing@example.test", password_hash="test", role="student"))
        db.commit()
        seed_initial_data(db)
        assert_workbook_catalog(db)
        assert db.get(University, "uni-001").has_dormitory is True
        assert db.scalar(select(func.count()).select_from(User)) == 1


def test_catalog_sync_removes_extra_admissions_and_preserves_user_data(tmp_path):
    with Session(make_engine()) as db:
        schools, logos = load_catalog()
        insert_catalog(db, schools, logos)
        db.get(University, "uni-002").short_name = "Old label"
        old_school = University(
            uni_id="uni-hnue", name="Đại học Sư phạm Hà Nội", location="Hà Nội", region="Miền Bắc",
        )
        old_program = Program(program_id="SPH-TOAN", major_code="7140209", name="Sư phạm Toán học")
        old_program.criteria.append(AdmissionCriteria(criteria_id="legacy-criteria", method="THPT"))
        old_school.programs.append(old_program)
        db.add(old_school)

        user = User(user_id="existing", email="existing@example.test", password_hash="test", role="student")
        profile = StudentProfile(first_name="An", last_name="Nguyễn")
        profile.personality_results.append(
            PersonalityResult(result_id="riasec", test_type="RIASEC", result_code="RIA")
        )
        chat = ChatSession(session_id="conversation", title="Tư vấn")
        chat.messages.append(ChatMessage(message_id="message", role="user", content="Hỏi về tuyển sinh"))
        profile.chat_sessions.append(chat)
        user.student_profile = profile
        db.add(user)
        db.commit()

        catalog = catalog_rows(schools, logos)
        snapshot, changes = plan_sync(db, catalog)
        _, added, changed, removed = changes[University]
        assert added == []
        assert [row["uni_id"] for row in changed] == ["uni-002"]
        assert removed == ["uni-hnue"]
        backup = tmp_path / "admissions-backup.json"
        write_backup(backup, snapshot)
        assert any(row["uni_id"] == "uni-hnue" for row in json.loads(backup.read_bytes())["universities"])
        assert set(snapshot) == {"universities", "programs", "admission_criteria"}
        apply_sync(db, changes)
        db.commit()

        assert_workbook_catalog(db)
        assert db.get(User, "existing").email == "existing@example.test"
        assert db.get(StudentProfile, "existing").first_name == "An"
        assert db.get(PersonalityResult, "riasec").result_code == "RIA"
        assert db.get(ChatMessage, "message").content == "Hỏi về tuyển sinh"
        _, remaining = plan_sync(db, catalog)
        assert not any(add or change or remove for _, add, change, remove in remaining.values())
