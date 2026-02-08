"""Core Unito font merging logic, ported from legacy ``unito.py``."""

from __future__ import annotations

import io
import json
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from .cache import ensure_dir, get_instantiated_font_path, open_font_cache
from .config import UnitoConfig, default_config
from .downloader import prepare_font_sources
from .utils import ensure_vendor_fonttools

ensure_vendor_fonttools()

try:
    from fontTools import unicodedata  # type: ignore[attr-defined]
except ImportError:
    import unicodedata  # fallback to stdlib
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

try:
    import unicodedata2
except ImportError:
    print("Warning: unicodedata2 not installed. Install with: pip install unicodedata2")
    unicodedata2 = None

MAX_GLYPHS = 65535


try:
    from fontTools.ttLib.scaleUpem import scale_upem
except ImportError:
    scale_upem = None


def is_power_of_two(n: int) -> bool:
    """Check if a number is a power of two."""
    return n > 0 and (n & (n - 1)) == 0


def get_closest_power_of_two(n: int) -> int:
    """Get the closest power of two to a number."""
    if n <= 0:
        return 1
    return 2 ** round(math.log2(n))


def scale_glyph(glyph: Any, scale_factor: float) -> None:
    """Scale a glyph's coordinates by ``scale_factor``."""
    if hasattr(glyph, "coordinates"):
        coords = glyph.coordinates
        glyph.coordinates = type(coords)((x * scale_factor, y * scale_factor) for x, y in coords)

    if hasattr(glyph, "xMin"):
        glyph.xMin = int(glyph.xMin * scale_factor)
        glyph.yMin = int(glyph.yMin * scale_factor)
        glyph.xMax = int(glyph.xMax * scale_factor)
        glyph.yMax = int(glyph.yMax * scale_factor)

    if (
        hasattr(glyph, "isComposite")
        and glyph.isComposite()
        and hasattr(glyph, "components")
        and glyph.components
    ):
        for component in glyph.components:
            component.x = int(component.x * scale_factor)
            component.y = int(component.y * scale_factor)


def scale_font_upm(font: TTFont, target_upm: int) -> None:
    """Robustly scale a font's UPM to target_upm."""
    source_upm = get_upm(font)
    if source_upm == target_upm:
        return

    print(f"    Scaling from UPM {source_upm} to {target_upm}")
    if scale_upem:
        scale_upem(font, target_upm)
    else:
        # Fallback manual scaling for basic tables
        scale_factor = target_upm / source_upm
        if "glyf" in font:
            for glyph_name in font.getGlyphOrder():
                glyph = font["glyf"][glyph_name]
                scale_glyph(glyph, scale_factor)
        if "hmtx" in font:
            for glyph_name in font["hmtx"].metrics:
                width, lsb = font["hmtx"].metrics[glyph_name]
                font["hmtx"].metrics[glyph_name] = (
                    int(width * scale_factor),
                    int(lsb * scale_factor),
                )
        if "head" in font:
            font["head"].unitsPerEm = target_upm


def is_excluded_codepoint(
    codepoint: int, exclude_hani: bool = True, exclude_hang: bool = True
) -> bool:
    """Check if a Unicode codepoint should be excluded."""
    try:
        script = unicodedata.script(chr(codepoint))
        if exclude_hani and script in {"Hani", "Hans", "Hant"}:
            return True
        if exclude_hang and script == "Hang":
            return True
        return False
    except (ValueError, KeyError):
        return False


def is_valid_unicode_character(codepoint: int) -> bool:
    """Check if codepoint is assigned (not unassigned/private/surrogate)."""
    if unicodedata2 is None:
        return True

    try:
        char = chr(codepoint)
        name = unicodedata2.name(char, None)
        if name is None:
            category = unicodedata2.category(char)
            if category in ("Cn", "Co", "Cs"):
                return False
        return True
    except (ValueError, KeyError):
        return False


