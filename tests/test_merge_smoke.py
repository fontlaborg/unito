"""End-to-end smoke test for the glyph merge on small synthetic fonts.

Unlike ``test_merger.py`` (which mocks fontTools), this builds two real
TrueType fonts in memory, merges one into the other, and checks the result
both for merge behaviour (the new codepoint arrives, existing ones are kept)
and for structural sanity (the merged font recompiles and its tables agree).
No network, no downloads - the fonts are assembled with ``FontBuilder``.
"""

from __future__ import annotations

import io

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from unito.merger import merge_glyphs_from_font


def _box_glyph() -> object:
    """Return a filled 500x700 square as a compiled TrueType glyph."""
    pen = TTGlyphPen(None)
    pen.moveTo((50, 0))
    pen.lineTo((50, 700))
    pen.lineTo((550, 700))
    pen.lineTo((550, 0))
    pen.closePath()
    return pen.glyph()


def _build_font(cmap: dict[int, str], upm: int = 1000) -> TTFont:
    """Build a minimal, valid TrueType font covering ``cmap``.

    ``cmap`` maps codepoints to glyph names; every named glyph gets the same
    placeholder box outline. ``.notdef`` is always present.
    """
    glyph_names = [".notdef", *dict.fromkeys(cmap.values())]

    fb = FontBuilder(upm, isTTF=True)
    fb.setupGlyphOrder(glyph_names)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf({name: _box_glyph() for name in glyph_names})
    fb.setupHorizontalMetrics({name: (600, 50) for name in glyph_names})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({"familyName": "Synthetic", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()

    buf = io.BytesIO()
    fb.font.save(buf)
    buf.seek(0)
    return TTFont(buf)


def test_merge_adds_new_codepoint_and_keeps_existing():
    # Target owns 'A' (0x41); source adds 'B' (0x42) and also claims 'A'.
    target = _build_font({0x41: "A"})
    source = _build_font({0x41: "A", 0x42: "B"})

    before = target.getBestCmap()
    assert 0x42 not in before

    added, _conflicts = merge_glyphs_from_font(
        source, target, "Synthetic", exclude_hani=False, exclude_hang=False
    )

    # Exactly one new codepoint (0x42); the shared 0x41 must not be re-added.
    assert added == 1
    after = target.getBestCmap()
    assert 0x42 in after
    assert 0x41 in after


def test_merged_font_recompiles_and_tables_agree():
    target = _build_font({0x41: "A"})
    source = _build_font({0x42: "B"})

    merge_glyphs_from_font(source, target, "Synthetic", exclude_hani=False, exclude_hang=False)

    # Table sanity: the merged font must round-trip through save/reload and
    # keep glyf, cmap, hmtx and glyph order mutually consistent.
    buf = io.BytesIO()
    target.save(buf)
    buf.seek(0)
    reloaded = TTFont(buf)

    order = set(reloaded.getGlyphOrder())
    cmap = reloaded.getBestCmap()
    assert 0x41 in cmap and 0x42 in cmap
    for glyph_name in cmap.values():
        assert glyph_name in order, f"cmap points at missing glyph {glyph_name!r}"
        assert glyph_name in reloaded["hmtx"].metrics, f"no metrics for {glyph_name!r}"
    assert reloaded["maxp"].numGlyphs == len(reloaded.getGlyphOrder())
