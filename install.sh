#!/usr/bin/env bash
# this_file: install.sh
# Install unito as an editable package in the current environment.
#
# unito is a Unicode font merger — it combines multiple font sources
# into a unified font family with broad Unicode coverage.
#
# Usage: ./install.sh
#
# made by FontLab https://www.fontlab.com/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[install] unito — installing editable Python package"
uv pip install -e .

echo "[install] done."
