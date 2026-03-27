#!/usr/bin/env python3
"""Patch Devanagari OpenType features for correct Marathi (dev2/MAR) support.

Glyphs has bugs that break Marathi shaping:

1. cjct: only the last lookup is emitted for language MAR; deva script block
   is missing entirely. Fix: add all three lookups for dev2/MAR, deva/dflt,
   and deva/MAR.

2. blws: no language MAR block at all; rakar conjuncts (e.g. प्र, त्र) never
   form in Marathi. Fix: add 'language MAR include_dflt;' so dev2/MAR inherits
   the anonymous dflt lookups.

3. pres: language MAR block is missing Iimatra_devanagari (long-ī matra width
   selection). Fix: add it to all three language/script-specific blocks.
"""
import sys


# ---------------------------------------------------------------------------
# cjct
# ---------------------------------------------------------------------------

CJCT_BROKEN_TAIL = (
    "language MAR;\n"
    "lookup cjct_devanagari;\n"
    "language MAR;\n"
    "lookup cjct_devanagari;\n"
)

CJCT_FIXED_TAIL = (
    "language MAR;\n"
    "lookup cjct_devanagari_rakar_forms;\n"
    "lookup cjct_Halfdevanagari;\n"
    "lookup cjct_devanagari;\n"
    "\n"
    "script deva;\n"
    "lookup cjct_devanagari_rakar_forms;\n"
    "lookup cjct_Halfdevanagari;\n"
    "lookup cjct_devanagari;\n"
    "language MAR;\n"
    "lookup cjct_devanagari_rakar_forms;\n"
    "lookup cjct_Halfdevanagari;\n"
    "lookup cjct_devanagari;\n"
)

CJCT_MARKER = "lookup cjct_devanagari_rakar_forms;\nlookup cjct_Halfdevanagari;\n"


# ---------------------------------------------------------------------------
# blws
# ---------------------------------------------------------------------------

# blws uses anonymous inline rules under 'script dev2;' only — no named
# lookups, so we can't use 'lookup X;' syntax. 'include_dflt' inherits
# the anonymous dflt registrations for the language-specific context.
BLWS_BROKEN_TAIL = (
    "\tsub za-deva rakar-deva by za_rakar-deva;\n"
    '";\n'
    "tag = blws;"
)

BLWS_FIXED_TAIL = (
    "\tsub za-deva rakar-deva by za_rakar-deva;\n"
    "\n"
    "language MAR include_dflt;\n"
    '";\n'
    "tag = blws;"
)

BLWS_MARKER = "language MAR include_dflt;"


# ---------------------------------------------------------------------------
# pres
# ---------------------------------------------------------------------------

# pres MAR/deva blocks reference cjct_devanagari + Imatra1/2 but are missing
# Iimatra_devanagari (long-ī matra width selection).
PRES_BROKEN_TAIL = (
    "language MAR;\n"
    "lookup cjct_devanagari;\n"
    "lookup Imatra1_devanagari;\n"
    "lookup Imatra2_devanagari;\n"
    "\n"
    "script deva;\n"
    "lookup cjct_devanagari;\n"
    "lookup Imatra1_devanagari;\n"
    "lookup Imatra2_devanagari;\n"
    "language MAR;\n"
    "lookup cjct_devanagari;\n"
    "lookup Imatra1_devanagari;\n"
    "lookup Imatra2_devanagari;\n"
)

PRES_FIXED_TAIL = (
    "language MAR;\n"
    "lookup cjct_devanagari;\n"
    "lookup Imatra1_devanagari;\n"
    "lookup Imatra2_devanagari;\n"
    "lookup Iimatra_devanagari;\n"
    "\n"
    "script deva;\n"
    "lookup cjct_devanagari;\n"
    "lookup Imatra1_devanagari;\n"
    "lookup Imatra2_devanagari;\n"
    "lookup Iimatra_devanagari;\n"
    "language MAR;\n"
    "lookup cjct_devanagari;\n"
    "lookup Imatra1_devanagari;\n"
    "lookup Imatra2_devanagari;\n"
    "lookup Iimatra_devanagari;\n"
)

PRES_MARKER = "lookup Iimatra_devanagari;\n\";\ntag = pres;"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def _patch(content, broken, fixed, marker, label):
    # Idempotent behavior: if a fixed marker is present, never patch twice.
    if marker in content:
        print(f"{label}: already patched, skipping")
        return content, False
    if broken not in content:
        # Fail loudly when source structure changes so builds do not silently
        # ship with partially broken feature logic.
        print(
            f"ERROR: expected {label} tail not found — the feature may have "
            "been regenerated with a different structure. Inspect the code "
            f"block and update patch_cjct.py if needed.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"{label}: patched")
    return content.replace(broken, fixed, 1), True


def patch_file(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    content, c1 = _patch(content, CJCT_BROKEN_TAIL, CJCT_FIXED_TAIL, CJCT_MARKER, "cjct")
    content, c2 = _patch(content, BLWS_BROKEN_TAIL, BLWS_FIXED_TAIL, BLWS_MARKER, "blws")
    content, c3 = _patch(content, PRES_BROKEN_TAIL, PRES_FIXED_TAIL, PRES_MARKER, "pres")

    if c1 or c2 or c3:
        # Write only when needed to avoid noisy file churn.
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else "sources/Kripa.glyphs"
    patch_file(source)
