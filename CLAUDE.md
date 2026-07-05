# CLAUDE.md - Development Instructions for Unito

## Commands
- **Build**: `python scripts/build.py` or `unito-build` (builds fonts from config)
- **Test**: `python -m pytest` (runs all tests in `tests/`)
- **Lint/format**:
  - `uvx ruff check .` (lints Python code)
  - `uvx ruff format .` (formats Python code; replaces black)
  - `uvx mypy src` (checks static types)
- **Install**: `uv pip install -e .` (installs package in editable mode)
- **Install Dev**: `uv pip install -e ".[dev]"` (includes lint/test tools)

Versioning is git-tag driven via `hatch-vcs` (tags `vX.Y.Z`); there is no
hand-edited version string. Release with `uvx gitnextver@latest .`.

## Project Structure
- `src/unito/`: Main package source code
  - `font_sources.yaml`: Configuration for input fonts (sources 01-06)
  - `merger.py`: Core logic for merging fonts
  - `downloader.py`: Handles fetching fonts from URLs/repos
  - `cache.py`: Manages caching of downloaded files
  - `config.py`: Configuration loading and parsing
  - `cli.py`: Command-line interface entry point
- `scripts/`: Helper scripts (e.g., `build.py`)
- `tests/`: Test suite (pytest)
- `external/unito/`: External dependencies/vendors (FontTools, etc.)
- `sources/`: Working directory for build inputs
  - `cache/`: Downloaded font cache
- `fonts/ttf/`: Final output directory for built fonts

## Style Guidelines
- **Code Style**: 
  - Follow **ruff format** (line length 100).
  - Use **Ruff** for linting (Python 3.11+ target).
  - Type hints required (checked by **MyPy**).
- **Commits**: Use Conventional Commits (e.g., `feat: add new script`, `fix: merge logic`).
- **Imports**: Sorted by Ruff/Isort (standard lib, third-party, local).
- **Documentation**: Docstrings for all public modules, classes, and functions.

## Workflow
1. Modify `src/unito/font_sources.yaml` to add/remove fonts.
2. Run `python scripts/build.py` to test the build.
3. Run `python -m pytest` to ensure no regressions.
4. Lint with `uvx ruff check .` and `uvx ruff format .` before committing.
