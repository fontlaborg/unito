from pathlib import Path
from unito.utils import project_root, derive_google_fonts_family, parse_semver_from_dirname


def test_project_root():
    root = project_root()
    assert isinstance(root, Path)
    assert (root / "src").exists()


def test_derive_google_fonts_family():
    assert derive_google_fonts_family("NotoSans-Regular.ttf") == "notosans"
    assert derive_google_fonts_family("Font.ttf") == "font"
    assert derive_google_fonts_family("MyFont") == "myfont"


def test_parse_semver_from_dirname():
    assert parse_semver_from_dirname("unifont-15.0.01") == (15, 0, 1)
    assert parse_semver_from_dirname("font-v1.2.3") is None
    assert parse_semver_from_dirname("font") is None
