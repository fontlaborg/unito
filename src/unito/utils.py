"""Utility helpers for the Unito package."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def project_root() -> Path:
    """Return repository root when running from source checkout."""
    return Path(__file__).resolve().parents[2]


def ensure_vendor_fonttools() -> None:
    """Prepend vendored fonttools path to ``sys.path`` when present."""
    root = project_root()
    candidates = [
        root / "src" / "unito" / "vendor" / "fonttools" / "Lib",
        root / "external" / "unito" / "vendor" / "fonttools" / "Lib",
    ]
    for candidate in candidates:
        if candidate.exists():
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)
            return


def env_truthy(name: str, default: bool = False) -> bool:
    """Read a boolean environment flag."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_semver_from_dirname(value: str) -> tuple[int, int, int] | None:
    """Extract semantic version tuple from a ``unifont-X.Y.Z`` string."""
    match = re.search(r"unifont-(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def derive_google_fonts_family(filename: str) -> str:
    """Derive a Google Fonts OFL family slug from a font filename."""
    stem = Path(filename).stem
    stem = re.sub(r"\[[^\]]+\]", "", stem)
    stem = re.sub(
        r"-(Regular|Italic|Bold|Medium|Light|Thin|Black|ExtraBold)$", "", stem
    )
    stem = stem.replace("_", "")
    return stem.lower()