def instantiate_font(
    font_path: Path,
    wght: int = 400,
    wdth: int = 100,
    cache_dir: Path | None = None,
) -> TTFont:
    """Load a font and instantiate to specified instance if variable."""
    instantiated_path: Path | None = None
    if cache_dir:
        ensure_dir(cache_dir)
        instantiated_path = get_instantiated_font_path(cache_dir, font_path, wght, wdth)
        if instantiated_path.exists():
            print(f"  Loading: {font_path.name} (cached: {instantiated_path.name})")
            return TTFont(instantiated_path)

    print(f"  Loading: {font_path.name}")
    font = TTFont(font_path)

    if "fvar" in font:
        fvar = font["fvar"]
        location: dict[str, float] = {}
        axis_tags = {axis.axisTag for axis in fvar.axes}

        if "wght" in axis_tags:
            # Fallback to regular (400) if requested weight is outside range
            target_wght = float(wght)
            wght_axis = next(a for a in fvar.axes if a.axisTag == "wght")
            if target_wght < wght_axis.minValue or target_wght > wght_axis.maxValue:
                print(
                    f"    Weight {wght} outside range [{wght_axis.minValue}, {wght_axis.maxValue}], using 400"
                )
                target_wght = 400.0
            location["wght"] = target_wght

        if "wdth" in axis_tags:
            # Fallback to regular (100) if requested width is outside range
            target_wdth = float(wdth)
            wdth_axis = next(a for a in fvar.axes if a.axisTag == "wdth")
            if target_wdth < wdth_axis.minValue or target_wdth > wdth_axis.maxValue:
                print(
                    f"    Width {wdth} outside range [{wdth_axis.minValue}, {wdth_axis.maxValue}], using 100"
                )
                target_wdth = 100.0
            location["wdth"] = target_wdth

        for axis in fvar.axes:
            if axis.axisTag not in location:
                location[axis.axisTag] = axis.defaultValue

        print(f"    Instantiating variable font at: {location}")
        font = instantiateVariableFont(font, location)

        if instantiated_path:
            font.save(instantiated_path)

    return font


def get_unicode_to_glyph_map(font: TTFont) -> dict[int, str]:
    """Get mapping from Unicode codepoints to glyph names."""
    cmap = font.getBestCmap()
    return dict(cmap) if cmap else {}


def get_component_glyphs(font: TTFont, glyph_name: str) -> set[str]:
    """Recursively get component glyph names used by a composite glyph."""
    components: set[str] = set()
    if "glyf" not in font:
        return components

    glyf = font["glyf"]
    if glyph_name not in glyf:
        return components

    glyph = glyf[glyph_name]
    if not hasattr(glyph, "isComposite") or not glyph.isComposite():
        return components

    for component in glyph.components:
        comp_name = component.glyphName
        components.add(comp_name)
        components.update(get_component_glyphs(font, comp_name))
    return components


def copy_glyph(
    source_font: TTFont,
    target_font: TTFont,
    source_glyph_name: str,
    target_glyph_name: str,
    component_name_map: dict[str, str] | None = None,
) -> bool:
    """Copy a glyph from source to target with optional renaming."""
    if component_name_map is None:
        component_name_map = {}

    if "glyf" in source_font and "glyf" in target_font:
        source_glyf = source_font["glyf"]
        target_glyf = target_font["glyf"]
        if source_glyph_name not in source_glyf:
            return False

        source_glyph = source_glyf[source_glyph_name]
        source_glyph.expand(source_glyf)
        target_glyph = deepcopy(source_glyph)

        if (
            hasattr(target_glyph, "isComposite")
            and target_glyph.isComposite()
            and hasattr(target_glyph, "components")
            and target_glyph.components
        ):
            for component in target_glyph.components:
                old_name = component.glyphName
                if old_name in component_name_map:
                    component.glyphName = component_name_map[old_name]

        target_glyf[target_glyph_name] = target_glyph

        if (
            "hmtx" in source_font
            and "hmtx" in target_font
            and source_glyph_name in source_font["hmtx"].metrics
        ):
            source_width, source_lsb = source_font["hmtx"].metrics[source_glyph_name]
            target_font["hmtx"].metrics[target_glyph_name] = (source_width, source_lsb)

        glyph_order = target_font.getGlyphOrder()
        if target_glyph_name not in glyph_order:
            glyph_order.append(target_glyph_name)
            target_font.setGlyphOrder(glyph_order)

        return True
    return False


