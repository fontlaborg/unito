from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fontTools.ttLib import TTFont
from unito.merger import (
    is_power_of_two,
    get_closest_power_of_two,
    instantiate_font,
    merge_glyphs_from_font,
    is_excluded_codepoint,
)


def test_is_power_of_two():
    assert is_power_of_two(1)
    assert is_power_of_two(2)
    assert is_power_of_two(1024)
    assert not is_power_of_two(0)
    assert not is_power_of_two(3)


def test_get_closest_power_of_two():
    assert get_closest_power_of_two(3) == 4
    assert get_closest_power_of_two(100) == 128
    assert get_closest_power_of_two(128) == 128


def test_is_excluded_codepoint():
    assert is_excluded_codepoint(0x4E00)
    assert not is_excluded_codepoint(0x4E00, exclude_hani=False)
    assert is_excluded_codepoint(0xAC00)
    assert not is_excluded_codepoint(0xAC00, exclude_hang=False)
    assert is_excluded_codepoint(0x17000, exclude_tang=True)
    assert not is_excluded_codepoint(0x17000, exclude_tang=False)
    assert not is_excluded_codepoint(0x0041)


def test_instantiate_font(tmp_path):
    font_path = tmp_path / "Variable.ttf"
    font_path.write_text("dummy")
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    with (
        patch("unito.merger.TTFont") as mock_ttfont,
        patch("unito.merger.instantiateVariableFont") as mock_instantiate,
        patch("unito.merger.get_instantiated_font_path") as mock_get_path,
    ):
        mock_font = MagicMock()
        mock_font.__contains__.side_effect = lambda k: k == "fvar"

        mock_ttfont.return_value = mock_font
        mock_ttfont.return_value.__enter__.return_value = mock_font

        # FIX: instantiateVariableFont returns the font (or modified one)
        # instantiate_font uses the RETURN value to call save()
        mock_instantiate.return_value = mock_font

        # Ensure path is returned
        mock_get_path.return_value = cache_dir / "Instantiated.ttf"

        instantiate_font(font_path, 400, 100, cache_dir=cache_dir)

        mock_instantiate.assert_called_once()
        mock_font.save.assert_called_once()


def test_merge_glyphs_from_font():
    target = MagicMock()
    target.__getitem__.return_value.tables = []
    target.getGlyphOrder.return_value = [".notdef"]

    source = MagicMock()
    source.__getitem__.return_value = MagicMock()

    with (
        patch("unito.merger.is_truetype_font", return_value=True),
        patch("unito.merger.get_unicode_to_glyph_map", return_value={}),
        patch(
            "unito.merger.build_glyph_to_codepoints_map", return_value={"A": {0x41}}
        ) as mock_build_map,
        patch("unito.merger.extract_font_glyph_data", return_value=(MagicMock(), MagicMock())),
        patch("unito.merger.copy_glyph") as mock_copy,
        patch("unito.merger.is_valid_unicode_character", return_value=True),
    ):
        mock_copy.return_value = True

        added, conflicts = merge_glyphs_from_font(source, target, "Source")

        mock_build_map.assert_called_once()
        mock_copy.assert_called()

        assert added == 1
