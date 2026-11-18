"""Compare or synchronize the original 2026 admissions catalog on Aiven."""

import argparse
import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, delete, insert, select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))

from app.core.admissions_catalog import catalog_rows, load_catalog
from app.core.config import settings
from app.core.models_db import AdmissionCriteria, Program, University


def plan_sync(db, catalog):
    snapshot = {}
    changes = {}
    for model, rows in catalog.items():
        table = model.__table__
        key = next(iter(table.primary_key.columns)).key
        existing = {
            row[key]: dict(row) for row in db.execute(select(table)).mappings()
        }
        snapshot[table.name] = list(existing.values())
        expected = {row[key]: row for row in rows}
        if len(expected) != len(rows):
            raise ValueError(f"Duplicate catalog key in {table.name}")

        additions = []
        updates = []
        for row_id, row in expected.items():
            current = existing.get(row_id)
            if current is None:
                additions.append(row)
            elif any(current[field] != value for field, value in row.items()):
                updates.append(row)
        changes[model] = (key, additions, updates, sorted(existing.keys() - expected.keys()))
    return snapshot, changes


def apply_sync(db, changes):
    for model, (key, _, _, removals) in reversed(changes.items()):
        if removals:
            db.execute(delete(model).where(getattr(model, key).in_(removals)))
    for model, (_, additions, updates, _) in changes.items():
        if additions:
            db.execute(insert(model).execution_options(render_nulls=True), additions)
        if updates:
            db.execute(update(model), updates)


def write_backup(path, snapshot):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(snapshot, output, ensure_ascii=False, default=str)
        output.flush()
        os.fsync(output.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path, help="New file for the pre-update catalog backup")
    args = parser.parse_args()
    if args.apply != (args.backup is not None):
        parser.error("--apply and --backup must be used together")

    url = make_url(settings.DATABASE_URL)
    if (
        url.get_backend_name() != "postgresql"
        or not url.password
        or url.password == "your_aiven_password_here"
        or url.query.get("sslmode") not in {"require", "verify-ca", "verify-full"}
    ):
        parser.error("Provide the existing Aiven DATABASE_URL with credentials and SSL enabled.")

    engine = create_engine(url, connect_args={"connect_timeout": 10})
    try:
        schools, logos = load_catalog()
        catalog = catalog_rows(schools, logos)
        report = json.loads((ROOT / "data/staging/workbook_import_report.json").read_bytes())
        if (
            len(catalog[University]) != 126
            or len(catalog[Program]) != report["programs"]
            or len(catalog[AdmissionCriteria]) != report["admission_cells"]
            or any(school["revision"] != report["revision"] for school in schools)
        ):
            raise ValueError("Catalog does not match the workbook import report.")

        with Session(engine) as db, db.begin():
            if args.apply:
                db.execute(text("SET LOCAL lock_timeout = '10s'"))
                db.execute(text("LOCK TABLE universities, programs, admission_criteria IN SHARE ROW EXCLUSIVE MODE"))
            else:
                db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))

            snapshot, changes = plan_sync(db, catalog)
            for model, (_, additions, updates, removals) in changes.items():
                print(
                    f"{model.__tablename__}: target={len(catalog[model])}, "
                    f"insert={len(additions)}, update={len(updates)}, remove={len(removals)}"
                )
            if args.apply and any(additions or updates or removals for _, additions, updates, removals in changes.values()):
                write_backup(args.backup, snapshot)
                apply_sync(db, changes)
                _, remaining = plan_sync(db, catalog)
                if any(additions or updates or removals for _, additions, updates, removals in remaining.values()):
                    raise ValueError("Catalog verification failed. Changes rolled back.")
        print("Catalog synchronized." if args.apply else "Comparison complete.")
    except (SQLAlchemyError, OSError, ValueError) as error:
        print(f"Catalog synchronization failed ({type(error).__name__}).", file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
