#!/usr/bin/env python3
import sys
from pathlib import Path
from fontTools.ttLib import TTFont

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unito.exclude import is_in_han_range


def verify_font(font_path):
    print(f"Verifying {font_path}...")
    font = TTFont(font_path)
    cmap = font.getBestCmap()

    han_chars = []
    for codepoint in cmap:
        if is_in_han_range(codepoint):
            han_chars.append(codepoint)

    if han_chars:
        print(f"FAILED: Found {len(han_chars)} Han codepoints in {font_path.name}")
        for cp in han_chars[:10]:
            print(f"  U+{cp:04X}")
        if len(han_chars) > 10:
            print("  ...")
        return False
    else:
        print(f"PASSED: No Han codepoints found in {font_path.name}")
        return True


def main():
    fonts_dir = Path("fonts")
    if not fonts_dir.exists():
        print("fonts/ directory not found!")
        sys.exit(1)

    variants = [
        "Unito-Regular.ttf",
        "Unito-Bold.ttf",
        "Unito-Condensed.ttf",
        "Unito-BoldCondensed.ttf",
    ]
    failed = False

    for variant in variants:
        path = fonts_dir / variant
        if not path.exists():
            print(f"WARNING: {path} not found")
            continue

        if not verify_font(path):
            failed = True

    if failed:
        sys.exit(1)
    else:
        print("All verified fonts are clean.")
        sys.exit(0)


if __name__ == "__main__":
    main()
