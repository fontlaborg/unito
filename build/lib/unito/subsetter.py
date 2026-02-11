"""Font subsetting operations for Unito.

This module provides utilities for extracting glyphsets from fonts and subsetting
fonts to match specific codepoint coverage. Primary use case is CJK family subsetting
(e.g., subsetting NotoSansHK to match SourceHanSansHK glyphset).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

if TYPE_CHECKING:
    pass


def extract_codepoints(font_path: Path) -> set[int]:
    """Extract all Unicode codepoints supported by a font file (OTF or TTF).

    Uses the font's best cmap subtable to determine supported codepoints.

    Args:
        font_path: Path to the font file (OTF or TTF).

    Returns:
        Set of Unicode codepoints (integers) supported by the font.

    Raises:
        FileNotFoundError: If the font file does not exist.
        ValueError: If the font has no cmap table or no usable cmap subtable.
    """
    if not font_path.exists():
        raise FileNotFoundError(f"Font file not found: {font_path}")

    font = TTFont(font_path)
    try:
        cmap = font.getBestCmap()
        if cmap is None:
            raise ValueError(f"No usable cmap subtable found in font: {font_path}")
        return set(cmap.keys())
    finally:
        font.close()


def subset_font_to_codepoints(
    font: TTFont,
    keep_codepoints: set[int],
    *,
    drop_layout: bool = False,
) -> TTFont:
    """Subset a font to only include the specified codepoints.

    Uses fontTools.subset.Subsetter to perform the subsetting operation.
    The font object is modified in-place and also returned.

    Args:
        font: The TTFont object to subset.
        keep_codepoints: Set of Unicode codepoints to keep in the font.
        drop_layout: If False (default), keep GSUB/GPOS/GDEF tables.
            If True, drop layout tables for smaller file size.

    Returns:
        The subsetted TTFont object (same object, modified in-place).

    Raises:
        ValueError: If keep_codepoints is empty.
    """
    if not keep_codepoints:
        raise ValueError("Cannot subset font: keep_codepoints set is empty")

    options = Options()
    options.notdef_outline = True
    options.name_IDs = ["*"]

    if drop_layout:
        options.layout_features = []
        options.layout_scripts = []
    else:
        options.layout_features = ["*"]

    subsetter = Subsetter(options=options)
    subsetter.populate(unicodes=keep_codepoints)
    subsetter.subset(font)

    return font


def remove_codepoints_from_font(
    font: TTFont,
    remove_codepoints: set[int],
) -> TTFont:
    """Remove specific codepoints from a font (inverse of subset).

    Gets all codepoints currently in the font, subtracts the remove set,
    and subsets to keep the remaining codepoints.

    Args:
        font: The TTFont object to modify.
        remove_codepoints: Set of Unicode codepoints to remove from the font.

    Returns:
        The modified TTFont object (same object, modified in-place).

    Raises:
        ValueError: If removing codepoints would result in an empty font.
    """
    cmap = font.getBestCmap()
    if cmap is None:
        raise ValueError("Font has no usable cmap subtable")

    current_codepoints = set(cmap.keys())
    keep_codepoints = current_codepoints - remove_codepoints

    if not keep_codepoints:
        raise ValueError(
            "Cannot remove codepoints: would result in empty font. "
            f"Font has {len(current_codepoints)} codepoints, "
            f"attempting to remove {len(remove_codepoints)}."
        )

    return subset_font_to_codepoints(font, keep_codepoints)


def subset_to_reference(
    source_path: Path,
    reference_path: Path,
    output_path: Path,
    *,
    wght: int = 400,
    wdth: int = 100,
) -> Path:
    """Subset a variable font to match a reference font's glyphset.

    This function:
    1. Extracts codepoints from the reference font
    2. Loads the source font
    3. Instantiates the source font if it's a variable font (using fontTools.varLib.instancer)
    4. Subsets to only include codepoints present in the reference font
    5. Saves the result to output_path

    Args:
        source_path: Path to the source font (variable TTF).
        reference_path: Path to the reference font (OTF or TTF) whose glyphset to match.
        output_path: Path where the subsetted font will be saved.
        wght: Weight axis value for instantiation (default 400 = Regular).
        wdth: Width axis value for instantiation (default 100 = Normal).

    Returns:
        The output_path where the font was saved.

    Raises:
        FileNotFoundError: If source or reference font files do not exist.
        ValueError: If the reference font has no codepoints or no usable cmap.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source font file not found: {source_path}")
    if not reference_path.exists():
        raise FileNotFoundError(f"Reference font file not found: {reference_path}")

    reference_codepoints = extract_codepoints(reference_path)
    if not reference_codepoints:
        raise ValueError(f"Reference font has no codepoints: {reference_path}")

    font = TTFont(source_path)

    if "fvar" in font:
        from fontTools.varLib.instancer import instantiateVariableFont

        axis_values = {"wght": wght, "wdth": wdth}
        fvar = font["fvar"]
        available_axes = {axis.axisTag for axis in fvar.axes}
        axis_values = {k: v for k, v in axis_values.items() if k in available_axes}

        if axis_values:
            instantiateVariableFont(font, axis_values, inplace=True)

    subset_font_to_codepoints(font, reference_codepoints)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    font.save(output_path)
    font.close()

    return output_path
