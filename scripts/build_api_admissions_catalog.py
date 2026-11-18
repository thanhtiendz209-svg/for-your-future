"""Package the published admissions JSON for the FastAPI catalog seed."""

import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATA = ROOT / "apps/web/public/data"
API_CATALOG = ROOT / "apps/api/app/core/admissions_catalog.json.gz"


def main():
    schools = json.loads((PUBLIC_DATA / "school_details.json").read_bytes())
    universities = json.loads((PUBLIC_DATA / "universities.json").read_bytes())
    logos = {school["id"]: school.get("logo") for school in universities}
    payload = json.dumps(
        {"schools": schools, "logos": logos},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    API_CATALOG.write_bytes(gzip.compress(payload, mtime=0))


if __name__ == "__main__":
    main()
