from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest
from unito.pipeline import (
    BuildVariant,
    FamilyConfig,
    _get_static_font_name,
    prepare_source_folder,
    build_base_unito,
    build_all,
    main,
    _strip_axis_tags,
)


def test_build_variant_dataclass():
    v = BuildVariant("Regular", 400, 100)
    assert v.name == "Regular"
    assert v.wght == 400


def test_family_config_dataclass():
    f = FamilyConfig("Name", "Slug", "dir")
    assert f.name == "Name"


def test_strip_axis_tags():
    assert _strip_axis_tags("Weight") == "Weight"
    assert _strip_axis_tags("Weight[wght]") == "Weight"


def test_get_static_font_name():
    v = BuildVariant("Regular", 400, 100)
    name = _get_static_font_name(Path("NotoSans[wght].ttf"), v)
    assert name == "NotoSans-Regular.ttf"


def test_prepare_source_folder(tmp_path):
    src_dir = tmp_path / "10base"
    src_dir.mkdir(parents=True)
    (src_dir / "Font.ttf").write_text("")

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    variant = BuildVariant("Regular", 400, 100)

    with patch("unito.pipeline.instantiate_to_static") as mock_inst:
        mock_inst.return_value = cache_dir / "Font-Regular.ttf"

        paths = prepare_source_folder(tmp_path, "10base", variant, cache_dir)

        assert len(paths) == 1
        mock_inst.assert_called()


def test_build_base_unito(tmp_path):
    output_dir = tmp_path / "output"
    sources_dir = tmp_path / "sources"
    cache_dir = tmp_path / "cache"

    variant = BuildVariant("Regular", 400, 100)

    # 1. Setup 10base (Base) - used for instantiate_font
    (sources_dir / "10base" / "static").mkdir(parents=True)
    (sources_dir / "10base" / "static" / "Base-Regular.ttf").write_text("base")

    # 2. Setup 20symb - used for merge loop (glob)
    (sources_dir / "20symb" / "static").mkdir(parents=True)
    (sources_dir / "20symb" / "static" / "Symb-Regular.ttf").write_text("symb")

    with (
        patch("unito.pipeline.prepare_source_folder") as mock_prep,
        patch("unito.pipeline.instantiate_font") as mock_instantiate,
        patch("unito.pipeline.merge_glyphs_from_font") as mock_merge_glyphs,
        patch("unito.pipeline.deliver"),
        patch("fontTools.ttLib.TTFont") as mock_ttfont,
        patch("unito.pipeline.is_truetype_font", return_value=True) as mock_is_ttf,
    ):
        # Base font mock
        mock_base = MagicMock()
        mock_base.save.side_effect = lambda p: Path(p).write_text("dummy")

        # We need instantiate_font to return mock_base when called for base
        # But also return something for 20symb source
        mock_instantiate.return_value = mock_base

        # TTFont mock for source files loaded via TTFont(path) if not instantiated?
        # Step 1 loads base from static using instantiate_font(path, cache_dir=None)
        # Step 2 loads symb from static using instantiate_font(path)
        # So mock_instantiate handles both.

        mock_merge_glyphs.return_value = (0, 0)

        build_base_unito(sources_dir, variant, cache_dir)

        assert mock_instantiate.called
        assert mock_is_ttf.called
        assert mock_merge_glyphs.called


def test_main():
    with (
        patch("unito.pipeline.build_all") as mock_build,
        patch("argparse.ArgumentParser.parse_args") as mock_args,
    ):
        mock_args.return_value = MagicMock(sources_dir=None, output_dir=None)
        main()
        mock_build.assert_called()
