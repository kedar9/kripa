# Fail fast
set -e

SOURCE="sources/Kripa.glyphs"
BUILDER="builder.yaml"

# Build from temporary files so the source is not modified in place.
TMP_SOURCE="sources/tmp.Kripa.$$.glyphs"
TMP_BUILDER="tmp.builder.$$.yaml"

cleanup() {
	if [ "${KEEP_TEMP:-0}" = "1" ]; then
		echo "Keeping temporary files: $TMP_SOURCE $TMP_BUILDER"
		return
	fi
	rm -f "$TMP_SOURCE" "$TMP_BUILDER"
}
trap cleanup EXIT

cp "$SOURCE" "$TMP_SOURCE"
sed "s|sources/Kripa.glyphs|$TMP_SOURCE|" "$BUILDER" > "$TMP_BUILDER"

# Patch Devanagari glyph metadata and regenerate cjct lookup
python3 scripts/generate_cjct.py --glyphs "$TMP_SOURCE" --patch-glyphs

# Patch cjct feature for Marathi language support
python3 scripts/patch_cjct.py "$TMP_SOURCE"

# Build font
gftools builder "$TMP_BUILDER"
python3 scripts/compress_build.py
# fonttools varLib.instancer -o "fonts/variable/Kripa[wght].ttf"
