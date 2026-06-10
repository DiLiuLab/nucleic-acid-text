#!/usr/bin/env python3
"""
NA_text_converter_finderV5.py

A compact PyQt5 GUI for nucleic-acid sequence conversion, text addition, and
sequence search/highlighting.

Inputs:
    - Original DNA/RNA sequence pasted or typed into the GUI. Repeat notation such as
      T6 or (CAG)3 is expanded before conversion, search, and sequence statistics.
    - Optional search sequence in Search mode.
    - Optional text or phrase in Add mode.

Outputs:
    - Converted sequence text,
    - Sequence text with custom text added before each standard base, or
    - Original sequence with exact search matches highlighted in blue and complementary/
      reverse-complementary matches highlighted in yellow.
    - Summary information for the expanded original sequence: DNA/RNA length, total
      length, A, T/U, C, G, whitespace, other characters, and GC%.

Example command:
    python NA_text_converter_finderV5.py
"""

import html
import sys
from typing import Dict, Iterable, List, Sequence, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCharFormat, QTextCursor
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


CONVERT_REVERSE_COMPLEMENT = "Reverse Complementary"
CONVERT_REVERSE = "Reverse"
CONVERT_TO_DNA = "DNA (T instead of U)"
CONVERT_TO_RNA = "RNA (U instead of T)"
MODE_CONVERT = "Convert"
MODE_SEARCH = "Search"
MODE_ADD = "Add"

CASE_PRESERVE = "Preserve original case"
CASE_UPPER = "UPPERCASE"
CASE_LOWER = "lowercase"

WHITESPACE_PRESERVE = "Preserve Space/whitespace"
WHITESPACE_REMOVE = "Remove Space/whitespace"

OTHER_NON_BASE_PRESERVE = "Preserve other non-base characters"
OTHER_NON_BASE_REMOVE = "Remove other non-base characters"

# The statistics and optional non-base removal use standard DNA/RNA bases only.
STANDARD_BASES = set("ACGTUacgtu")
STANDARD_BASES_UPPER = set("ACGTU")

# IUPAC nucleic-acid letters are treated as searchable sequence letters. U is
# normalized to T during search so DNA and RNA search sequences can be compared.
NA_LETTERS = set("ACGTURYSWKMBDHVNacgturyswkmbdhvn")

DNA_COMPLEMENT_UPPER = {
    "A": "T",
    "T": "A",
    "U": "A",
    "C": "G",
    "G": "C",
    "R": "Y",
    "Y": "R",
    "S": "S",
    "W": "W",
    "K": "M",
    "M": "K",
    "B": "V",
    "V": "B",
    "D": "H",
    "H": "D",
    "N": "N",
}

RNA_COMPLEMENT_UPPER = dict(DNA_COMPLEMENT_UPPER)
RNA_COMPLEMENT_UPPER["A"] = "U"

CANONICAL_DNA_COMPLEMENT = dict(DNA_COMPLEMENT_UPPER)
CANONICAL_DNA_COMPLEMENT["U"] = "A"


