# Fail fast
set -e

SOURCE="sources/Kripa.glyphs"

# Back up source; restore it after build even on failure
cp "$SOURCE" "$SOURCE.bak"
trap 'mv "$SOURCE.bak" "$SOURCE"' EXIT

# Patch cjct feature for Marathi language support
python3 patch_cjct.py "$SOURCE"

# Build font
gftools builder builder.yaml
# fonttools varLib.instancer -o "fonts/variable/Kripa[wght].ttf"
