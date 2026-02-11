"""Font download and source material preparation for Unito."""

from __future__ import annotations

import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from .cache import cache_key_for_url, ensure_dir
from .config import GitHubFontSpec, UnitoConfig, default_config
from .utils import parse_semver_from_dirname


def _download_binary(url: str, destination: Path, force: bool) -> bool:
    """Download a binary URL into ``destination``; returns True when written."""
    if destination.exists() and not force:
        return False
    ensure_dir(destination.parent)
    request = urllib.request.Request(url, headers={"User-Agent": "unito-font-builder/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
        data = response.read()
    destination.write_bytes(data)
    return True


def _github_raw_url(spec: GitHubFontSpec) -> str:
    path = "/".join(urllib.parse.quote(part) for part in spec.path.split("/"))
    return f"https://raw.githubusercontent.com/{spec.repo}/{spec.branch}/{path}"


def download_github_fonts(config: UnitoConfig, force: bool = False) -> dict[str, int]:
    """Download configured GitHub-hosted font files."""
    downloaded = 0
    skipped = 0
    failures = 0

    for spec in config.github_fonts:
        target_path = config.paths.sources_dir / spec.target_folder / spec.target_name
        url = _github_raw_url(spec)
        try:
            changed = _download_binary(url, target_path, force=force)
            if changed:
                downloaded += 1
                print(f"  Downloaded: {spec.target_folder}/{spec.target_name}")
            else:
                skipped += 1
                print(f"  Cached: {spec.target_folder}/{spec.target_name}")
        except Exception as exc:
            failures += 1
            print(f"  ERROR downloading {url}: {exc}")

    return {"downloaded": downloaded, "skipped": skipped, "failed": failures}


def _discover_latest_unifont_release(base_url: str) -> str:
    request = urllib.request.Request(base_url, headers={"User-Agent": "unito-font-builder/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        html = response.read().decode("utf-8", errors="replace")

    matches = re.findall(r"href=[\"'](unifont-\d+\.\d+\.\d+/)[\"']", html)
    if not matches:
        raise RuntimeError("Unable to detect unifont release directory")
    latest = max(matches, key=lambda item: parse_semver_from_dirname(item) or (0, 0, 0))
    return latest.rstrip("/")


def _convert_otf_to_ttf(otf_path: Path, ttf_path: Path, force: bool) -> None:
    if ttf_path.exists() and not force:
        return

    ensure_dir(ttf_path.parent)
    try:
        subprocess.run(
            ["otf2ttf", "-o", str(ttf_path), str(otf_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return
    except subprocess.CalledProcessError:
        subprocess.run(["otf2ttf", str(otf_path)], check=True, capture_output=True, text=True)
        generated = otf_path.with_suffix(".ttf")
        if not generated.exists():
            raise RuntimeError(f"otf2ttf did not create expected output for {otf_path}")
        shutil.move(str(generated), str(ttf_path))


def download_unifoundry_fonts(config: UnitoConfig, force: bool = False) -> dict[str, int]:
    """Download latest Unifont OTF files and convert to TTF."""
    downloaded = 0
    skipped = 0
    failures = 0

    release = _discover_latest_unifont_release(config.unifont_web.base_url)
    release_base = f"{config.unifont_web.base_url.rstrip('/')}/{release}/font-builds"
    filenames = [
        f"{release}.otf",
        f"{release.replace('unifont-', 'unifont_upper-')}.otf",
    ]

    download_cache_root = ensure_dir(config.paths.cache_downloads / "unifoundry")
    target_root = ensure_dir(config.paths.sources_dir / config.unifont_web.target_folder)

    for filename in filenames:
        file_url = f"{release_base}/{urllib.parse.quote(filename)}"
        otf_cache_path = download_cache_root / f"{cache_key_for_url(file_url)}.otf"
        ttf_name = filename.replace(".otf", ".ttf")
        ttf_path = target_root / ttf_name
        try:
            changed = _download_binary(file_url, otf_cache_path, force=force)
            _convert_otf_to_ttf(otf_cache_path, ttf_path, force=force)
            if changed or force:
                downloaded += 1
                print(f"  Downloaded+Converted: {config.unifont_web.target_folder}/{ttf_name}")
            else:
                skipped += 1
                print(f"  Cached: {config.unifont_web.target_folder}/{ttf_name}")
        except Exception as exc:
            failures += 1
            print(f"  ERROR handling {file_url}: {exc}")

    return {"downloaded": downloaded, "skipped": skipped, "failed": failures}


def _prepare_hani_from_package(config: UnitoConfig) -> bool:
    """Copy Hani.jsonl from package data directory to input tree."""
    source = config.paths.data_dir / "Hani.jsonl"
    target = config.paths.sources_dir / "hani" / "Hani.jsonl"

    if not source.exists():
        return False

    if target.exists():
        return True

    ensure_dir(target.parent)
    shutil.copy2(source, target)
    print("  Prepared: hani/Hani.jsonl (from package data)")
    return True


def ensure_hani_frequency_file(config: UnitoConfig, force: bool = False) -> bool:
    """Ensure ``Hani.jsonl`` exists in active input tree."""
    target = config.paths.sources_dir / "hani" / "Hani.jsonl"

    # Try package data dir first
    if _prepare_hani_from_package(config):
        if force:
            return True

    if target.exists() and not force:
        return False

    ensure_dir(target.parent)
    fallback = config.paths.reference_input_dir / "hani" / "Hani.jsonl"
    if fallback.exists():
        shutil.copy2(fallback, target)
        print("  Prepared: hani/Hani.jsonl (from reference)")
        return True

    url = "https://raw.githubusercontent.com/fontlaborg/unito-font/main/external/unito/01in/hani/Hani.jsonl"
    _download_binary(url, target, force=True)
    print("  Downloaded: hani/Hani.jsonl")
    return True


def prepare_font_sources(
    force: bool = False, config: UnitoConfig | None = None
) -> dict[str, dict[str, int]]:
    """Download all required source fonts and auxiliary data."""
    cfg = config or default_config()
    ensure_dir(cfg.paths.sources_dir)
    ensure_dir(cfg.paths.cache_downloads)

    print("\n[PREP] Downloading GitHub font sources...")
    github_stats = download_github_fonts(cfg, force=force)

    print("\n[PREP] Downloading Unifoundry releases...")
    unifoundry_stats = download_unifoundry_fonts(cfg, force=force)

    print("\n[PREP] Ensuring Han frequency map...")
    ensure_hani_frequency_file(cfg, force=force)

    return {"github": github_stats, "unifoundry": unifoundry_stats}
