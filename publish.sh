#!/usr/bin/env bash
# this_file: publish.sh
# Publish unito to PyPI.
#
# unito is a Unicode font merger — it combines multiple font sources
# into a unified font family with broad Unicode coverage.
#
# Workflow:
#   ./publish.sh        # build, bump tag, publish to PyPI
#
# Prerequisites:
#   - uv          (astral.sh/uv)
#   - gitnextver  (uvx gitnextver@latest)
#   - UV_PUBLISH_TOKEN or PYPI credentials configured
#
# made by FontLab https://www.fontlab.com/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[publish] unito — running build"
bash "$SCRIPT_DIR/build.sh"

echo "[publish] unito — installing editable"
bash "$SCRIPT_DIR/install.sh"

echo "[publish] bumping version tag via gitnextver"
uvx gitnextver@latest

echo "[publish] building distribution"
uvx hatch build

echo "[publish] uploading to PyPI"
uv publish

echo "[publish] done."
