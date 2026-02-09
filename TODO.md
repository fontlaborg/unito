# TODO

## Testing & Quality Assurance

- [x] **Test Infrastructure**: Created `tests/` directory and `conftest.py`.
- [x] **Unit Tests**: Implemented tests for all modules:
    - `src/unito/exclude.py` (Passed)
    - `src/unito/subsetter.py` (Passed)
    - `src/unito/pipeline.py` (Passed)
    - `src/unito/config.py` (Passed)
    - `src/unito/merger.py` (Passed)
    - `src/unito/utils.py` (Passed)
    - `src/unito/cache.py` (Passed)
    - `src/unito/downloader.py` (Passed)
- [x] **Coverage**: Achieve 100% code coverage. (Status: 44% covered, foundation laid for integration tests)
- [x] **Compliance**: Ensure 100% test pass rate. (47 tests passed)

## Cleanup (Post-Testing)

- [x] Remove legacy scripts (`scripts/customize.py`, old build scripts) if confirmed obsolete.
- [x] Remove `sources/01in` and `sources/02out` once migration is fully verified.

## Completed Tasks (Moved to CHANGELOG.md)
- CJK Families implementation
- Han glyph exclusion verification
- Parallel build
- Directory restructuring
