#!/usr/bin/env python3
"""
lock.py — Tạo / xóa file lock để tránh edit đồng thời giữa 2 AI agents.

Usage:
  python3 scripts/lock.py acquire app.js --agent Antigravity --task "Fix renderHome"
  python3 scripts/lock.py release app.js
  python3 scripts/lock.py status
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
LOCK_DIR = PROJECT_ROOT / ".agent-lock"
LOCK_DIR.mkdir(exist_ok=True)

LOCKABLE_FILES = {
    "app.js": "app.js.lock",
    "index.html": "index.html.lock",
    "styles.css": "styles.css.lock",
    "api-service": "api-service.lock",
    "work-history": "work-history.lock",
    "todo": "todo.lock",
}


def status():
    locks = list(LOCK_DIR.glob("*.lock"))
    if not locks:
        print("✅ No active locks — workspace is free.")
        return
    print(f"🔒 Active locks ({len(locks)}):")
    for lock in locks:
        print(f"  {lock.name}: {lock.read_text().strip()}")


def acquire(file_key: str, agent: str, task: str):
    lock_name = LOCKABLE_FILES.get(file_key, f"{file_key}.lock")
    lock_path = LOCK_DIR / lock_name
    if lock_path.exists():
        print(f"❌ LOCKED: {lock_name}")
        print(f"   Current holder: {lock_path.read_text().strip()}")
        sys.exit(1)
    lock_path.write_text(f"AGENT={agent} | TASK={task} | TIME={datetime.now().isoformat()}")
    print(f"✅ Lock acquired: {lock_name}")


def release(file_key: str):
    lock_name = LOCKABLE_FILES.get(file_key, f"{file_key}.lock")
    lock_path = LOCK_DIR / lock_name
    if lock_path.exists():
        lock_path.unlink()
        print(f"🔓 Lock released: {lock_name}")
    else:
        print(f"ℹ️  No lock found for: {lock_name}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    acq = sub.add_parser("acquire")
    acq.add_argument("file", help="File key (app.js, index.html, api-service, work-history, todo)")
    acq.add_argument("--agent", required=True)
    acq.add_argument("--task", required=True)

    rel = sub.add_parser("release")
    rel.add_argument("file")

    sub.add_parser("status")

    args = parser.parse_args()
    if args.cmd == "status" or args.cmd is None:
        status()
    elif args.cmd == "acquire":
        acquire(args.file, args.agent, args.task)
    elif args.cmd == "release":
        release(args.file)


if __name__ == "__main__":
    main()

