#!/usr/bin/env python3
"""Build helper script for Unito font generation.

Delegates to unito.pipeline.main() which handles all argument parsing,
font downloading, instantiation, merging, and delivery.

Usage:
    python scripts/build.py [options]

See `python -m unito.pipeline --help` for available options.
"""

import sys

from unito.pipeline import main as pipeline_main


def main():
    """Entry point that delegates to pipeline.main()."""
    try:
        pipeline_main()
    except KeyboardInterrupt:
        print("\nBuild interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
