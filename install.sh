#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3.10 through 3.13 is required." >&2
    exit 1
fi

python3 - <<'PY'
import sys

if not ((3, 10) <= sys.version_info[:2] <= (3, 13)):
    raise SystemExit(
        f"Error: Python 3.10 through 3.13 is required; found {sys.version_info.major}.{sys.version_info.minor}."
    )
PY

python3 -m pip install --upgrade uv ninja
python3 -m uv venv "${HOME}/.venvs/local-pdf2md" --python python3
python3 -m uv pip install \
    --python "${HOME}/.venvs/local-pdf2md/bin/python" \
    --upgrade \
    --requirement requirements.txt

python3 verify_install.py
