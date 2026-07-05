"""Unito font build package."""

from .downloader import prepare_font_sources
from .exclude import get_all_excluded_codepoints, load_control_file, should_exclude_codepoint
from .merger import main as merge_fonts
from .pipeline import build_all
from .pipeline import main as build_pipeline
from .subsetter import extract_codepoints, subset_to_reference

__all__ = [
    "build_all",
    "build_pipeline",
    "extract_codepoints",
    "get_all_excluded_codepoints",
    "load_control_file",
    "merge_fonts",
    "prepare_font_sources",
    "should_exclude_codepoint",
    "subset_to_reference",
]
try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("unito-font")
except PackageNotFoundError:  # package not installed (e.g. running from a source checkout)
    __version__ = "0.0.0+unknown"
