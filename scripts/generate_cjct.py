#!/usr/bin/env python3
"""
README
======

Why this script exists
----------------------
Kripa relies on explicit Devanagari glyph metadata (for example, setting
conjunct outputs to Letter/Other) so mark attachment works correctly in the
fontmake/gftools pipeline.

When Glyphs auto-generates `cjct`, some valid conjunct substitutions can be
dropped after metadata changes. That causes shaping regressions (for example,
`h_ma-deva` or `d_da-deva` no longer being produced in the feature output).

What this script does
---------------------
1. Reads the current Glyphs source.
2. Extracts cjct substitution outputs from the existing cjct code.
3. Rebuilds `lookup cjct_devanagari` deterministically from glyph names.
4. Filters candidates using glyph metadata (with optional strict mode).
5. Optionally patches the cjct lookup in-place before build.

Why this is in build flow
-------------------------
The build uses a temporary source copy and restores the original file after
completion. This script runs on the temporary copy so the generated lookup is
always reproducible, while source editing in Glyphs remains straightforward.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GlyphMeta:
    name: str
    script: str | None
    category: str | None
    subcategory: str | None
    export: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate cjct_devanagari lookup")
    parser.add_argument(
        "--glyphs",
        default="sources/Kripa.glyphs",
        help="Path to .glyphs source file",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Write generated lookup to file (default: stdout)",
    )
    parser.add_argument(
        "--strict-metadata",
        action="store_true",
        help=(
            "Require explicit script=devanagari and category=Letter. "
            "Without this flag, missing metadata is allowed."
        ),
    )
    parser.add_argument(
        "--patch-glyphs",
        action="store_true",
        help="Replace lookup cjct_devanagari in the Glyphs source code block",
    )
    return parser.parse_args()


def extract_cjct_code_match(full_text: str) -> re.Match[str]:
    match = re.search(r'code = "(?P<code>.*?)";\ntag = cjct;', full_text, re.S)
    if not match:
        raise ValueError("Could not find cjct feature code block")
    return match


def extract_cjct_outputs(cjct_code: str) -> list[str]:
    outputs: list[str] = []
    seen: set[str] = set()
    # Keep original order from the source feature while de-duplicating outputs.
    for out in re.findall(r"\bsub\s+.+?\s+by\s+([A-Za-z0-9_.-]+);", cjct_code):
        if out not in seen:
            outputs.append(out)
            seen.add(out)
    return outputs


def parse_top_level_glyph_dicts(full_text: str) -> list[str]:
    lines = full_text.splitlines()
    in_glyphs = False
    paren_depth = 0
    brace_depth = 0
    current: list[str] | None = None
    blocks: list[str] = []

    # .glyphs is plist-like text. We track parentheses for the `glyphs = (...)`
    # array and braces for each top-level glyph dictionary.
    for line in lines:
        stripped = line.strip()
        if not in_glyphs:
            if stripped == "glyphs = (":
                in_glyphs = True
                paren_depth = 1
            continue

        paren_depth += line.count("(") - line.count(")")

        if brace_depth == 0 and stripped == "{":
            current = [line]
            brace_depth = 1
            continue

        if brace_depth > 0 and current is not None:
            current.append(line)
            brace_depth += line.count("{") - line.count("}")
            if brace_depth == 0:
                blocks.append("\n".join(current))
                current = None

        if in_glyphs and paren_depth == 0:
            break

    return blocks


def parse_glyph_metadata(full_text: str) -> dict[str, GlyphMeta]:
    metadata: dict[str, GlyphMeta] = {}
    for block in parse_top_level_glyph_dicts(full_text):
        name_m = re.search(r'glyphname = "([^"]+)";', block)
        if not name_m:
            continue

        name = name_m.group(1)
        script_m = re.search(r"\nscript = ([A-Za-z0-9_.-]+);", block)
        category_m = re.search(r"\ncategory = ([A-Za-z0-9_.-]+);", block)
        subcategory_m = re.search(r"\nsubCategory = ([A-Za-z0-9_.-]+);", block)
        export_zero = re.search(r"\nexport = 0;", block) is not None

        metadata[name] = GlyphMeta(
            name=name,
            script=script_m.group(1) if script_m else None,
            category=category_m.group(1) if category_m else None,
            subcategory=subcategory_m.group(1) if subcategory_m else None,
            export=not export_zero,
        )

    return metadata


def eligible_for_cjct(meta: GlyphMeta, strict_metadata: bool) -> bool:
    if not meta.export:
        return False

    if strict_metadata:
        # Strict mode is useful for validating explicit metadata coverage.
        if meta.script != "devanagari":
            return False
        if meta.category != "Letter":
            return False
        if meta.subcategory not in (None, "Other"):
            return False
        return True

    # Default mode is intentionally tolerant: if a field is missing in source,
    # do not reject the glyph (needed for entries like d_v_ya-deva).
    if meta.script is not None and meta.script != "devanagari":
        return False
    if meta.category is not None and meta.category != "Letter":
        return False
    if meta.subcategory is not None and meta.subcategory != "Other":
        return False
    return True


def output_to_inputs(output_glyph: str) -> list[str] | None:
    if not output_glyph.endswith("-deva"):
        return None
    stem = output_glyph[: -len("-deva")]
    if "_" not in stem:
        return None
    parts = [p for p in stem.split("_") if p]
    if len(parts) < 2:
        return None
    # Example: d_v_ya-deva -> d-deva v-deva ya-deva
    return [f"{p}-deva" for p in parts]


def generate_lookup(
    outputs: list[str], glyphs: dict[str, GlyphMeta], strict_metadata: bool
) -> tuple[str, int, int, int]:
    lines: list[str] = ["lookup cjct_devanagari {"]
    kept = 0
    skipped = 0

    for out in outputs:
        meta = glyphs.get(out)
        if meta is None:
            skipped += 1
            continue
        if not eligible_for_cjct(meta, strict_metadata):
            skipped += 1
            continue

        inputs = output_to_inputs(out)
        if not inputs:
            skipped += 1
            continue

        if any(inp not in glyphs for inp in inputs):
            # Skip rules that would reference non-existent input glyphs.
            skipped += 1
            continue

        lines.append(f"\tsub {' '.join(inputs)} by {out};")
        kept += 1

    lines.append("} cjct_devanagari;")
    lookup = "\n".join(lines)
    return lookup, kept, skipped, len(outputs)


def patch_cjct_lookup(cjct_code: str, new_lookup: str) -> str:
    pattern = r"lookup cjct_devanagari \{.*?\} cjct_devanagari;"
    # Replace exactly one lookup body to keep the rest of cjct code untouched.
    updated, count = re.subn(pattern, new_lookup, cjct_code, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Could not replace lookup cjct_devanagari in cjct code")
    return updated


def main() -> int:
    args = parse_args()
    glyphs_path = Path(args.glyphs)
    if not glyphs_path.exists():
        print(f"Error: file not found: {glyphs_path}", file=sys.stderr)
        return 2

    text = glyphs_path.read_text(encoding="utf-8")
    cjct_match = extract_cjct_code_match(text)
    cjct_code = cjct_match.group("code")
    outputs = extract_cjct_outputs(cjct_code)
    metadata = parse_glyph_metadata(text)
    lookup, kept, skipped, total = generate_lookup(outputs, metadata, args.strict_metadata)

    print(f"Generated cjct lookup: kept={kept} skipped={skipped} total={total}", file=sys.stderr)

    if args.patch_glyphs:
        updated_code = patch_cjct_lookup(cjct_code, lookup)
        patched_text = text[: cjct_match.start("code")] + updated_code + text[cjct_match.end("code") :]
        glyphs_path.write_text(patched_text, encoding="utf-8")

    if args.output:
        Path(args.output).write_text(lookup, encoding="utf-8")
    elif not args.patch_glyphs:
        print(lookup)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
