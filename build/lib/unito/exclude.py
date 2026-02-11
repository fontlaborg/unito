"""Codepoint exclusion logic for Unito font building.

This module provides functions for determining which codepoints should be excluded
from font merging operations. Supports exclusion by:
- Unicode script (Han, Hangul, Tangut)
- Unicode ranges (CJK blocks, Tangut blocks)
- YAML control files specifying custom exclusion rules

The exclusion logic is used to selectively remove glyphs from base fonts before
merging with script-specific fonts (e.g., removing CJK from Noto Sans before
merging with Noto Sans CJK).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml

# Import script function with fallbacks (fontTools.unicodedata -> unicodedata2 -> stub)
try:
    from fontTools.unicodedata import script
except ImportError:
    try:
        from unicodedata2 import script  # type: ignore[import-not-found,no-redef]
    except ImportError:

        def script(char: str) -> str:  # type: ignore[misc]
            """Fallback script detection - returns 'Unknown' for all characters."""
            return "Unknown"


# Import unicodedata2 with fallback to standard unicodedata
try:
    import unicodedata2 as ucd  # type: ignore[import-not-found]
except ImportError:
    pass

if TYPE_CHECKING:
    from typing import Any

# =============================================================================
# Unicode Range Constants
# =============================================================================

# CJK Han ranges (Unified Ideographs and Extensions)
HAN_RANGES: list[tuple[int, int, str]] = [
    (0x4E00, 0x9FFF, "CJK Unified Ideographs"),
    (0x3400, 0x4DBF, "CJK Unified Ideographs Extension A"),
    (0x20000, 0x2A6DF, "CJK Unified Ideographs Extension B"),
    (0x2A700, 0x2B73F, "CJK Unified Ideographs Extension C"),
    (0x2B740, 0x2B81F, "CJK Unified Ideographs Extension D"),
    (0x2B820, 0x2CEAF, "CJK Unified Ideographs Extension E"),
    (0x2CEB0, 0x2EBEF, "CJK Unified Ideographs Extension F"),
    (0x30000, 0x3134F, "CJK Unified Ideographs Extension G"),
    (0x31350, 0x323AF, "CJK Unified Ideographs Extension H"),
    (0x2EBF0, 0x2EE5F, "CJK Unified Ideographs Extension I"),
    (0xF900, 0xFAFF, "CJK Compatibility Ideographs"),
    (0x2F800, 0x2FA1F, "CJK Compatibility Ideographs Supplement"),
]

# Tangut ranges
TANGUT_RANGES: list[tuple[int, int, str]] = [
    (0x17000, 0x187FF, "Tangut"),
    (0x18800, 0x18AFF, "Tangut Components"),
    (0x18D00, 0x18D7F, "Tangut Supplement"),
]

# Hangul ranges (for reference, primarily detected via script())
HANGUL_RANGES: list[tuple[int, int, str]] = [
    (0xAC00, 0xD7AF, "Hangul Syllables"),
    (0x1100, 0x11FF, "Hangul Jamo"),
    (0x3130, 0x318F, "Hangul Compatibility Jamo"),
    (0xA960, 0xA97F, "Hangul Jamo Extended-A"),
    (0xD7B0, 0xD7FF, "Hangul Jamo Extended-B"),
]


# =============================================================================
# Range Check Functions
# =============================================================================


def is_in_han_range(cp: int) -> bool:
    """Check if a codepoint is in any CJK Han Unicode range.

    Args:
        cp: Unicode codepoint to check.

    Returns:
        True if the codepoint is within a CJK Han range.
    """
    return any(start <= cp <= end for start, end, _ in HAN_RANGES)


def is_in_tangut_range(cp: int) -> bool:
    """Check if a codepoint is in any Tangut Unicode range.

    Args:
        cp: Unicode codepoint to check.

    Returns:
        True if the codepoint is within a Tangut range.
    """
    return any(start <= cp <= end for start, end, _ in TANGUT_RANGES)


def is_in_hangul_range(cp: int) -> bool:
    """Check if a codepoint is in any Hangul Unicode range.

    Args:
        cp: Unicode codepoint to check.

    Returns:
        True if the codepoint is within a Hangul range.
    """
    return any(start <= cp <= end for start, end, _ in HANGUL_RANGES)


# =============================================================================
# Script Detection Functions
# =============================================================================


def is_han_script(cp: int) -> bool:
    """Check if a codepoint belongs to the Han script.

    Uses Unicode script property detection with range fallback.

    Args:
        cp: Unicode codepoint to check.

    Returns:
        True if the codepoint is Han script.
    """
    try:
        char = chr(cp)
        script_name = script(char)
        if script_name in ("Han", "Hani"):
            return True
    except (ValueError, KeyError):
        pass
    # Fallback to range check
    return is_in_han_range(cp)


def is_hangul_script(cp: int) -> bool:
    """Check if a codepoint belongs to the Hangul script.

    Uses Unicode script property detection with range fallback.

    Args:
        cp: Unicode codepoint to check.

    Returns:
        True if the codepoint is Hangul script.
    """
    try:
        char = chr(cp)
        script_name = script(char)
        if script_name in ("Hangul", "Hang"):
            return True
    except (ValueError, KeyError):
        pass
    # Fallback to range check
    return is_in_hangul_range(cp)


def is_tangut_script(cp: int) -> bool:
    """Check if a codepoint belongs to the Tangut script.

    Uses Unicode script property detection with range fallback.

    Args:
        cp: Unicode codepoint to check.

    Returns:
        True if the codepoint is Tangut script.
    """
    try:
        char = chr(cp)
        script_name = script(char)
        if script_name in ("Tangut", "Tang"):
            return True
    except (ValueError, KeyError):
        pass
    # Fallback to range check
    return is_in_tangut_range(cp)


# =============================================================================
# YAML Control File Functions
# =============================================================================


def _parse_hex_value(value: int | str) -> int:
    """Parse a hex value that may be an int or string.

    Args:
        value: Either an integer or a hex string (e.g., "0x4E00").

    Returns:
        The integer value.
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 16) if value.startswith("0x") else int(value)
    raise ValueError(f"Invalid hex value: {value}")


