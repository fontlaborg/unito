"""Caching helpers used by downloader and merger."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> Path:
    """Create a directory if missing and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_key_for_url(url: str) -> str:
    """Create a filesystem-safe key for a URL."""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return digest


def get_file_hash(file_path: Path) -> str:
    """Build hash token for a local file state."""
    stat = file_path.stat()
    return hashlib.md5(f"{file_path.name}_{stat.st_size}_{stat.st_mtime_ns}".encode()).hexdigest()


def get_instantiation_cache_key(font_path: Path, wght: int, wdth: int) -> str:
    """Generate cache key for variable font instantiation."""
    file_hash = get_file_hash(font_path)
    return f"inst_{file_hash}_{wght}_{wdth}"


def get_instantiated_font_path(cache_dir: Path, font_path: Path, wght: int, wdth: int) -> Path:
    """Get the path where an instantiated font should be stored."""
    key = get_instantiation_cache_key(font_path, wght, wdth)
    return cache_dir / f"{key}.ttf"


def open_font_cache(cache_dir: Path) -> Any:
    """Create diskcache instance when available, else return None."""
    ensure_dir(cache_dir)
    try:
        import diskcache as dc

        return dc.Cache(str(cache_dir))
    except ImportError:
        return None
