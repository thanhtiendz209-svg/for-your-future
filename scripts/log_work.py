#!/usr/bin/env python3
"""
log_work.py — Script tự động thêm entry vào docs/WORK_HISTORY.md

Dùng bởi AI agents sau khi hoàn thành task:
  python3 scripts/log_work.py --agent "Antigravity" --task "Mô tả task" \
    --files "app.js:Thay đổi X" "index.html:Bump version" \
    --results "✅ Điều 1" "✅ Điều 2" \
    --notes "Lưu ý cho AI tiếp theo"
"""

import argparse
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
WORK_HISTORY = PROJECT_ROOT / "docs" / "WORK_HISTORY.md"
LOCK_DIR = PROJECT_ROOT / ".agent-lock"
LOCK_FILE = LOCK_DIR / "work-history.lock"


def acquire_lock(agent: str, task: str) -> bool:
    """Try to acquire lock on WORK_HISTORY."""
    LOCK_DIR.mkdir(exist_ok=True)
    if LOCK_FILE.exists():
        content = LOCK_FILE.read_text()
        print(f"⚠️  LOCK EXISTS: {content.strip()}")
        print("   Waiting for lock to be released...")
        return False
    LOCK_FILE.write_text(f"AGENT={agent} | TASK={task} | TIME={datetime.now().isoformat()}")
    return True


def release_lock():
    """Release lock."""
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()


def prepend_entry(agent: str, task: str, files: list, results: list, notes: str):
    """Prepend new entry to WORK_HISTORY.md."""
    tz_vn = timezone(timedelta(hours=7))
    now = datetime.now(tz_vn)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%Y-%m-%d %H:%M (GMT+7)")

    # Build entry
    files_md = "\n".join(f"- `{f.split(':')[0]}` — {':'.join(f.split(':')[1:]).strip()}" for f in files) if files else "- (không có thay đổi)"
    results_md = "\n".join(f"- {r}" for r in results) if results else "- (không có kết quả)"

    entry = f"""## [{date_str}] {agent} — {task}

**Agent**: {agent}  
**Thời gian**: {time_str}  
**Files đã thay đổi**:
{files_md}

**Kết quả**:
{results_md}
"""
    if notes:
        entry += f"\n**Lưu ý cho AI tiếp theo**:\n- {notes}\n"

    entry += "\n---\n\n"

    # Read existing content
    existing = WORK_HISTORY.read_text(encoding="utf-8") if WORK_HISTORY.exists() else ""

    # Find insertion point (after the header section, before first "## [")
    header_end = existing.find("\n## [")
    if header_end == -1:
        # No existing entries
        new_content = existing.rstrip() + "\n\n" + entry
    else:
        new_content = existing[:header_end + 1] + "\n" + entry + existing[header_end + 1:]

    WORK_HISTORY.write_text(new_content, encoding="utf-8")
    print(f"✅ Added entry to {WORK_HISTORY}")


def main():
    parser = argparse.ArgumentParser(description="Log work to WORK_HISTORY.md")
    parser.add_argument("--agent", required=True, help="Agent name (Antigravity / Codex)")
    parser.add_argument("--task", required=True, help="Short task description")
    parser.add_argument("--files", nargs="*", default=[], help="Files changed: 'path:description'")
    parser.add_argument("--results", nargs="*", default=[], help="Results achieved")
    parser.add_argument("--notes", default="", help="Notes for next AI")
    args = parser.parse_args()

    # Acquire lock (retry 3 times)
    for attempt in range(3):
        if acquire_lock(args.agent, args.task):
            break
        import time
        time.sleep(2)
    else:
        print("❌ Could not acquire lock after 3 attempts. Write entry manually.")
        sys.exit(1)

    try:
        prepend_entry(args.agent, args.task, args.files, args.results, args.notes)
    finally:
        release_lock()


if __name__ == "__main__":
    main()

