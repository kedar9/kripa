# Fail fast
set -e

SOURCE="sources/Kripa.glyphs"
BUILDER="sources/config.yaml"

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
sed "s|Kripa.glyphs|$TMP_SOURCE|g" "$BUILDER" > "$TMP_BUILDER"

# Patch Devanagari glyph metadata and regenerate cjct lookup
python3 scripts/generate_cjct.py --glyphs "$TMP_SOURCE" --patch-glyphs

# Patch cjct feature for Marathi language support
python3 scripts/patch_cjct.py "$TMP_SOURCE"

# Build font
gftools builder "$TMP_BUILDER"

# Generate subsets for Devanagari, Latin  and Latin extended character sets.
pyftsubset "fonts/webfonts/Kripa[wght].woff2" \
	--unicodes="U+0900-097F,U+1CD0-1CF9,U+200C-200D,U+20A8,U+20B9,U+20F0,U+25CC,U+A830-A839,U+A8E0-A8FF,U+11B00-11B09" \
	--output-file="fonts/webfonts/Kripa[wght].devanagari.woff2" \
	--flavor=woff2

pyftsubset "fonts/webfonts/Kripa[wght].woff2" \
	--unicodes="U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF" \
	--output-file="fonts/webfonts/Kripa[wght].latin-ext.woff2" \
	--flavor=woff2

pyftsubset "fonts/webfonts/Kripa[wght].woff2" \
	--unicodes="U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD" \
	--output-file="fonts/webfonts/Kripa[wght].latin.woff2" \
	--flavor=woff2

python3 scripts/compress_build.py
# fonttools varLib.instancer -o "fonts/variable/Kripa[wght].ttf"
