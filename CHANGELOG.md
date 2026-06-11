# Changelog

This file records notable changes to the Nucleic Acid Text Converter and Finder.

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
