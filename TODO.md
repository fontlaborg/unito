# TODO

## Done
- [x] Build minisite for Unito font family (`docs/index.html`)
- [x] Baseline test suite green (49 tests pass)
- [x] Git-tag versioning via hatch-vcs; hatchling build backend
- [x] Toolchain modernized (uv + ruff format; dropped black)
- [x] Synthetic-font merge smoke + table-sanity tests
- [x] BUILDING.md; README/AGENTS accuracy fixes; merger priority comment
- [x] .gitignore hygiene for build/test artifacts

## Backlog (bigger ideas)
- [ ] Untrack redundant tracked binaries (`build/lib/`, `src/unito_font.egg-info/`, `.coverage`, `sources/*/build/`) in a dedicated post-release commit — they stay in history but stop bloating fresh clones.
- [ ] Pin fontspector version and document which QA checks are expected to warn/fail for a glyph-collection (many googlefonts-profile checks assume a text font).
- [ ] Developer docs site in `src_docs/` (mkdocs+Material): how the merge works, how to add a source/block — keep `docs/` for the user-facing specimen + download page.
- [ ] Evaluate Git LFS for `fonts/*.ttf` (largest is ~19 MB, under GitHub's 100 MB limit today, but the tree is heavy).
- [ ] Document or replace vendored `external/` FontTools now that `fonttools` is a normal dependency.
