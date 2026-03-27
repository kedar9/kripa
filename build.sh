# Fail fast
set -e

SOURCE="sources/Kripa.glyphs"

# Back up source; restore it after build even on failure
cp "$SOURCE" "$SOURCE.bak"
trap 'mv "$SOURCE.bak" "$SOURCE"' EXIT

# Regenerate cjct lookup from current source glyph metadata
python3 scripts/generate_cjct.py --glyphs "$SOURCE" --patch-glyphs

# Patch cjct feature for Marathi language support
python3 scripts/patch_cjct.py "$SOURCE"

# Build font
gftools builder builder.yaml
# fonttools varLib.instancer -o "fonts/variable/Kripa[wght].ttf"