def add_cmap_entry(font: TTFont, codepoint: int, glyph_name: str) -> None:
    """Add a codepoint mapping to all cmap subtables."""
    if "cmap" not in font:
        return
    for table in font["cmap"].tables:
        if hasattr(table, "cmap") and table.cmap is not None:
            table.cmap[codepoint] = glyph_name


def get_source_fonts(folder: Path) -> list[Path]:
    """Get all ``.ttf`` and ``.otf`` files from folder, sorted by name."""
    fonts: list[Path] = []
    if folder.exists():
        for ext in ["*.ttf", "*.otf"]:
            fonts.extend(folder.glob(ext))
    return sorted(fonts)


def is_truetype_font(font: TTFont) -> bool:
    """Check if font has TrueType outlines (glyf table)."""
    return "glyf" in font


def build_glyph_to_codepoints_map(font: TTFont) -> dict[str, set[int]]:
    """Build reverse map: glyph_name -> set[codepoint]."""
    glyph_to_codepoints: dict[str, set[int]] = {}
    cmap = get_unicode_to_glyph_map(font)
    for codepoint, glyph_name in cmap.items():
        glyph_to_codepoints.setdefault(glyph_name, set()).add(codepoint)
    return glyph_to_codepoints


def synthesize_glyph_name(codepoint: int) -> str:
    """Generate glyph name from codepoint: ``uNNNN`` or ``uNNNNN``."""
    if codepoint <= 0xFFFF:
        return f"u{codepoint:04X}"
    return f"u{codepoint:05X}"


def extract_font_glyph_data(
    font_path: Path,
    wght: int,
    wdth: int,
    exclude_hani: bool,
    exclude_hang: bool,
    cache_dir_str: str,
) -> dict[str, Any]:
    """Extract glyph and codepoint data from a font file (parallel worker)."""
    try:
        cache_dir = Path(cache_dir_str)
        source_font = instantiate_font(font_path, wght=wght, wdth=wdth, cache_dir=cache_dir)

        if not is_truetype_font(source_font):
            source_font.close()
            return {
                "font_path": font_path,
                "skip": True,
                "reason": "CFF/OTF (not TrueType)",
            }

        source_upm = get_upm(source_font)
        glyph_to_codepoints = build_glyph_to_codepoints_map(source_font)
        glyph_data: dict[str, dict[str, Any]] = {}

        for glyph_name, codepoints in glyph_to_codepoints.items():
            valid_codepoints: set[int] = set()
            for cp in codepoints:
                if is_excluded_codepoint(cp, exclude_hani, exclude_hang):
                    continue
                if not is_valid_unicode_character(cp):
                    continue
                valid_codepoints.add(cp)

            if valid_codepoints:
                glyph_data[glyph_name] = {
                    "codepoints": valid_codepoints,
                    "components": get_component_glyphs(source_font, glyph_name),
                }

        source_font.close()
        return {
            "font_path": font_path,
            "skip": False,
            "source_upm": source_upm,
            "glyph_data": glyph_data,
        }
    except Exception as exc:
        return {"font_path": font_path, "skip": True, "reason": f"Error: {exc}"}


def get_upm(font: TTFont) -> int:
    """Get the units per em (UPM) from the head table."""
    if "head" in font:
        return int(getattr(font["head"], "unitsPerEm", 1000))
    return 1000


