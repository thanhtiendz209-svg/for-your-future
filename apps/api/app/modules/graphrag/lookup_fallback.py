"""Format a lookup answer using the records already returned by Neo4j."""

import math
import re


FILTER_LINK = "[Bộ lọc tuyển sinh](https://foryourfuture.vercel.app/#huong-nghiep)"


def _text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"([\\`*_\[\]<>])", r"\\\1", " ".join(value.split()))


def _records(value: object) -> list[dict]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _job_titles(value: object) -> str:
    titles = (_text(job.get("title")) for job in _records(value))
    return ", ".join(list(dict.fromkeys(title for title in titles if title))[:4])


def _cutoffs(value: object) -> list[str]:
    cutoffs = []
    for row in _records(value):
        year = row.get("year")
        score = row.get("score")
        method = _text(row.get("method"))
        if type(year) is not int or not 2000 <= year <= 2100 or not method:
            continue
        if type(score) not in (int, float) or not 0 < score or not math.isfinite(score):
            continue
        formatted_score = str(score).removesuffix(".0").replace(".", ",")
        cutoffs.append(f"- Năm {year} · {method} · {formatted_score} điểm")
    return list(dict.fromkeys(cutoffs))


def build_lookup_fallback(
    lookup_data: dict, *, university_requested: bool, major_requested: bool
) -> str:
    school = lookup_data.get("target_university")
    school_name = _text(school.get("name")) if isinstance(school, dict) else ""
    sections = ["Trợ lý AI đang gián đoạn."]

    programs = []
    for row in _records(lookup_data.get("specific_program_analysis")):
        program_name = _text(row.get("program_name"))
        university_name = _text(row.get("university_name"))
        if not program_name or not university_name:
            continue
        if school_name and university_name.casefold() != school_name.casefold():
            continue

        details = [f"**{program_name}** tại **{university_name}**"]
        cutoffs = _cutoffs(row.get("admission_criteria"))
        if cutoffs:
            details.append("Mốc điểm đã lưu theo năm và phương thức\n\n" + "\n".join(cutoffs))
        else:
            details.append("Dữ liệu tra cứu chưa có mốc điểm kèm năm và phương thức cho chương trình này.")
        jobs = _job_titles(row.get("sample_jobs"))
        if jobs:
            details.append(f"Vị trí việc làm tham khảo liên quan đến chương trình gồm {jobs}.")
        programs.append("\n\n".join(details))

    if programs:
        sections.extend(["**Chương trình tra được**", *dict.fromkeys(programs)])
    elif university_requested and major_requested:
        target = f"**{school_name}**" if school_name else "trường bạn hỏi"
        sections.append(f"Dữ liệu tra cứu chưa xác nhận được ngành bạn hỏi tại {target}.")
    elif university_requested and school_name:
        sections.append(f"Trường tra được là **{school_name}**.")
    else:
        sections.append("Dữ liệu tra cứu hiện chưa đủ để xác nhận thông tin bạn hỏi.")

    career = lookup_data.get("career_insight")
    if isinstance(career, dict):
        career_name = _text(career.get("title"))
        jobs = _job_titles(career.get("positions"))
        if career_name and jobs and not programs:
            sections.append(f"Tham khảo việc làm chung trong lĩnh vực **{career_name}**, gồm {jobs}.")

    sections.append(f"Bạn có thể xem thêm trường, ngành và phương thức xét tuyển tại {FILTER_LINK}.")
    return "\n\n".join(sections)
