# CONTRIBUTING

For new features or in case of bugs, please log an issue in the repo.

## GlyphsApp

This font is built with [GlyphsApp](https://glyphsapp.com/), a popular font development tool.
To contribute, you will need a Macbook and a licensed copy of GlyphsApp.

## Devanagari Conjuncts

[Conjuncts](https://en.wikipedia.org/wiki/Devanagari_conjuncts) are a key characteristic of Devanagari script and other Brahmic scripts. They are constructed of more than two consonant letters. For example: `क्य`, `ज्ञ`, `द्ध` and `श्र` etc.
The library [fontmake](https://github.com/googlefonts/fontmake) has an [known issue](https://github.com/googlefonts/fontmake/issues/703) with
reading the ligature/conjunct anchors and not handling them as expected. More details [here](#known-issue).

## Building

To build the fonts from the source file, you will need to install [gftools](https://github.com/googlefonts/gftools).
Once you have installed it, run the following:
`bash build.sh` from the root of the project.

The build script runs the following:

1. generate_cjct.py: Devanagari conjuncts need to be tagged as category=Letter and subCategory=Other so that fontmake can correctly handle Devanagari conjuncts and associated matras. More details [here](#known-issue). But, since the default subCategory for a conjunct is `Conjunct`, setting it to `Other` removes it from automatically generated list in the `cjct` feature. The generate_cjct script adds those conjuncts to that list.
2. patch_cjct.py: Glyphs has bugs that break Marathi shaping. It does not add the language MAR block to the `cjct`, `blws` and `pres` features. The patch_cjct script correctly adds the necessary block to identify Marathi locale.
3. gftools builder: This builds the actual font files (variable and static) based on the configuration specified in sources/config.yml.

## Versioning

Update the version number for the font. Follow the [Semantic Versioning](https://semver.org/) guidelines when updating the version. In the [CHANGELOG](CHANGELOG.md) file, list the enhancements/updates/fixes made under the new version number.

## Known Issue

When Glyphs exports a font, fontmake uses glyph metadata to determine what type of OpenType mark attachment rule to generate. Conjuncts that had no explicit metadata were classified as Letter/Ligature by default. The shaping pipeline then generates mark-to-ligature rules for them, which requires the matra and its attachment point to be split per component. If the components don't match exactly, the matra simply doesn't attach.

Setting them to category=Letter, subCategory=Other tells fontmake to generate a mark-to-base rule instead, which is simpler and works correctly and the matra attaches to the conjunct as a plain base glyph.