def _get_codepoints_for_script(script_code: str) -> set[int]:
    """Get all codepoints for a given script code.

    Args:
        script_code: ISO 15924 script code (e.g., "Hang", "Tang", "Hani").

    Returns:
        Set of codepoints belonging to that script.
    """
    codepoints: set[int] = set()

    # Map script codes to their range lists
    script_ranges: dict[str, list[tuple[int, int, str]]] = {
        "Hani": HAN_RANGES,
        "Han": HAN_RANGES,
        "Hang": HANGUL_RANGES,
        "Hangul": HANGUL_RANGES,
        "Tang": TANGUT_RANGES,
        "Tangut": TANGUT_RANGES,
    }

    if script_code in script_ranges:
        for start, end, _ in script_ranges[script_code]:
            codepoints.update(range(start, end + 1))

    return codepoints


def load_control_file(path: Path) -> set[int]:
    """Load a YAML control file specifying codepoints to exclude.

    The YAML file format supports two exclusion methods:

    1. `exclude_ranges`: List of explicit Unicode ranges
       ```yaml
       exclude_ranges:
         - start: 0x4E00
           end: 0x9FFF
           description: "CJK Unified Ideographs"
       ```

    2. `exclude_scripts`: List of ISO 15924 script codes
       ```yaml
       exclude_scripts:
         - "Hang"
         - "Tang"
       ```

    Args:
        path: Path to the YAML control file.

    Returns:
        Set of codepoints to exclude.

    Raises:
        FileNotFoundError: If the control file doesn't exist.
        yaml.YAMLError: If the YAML is malformed.
        ValueError: If the file contains invalid range specifications.
    """
    if not path.exists():
        raise FileNotFoundError(f"Control file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    excludes: set[int] = set()

    # Process exclude_ranges
    for range_spec in data.get("exclude_ranges", []):
        if not isinstance(range_spec, dict):
            raise ValueError(f"Invalid range specification: {range_spec}")

        start = _parse_hex_value(range_spec.get("start", 0))
        end = _parse_hex_value(range_spec.get("end", start))

        if start > end:
            raise ValueError(f"Invalid range: start ({start:#x}) > end ({end:#x})")

        excludes.update(range(start, end + 1))

    # Process exclude_scripts
    for script_code in data.get("exclude_scripts", []):
        excludes.update(_get_codepoints_for_script(script_code))

    return excludes


# =============================================================================
# Main Exclusion Function
# =============================================================================


def should_exclude_codepoint(
    cp: int,
    exclude_hani: bool = False,
    exclude_hang: bool = False,
    exclude_tang: bool = False,
    extra_excludes: set[int] | None = None,
) -> bool:
    """Determine if a codepoint should be excluded from font merging.

    This is the unified exclusion check function that combines script-based
    exclusion with custom exclusion sets.

    Args:
        cp: Unicode codepoint to check.
        exclude_hani: If True, exclude CJK Han codepoints.
        exclude_hang: If True, exclude Hangul codepoints.
        exclude_tang: If True, exclude Tangut codepoints.
        extra_excludes: Optional set of additional codepoints to exclude.

    Returns:
        True if the codepoint should be excluded.

    Examples:
        >>> should_exclude_codepoint(0x4E00, exclude_hani=True)
        True
        >>> should_exclude_codepoint(0x0041, exclude_hani=True)  # Latin 'A'
        False
        >>> should_exclude_codepoint(0xAC00, exclude_hang=True)  # Hangul '가'
        True
    """
    # Check extra excludes first (fastest check)
    if extra_excludes and cp in extra_excludes:
        return True

    # Check Han exclusion
    if exclude_hani and is_han_script(cp):
        return True

    # Check Hangul exclusion
    if exclude_hang and is_hangul_script(cp):
        return True

    # Check Tangut exclusion
    if exclude_tang and is_tangut_script(cp):
        return True

    return False


def get_all_excluded_codepoints(
    exclude_hani: bool = False,
    exclude_hang: bool = False,
    exclude_tang: bool = False,
    extra_excludes: set[int] | None = None,
) -> set[int]:
    """Get the complete set of excluded codepoints based on configuration.

    This function builds a set of all codepoints that would be excluded,
    useful for pre-computing exclusions before font processing.

    Args:
        exclude_hani: If True, include CJK Han codepoints in exclusion set.
        exclude_hang: If True, include Hangul codepoints in exclusion set.
        exclude_tang: If True, include Tangut codepoints in exclusion set.
        extra_excludes: Optional set of additional codepoints to exclude.

    Returns:
        Set of all codepoints to exclude.
    """
    excludes: set[int] = set()

    if extra_excludes:
        excludes.update(extra_excludes)

    if exclude_hani:
        excludes.update(_get_codepoints_for_script("Hani"))

    if exclude_hang:
        excludes.update(_get_codepoints_for_script("Hang"))

    if exclude_tang:
        excludes.update(_get_codepoints_for_script("Tang"))

    return excludes
