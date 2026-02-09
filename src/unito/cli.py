"""CLI entrypoints for the Unito package."""

from __future__ import annotations

from .pipeline import main as pipeline_main


def main() -> None:
    """Run Unito command line interface.

    Delegates to the pipeline module which handles argument parsing,
    font downloading, instantiation, merging, and delivery.
    """
    pipeline_main()


if __name__ == "__main__":
    main()
