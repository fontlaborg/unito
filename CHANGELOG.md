# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - Unreleased

### Added
- **Minisite**: Built a spectacular font specimen site at `docs/index.html` (GitHub Pages at `fontlab.org/unito-font/`).
  - Dark-mode design with gold accents, Inter UI font, scroll-reveal animations.
  - Family overview cards with CJK sample text for all 6 families.
  - Interactive type tester with family/style/size controls.
  - Glyph explorer using opentype.js — renders glyphs on canvas with Unicode labels and pagination.
  - Direct download links for all 24 TTF files.
- **CJK Families Support**: Implemented build pipeline for 'Unito HK', 'Unito JP', 'Unito KR', 'Unito CN', 'Unito TW'.
  - Sourced Noto Sans CJK variants from Google Fonts.
  - Subsetting to Source Han Sans region-specific glyphsets (HK, JP, KR, CN, TW).
  - Merging base Unito statics with CJK subsets.
- **Parallel Build**: Pipeline now builds variants and families in parallel.
- **New Directory Structure**:
  - Reorganized `sources/` into `10base`, `20symb`, `30mult`, `40cjkb`, `50unif`.
  - Added `71hk`, `72jp`, `73kr`, `74cn`, `75tw` for CJK families.
  - Added `60unito` and `60cjk2` for build outputs and intermediate fonts.
- **Exclusion Logic**: Added `exclude_tang` parameter to exclude Tangut characters (e.g., from Unifont).
- **Subsetting Module**: Added `unito.subsetter` for font subsetting using fontTools.
- **Pipeline Module**: Added `unito.pipeline` as the main orchestrator replacing shell scripts.

### Changed
- **Base Font**: Now inherits GSUB/GPOS tables from the base font (Folder 10base).
- **Naming**: Predictable static naming in `static/` subfolders.
- **Delivery**: Final fonts are delivered to `./fonts/`.
- **Config**: Updated `font_sources.yaml` structure to support new folders and exclusion rules.

### Fixed
- **Exclusions**: Ensured Tangut/Han/Hangul are excluded from specific sources (e.g. Unifont, Noto Sans CJK Base) where appropriate to prevent conflicts.
