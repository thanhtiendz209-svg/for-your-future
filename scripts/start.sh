#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$DIR")"

echo "=================================================="
echo " Starting 'For Your Future' Platform"
echo " (PostgreSQL Aiven Cloud + Neo4j Graph + Ollama)"
echo "=================================================="

cd "$ROOT_DIR/apps/api"
export PYTHONPATH="$ROOT_DIR/apps/api:$PYTHONPATH"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

