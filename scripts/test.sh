#!/usr/bin/env bash
# One command to run every test. No AI model needed.
# Usage:  bash scripts/test.sh
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pytest -q "$@"
