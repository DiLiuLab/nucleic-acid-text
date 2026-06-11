# Changelog

This file records notable changes to the Nucleic Acid Text Converter and Finder.

## v6.3 - 2026-06-11

### Added

- A Clear Input button directly below the original sequence editor.
- A Copy Output button that copies plain output text to the clipboard.
- Live essential statistics for the Search Sequence, including repeat-expanded
  length, base counts, whitespace, other characters, and GC percentage.

### Changed

- The complementary-search option now explicitly notes that complementary is
  different from reverse-complementary.
- The Python package and GUI version are now `6.3`.

## v6.2 - 2026-06-11

### Changed

- `NA_text_converter_finder.py` now runs normally when `app_resources.py` is
  unavailable, allowing the main file to be used as a standalone script.
- The custom application icon still loads automatically when `app_resources.py`
  is available.
- The Python package and GUI version are now `6.2`.
- The GitHub release includes `NA_text_converter_finder.py` as a directly
  downloadable standalone script.

## v6.1 - 2026-06-10

### Added

- A stable main filename: `NA_text_converter_finder.py`.
- Version information in the GUI window title and mode bar.
- Terminal version output through `-v` and `--version`.
- A custom DNA-search application icon, with PNG, macOS ICNS, and Windows ICO
  assets.
- A macOS x86_64 application bundle with the custom Dock icon, attached to the
  GitHub release.
- Separate search highlighting:
  - exact matches in yellow
  - reverse-complementary matches in light blue
  - complementary matches in red
- An unchecked-by-default option to include complementary matches.
- Independent counts for exact, reverse-complementary, and complementary matches.
- Explicit handling and warnings when search patterns are identical.

### Changed

- Packaging, documentation, and CI now use the stable script filename.
- The Python package version is now `6.1`.
- The application icon is embedded in the Python package so it is available when
  the program is launched from source or installed with `pip`.

## v5 - 2026-06-10

### Added

- A dedicated Add mode that inserts any letter or phrase before each standard
  nucleic-acid base.
- Example: adding `i` to `ATCG` produces `iAiTiCiG`.

### Changed

- Add mode retains the existing case, whitespace, and non-base-character options.
