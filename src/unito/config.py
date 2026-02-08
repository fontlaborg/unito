"""Configuration models and defaults for Unito."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import re
import yaml
from .utils import derive_google_fonts_family, project_root


@dataclass(frozen=True)
class GitHubFontSpec:
    """A single font file fetched from a GitHub repository."""

    repo: str
    branch: str
    path: str
    target_folder: str
    target_name: str


@dataclass(frozen=True)
class UnifontWebSpec:
    """Unifoundry source definition for OTF downloads."""

    base_url: str = "https://unifoundry.com/pub/unifont/"
    target_folder: str = "05"


@dataclass(frozen=True)
class UnitoPaths:
    """Filesystem paths used by downloader and merger."""

    root: Path
    input_dir: Path
    output_dir: Path
    cache_dir: Path
    cache_downloads: Path
    cache_instantiation: Path
    reference_input_dir: Path
    data_dir: Path


@dataclass(frozen=True)
class UnitoConfig:
    """Top-level config object for package operations."""

    paths: UnitoPaths
    github_fonts: list[GitHubFontSpec] = field(default_factory=list)
    unifont_web: UnifontWebSpec = field(default_factory=UnifontWebSpec)


def load_font_sources(config_path: Path) -> list[GitHubFontSpec]:
    """Load font specifications from YAML configuration."""
    if not config_path.exists():
        return []

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "sources" not in data:
        return []

    repos = data.get("repos", {})
    specs: list[GitHubFontSpec] = []

    for folder_key, folder_data in data["sources"].items():
        if not folder_key.startswith("folder_"):
            continue

        folder_num = folder_key.replace("folder_", "")
        repo_key = folder_data.get("repo", "google_fonts")
        repo_info = repos.get(repo_key, {})

        # Default to google/fonts main if not specified
        repo_full = "google/fonts"
        branch = "main"

        if repo_key == "google_fonts":
            repo_full = "google/fonts"
        elif "url" in repo_info:
            # Simple heuristic for GitHub URLs
            match = re.search(r"github\.com/([^/]+/[^/]+)", repo_info["url"])
            if match:
                repo_full = match.group(1).replace("/tree/main", "").replace("/tree/master", "")

        for font_entry in folder_data.get("fonts", []):
            if "path" not in font_entry:
                continue

            path = font_entry["path"]
            filename = Path(path).name
            family = derive_google_fonts_family(filename)

            # For Google Fonts, path in repo is ofl/Family/Filename
            repo_path = path
            if repo_key == "google_fonts" and not path.startswith("ofl/"):
                repo_path = f"ofl/{family}/{filename}"

            specs.append(
                GitHubFontSpec(
                    repo=repo_full,
                    branch=branch,
                    path=repo_path,
                    target_folder=folder_num,
                    target_name=filename,
                )
            )

    return specs


def _default_seed_specs() -> list[GitHubFontSpec]:
    """Fallback source set when no reference folder is available."""
    entries = [
        ("01", "NotoSans[wdth,wght].ttf"),
        ("02", "NotoEmoji[wght].ttf"),
        ("02", "NotoSansSymbols[wght].ttf"),
        ("02", "NotoSansSymbols2-Regular.ttf"),
        ("04", "NotoSansKR[wght].ttf"),
        ("04", "NotoSansSC[wght].ttf"),
        ("04", "NotoSansTC[wght].ttf"),
    ]
    specs: list[GitHubFontSpec] = []
    for folder, filename in entries:
        family = derive_google_fonts_family(filename)
        specs.append(
            GitHubFontSpec(
                repo="google/fonts",
                branch="main",
                path=f"ofl/{family}/{filename}",
                target_folder=folder,
                target_name=filename,
            )
        )
    return specs


def discover_google_font_specs(reference_input_dir: Path) -> list[GitHubFontSpec]:
    """Discover Google Fonts targets by scanning legacy ``01in`` content."""
    specs: list[GitHubFontSpec] = []
    if not reference_input_dir.exists():
        return _default_seed_specs()

    allowed_folders = {"01", "02", "03", "04"}
    for folder in sorted(reference_input_dir.iterdir()):
        if not folder.is_dir() or folder.name not in allowed_folders:
            continue
        for font_path in sorted(folder.glob("*.ttf")):
            family = derive_google_fonts_family(font_path.name)
            specs.append(
                GitHubFontSpec(
                    repo="google/fonts",
                    branch="main",
                    path=f"ofl/{family}/{font_path.name}",
                    target_folder=folder.name,
                    target_name=font_path.name,
                )
            )

    if not specs:
        return _default_seed_specs()

    unique: dict[tuple[str, str], GitHubFontSpec] = {}
    for spec in specs:
        key = (spec.target_folder, spec.target_name)
        unique[key] = spec
    return sorted(unique.values(), key=lambda item: (item.target_folder, item.target_name))


def default_config() -> UnitoConfig:
    """Build default runtime config rooted in project directory."""
    root = project_root()
    input_dir = root / "sources" / "01in"
    output_dir = root / "sources" / "02out"
    cache_dir = root / "sources" / "cache"
    data_dir = root / "src" / "unito" / "data"
    paths = UnitoPaths(
        root=root,
        input_dir=input_dir,
        output_dir=output_dir,
        cache_dir=cache_dir,
        cache_downloads=cache_dir / "downloads",
        cache_instantiation=cache_dir / "instantiation",
        reference_input_dir=root / "external" / "unito" / "01in",
        data_dir=data_dir,
    )

    github_fonts = load_font_sources(root / "sources" / "font_sources.yaml")
    if not github_fonts:
        github_fonts = discover_google_font_specs(paths.reference_input_dir)
        github_fonts.append(
            GitHubFontSpec(
                repo="stgiga/UnifontEX",
                branch="main",
                path="UnifontExMono.ttf",
                target_folder="05",
                target_name="UnifontExMono.ttf",
            )
        )
    return UnitoConfig(paths=paths, github_fonts=github_fonts)
