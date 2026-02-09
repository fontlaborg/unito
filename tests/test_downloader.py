from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from unito.config import UnitoConfig, GitHubFontSpec, UnifontWebSpec, UnitoPaths
from unito.downloader import (
    _download_binary,
    download_github_fonts,
    prepare_font_sources,
    _github_raw_url,
)


@pytest.fixture
def mock_config(tmp_path):
    paths = UnitoPaths(
        tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, tmp_path, tmp_path
    )
    config = UnitoConfig(
        paths=paths,
        github_fonts=[],
        unifont_web=UnifontWebSpec(base_url="http://example.com", target_folder="50unif"),
    )
    return config


def test_download_binary_new(tmp_path):
    dest = tmp_path / "file.bin"
    dest.parent.mkdir(parents=True, exist_ok=True)

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = b"data"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = _download_binary("http://example.com", dest, force=False)

        assert result is True
        assert dest.read_bytes() == b"data"


def test_download_binary_cached(tmp_path):
    dest = tmp_path / "file.bin"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"existing")

    with patch("urllib.request.urlopen") as mock_urlopen:
        result = _download_binary("http://example.com", dest, force=False)

        assert result is False
        mock_urlopen.assert_not_called()


def test_download_binary_force(tmp_path):
    dest = tmp_path / "file.bin"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"existing")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = b"new"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = _download_binary("http://example.com", dest, force=True)

        assert result is True
        assert dest.read_bytes() == b"new"


def test_github_raw_url():
    spec = GitHubFontSpec(
        repo="user/repo",
        branch="main",
        path="fonts/Font.ttf",
        target_folder="folder",
        target_name="Font.ttf",
    )
    url = _github_raw_url(spec)
    expected = "https://raw.githubusercontent.com/user/repo/main/fonts/Font.ttf"
    assert url == expected


def test_download_github_fonts(mock_config, tmp_path):
    spec = GitHubFontSpec(
        repo="user/repo",
        branch="main",
        path="fonts/Font.ttf",
        target_folder="10base",
        target_name="Font.ttf",
    )
    # Fix frozen instance
    object.__setattr__(mock_config, "github_fonts", [spec])

    with patch("unito.downloader._download_binary") as mock_download:
        mock_download.return_value = True

        stats = download_github_fonts(mock_config, force=False)

        assert stats["downloaded"] == 1
        assert stats["skipped"] == 0
        mock_download.assert_called_once()
        args, _ = mock_download.call_args
        assert args[0] == "https://raw.githubusercontent.com/user/repo/main/fonts/Font.ttf"
        expected_path = mock_config.paths.sources_dir / "10base" / "Font.ttf"
        assert args[1] == expected_path


def test_prepare_font_sources(mock_config):
    with (
        patch("unito.downloader.download_github_fonts") as mock_gh,
        patch("unito.downloader.download_unifoundry_fonts") as mock_uf,
        patch("unito.downloader.ensure_hani_frequency_file") as mock_hani,
    ):
        mock_gh.return_value = {}
        mock_uf.return_value = {}

        # Fix signature call order
        prepare_font_sources(config=mock_config, force=True)

        mock_gh.assert_called_with(mock_config, force=True)
        mock_uf.assert_called_with(mock_config, force=True)
        mock_hani.assert_called_with(mock_config, force=True)
