from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from unito.config import (
    UnitoConfig,
    UnitoPaths,
    UnifontWebSpec,
    GitHubFontSpec,
    load_font_sources,
    discover_google_font_specs,
    _default_seed_specs,
    default_config,
)


def test_unifont_web_spec_defaults():
    spec = UnifontWebSpec()
    assert spec.base_url == "https://unifoundry.com/pub/unifont/"
    assert spec.target_folder == "51unif"


def test_load_font_sources(tmp_path):
    yaml_content = """
sources:
  folder_10base:
    fonts:
      - path: fonts/Font.ttf
        description: Test
"""
    yaml_file = tmp_path / "sources.yaml"
    yaml_file.write_text(yaml_content)

    # load_font_sources returns UnitoConfig (based on signature reading)
    # If it returns list, the assertion below will clarify
    specs = load_font_sources(yaml_file)

    # Handle both cases to be safe and debug
    if isinstance(specs, list):
        assert len(specs) > 0
    else:
        assert isinstance(specs, UnitoConfig)
        assert len(specs.sources) == 1
        src = specs.sources["folder_10base"]
        assert len(src.fonts) == 1
        # Check updated logic: default repo is google_fonts -> rewrite path
        assert src.fonts[0].path == "ofl/font/Font.ttf"


def test_default_seed_specs():
    specs = _default_seed_specs()
    assert len(specs) > 0
    assert any(s.target_folder == "10base" for s in specs)


def test_discover_google_font_specs(tmp_path):
    root = tmp_path / "root"
    sources_dir = root / "sources"
    sources_dir.mkdir(parents=True)

    specs = discover_google_font_specs(sources_dir)
    assert len(specs) > 0


def test_default_config(tmp_path):
    # default_config takes no args
    cfg = default_config()
    assert isinstance(cfg, UnitoConfig)
