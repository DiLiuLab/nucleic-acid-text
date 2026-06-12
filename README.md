# Nucleic Acid Text Converter and Finder

A compact PyQt5 desktop GUI for converting, cleaning, inspecting, and searching
nucleic-acid text.

The main script is `NA_text_converter_finder.py`. The current version is **v6.4**.
See [CHANGELOG.md](CHANGELOG.md) for version history and release details.

## Features

- Expand compact repeat notation before conversion or search:
  - `T6` becomes `TTTTTT`
  - `(CAG)3` becomes `CAGCAGCAG`
- Convert input sequence text:
  - reverse complement
  - reverse
  - DNA output with `T` instead of `U`
  - RNA output with `U` instead of `T`
- Use the dedicated Add mode to add any letter or phrase before each standard
  base; for example, adding `i` to `ATCG` produces `iAiTiCiG`.
- Preserve, uppercase, or lowercase output.
- Preserve or remove whitespace independently from other non-base characters.
- Search for sequence matches while ignoring whitespace and treating `T` and `U`
  as equivalent.
- Highlight exact matches in yellow and reverse-complementary matches in light blue.
- Optionally include complementary matches, highlighted in red. Complementary
  searching is disabled by default.
- Display the application version in the GUI and report it in the terminal with
  `-v` or `--version`.
- Use a custom DNA-search application icon in the GUI and packaged applications.
- Continue running as a standalone script when `app_resources.py` is unavailable;
  in that case, only the custom icon is omitted.
- Clear the original sequence from the compact Mode row or copy output text with
  dedicated buttons.
- Navigate long original, search, and output sequences with vertical scrollbars
  or the mouse wheel while text wraps within each editor.
- Display live sequence statistics for both the original and search sequences.
- Clarify that complementary matching uses the same sequence direction and is
  different from reverse-complementary matching.
- Show expanded-sequence statistics, including recognized DNA/RNA length, total
  length, base counts, whitespace, other characters, and GC percentage.

## Requirements

- Python 3.9 or newer
- PyQt5

## Download or Update the Repository

If you do not already have the repository on your computer, download it with
`git clone`:

```bash
git clone https://github.com/DiLiuLab/nucleic-acid-text.git
cd nucleic-acid-text
```

If you already downloaded the repository earlier and want the newest version,
go into the repository folder and run `git pull`:

```bash
cd nucleic-acid-text
git pull
```

After downloading or updating the repository, install the Python dependencies
from inside the `nucleic-acid-text` folder.

Install dependencies with:

```bash
python3 -m pip install -r requirements.txt
```

Or install the project in editable mode:

```bash
python3 -m pip install -e .
```

## Run the GUI

Run the script directly with Python:

```bash
python3 NA_text_converter_finder.py
```

If installed with `pip install -e .`, you can also launch it with:

```bash
na-text-converter
```

Show the installed version without opening the GUI:

```bash
python3 NA_text_converter_finder.py --version
na-text-converter -v
```

GitHub releases also provide a macOS x86_64 application bundle with the custom
Dock icon and a directly downloadable standalone Python script. The macOS
application is ad-hoc signed but not Apple-notarized.

For standalone use, `NA_text_converter_finder.py` may be copied and run without
`app_resources.py`. All sequence functions remain available, but the custom
application icon is not loaded.

## Make the Script Executable

The script already includes a Python shebang. On macOS or Linux, mark it
executable and run it directly:

```bash
chmod +x NA_text_converter_finder.py
./NA_text_converter_finder.py
```

This still requires Python and PyQt5 to be installed in the environment that
launches the script.

## Build a Standalone App or Executable

For a single-file executable with bundled dependencies, install PyInstaller:

```bash
python3 -m pip install pyinstaller
pyinstaller --onefile --windowed --name na-text-converter \
  --icon assets/nucleic_acid_text.icns NA_text_converter_finder.py
```

The built executable will be placed in `dist/`.

Notes:

- Use `--windowed` for a GUI-style app without a terminal window.
- The command above uses the macOS `.icns` icon. On Windows, use
  `assets/nucleic_acid_text.ico`; on Linux, use `assets/nucleic_acid_text.png`.
- PyInstaller builds for the current platform and architecture.
- If you use a virtual environment, run PyInstaller from the same environment
  where PyQt5 is installed.

## Development Check

Run a basic syntax/import compile check:

```bash
python3 -m py_compile NA_text_converter_finder.py app_resources.py
```

## License

This project is licensed under the MIT License. See `LICENSE`.