class NAToolsGUI(QWidget):
    """GUI for nucleic-acid conversion, text addition, and sequence searching."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Nucleic Acid Converter and Finder")
        self.setMinimumSize(780, 760)
        self._init_ui()
        self.update_visible_controls()
        self.update_sequence_info()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout()
        sequence_font = QFont("Courier New")
        sequence_font.setStyleHint(QFont.Monospace)

        # Original sequence field.
        input_group = QGroupBox("Original Sequence")
        input_layout = QVBoxLayout()
        self.sequence_input = QTextEdit()
        self.sequence_input.setFont(sequence_font)
        self.sequence_input.setPlaceholderText("Paste or type DNA/RNA sequence here...")
        self.sequence_input.setMinimumHeight(260)
        self.sequence_input.textChanged.connect(self.update_sequence_info)

        self.sequence_info_text = QTextEdit()
        self.sequence_info_text.setReadOnly(True)
        self.sequence_info_text.setMaximumHeight(92)
        self.sequence_info_text.setPlaceholderText("Original sequence info will appear here.")
        self.sequence_info_text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

        input_layout.addWidget(self.sequence_input)
        input_layout.addWidget(self.sequence_info_text)
        input_group.setLayout(input_layout)

        # Mode selector, always visible.
        mode_group = QGroupBox("Mode")
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([MODE_CONVERT, MODE_SEARCH, MODE_ADD])
        self.mode_combo.currentTextChanged.connect(self.update_visible_controls)
        mode_layout.addWidget(QLabel("Mode:"))
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)

        # Convert/Add controls, hidden in Search mode.
        self.convert_group = QGroupBox("Convert Options")
        convert_layout = QVBoxLayout()

        self.convert_to_row_widget = QWidget()
        convert_to_row = QHBoxLayout()
        convert_to_row.setContentsMargins(0, 0, 0, 0)
        self.convert_combo = QComboBox()
        self.convert_combo.addItems(
            [
                CONVERT_REVERSE_COMPLEMENT,
                CONVERT_REVERSE,
                CONVERT_TO_DNA,
                CONVERT_TO_RNA,
            ]
        )
        convert_to_row.addWidget(QLabel("Convert to:"))
        convert_to_row.addWidget(self.convert_combo)
        self.convert_to_row_widget.setLayout(convert_to_row)

        case_row = QHBoxLayout()
        self.case_combo = QComboBox()
        self.case_combo.addItems([CASE_PRESERVE, CASE_UPPER, CASE_LOWER])
        case_row.addWidget(QLabel("Case mode:"))
        case_row.addWidget(self.case_combo)

        non_related_row = QHBoxLayout()
        self.whitespace_combo = QComboBox()
        self.whitespace_combo.addItems([WHITESPACE_PRESERVE, WHITESPACE_REMOVE])
        self.other_non_base_combo = QComboBox()
        self.other_non_base_combo.addItems([OTHER_NON_BASE_PRESERVE, OTHER_NON_BASE_REMOVE])
        non_related_row.addWidget(QLabel("Space/whitespace:"))
        non_related_row.addWidget(self.whitespace_combo)
        non_related_row.addWidget(QLabel("Other non-base characters:"))
        non_related_row.addWidget(self.other_non_base_combo)

        self.prefix_row_widget = QWidget()
        prefix_row = QHBoxLayout()
        prefix_row.setContentsMargins(0, 0, 0, 0)
        self.prefix_input = QLineEdit()
        self.prefix_input.setFont(sequence_font)
        self.prefix_input.setPlaceholderText(
            "Letter or phrase to add before each base, e.g., i or test-"
        )
        prefix_row.addWidget(QLabel("Text to add:"))
        prefix_row.addWidget(self.prefix_input)
        self.prefix_row_widget.setLayout(prefix_row)

        convert_layout.addWidget(self.convert_to_row_widget)
        convert_layout.addLayout(case_row)
        convert_layout.addLayout(non_related_row)
        convert_layout.addWidget(self.prefix_row_widget)
        self.convert_group.setLayout(convert_layout)

        # Search controls, hidden in Convert mode. The search field has the same
        # available width as the original sequence field, with about one-quarter
        # of the original field's height.
        self.search_group = QGroupBox("Search Sequence")
        search_layout = QVBoxLayout()
        self.search_input = QTextEdit()
        self.search_input.setFont(sequence_font)
        self.search_input.setPlaceholderText(
            "Enter search sequence here. T and U are treated as equivalent."
        )
        self.search_input.setMinimumHeight(80)
        self.search_input.setMaximumHeight(110)
        search_layout.addWidget(self.search_input)
        self.search_group.setLayout(search_layout)

        # Buttons.
        button_layout = QHBoxLayout()
        self.run_button = QPushButton("Convert")
        self.run_button.clicked.connect(self.run_selected_mode)
        self.clear_button = QPushButton("Clear Output")
        self.clear_button.clicked.connect(self.clear_output)
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.clear_button)

        # Output field.
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        self.output_summary = QLabel("")
        self.output_summary.setWordWrap(True)
        self.output_text = QTextEdit()
        self.output_text.setFont(sequence_font)
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_summary)
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)

        main_layout.addWidget(input_group)
        main_layout.addWidget(mode_group)
        main_layout.addWidget(self.convert_group)
        main_layout.addWidget(self.search_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(output_group)
        self.setLayout(main_layout)

    def update_visible_controls(self) -> None:
        """Show only controls related to the selected mode."""
        mode = self.mode_combo.currentText()
        is_convert = mode == MODE_CONVERT
        is_search = mode == MODE_SEARCH
        is_add = mode == MODE_ADD

        self.convert_group.setVisible(is_convert or is_add)
        self.convert_group.setTitle("Add Options" if is_add else "Convert Options")
        self.convert_to_row_widget.setVisible(is_convert)
        self.search_group.setVisible(is_search)
        self.prefix_row_widget.setVisible(is_add)

        if is_convert:
            self.run_button.setText("Convert")
            self.output_summary.setText("Conversion output will appear below.")
        elif is_add:
            self.run_button.setText("Add")
            self.output_summary.setText(
                "Add output will appear below. The entered text is added before each "
                "standard A/C/G/T/U base."
            )
        else:
            self.run_button.setText("Search")
            self.output_summary.setText(
                "Search output: exact matches = blue; complementary/reverse-complementary "
                "matches = yellow."
            )

    def update_sequence_info(self) -> None:
        """Display essential statistics for the expanded original sequence."""
        raw_sequence = self.sequence_input.toPlainText()
        expanded_sequence = expand_repeat_notation(raw_sequence)
        info = get_original_sequence_info(expanded_sequence)
        self.sequence_info_text.setPlainText(format_sequence_info(info))

    def run_selected_mode(self) -> None:
        """Run conversion, text addition, or search for the selected mode."""
        self.update_sequence_info()
        mode = self.mode_combo.currentText()
        if mode == MODE_SEARCH:
            self.search_sequence()
        elif mode == MODE_ADD:
            self.add_sequence()
        else:
            self.convert_sequence()

    def clear_output(self) -> None:
        self.output_summary.setText("")
        self.output_text.clear()
        self.output_text.setCurrentCharFormat(QTextCharFormat())

    def set_output_plain_text(self, text: str) -> None:
        """Set unhighlighted output text and clear any previous search formatting."""
        self.output_text.clear()
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.output_text.setTextCursor(cursor)
        self.output_text.setCurrentCharFormat(QTextCharFormat())
        self.output_text.setPlainText(text)

    def convert_sequence(self) -> None:
        raw_sequence = self.sequence_input.toPlainText()
        sequence = expand_repeat_notation(raw_sequence)
        operation = self.convert_combo.currentText()
        case_mode = self.case_combo.currentText()
        whitespace_mode = self.whitespace_combo.currentText()
        other_non_base_mode = self.other_non_base_combo.currentText()

        cleaned_sequence = prepare_sequence_for_conversion(
            sequence, whitespace_mode, other_non_base_mode
        )

        if operation == CONVERT_REVERSE_COMPLEMENT:
            result = reverse_complement_with_case(cleaned_sequence)
        elif operation == CONVERT_REVERSE:
            result = reverse_sequence(cleaned_sequence)
        elif operation == CONVERT_TO_DNA:
            result = rna_to_dna_with_case(cleaned_sequence)
        elif operation == CONVERT_TO_RNA:
            result = dna_to_rna_with_case(cleaned_sequence)
        else:
            result = cleaned_sequence

        result = apply_case_mode(result, case_mode)
        self.output_summary.setText(
            "Conversion complete. " + format_sequence_info(get_original_sequence_info(sequence))
        )
        self.set_output_plain_text(result)

    def add_sequence(self) -> None:
        """Add the entered text before each standard base in the expanded sequence."""
        raw_sequence = self.sequence_input.toPlainText()
        sequence = expand_repeat_notation(raw_sequence)
        case_mode = self.case_combo.currentText()
        whitespace_mode = self.whitespace_combo.currentText()
        other_non_base_mode = self.other_non_base_combo.currentText()

        cleaned_sequence = prepare_sequence_for_conversion(
            sequence, whitespace_mode, other_non_base_mode
        )
        result = add_text_before_each_base(cleaned_sequence, self.prefix_input.text())
        result = apply_case_mode(result, case_mode)

        self.output_summary.setText(
            "Text addition complete. "
            + format_sequence_info(get_original_sequence_info(sequence))
        )
        self.set_output_plain_text(result)

    def search_sequence(self) -> None:
        original_sequence = expand_repeat_notation(self.sequence_input.toPlainText())
        query_sequence = expand_repeat_notation(self.search_input.toPlainText())

        highlighted_html, same_count, complementary_count, warnings = highlight_search_matches(
            original_sequence, query_sequence
        )
        warning_text = ""
        if warnings:
            warning_text = " " + " ".join(warnings)

        self.output_summary.setText(
            f"Exact matches: {same_count}; complementary/reverse-complementary matches: "
            f"{complementary_count}. "
            + format_sequence_info(get_original_sequence_info(original_sequence))
            + warning_text
        )
        self.output_text.setHtml(highlighted_html)



def find_matching_parenthesis(text: str, open_index: int) -> int:
    """Return the matching ')' index for text[open_index] == '('; otherwise -1."""
    depth = 0
    for index in range(open_index, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    return -1


def read_repeat_number(text: str, start_index: int) -> Tuple[int, int]:
    """
    Read a nonnegative integer repeat count starting at start_index.

    Returns (repeat_count, next_index). If no number is present, returns (1, start_index).
    """
    index = start_index
    while index < len(text) and text[index].isdigit():
        index += 1

    if index == start_index:
        return 1, start_index
    return int(text[start_index:index]), index


def expand_repeat_notation(sequence: str) -> str:
    """
    Expand compact repeat notation in the input sequence.

    Examples:
        T6 -> TTTTTT
        (CAG)3 -> CAGCAGCAG

    Single-character expansion is applied only to standard DNA/RNA bases
    A/C/G/T/U. Parenthesized groups can contain bases, whitespace, or other
    characters; their contents are recursively expanded before repetition.
    Digits that do not immediately follow a standard base or a parenthesized
    group are preserved as regular characters.
    """
    result: List[str] = []
    index = 0

    while index < len(sequence):
        char = sequence[index]

        if char == "(":
            close_index = find_matching_parenthesis(sequence, index)
            if close_index != -1:
                repeat_count, next_index = read_repeat_number(sequence, close_index + 1)
                if next_index != close_index + 1:
                    group_text = sequence[index + 1 : close_index]
                    expanded_group = expand_repeat_notation(group_text)
                    result.append(expanded_group * repeat_count)
                    index = next_index
                    continue

            # No valid repeat after a matched parenthesis, or no matching parenthesis.
            result.append(char)
            index += 1
            continue

        if is_standard_base(char):
            repeat_count, next_index = read_repeat_number(sequence, index + 1)
            if next_index != index + 1:
                result.append(char * repeat_count)
                index = next_index
                continue

        result.append(char)
        index += 1

    return "".join(result)


def get_original_sequence_info(sequence: str) -> Dict[str, object]:
    """Return counts and GC% for the expanded original sequence."""
    counts = {
        "total_length": len(sequence),
        "A": 0,
        "T_or_U": 0,
        "C": 0,
        "G": 0,
        "whitespace": 0,
        "other": 0,
        "recognized_bases": 0,
        "gc_percent": None,
    }

    for char in sequence:
        upper_char = char.upper()
        if upper_char == "A":
            counts["A"] += 1
            counts["recognized_bases"] += 1
        elif upper_char in ("T", "U"):
            counts["T_or_U"] += 1
            counts["recognized_bases"] += 1
        elif upper_char == "C":
            counts["C"] += 1
            counts["recognized_bases"] += 1
        elif upper_char == "G":
            counts["G"] += 1
            counts["recognized_bases"] += 1
        elif char.isspace():
            counts["whitespace"] += 1
        else:
            counts["other"] += 1

    if counts["recognized_bases"]:
        counts["gc_percent"] = 100.0 * (counts["G"] + counts["C"]) / counts["recognized_bases"]

    return counts


def format_sequence_info(info: Dict[str, object]) -> str:
    """Format sequence statistics as one compact line for the GUI."""
    gc_percent = info["gc_percent"]
    gc_text = "N/A" if gc_percent is None else f"{gc_percent:.2f}%"
    return (
        "Original sequence info after repeat expansion: "
        f"DNA/RNA length={info['recognized_bases']}; Total length={info['total_length']}; "
        f"A={info['A']}; T/U={info['T_or_U']}; C={info['C']}; G={info['G']}; "
        f"Space/whitespace={info['whitespace']}; Other={info['other']}; "
        f"GC%={gc_text}."
    )


def is_standard_base(char: str) -> bool:
    """Return True for standard DNA/RNA bases A, C, G, T, or U."""
    return char in STANDARD_BASES


def prepare_sequence_for_conversion(
    sequence: str, whitespace_mode: str, other_non_base_mode: str
) -> str:
    """Preserve/remove whitespace and other non-base characters independently."""
    result = []
    preserve_whitespace = whitespace_mode == WHITESPACE_PRESERVE
    preserve_other_non_base = other_non_base_mode == OTHER_NON_BASE_PRESERVE

    for char in sequence:
        if is_standard_base(char):
            result.append(char)
        elif char.isspace():
            if preserve_whitespace:
                result.append(char)
        elif preserve_other_non_base:
            result.append(char)

    return "".join(result)


def infer_complement_alphabet(sequence: str) -> str:
    """Infer whether reverse/complement output should use DNA T or RNA U."""
    has_t = any(char in "Tt" for char in sequence)
    has_u = any(char in "Uu" for char in sequence)
    if has_u and not has_t:
        return "RNA"
    return "DNA"


def complement_char(char: str, target_alphabet: str) -> str:
    """Return the complement of one character while preserving its case."""
    upper_char = char.upper()
    complement_map = RNA_COMPLEMENT_UPPER if target_alphabet == "RNA" else DNA_COMPLEMENT_UPPER
    if upper_char not in complement_map:
        return char

    complemented = complement_map[upper_char]
    if char.islower():
        return complemented.lower()
    return complemented


def complement_sequence_with_case(sequence: str) -> str:
    """Complement a DNA/RNA sequence while preserving spaces and non-sequence characters."""
    target_alphabet = infer_complement_alphabet(sequence)
    return "".join(complement_char(char, target_alphabet) for char in sequence)


def reverse_complement_with_case(sequence: str) -> str:
    """Reverse-complement a DNA/RNA sequence while preserving case."""
    target_alphabet = infer_complement_alphabet(sequence)
    return "".join(complement_char(char, target_alphabet) for char in reversed(sequence))


def reverse_sequence(sequence: str) -> str:
    """Reverse the input text exactly after optional non-base removal."""
    return sequence[::-1]


def dna_to_rna_with_case(sequence: str) -> str:
    """Convert DNA to RNA by replacing T/t with U/u."""
    return sequence.replace("T", "U").replace("t", "u")


def rna_to_dna_with_case(sequence: str) -> str:
    """Convert RNA to DNA by replacing U/u with T/t."""
    return sequence.replace("U", "T").replace("u", "t")


def add_text_before_each_base(sequence: str, prefix: str) -> str:
    """Add a prefix before each A/C/G/T/U base and preserve other input characters."""
    return "".join(f"{prefix}{char}" if is_standard_base(char) else char for char in sequence)


def apply_case_mode(sequence: str, case_mode: str) -> str:
    """Apply the selected case mode to the output sequence."""
    if case_mode == CASE_UPPER:
        return sequence.upper()
    if case_mode == CASE_LOWER:
        return sequence.lower()
    return sequence


def canonicalize_base(char: str) -> str:
    """Normalize one nucleic-acid letter for DNA/RNA-compatible searching."""
    upper_char = char.upper()
    if upper_char == "U":
        return "T"
    return upper_char


def extract_searchable_sequence(raw_sequence: str) -> Tuple[str, List[int]]:
    """
    Extract a searchable nucleic-acid string and map each extracted base to its raw index.

    Non-nucleic-acid characters are ignored for searching, so spaces and line breaks do not
    prevent a match. The returned index map allows matches to be highlighted in the original text.
    """
    canonical_chars: List[str] = []
    raw_indices: List[int] = []
    for raw_index, char in enumerate(raw_sequence):
        if char in NA_LETTERS:
            canonical_chars.append(canonicalize_base(char))
            raw_indices.append(raw_index)
    return "".join(canonical_chars), raw_indices


def complement_canonical_dna(sequence: str) -> str:
    """Complement a canonical DNA-like search sequence."""
    complemented = []
    for char in sequence:
        complemented.append(CANONICAL_DNA_COMPLEMENT.get(char, char))
    return "".join(complemented)


def reverse_complement_canonical_dna(sequence: str) -> str:
    """Reverse-complement a canonical DNA-like search sequence."""
    return complement_canonical_dna(sequence)[::-1]


def find_all_overlapping(haystack: str, needle: str) -> List[int]:
    """Return start positions of all overlapping occurrences of needle in haystack."""
    if not needle:
        return []

    positions = []
    start = 0
    while True:
        found = haystack.find(needle, start)
        if found == -1:
            break
        positions.append(found)
        start = found + 1
    return positions


def unique_preserving_order(values: Iterable[str]) -> List[str]:
    """Return unique strings while preserving their original order."""
    seen = set()
    unique_values = []
    for value in values:
        if value not in seen:
            unique_values.append(value)
            seen.add(value)
    return unique_values


def collect_match_styles(
    searchable_original: str,
    raw_indices: Sequence[int],
    exact_pattern: str,
    complementary_patterns: Sequence[str],
) -> Tuple[Dict[int, str], int, int]:
    """Collect raw-character highlight styles for exact and complementary matches."""
    styles: Dict[int, str] = {}

    complementary_starts = set()
    for pattern in complementary_patterns:
        for start in find_all_overlapping(searchable_original, pattern):
            complementary_starts.add((start, pattern))
            for offset in range(len(pattern)):
                styles[raw_indices[start + offset]] = "complementary"

    exact_starts = find_all_overlapping(searchable_original, exact_pattern)
    for start in exact_starts:
        for offset in range(len(exact_pattern)):
            # Exact matches take priority if the two highlight classes overlap.
            styles[raw_indices[start + offset]] = "exact"

    return styles, len(exact_starts), len(complementary_starts)


def text_to_highlighted_html(raw_sequence: str, styles: Dict[int, str]) -> str:
    """Convert raw text to HTML with blue/yellow sequence highlights."""
    span_for_style = {
        "exact": '<span style="background-color:#4da3ff; color:white;">',
        "complementary": '<span style="background-color:#fff176; color:black;">',
    }

    parts = [
        '<html><body><pre style="font-family: Courier New, Menlo, Consolas, monospace; white-space: pre-wrap;">'
    ]
    active_style = None
    for index, char in enumerate(raw_sequence):
        style = styles.get(index)
        if style != active_style:
            if active_style is not None:
                parts.append("</span>")
            if style is not None:
                parts.append(span_for_style[style])
            active_style = style
        parts.append(html.escape(char))

    if active_style is not None:
        parts.append("</span>")
    parts.append("</pre></body></html>")
    return "".join(parts)


def highlight_search_matches(raw_sequence: str, query_sequence: str) -> Tuple[str, int, int, List[str]]:
    """
    Highlight exact and complementary matches of query_sequence inside raw_sequence.

    The search ignores spaces and line breaks and treats T and U as equivalent. Exact
    query matches are highlighted in blue. Complementary and reverse-complementary
    matches are highlighted in yellow unless they are identical to the exact pattern.
    """
    searchable_original, raw_indices = extract_searchable_sequence(raw_sequence)
    exact_pattern, _ = extract_searchable_sequence(query_sequence)
    warnings: List[str] = []

    if not exact_pattern:
        warnings.append("Please enter a search sequence containing nucleic-acid letters.")
        return text_to_highlighted_html(raw_sequence, {}), 0, 0, warnings

    complement_pattern = complement_canonical_dna(exact_pattern)
    reverse_complement_pattern = reverse_complement_canonical_dna(exact_pattern)
    complementary_patterns = unique_preserving_order(
        [
            pattern
            for pattern in [complement_pattern, reverse_complement_pattern]
            if pattern and pattern != exact_pattern
        ]
    )

    if not complementary_patterns:
        warnings.append(
            "The complementary/reverse-complementary pattern is identical to the exact "
            "pattern, so only blue exact matches are shown."
        )

    styles, same_count, complementary_count = collect_match_styles(
        searchable_original, raw_indices, exact_pattern, complementary_patterns
    )
    return text_to_highlighted_html(raw_sequence, styles), same_count, complementary_count, warnings


def main() -> None:
    """Start the GUI application."""
    app = QApplication(sys.argv)
    gui = NAToolsGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
