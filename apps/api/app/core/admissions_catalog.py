"""Admission catalog shipped with the API for databases without seed data."""

import gzip
import json
from pathlib import Path

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.core.models_db import AdmissionCriteria, Program, University

CATALOG_PATH = Path(__file__).with_name("admissions_catalog.json.gz")


def load_catalog():
    with gzip.open(CATALOG_PATH, "rt", encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)
    return catalog["schools"], catalog["logos"]


def catalog_rows(schools, logos):
    """Map the workbook's 2026 catalog and retain original score text and scale."""
    universities = []
    programs = []
    criteria = []
    for school in schools:
        universities.append({
            "uni_id": school["id"],
            "name": school["name"],
            "short_name": school["shortName"],
            "type": school["category"] or "Đa ngành",
            "location": school["provinceNew"] or "Chưa xác định",
            "region": school["region"] or "Chưa xác định",
            "website": school["website"],
            "admissions_url": school["admissionsUrl"],
            "focus_riasec": school["focusRiasec"] or [],
            "logo": logos[school["id"]],
        })
        for program in school["programs"]:
            programs.append({
                "program_id": program["programId"],
                "uni_id": school["id"],
                "major_code": program["code"],
                "name": program["name"],
                "tuition_annual": program["tuition_annual"],
                "effective_cost": program["tuition_annual"],
                "degree_level": None,
                "duration_years": None,
            })
            for index, admission in enumerate(program["admissions"]):
                criteria.append({
                    "criteria_id": f"{program['programId']}-{index}",
                    "program_id": program["programId"],
                    "year": 2026,
                    "method": admission["method"],
                    "benchmark_score": admission["value"],
                    "score_scale": admission["scale"] or 30,
                    "source_url": school["scoreSource"],
                    "special_conditions": json.dumps({
                        "raw": admission["raw"],
                        "scale_provided": admission["scale"],
                        "sheet": school["sheet"],
                        "row": program["row"],
                        "revision": school["revision"],
                    }, ensure_ascii=False),
                })
    return {University: universities, Program: programs, AdmissionCriteria: criteria}


def insert_catalog(db: Session, schools, logos):
    for model, rows in catalog_rows(schools, logos).items():
        db.execute(insert(model).execution_options(render_nulls=True), rows)