def merge_glyphs_from_font(
    source_font: TTFont,
    target_font: TTFont,
    source_name: str,
    exclude_hani: bool = True,
    exclude_hang: bool = True,
    is_base_font: bool = False,
) -> tuple[int, int]:
    """Merge glyphs from source font into target font."""
    if not is_truetype_font(source_font):
        print(f"    SKIP: {source_name} is CFF/OTF (not TrueType), cannot merge")
        return 0, 0

    source_upm = get_upm(source_font)
    target_upm = get_upm(target_font)
    binary_upm = get_closest_power_of_two(target_upm)

    if source_upm == target_upm or source_upm == binary_upm:
        pass
    elif is_power_of_two(source_upm):
        scale_font_upm(source_font, binary_upm)
    else:
        scale_font_upm(source_font, target_upm)

    target_glyph_order = target_font.getGlyphOrder()

    current_glyph_count = len(target_glyph_order)
    if current_glyph_count >= MAX_GLYPHS:
        print(f"    SKIP: {source_name} - glyph limit reached ({current_glyph_count}/{MAX_GLYPHS})")
        return 0, 0

    target_codepoints_covered = set(get_unicode_to_glyph_map(target_font).keys())
    target_glyphs = set(target_glyph_order)
    source_glyph_to_codepoints = build_glyph_to_codepoints_map(source_font)
    glyphs_to_add: list[dict[str, Any]] = []

    for source_glyph_name, source_codepoints in source_glyph_to_codepoints.items():
        new_codepoints: set[int] = set()
        for cp in source_codepoints:
            if cp in target_codepoints_covered:
                continue
            if is_excluded_codepoint(cp, exclude_hani=exclude_hani, exclude_hang=exclude_hang):
                continue
            if not is_base_font and not is_valid_unicode_character(cp):
                continue
            new_codepoints.add(cp)

        if not new_codepoints:
            continue

        if is_base_font:
            target_glyph_name = source_glyph_name
        else:
            primary_codepoint = min(new_codepoints)
            target_glyph_name = synthesize_glyph_name(primary_codepoint)
            counter = 1
            while target_glyph_name in target_glyphs:
                target_glyph_name = f"{synthesize_glyph_name(primary_codepoint)}.{counter}"
                counter += 1

        glyphs_to_add.append(
            {
                "source_name": source_glyph_name,
                "target_name": target_glyph_name,
                "codepoints": new_codepoints,
            }
        )

    glyphs_added = 0
    codepoints_added = 0
    glyph_name_mapping: dict[str, str] = {}

    for glyph_info in glyphs_to_add:
        if current_glyph_count + glyphs_added >= MAX_GLYPHS:
            print(
                f"    WARNING: Glyph limit reached, stopping at {glyphs_added} glyphs from {source_name}"
            )
            break

        source_glyph_name = glyph_info["source_name"]
        target_glyph_name = glyph_info["target_name"]
        components = get_component_glyphs(source_font, source_glyph_name)

        for comp_name in components:
            if comp_name not in target_glyphs and comp_name not in glyph_name_mapping:
                if current_glyph_count + glyphs_added >= MAX_GLYPHS:
                    break

                comp_target_name = comp_name if is_base_font else f"comp_{comp_name}"
                counter = 1
                while comp_target_name in target_glyphs:
                    comp_target_name = f"comp_{comp_name}.{counter}"
                    counter += 1

                if copy_glyph(
                    source_font,
                    target_font,
                    comp_name,
                    comp_target_name,
                ):
                    glyph_name_mapping[comp_name] = comp_target_name
                    target_glyphs.add(comp_target_name)
                    glyphs_added += 1

        if copy_glyph(
            source_font,
            target_font,
            source_glyph_name,
            target_glyph_name,
            glyph_name_mapping,
        ):
            glyph_name_mapping[source_glyph_name] = target_glyph_name
            target_glyphs.add(target_glyph_name)
            glyphs_added += 1

            for codepoint in glyph_info["codepoints"]:
                add_cmap_entry(target_font, codepoint, target_glyph_name)
                codepoints_added += 1
                target_codepoints_covered.add(codepoint)

    if glyphs_added > 0 or codepoints_added > 0:
        print(f"    Added {glyphs_added} glyphs, {codepoints_added} codepoints from {source_name}")

    return glyphs_added, codepoints_added


def remove_layout_tables(font: TTFont) -> None:
    """Remove all OpenType/AAT layout tables."""
    layout_tables = [
        "GSUB",
        "GPOS",
        "GDEF",
        "BASE",
        "JSTF",
        "morx",
        "mort",
        "kerx",
        "kern",
        "feat",
        "prop",
    ]
    for table in layout_tables:
        if table in font:
            del font[table]
            print(f"  Removed table: {table}")


