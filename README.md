# Nucleic Acid Text Converter and Finder

A compact PyQt5 desktop GUI for converting, cleaning, inspecting, and searching
nucleic-acid text.

The main script is `NA_text_converter_finderV4.py`.

## Features

- Expand compact repeat notation before conversion or search:
  - `T6` becomes `TTTTTT`
  - `(CAG)3` becomes `CAGCAGCAG`
- Convert input sequence text:
  - reverse complement
  - reverse
  - DNA output with `T` instead of `U`
  - RNA output with `U` instead of `T`
  - add custom text before each standard base
- Preserve, uppercase, or lowercase output.
- Preserve or remove whitespace independently from other non-base characters.
- Search for sequence matches while ignoring whitespace and treating `T` and `U`
  as equivalent.
- Highlight exact search matches in blue and complementary or reverse-complementary
  matches in yellow.
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
python3 NA_text_converter_finderV4.py
```

If installed with `pip install -e .`, you can also launch it with:

```bash
na-text-converter
```

## Make the Script Executable

The script already includes a Python shebang. On macOS or Linux, mark it
executable and run it directly:

```bash
chmod +x NA_text_converter_finderV4.py
./NA_text_converter_finderV4.py
```

This still requires Python and PyQt5 to be installed in the environment that
launches the script.

## Build a Standalone App or Executable

For a single-file executable with bundled dependencies, install PyInstaller:

```bash
python3 -m pip install pyinstaller
pyinstaller --onefile --windowed --name na-text-converter NA_text_converter_finderV4.py
```

The built executable will be placed in `dist/`.

Notes:

- Use `--windowed` for a GUI-style app without a terminal window.
- On macOS, PyInstaller builds for the current platform and architecture.
- If you use a virtual environment, run PyInstaller from the same environment
  where PyQt5 is installed.

## Development Check

Run a basic syntax/import compile check:

```bash
python3 -m py_compile NA_text_converter_finderV4.py
```

## License

This project is licensed under the MIT License. See `LICENSE`.
