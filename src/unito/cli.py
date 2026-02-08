"""CLI entrypoints for the Unito package."""

from __future__ import annotations

import sys

from .merger import main as merge_main

try:
    import fire
except ImportError:
    fire = None


def _normalize_argv(argv: list[str]) -> list[str]:
    """Normalize short legacy flags to Fire-compatible options."""
    normalized: list[str] = []
    for arg in argv:
        if arg == "-o":
            normalized.append("--output")
        else:
            normalized.append(arg)
    return normalized


def main() -> None:
    """Run Unito command line interface."""
    if fire is None:
        raise RuntimeError("fire is required for CLI execution. Install with: pip install fire")
    # Use Fire to wrap the merger main function directly.
    # Note: merge_main is the core function exported from merger.py.
    fire.Fire(merge_main)


if __name__ == "__main__":
    main()