def update_font_metadata(font: TTFont, style_name: str = "Regular") -> None:
    """Update font naming for Unito output family."""
    if "name" not in font:
        return
    name_table = font["name"]
    replacements = {
        1: "Unito",
        2: style_name,
        4: f"Unito {style_name}",
        6: f"Unito-{style_name}",
        16: "Unito",
        17: style_name,
    }

    for record in name_table.names:
        if record.nameID in replacements:
            try:
                record.toUnicode()
                name_table.setName(
                    replacements[record.nameID],
                    record.nameID,
                    record.platformID,
                    record.platEncID,
                    record.langID,
                )
            except UnicodeDecodeError:
                pass


def rebuild_cmap(font: TTFont) -> None:
    """Rebuild cmap table using format 12 for large codepoint ranges."""
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

    cmap = font["cmap"]
    unicode_map = get_unicode_to_glyph_map(font)
    cmap.tableVersion = 0
    cmap.tables = []

    format12 = CmapSubtable.newSubtable(12)
    format12.platformID = 3
    format12.platEncID = 10
    format12.language = 0
    format12.cmap = unicode_map
    cmap.tables.append(format12)


def set_post_format_3(font: TTFont) -> None:
    """Set post table to format 3.0 to avoid glyph-name overflow."""
    if "post" in font:
        post = font["post"]
        setattr(post, "formatType", 3.0)
        setattr(post, "extraNames", [])
        setattr(post, "mapping", {})
        if hasattr(post, "glyphOrder"):
            delattr(post, "glyphOrder")


def build_hani_cmap(
    hani_dir: Path,
    wght: int,
    wdth: int,
    cache_dir: Path | None = None,
) -> tuple[dict[int, tuple[TTFont, str]], list[tuple[str, TTFont]]]:
    """Build collective cmap for Han characters from ``hani/`` fonts."""
    hani_fonts: list[tuple[str, TTFont]] = []
    for font_path in get_source_fonts(hani_dir):
        font = instantiate_font(font_path, wght=wght, wdth=wdth, cache_dir=cache_dir)
        hani_fonts.append((font_path.name, font))

    collective_cmap: dict[int, tuple[TTFont, str]] = {}
    for _font_name, font in hani_fonts:
        cmap = get_unicode_to_glyph_map(font)
        for codepoint, glyph_name in cmap.items():
            if codepoint not in collective_cmap:
                collective_cmap[codepoint] = (font, glyph_name)

    return collective_cmap, hani_fonts


