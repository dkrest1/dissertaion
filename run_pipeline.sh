#!/usr/bin/env bash
set -euo pipefail

# Simple helper to create venv, install deps, and run the pipeline steps.
# Usage: ./run_pipeline.sh [--no-venv]

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [ "${1-}" != "--no-venv" ]; then
  if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
  fi
  # shellcheck source=/dev/null
  source "$VENV_DIR/bin/activate"
  pip install --upgrade pip
  pip install -r "$ROOT_DIR/requirements.txt"
fi

echo "Fetching workflow runs..."
python3 "$ROOT_DIR/get_data.py"

echo "Downloading logs..."
python3 "$ROOT_DIR/download.py"

echo "Filtering memory-related logs..."
python3 "$ROOT_DIR/filter_momory_logs.py"

echo "Done. Check workflow_runs.csv, logs_failure/, and memory_logs.txt"