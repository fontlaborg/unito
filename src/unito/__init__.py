"""Unito font build package."""

from .downloader import prepare_font_sources
from .merger import main as merge_fonts

__all__ = ["merge_fonts", "prepare_font_sources"]
__version__ = "0.1.0"