def add_hani_by_frequency(
    target_font: TTFont,
    hani_dir: Path,
    wght: int,
    wdth: int,
    cache_dir: Path | None = None,
) -> tuple[int, int]:
    """Add Han characters by frequency until glyph limit is reached."""
    jsonl_path = hani_dir / "Hani.jsonl"
    if not jsonl_path.exists():
        print(f"  WARNING: {jsonl_path} not found, skipping Han characters")
        return 0, 0

    print("\n[HANI] Building collective cmap from hani/ fonts...")
    collective_cmap, hani_fonts = build_hani_cmap(hani_dir, wght, wdth, cache_dir=cache_dir)
    print(f"  Collective cmap: {len(collective_cmap)} Han codepoints available")

    with jsonl_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
        hani_string = data.get("Hani", "")

    print(f"  Frequency list: {len(hani_string)} Han characters (sorted by frequency)")

    target_upm = get_upm(target_font)
    target_codepoints_covered = set(get_unicode_to_glyph_map(target_font).keys())
    target_glyphs = set(target_font.getGlyphOrder())
    current_glyph_count = len(target_glyphs)

    glyphs_added = 0
    codepoints_added = 0
    glyph_name_mapping: dict[str, str] = {}

    print(f"  Current glyph count: {current_glyph_count}/{MAX_GLYPHS}")
    print("  Adding Han characters by frequency...")

    for i, char in enumerate(hani_string):
        if current_glyph_count + glyphs_added >= MAX_GLYPHS:
            print(f"  STOP: Glyph limit reached at {glyphs_added} Han glyphs added")
            break

        codepoint = ord(char)
        if codepoint in target_codepoints_covered or codepoint not in collective_cmap:
            continue

        source_font, source_glyph_name = collective_cmap[codepoint]
        source_upm = get_upm(source_font)
        scale_factor = target_upm / source_upm if source_upm != target_upm else 1.0

        target_glyph_name = synthesize_glyph_name(codepoint)
        counter = 1
        while target_glyph_name in target_glyphs:
            target_glyph_name = f"{synthesize_glyph_name(codepoint)}.{counter}"
            counter += 1

        components = get_component_glyphs(source_font, source_glyph_name)
        for comp_name in components:
            if comp_name not in target_glyphs and comp_name not in glyph_name_mapping:
                if current_glyph_count + glyphs_added >= MAX_GLYPHS:
                    break

                comp_target_name = f"comp_{comp_name}"
                counter = 1
                while comp_target_name in target_glyphs:
                    comp_target_name = f"comp_{comp_name}.{counter}"
                    counter += 1

                if copy_glyph(
                    source_font,
                    target_font,
                    comp_name,
                    comp_target_name,
                ):
                    glyph_name_mapping[comp_name] = comp_target_name
                    target_glyphs.add(comp_target_name)
                    glyphs_added += 1

        if copy_glyph(
            source_font,
            target_font,
            source_glyph_name,
            target_glyph_name,
            glyph_name_mapping,
        ):
            glyph_name_mapping[source_glyph_name] = target_glyph_name
            target_glyphs.add(target_glyph_name)
            glyphs_added += 1
            add_cmap_entry(target_font, codepoint, target_glyph_name)
            codepoints_added += 1
            target_codepoints_covered.add(codepoint)

        if (i + 1) % 1000 == 0:
            print(
                f"    Progress: {i + 1}/{len(hani_string)} chars processed, "
                f"{codepoints_added} added, {current_glyph_count + glyphs_added}/{MAX_GLYPHS} glyphs"
            )

    for _font_name, font in hani_fonts:
        font.close()

    print(f"  Added {glyphs_added} glyphs, {codepoints_added} Han codepoints")
    return glyphs_added, codepoints_added


def process_fonts_parallel(
    font_paths: list[Path],
    wght: int,
    wdth: int,
    exclude_hani: bool,
    exclude_hang: bool,
    cache_dir: Path,
    max_workers: int | None = None,
) -> list[dict[str, Any]]:
    """Process multiple fonts in parallel to extract glyph data."""
    if not font_paths:
        return []
    if max_workers is None:
        import os

        max_workers = min(os.cpu_count() or 1, len(font_paths))

    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                extract_font_glyph_data,
                fp,
                wght,
                wdth,
                exclude_hani,
                exclude_hang,
                str(cache_dir),
            ): fp
            for fp in font_paths
        }

        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                if result["skip"]:
                    print(
                        f"  [{len(results)}/{len(font_paths)}] "
                        f"SKIP: {result['font_path'].name} - {result.get('reason', 'unknown')}"
                    )
                else:
                    glyph_count = len(result.get("glyph_data", {}))
                    print(
                        f"  [{len(results)}/{len(font_paths)}] "
                        f"Processed: {result['font_path'].name} ({glyph_count} glyphs)"
                    )
            except Exception as exc:
                fp = futures[future]
                print(f"  ERROR processing {fp.name}: {exc}")
                results.append({"font_path": fp, "skip": True, "reason": str(exc)})
    return results


