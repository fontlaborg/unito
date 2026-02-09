import pytest
import yaml


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test artifacts."""
    return tmp_path


@pytest.fixture
def mock_font_sources(temp_dir):
    """Create a mock font sources directory structure."""
    sources = temp_dir / "sources"
    sources.mkdir()
    (sources / "10base").mkdir()
    (sources / "20symb").mkdir()
    (sources / "30mult").mkdir()
    (sources / "40cjkb").mkdir()
    (sources / "50unif").mkdir()
    (sources / "51unif").mkdir()

    # Create exclude.yaml
    exclude_data = {
        "exclude_ranges": [{"start": "0x4E00", "end": "0x9FFF", "description": "Test Range"}],
        "exclude_scripts": ["Tang"],
    }
    with open(sources / "10base" / "exclude.yaml", "w") as f:
        yaml.dump(exclude_data, f)

    return sources


@pytest.fixture
def mock_config_file(temp_dir):
    """Create a mock font_sources.yaml."""
    config_path = temp_dir / "font_sources.yaml"
    data = {
        "repos": {"google": "https://example.com"},
        "sources": {"folder_10base": {"target_dir": "10base", "fonts": [{"path": "font.ttf"}]}},
        "output": {"families": {"Unito": {"variants": ["Regular", "Bold"]}}},
        "build": {"cache_dir": str(temp_dir / "cache"), "output_dir": str(temp_dir / "fonts")},
    }
    with open(config_path, "w") as f:
        yaml.dump(data, f)
    return config_path
