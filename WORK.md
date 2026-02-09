---
this_file: WORK.md
---

## 2026-02-09

### Scope
Fix Unifont source routing so:
- `50unif` downloads `UnifontExMono.ttf` from `stgiga/UnifontEX`.
- `51unif` receives latest Unifoundry OTFs and converts them to TTF.

### Changes made
- Updated `src/unito/config.py`:
  - Added `_resolve_github_repo()` helper.
  - `load_font_sources()` now supports per-font `repo` override (`font_entry.repo`).
  - `UnifontWebSpec.target_folder` changed to `51unif`.
- Updated `src/unito/pipeline.py`:
  - Added `51unif` to `SOURCE_FOLDERS` and base merge order.
  - Base build now merges `50unif` (UnifontEX) then `51unif` (Unifoundry).
- Updated `sources/font_sources.yaml`:
  - `folder_50unif` now explicitly uses repo `unifontex`.
  - Added/renamed Unifoundry section to `folder_51unif` with `target_dir: "51unif"`.
- Updated tests:
  - `tests/test_config.py` covers font-level repo override and `51unif` default target.
  - `tests/conftest.py` includes `51unif` fixture folder.

### Verification
- Confirmed live latest Unifoundry release directory from `https://unifoundry.com/pub/unifont/`:
  - Latest detected: `unifont-17.0.03` (checked 2026-02-09).
- Confirmed URLs respond:
  - `https://raw.githubusercontent.com/stgiga/UnifontEX/main/UnifontExMono.ttf` -> HTTP 200.
  - `https://unifoundry.com/pub/unifont/unifont-17.0.03/font-builds/unifont-17.0.03.otf` -> HTTP 200.
  - `https://unifoundry.com/pub/unifont/unifont-17.0.03/font-builds/unifont_upper-17.0.03.otf` -> HTTP 200.
- Tests:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run --python 3.13 pytest tests/test_config.py -q` -> **6 passed**.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run --python 3.13 pytest -q` -> **3 failed, 36 passed** (pre-existing failures in `tests/test_merger.py` and `tests/test_pipeline.py`, unrelated to this Unifont routing fix).
  - `uvx hatch test` -> fails in this environment due hatch selecting CPython 3.14 and `skia-python` wheel incompatibility.

### Next
- Resolve baseline failing tests in `tests/test_merger.py` and `tests/test_pipeline.py`.
- Pin hatch test interpreter to 3.13 or adjust dependencies to avoid CPython 3.14 wheel conflict.
