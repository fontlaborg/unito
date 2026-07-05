# Building Unito

Unito is not drawn. It is assembled — hundreds of source fonts poured into a
single file, one codepoint at a time. This page explains where the sources come
from, who wins when two of them cover the same codepoint, and how to add a new
one.

## The one command

```bash
python scripts/build.py
```

That downloads every source, instantiates the variable fonts to static weights,
merges them in priority order, and writes the 24 finished TTFs to `fonts/`. The
`Makefile` wraps it (`make build`) and adds `make test` (fontspector QA) and
`make proof` (HTML specimens). `scripts/build.py` is the canonical entry point;
the Makefile is a convenience.

## Where sources come from

Every input font is declared in [`sources/font_sources.yaml`](sources/font_sources.yaml).
The `repos` block names the upstreams and pins the ones that need pinning:

| Repo | What it supplies | Pin |
|------|------------------|-----|
| `google_fonts` | The Noto families — the bulk of the coverage | tracks `main` |
| `source_han_sans` | Region-specific CJK subsets (HK/JP/KR/CN/TW) | release branch |
| `unifontex` / `unifoundry` | Unifont — bitmap-derived fallbacks for the newest Unicode blocks Noto has not reached | `version: "17.0.03"` |

Downloads land in `sources/cache/` and are reused across builds, so a second
run is fast and offline.

## Priority: folder order is the whole rule

Sources are grouped into numbered folders, and **the number is the priority**.
The build merges them low-to-high:

```
10base  ->  20symb  ->  30mult  ->  40cjkb  ->  50unif / 51unif
```

Merging is first-come, first-served: the first font to supply a codepoint keeps
it, and every later font skips codepoints already covered (see
`merge_glyphs_from_font` in `src/unito/merger.py`). So `10base` (Noto Sans) wins
every conflict, and Unifont — last in line — only fills the gaps nobody else
did. The regional CJK families (`71hk`, `72jp`, `73kr`, `74cn`, `75tw`) layer on
top of the shared base to produce the `UnitoHK` … `UnitoTW` variants.

If a glyph looks wrong in the output, this ordering is the first thing to check:
a higher-priority folder is probably claiming that codepoint before the source
you expected.

## Excluding codepoints

Some sources over-reach. Noto Sans CJK Base carries Han and Hangul that belong
to the regional families; Unifont carries Tangut that would collide. Each source
folder can carry a `control_file` (e.g. `10base/exclude.yaml`) listing
`exclude_ranges` and `exclude_scripts`. The exclusion logic lives in
`src/unito/exclude.py`, with fast paths for Han (`exclude_hani`), Hangul
(`exclude_hang`), and Tangut (`exclude_tang`).

## Adding a new source

1. Add the font under the right numbered folder in `sources/font_sources.yaml`,
   choosing the folder by the priority you want it to have.
2. If it duplicates codepoints owned by an earlier folder, add an entry to that
   folder's `exclude.yaml` (or the new source's) so the wrong copy is dropped.
3. Rebuild: `python scripts/build.py`.
4. Sanity-check the result: `make test` (fontspector), and confirm the new
   codepoints landed with `python scripts/verify_han.py` or a quick fontTools
   `getBestCmap()` diff.

## Adding a new Unicode block

New blocks usually arrive first in Unifont. Bump `unifoundry.version` in
`font_sources.yaml` to the release that carries the block, then rebuild. If Noto
later ships a real design for that block, add the Noto source to a
higher-priority folder and Unifont will step aside automatically — priority does
the work, no manual removal needed.

## Tests

`python -m pytest` runs the pipeline unit tests, including
`tests/test_merge_smoke.py`, which builds two synthetic fonts, merges them, and
checks both the merge behaviour and that the result recompiles cleanly. These
run without any network access.
