import pytest
from unito.exclude import (
    should_exclude_codepoint,
    get_all_excluded_codepoints,
    is_han_script,
    is_hangul_script,
    is_tangut_script,
    load_control_file,
    HAN_RANGES,
    TANGUT_RANGES,
    HANGUL_RANGES,
)


def test_han_script_detection():
    # Test typical Han characters
    assert is_han_script(0x4E00)  # CJK Unified Ideograph
    assert is_han_script(0x9FFF)  # CJK Unified Ideograph
    assert is_han_script(0x3400)  # Extension A

    # Test non-Han characters
    assert not is_han_script(0x0041)  # Latin A
    assert not is_han_script(0xAC00)  # Hangul


def test_hangul_script_detection():
    assert is_hangul_script(0xAC00)  # Hangul Syllable
    assert is_hangul_script(0xD7AF)
    assert not is_hangul_script(0x4E00)


def test_tangut_script_detection():
    assert is_tangut_script(0x17000)
    assert is_tangut_script(0x187FF)
    assert not is_tangut_script(0x4E00)


def test_should_exclude_codepoint():
    # Test Han exclusion
    assert should_exclude_codepoint(0x4E00, exclude_hani=True)
    assert not should_exclude_codepoint(0x4E00, exclude_hani=False)

    # Test Hangul exclusion
    assert should_exclude_codepoint(0xAC00, exclude_hang=True)
    assert not should_exclude_codepoint(0xAC00, exclude_hang=False)

    # Test Tangut exclusion
    assert should_exclude_codepoint(0x17000, exclude_tang=True)
    assert not should_exclude_codepoint(0x17000, exclude_tang=False)

    # Test extra excludes
    assert should_exclude_codepoint(0x0041, extra_excludes={0x0041})
    assert not should_exclude_codepoint(0x0042, extra_excludes={0x0041})


def test_get_all_excluded_codepoints():
    excludes = get_all_excluded_codepoints(exclude_hani=True)
    assert 0x4E00 in excludes
    assert 0xAC00 not in excludes

    excludes = get_all_excluded_codepoints(exclude_tang=True)
    assert 0x17000 in excludes

    excludes = get_all_excluded_codepoints(extra_excludes={1, 2, 3})
    assert 1 in excludes


def test_load_control_file(temp_dir):
    control_file = temp_dir / "control.yaml"
    with open(control_file, "w") as f:
        f.write("""
exclude_ranges:
  - start: 0x100
    end: 0x102
exclude_scripts:
  - Tang
""")

    excludes = load_control_file(control_file)
    assert 0x100 in excludes
    assert 0x101 in excludes
    assert 0x102 in excludes
    # Check Tangut inclusion from script
    assert 0x17000 in excludes


def test_load_control_file_errors(temp_dir):
    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        load_control_file(temp_dir / "nonexistent.yaml")

    # Test invalid range
    invalid_file = temp_dir / "invalid.yaml"
    with open(invalid_file, "w") as f:
        f.write("""
exclude_ranges:
  - start: 0x200
    end: 0x100
""")
    with pytest.raises(ValueError):
        load_control_file(invalid_file)
