# Changelog

This file records notable changes to the Nucleic Acid Text Converter and Finder.

## v7_3 - 2026-09-21

### Added

- A bottom status banner that reports the 1-based letter position clicked in
  Output, or the first and last positions and length of a selected region.
  Spaces and punctuation are ignored. Hairpin sequence lines use their own
  sequence positions.

### Changed

- The GUI and terminal version output are now `v7_3`; the package version is `7.3`.

## v7_2 - 2026-09-21

### Added

- A Circular sequence checkbox below the original input for Search matches
  that cross the end/start boundary.
- IUPAC degenerate-code matching for exact, complementary, and
  reverse-complementary searches, including compact repeats such as `N5`.
- A Search popup table showing every IUPAC code, its possible bases, and its
  DNA and RNA complements.
- Search statistics showing searchable length and degenerate-code count.
- Search count phrases colored to match their highlighted sequence results, with
  the IUPAC reference button alongside the complementary-search checkbox.

### Changed

- The GUI and terminal version output are now `v7_2`; the package version is `7.2`.

## v7_1 - 2026-06-25

### Added

- An Original Sequence option to treat single-`i`-prefixed bases as reverse-order
  biological notation before running Convert, Add, Search, or Find hairpins.
- A Convert option named `Reverse (with i prefix)` that reverses the processed
  sequence and adds lowercase `i` before each standard base.

### Changed

- The GUI and terminal version output are now `v7_1`.
- The Python package version is now `7.1`.

## v7 - 2026-06-18

### Added

- A Find hairpins mode in the main PyQt GUI.
- Configurable hairpin minimum stem length, minimum loop length, and 0-based or
  1-based position reporting.
- Hairpin output highlighting: red stem nucleotides, underlined wobble-pair
  nucleotides, and bold maximal-stem hairpins.
- Optional RTF export for hairpin results.
- `lib/find_hairpins.py`, preserving the supplied hairpin finder as a
  standalone Tkinter GUI and command-line tool.

### Changed

- The Python package and GUI version are now `7`.

## v6.4 - 2026-06-11

### Added

- Vertical scrollbars and mouse-wheel scrolling for the Original Sequence,
  Search Sequence, and Output editors.

### Changed

- Long sequence text wraps within each editor and can be navigated vertically.
- The Clear Input button now sits outside the Original Sequence box on the same
  compact row as the Mode selector.
- The redundant Mode group title was removed to save vertical space.
- Search-mode editor and statistics panels no longer overlap at the minimum
  window size.
- The Python package and GUI version are now `6.4`.

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
