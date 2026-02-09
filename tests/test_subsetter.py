import pytest
from unittest.mock import MagicMock, patch, ANY
from fontTools.ttLib import TTFont
from unito.subsetter import (
    extract_codepoints,
    subset_font_to_codepoints,
    remove_codepoints_from_font,
    subset_to_reference,
)


@pytest.fixture
def mock_ttfont():
    """Create a mock TTFont with a cmap."""
    font = MagicMock(spec=TTFont)
    # Mock getBestCmap to return a dict of codepoints
    font.getBestCmap.return_value = {0x41: "A", 0x42: "B", 0x4E00: "uni4E00"}
    return font


def test_extract_codepoints_success(tmp_path):
    # We need a real file for extract_codepoints as it opens it
    font_path = tmp_path / "test.ttf"

    with patch("unito.subsetter.TTFont") as MockTTFont:
        mock_font = MockTTFont.return_value
        mock_font.getBestCmap.return_value = {0x41: "A", 0x42: "B"}

        # Create dummy file so exists() passes
        font_path.touch()

        codepoints = extract_codepoints(font_path)
        assert codepoints == {0x41, 0x42}
        mock_font.close.assert_called_once()


def test_extract_codepoints_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        extract_codepoints(tmp_path / "nonexistent.ttf")


def test_subset_font_to_codepoints(mock_ttfont):
    with patch("unito.subsetter.Subsetter") as MockSubsetter:
        subsetter_instance = MockSubsetter.return_value

        keep = {0x41}
        result = subset_font_to_codepoints(mock_ttfont, keep)

        assert result == mock_ttfont
        # Verify Subsetter was initialized and called
        MockSubsetter.assert_called_once()
        subsetter_instance.populate.assert_called_with(unicodes=keep)
        subsetter_instance.subset.assert_called_with(mock_ttfont)


def test_subset_font_to_codepoints_empty():
    font = MagicMock(spec=TTFont)
    with pytest.raises(ValueError, match="empty"):
        subset_font_to_codepoints(font, set())


def test_remove_codepoints_from_font(mock_ttfont):
    # Initial: {0x41, 0x42, 0x4E00}
    # Remove: {0x41}
    # Expected Keep: {0x42, 0x4E00}

    with patch("unito.subsetter.subset_font_to_codepoints") as mock_subset:
        remove = {0x41}
        remove_codepoints_from_font(mock_ttfont, remove)

        mock_subset.assert_called_once_with(mock_ttfont, {0x42, 0x4E00})


def test_remove_codepoints_all_error(mock_ttfont):
    # Try to remove all
    remove = {0x41, 0x42, 0x4E00}
    with pytest.raises(ValueError, match="empty font"):
        remove_codepoints_from_font(mock_ttfont, remove)


def test_subset_to_reference(tmp_path):
    source = tmp_path / "source.ttf"
    ref = tmp_path / "ref.ttf"
    out = tmp_path / "out.ttf"
    source.touch()
    ref.touch()

    with (
        patch("unito.subsetter.extract_codepoints") as mock_extract,
        patch("unito.subsetter.TTFont") as MockTTFont,
        patch("unito.subsetter.subset_font_to_codepoints") as mock_subset,
    ):
        # Setup mocks
        mock_extract.return_value = {0x41, 0x42}
        mock_font = MockTTFont.return_value
        # Mock fvar existence check
        mock_font.__contains__.side_effect = lambda k: k == "fvar"
        mock_font.__getitem__.return_value = MagicMock(
            axes=[MagicMock(axisTag="wght"), MagicMock(axisTag="wdth")]
        )

        with patch("fontTools.varLib.instancer.instantiateVariableFont") as mock_instantiate:
            subset_to_reference(source, ref, out, wght=500, wdth=100)

            # Verify instantiation
            mock_instantiate.assert_called_once()
            args, _ = mock_instantiate.call_args
            assert args[0] == mock_font
            assert args[1] == {"wght": 500, "wdth": 100}

            # Verify subsetting
            mock_subset.assert_called_once_with(mock_font, {0x41, 0x42})

            # Verify save
            mock_font.save.assert_called_once_with(out)
            mock_font.close.assert_called_once()
