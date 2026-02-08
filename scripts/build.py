#!/usr/bin/env python3
"""Build helper script for Unito font generation.

This script builds the 4 standard Unito font variants:
- Regular (wght=400, wdth=100)
- Bold (wght=700, wdth=100)
- Condensed (wght=400, wdth=75)
- BoldCondensed (wght=700, wdth=75)

Usage:
    python scripts/build.py [options]

Options:
    --download, --no-download    Enable/disable font download (default: enabled)
    --force                      Force re-download of all fonts
    --variants VARIANTS          Comma-separated list of variants to build
                                (all|regular,bold,condensed,boldcondensed)
    --output-dir DIR             Output directory (default: sources/)
"""

import argparse
import sys
from pathlib import Path

from unito.merger import main as unito_main


def build_variant(wght: int, wdth: int, style_name: str, output_dir: Path, **kwargs) -> None:
    """Build a single font variant using the unito main function."""
    output_path = output_dir / f"Unito-{style_name}.ttf"
    print(f"\n{'=' * 60}")
    print(f"Building: {style_name}")
    print(f"{'=' * 60}")

    unito_main(wght=wght, wdth=wdth, style_name=style_name, output=str(output_path), **kwargs)

    if output_path.exists():
        size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"✓ Built: {output_path} ({size_mb:.2f} MB)")
    else:
        print(f"✗ Failed: {output_path}")


def main():
    """Main entry point for the build script."""
    parser = argparse.ArgumentParser(description="Build Unito fonts")
    parser.add_argument(
        "--download/--no-download",
        dest="download",
        default=True,
        help="Enable/disable font download",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download of all fonts",
    )
    parser.add_argument(
        "--variants",
        default="all",
        help="Comma-separated list of variants to build (all|regular,bold,condensed,boldcondensed)",
    )
    parser.add_argument(
        "--output-dir",
        default="sources/",
        help="Output directory for built fonts (default: sources/)",
    )

    args = parser.parse_args()

    # Parse variants
    requested_variants = [v.strip().lower() for v in args.variants.split(",")]

    all_variants = ["regular", "bold", "condensed", "boldcondensed"]

    if "all" in requested_variants:
        variants_to_build = all_variants
    else:
        variants_to_build = [v for v in requested_variants if v in all_variants]
        if not variants_to_build:
            print(f"Error: No valid variants found. Choose from: {', '.join(all_variants)}")
            sys.exit(1)

    # Determine output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build configuration for each variant
    variant_configs = {
        "regular": {"wght": 400, "wdth": 100, "style_name": "Regular"},
        "bold": {"wght": 700, "wdth": 100, "style_name": "Bold"},
        "condensed": {"wght": 400, "wdth": 75, "style_name": "Condensed"},
        "boldcondensed": {"wght": 700, "wdth": 75, "style_name": "BoldCondensed"},
    }

    # Build each variant
    kwargs = {
        "download": args.download,
        "force": args.force,
        "hang": True,
        "hani": True,
    }

    # Also build to fonts/ttf as requested
    final_fonts_dir = Path("fonts/ttf")
    final_fonts_dir.mkdir(parents=True, exist_ok=True)

    failed_variants = []

    for variant in variants_to_build:
        config = variant_configs[variant]
        try:
            # Build to sources/
            build_variant(**config, output_dir=output_dir, **kwargs)
            # Copy to fonts/ttf
            import shutil

            src_file = output_dir / f"Unito-{config['style_name']}.ttf"
            dst_file = final_fonts_dir / f"Unito-{config['style_name']}.ttf"
            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                print(f"✓ Copied to: {dst_file}")
        except Exception as e:
            print(f"✗ Error building {variant}: {e}")
            failed_variants.append(variant)

    # Summary
    print(f"\n{'=' * 60}")
    print("BUILD SUMMARY")
    print(f"{'=' * 60}")
    print(f"Requested: {', '.join(variants_to_build)}")
    print(f"Built: {len(variants_to_build) - len(failed_variants)}/{len(variants_to_build)}")

    if failed_variants:
        print(f"Failed: {', '.join(failed_variants)}")
        sys.exit(1)
    else:
        print("✓ All variants built successfully!")


if __name__ == "__main__":
    main()
