"""Attach the verified 2026 V-SAT cutoffs to the workbook programs."""

import json
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data/raw/vsat_2026_cutoffs.json"
CATALOGS = (
    ROOT / "apps/web/public/data/school_details.json",
    ROOT / "apps/web/dist/data/school_details.json",
    ROOT / "data/staging/school_details.json",
)


def update_vsat_cutoffs(schools, sources):
    by_id = {school["id"]: school for school in schools}
    for school_id, source in sources.items():
        programs = {program["programId"]: program for program in by_id[school_id]["programs"]}
        scale = source["scale"]
        source_url = urlsplit(source["sourceUrl"])
        if scale not in (30, 450) or source_url.scheme != "https" or not source_url.hostname:
            raise ValueError(f"Invalid V-SAT source for {school_id}")

        for program_id, score in source["scores"].items():
            if not isinstance(score, (int, float)) or not 0 < score <= scale:
                raise ValueError(f"Invalid V-SAT cutoff for {program_id}")
            admissions = programs[program_id]["admissions"]
            vsat = [admission for admission in admissions if admission["method"] == "V-SAT 2026"]
            if len(vsat) != 1:
                raise ValueError(f"Expected one workbook V-SAT admission for {program_id}")
            vsat[0]["published"] = {"score": score, "scale": scale, "sourceUrl": source["sourceUrl"]}
            if scale == 450 and (vsat[0]["value"], vsat[0]["scale"]) != (score, scale):
                vsat[0].update(value=score, scale=scale)


def main():
    schools = json.loads(CATALOGS[0].read_bytes())
    update_vsat_cutoffs(schools, json.loads(SOURCES.read_bytes()))
    content = json.dumps(schools, ensure_ascii=False, indent=2) + "\n"
    for catalog in CATALOGS:
        catalog.write_text(content)


if __name__ == "__main__":
    main()