def main(
    wght: int = 400,
    wdth: int = 100,
    style_name: str = "Regular",
    hang: bool = True,
    hani: bool = True,
    output: str | None = None,
    force: bool = False,
    download: bool = True,
    config: UnitoConfig | None = None,
) -> None:
    """Main entry point for Unito font merger."""
    cfg = config or default_config()
    exclude_hang = not hang
    exclude_hani = True

    input_dir = cfg.paths.input_dir
    output_dir = cfg.paths.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if output:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = cfg.paths.root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = output_dir / f"Unito-{style_name}.ttf"

    if download:
        prepare_font_sources(force=force, config=cfg)

    print("=" * 60)
    print("Unito Font Merger")
    print("=" * 60)
    print(f"  Weight: {wght}")
    print(f"  Width: {wdth}")
    print(f"  Style: {style_name}")
    print(f"  Download: {download}")
    print(f"  Force refresh: {force}")

    print("\n[1/6] Loading base font from 01in/01...")
    base_font_path = input_dir / "01" / "NotoSans[wdth,wght].ttf"
    if not base_font_path.exists():
        raise FileNotFoundError(f"Base font not found: {base_font_path}")

    target_font = instantiate_font(
        base_font_path, wght=wght, wdth=wdth, cache_dir=cfg.paths.cache_instantiation
    )

    master_upm = get_upm(target_font)
    print(f"  Master UPM: {master_upm}")

    initial_glyphs = len(target_font.getGlyphOrder())
    initial_cmap = len(get_unicode_to_glyph_map(target_font))
    print(f"  Base font: {initial_glyphs} glyphs, {initial_cmap} codepoints")

    total_glyphs_added = 0
    total_codepoints_added = 0

    print("\n[2/6] Processing 01in/02 (symbols, emoji)...")
    for font_path in get_source_fonts(input_dir / "02"):
        source_font = instantiate_font(
            font_path, wght=wght, wdth=wdth, cache_dir=cfg.paths.cache_instantiation
        )
        g, c = merge_glyphs_from_font(
            source_font,
            target_font,
            font_path.name,
            exclude_hani=exclude_hani,
            exclude_hang=exclude_hang,
            is_base_font=False,
        )
        total_glyphs_added += g
        total_codepoints_added += c
        source_font.close()

    print("\n[3/6] Processing 01in/03 (world scripts)...")
    fonts_03 = get_source_fonts(input_dir / "03")
    print(f"  Found {len(fonts_03)} fonts - using parallel processing")
    font_data_list = process_fonts_parallel(
        fonts_03,
        wght,
        wdth,
        exclude_hani=exclude_hani,
        exclude_hang=exclude_hang,
        cache_dir=cfg.paths.cache_instantiation,
    )

    print(f"  Merging {len([d for d in font_data_list if not d['skip']])} fonts into target...")
    for font_data in font_data_list:
        if font_data["skip"]:
            continue
        source_font = instantiate_font(
            font_data["font_path"], wght=wght, wdth=wdth, cache_dir=cfg.paths.cache_instantiation
        )
        g, c = merge_glyphs_from_font(
            source_font,
            target_font,
            font_data["font_path"].name,
            exclude_hani=exclude_hani,
            exclude_hang=exclude_hang,
            is_base_font=False,
        )
        total_glyphs_added += g
        total_codepoints_added += c
        source_font.close()

    print("\n[3/6] Processing 01in/03 (world scripts)...")
    fonts_03 = get_source_fonts(input_dir / "03")
    print(f"  Found {len(fonts_03)} fonts - using parallel processing")
    font_data_list = process_fonts_parallel(
        fonts_03,
        wght,
        wdth,
        exclude_hani=True,
        exclude_hang=True,
        cache_dir=cfg.paths.cache_instantiation,
    )

    print(f"  Merging {len([d for d in font_data_list if not d['skip']])} fonts into target...")
    for font_data in font_data_list:
        if font_data["skip"]:
            continue

        source_font = instantiate_font(
            font_data["font_path"], wght=wght, wdth=wdth, cache=font_cache
        )
        g, c = merge_glyphs_from_font(
            source_font,
            target_font,
            font_data["font_path"].name,
            exclude_hani=exclude_hani,
            exclude_hang=exclude_hang,
            is_base_font=False,
        )
        total_glyphs_added += g
        total_codepoints_added += c
        source_font.close()

    print("\n[4/6] Processing 01in/04 (CJK fonts, excluding Han)...")
    fonts_04 = get_source_fonts(input_dir / "04")
    if len(fonts_04) > 2:
        print(f"  Found {len(fonts_04)} fonts - using parallel processing")
        font_data_list = process_fonts_parallel(
            fonts_04,
            wght,
            wdth,
            exclude_hani=exclude_hani,
            exclude_hang=exclude_hang,
            cache_dir=cfg.paths.cache_instantiation,
        )
        print(f"  Merging {len([d for d in font_data_list if not d['skip']])} fonts into target...")
        for font_data in font_data_list:
            if font_data["skip"]:
                continue
            source_font = instantiate_font(
                font_data["font_path"], wght=wght, wdth=wdth, cache=font_cache
            )
            g, c = merge_glyphs_from_font(
                source_font,
                target_font,
                font_data["font_path"].name,
                exclude_hani=exclude_hani,
                exclude_hang=exclude_hang,
                is_base_font=False,
            )
            total_glyphs_added += g
            total_codepoints_added += c
            source_font.close()
    else:
        for font_path in fonts_05:
            source_font = instantiate_font(
                font_path, wght=wght, wdth=wdth, cache_dir=cfg.paths.cache_instantiation
            )

            total_glyphs_added += g
            total_codepoints_added += c
            source_font.close()

    print("\n[5/6] Processing 01in/05 (Unifont, excluding Han)...")
    fonts_05 = get_source_fonts(input_dir / "05")
    if len(fonts_05) > 2:
        print(f"  Found {len(fonts_05)} fonts - using parallel processing")
        font_data_list = process_fonts_parallel(
            fonts_05,
            wght,
            wdth,
            exclude_hani=exclude_hani,
            exclude_hang=exclude_hang,
            cache_dir=cfg.paths.cache_instantiation,
        )
        print(f"  Merging {len([d for d in font_data_list if not d['skip']])} fonts into target...")
        for font_data in font_data_list:
            if font_data["skip"]:
                continue
            source_font = instantiate_font(
                font_data["font_path"], wght=wght, wdth=wdth, cache=font_cache
            )
            g, c = merge_glyphs_from_font(
                source_font,
                target_font,
                font_data["font_path"].name,
                exclude_hani=exclude_hani,
                exclude_hang=exclude_hang,
                is_base_font=False,
            )
            total_glyphs_added += g
            total_codepoints_added += c
            source_font.close()
    else:
        for font_path in fonts_05:
            source_font = instantiate_font(font_path, wght=wght, wdth=wdth, cache=font_cache)
            g, c = merge_glyphs_from_font(
                source_font,
                target_font,
                font_path.name,
                exclude_hani=exclude_hani,
                exclude_hang=exclude_hang,
                is_base_font=False,
            )
            total_glyphs_added += g
            total_codepoints_added += c
            source_font.close()

    if hani:
        hani_dir = input_dir / "hani"
        if hani_dir.exists():
            g, c = add_hani_by_frequency(
                target_font, hani_dir, wght, wdth, cache_dir=cfg.paths.cache_instantiation
            )
            total_glyphs_added += g
            total_codepoints_added += c
        else:
            print(f"\n  WARNING: --hani specified but {hani_dir} not found")

    print(f"\n[6/6] Finalizing font...")
    print("  Removing OpenType layout tables...")
    remove_layout_tables(target_font)

    print("  Updating font metadata...")
    update_font_metadata(target_font, style_name)

    print("  Rebuilding cmap table...")
    rebuild_cmap(target_font)

    print("  Setting post table to format 3.0 (no glyph names)...")
    target_font["post"].formatType = 3.0

    final_glyphs = len(target_font.getGlyphOrder())
    final_cmap = len(get_unicode_to_glyph_map(target_font))

    print(f"  Saving to: {output_path}")
    target_font.save(str(output_path))

    target_font.close()

    final_font = TTFont(output_path)
    final_glyphs = len(final_font.getGlyphOrder())
    final_cmap = len(get_unicode_to_glyph_map(final_font))
    final_font.close()

    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print(f"  Output: {output_path}")
    print(f"  Base glyphs: {initial_glyphs}")
    print(f"  Glyphs added: {total_glyphs_added}")
    print(f"  Final glyphs: {final_glyphs}")
    print(f"  Base codepoints: {initial_cmap}")
    print(f"  Codepoints added: {total_codepoints_added}")
    print(f"  Final codepoints: {final_cmap}")
    print(f"  File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
