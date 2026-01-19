#!/usr/bin/env bash
set -euo pipefail

# Resolve project root (location of this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer the project venv Python if available, else fall back to system python3/python
PY="${ROOT_DIR}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PY=python3
  else
    PY=python
  fi
fi

INPUT_FILE="${ROOT_DIR}/inputTexts.md"
if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Error: $INPUT_FILE not found. Please create it or adjust the script." >&2
  exit 1
fi

PY_SCRIPT="${ROOT_DIR}/md_2_images.py"

# Execute. The Python script supports positional input; outdir will default to input filename stem
exec "$PY" "$PY_SCRIPT" "$INPUT_FILE"
