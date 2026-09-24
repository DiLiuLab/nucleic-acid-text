#!/usr/bin/env python3
"""
NA_text_converter_finder.py

A compact PyQt5 GUI for nucleic-acid sequence conversion, text addition, and
sequence search/highlighting.

Inputs:
    - Original DNA/RNA sequence pasted or typed into the GUI. Repeat notation such as
      T6 or (CAG)3 is expanded before conversion, search, and sequence statistics.
    - Optional search sequence in Search mode.
    - Optional text or phrase in Add mode.
    - Optional hairpin parameters in Find hairpins mode.
    - Optional i-prefix reverse-order handling for the Original Sequence.

Outputs:
    - Converted sequence text,
    - Sequence text with custom text added before each standard base, or
    - Original sequence with exact matches highlighted in yellow, reverse-complementary
      matches highlighted in light blue, and optional complementary matches highlighted
      in red.
    - Hairpin candidates with stem nucleotides highlighted in red, wobble pairs
      underlined, and maximal-stem hairpins shown in bold.
    - Summary information for the expanded original sequence: DNA/RNA length, total
      length, A, T/U, C, G, whitespace, other characters, and GC%.

Example command:
    python NA_text_converter_finder.py
"""

import argparse
import html
import sys
from typing import Dict, List, Sequence, Tuple

try:
    import app_resources  # Registers the embedded application icon.
except ModuleNotFoundError as error:
    if error.name != "app_resources":
        raise
    APP_RESOURCES_AVAILABLE = False
else:
    APP_RESOURCES_AVAILABLE = True

try:
    from lib.find_hairpins import find_hairpins, write_hairpins_rtf
except ModuleNotFoundError as error:
    if error.name not in {"lib", "lib.find_hairpins"}:
        raise
    HAIRPIN_MODULE_AVAILABLE = False
else:
    HAIRPIN_MODULE_AVAILABLE = True

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QFont, QIcon, QTextCharFormat, QTextCursor
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "Nucleic Acid Converter and Finder"
APP_VERSION = "7_3"
APP_ICON_RESOURCE = ":/icons/nucleic_acid_text.png"

CONVERT_REVERSE_COMPLEMENT = "Reverse Complementary"
CONVERT_REVERSE = "Reverse"
CONVERT_REVERSE_WITH_I_PREFIX = "Reverse (with i prefix)"
CONVERT_TO_DNA = "DNA (T instead of U)"
CONVERT_TO_RNA = "RNA (U instead of T)"
MODE_CONVERT = "Convert"
MODE_SEARCH = "Search"
MODE_ADD = "Add"
MODE_FIND_HAIRPINS = "Find hairpins"

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
IUPAC_BASES = {
    "A": frozenset("A"),
    "C": frozenset("C"),
    "G": frozenset("G"),
    "T": frozenset("T"),
    "R": frozenset("AG"),
    "Y": frozenset("CT"),
    "S": frozenset("CG"),
    "W": frozenset("AT"),
    "K": frozenset("GT"),
    "M": frozenset("AC"),
    "B": frozenset("CGT"),
    "D": frozenset("AGT"),
    "H": frozenset("ACT"),
    "V": frozenset("ACG"),
    "N": frozenset("ACGT"),
}
IUPAC_CODE_ORDER = "ACGTURYSWKMBDHVN"
MATCH_STYLE_CSS = {
    "exact": "background-color:#fff176; color:black;",
    "reverse_complementary": "background-color:#81d4fa; color:black;",
    "complementary": "background-color:#ef5350; color:white;",
}

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
    """GUI for nucleic-acid conversion, text addition, searching, and hairpins."""

    def __init__(self) -> None:
        super().__init__()
        self._hairpin_output_sequence = ""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        if APP_RESOURCES_AVAILABLE:
            self.setWindowIcon(QIcon(APP_ICON_RESOURCE))
        self.setMinimumSize(780, 840)
        self._init_ui()
        self.update_visible_controls()
        self.update_sequence_info()
        self.update_search_sequence_info()

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
        self.sequence_input.setMinimumHeight(80)
        self.sequence_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.sequence_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sequence_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sequence_input.textChanged.connect(self.update_sequence_info)

        self.circular_checkbox = QCheckBox("Circular sequence (Search wraps end to start)")
        self.circular_checkbox.setToolTip(
            "Search the original sequence as a circle. A match may cross the "
            "boundary between its last and first bases."
        )

        self.clear_input_button = QPushButton("Clear Input")
        self.clear_input_button.clicked.connect(self.clear_input)

        self.sequence_info_text = QTextEdit()
        self.sequence_info_text.setReadOnly(True)
        self.sequence_info_text.setMaximumHeight(92)
        self.sequence_info_text.setPlaceholderText("Original sequence info will appear here.")
        self.sequence_info_text.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

        self.i_prefix_reverse_checkbox = QCheckBox(
            "Treat i-prefixed bases as reversed biological order"
        )
        self.i_prefix_reverse_checkbox.setChecked(False)
        self.i_prefix_reverse_checkbox.setToolTip(
            "When checked, a sequence like iAiTiCiG is interpreted as GCTA "
            "before Convert, Add, Search, and Find hairpins. Only a single "
            "letter i immediately before A/C/G/T/U is removed."
        )
        self.i_prefix_reverse_checkbox.stateChanged.connect(self.update_sequence_info)

        input_layout.addWidget(self.sequence_input)
        input_layout.addWidget(self.circular_checkbox)
        input_layout.addWidget(self.sequence_info_text)
        input_layout.addWidget(self.i_prefix_reverse_checkbox)
        input_group.setLayout(input_layout)

        # Mode selector, Clear Input action, and version are always visible.
        mode_row_widget = QWidget()
        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(0, 0, 0, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            [MODE_CONVERT, MODE_SEARCH, MODE_ADD, MODE_FIND_HAIRPINS]
        )
        self.mode_combo.currentTextChanged.connect(self.update_visible_controls)
        mode_layout.addWidget(QLabel("Mode:"))
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        mode_layout.addWidget(self.clear_input_button)
        self.version_label = QLabel(f"v{APP_VERSION}")
        self.version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        mode_layout.addWidget(self.version_label)
        mode_row_widget.setLayout(mode_layout)

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
                CONVERT_REVERSE_WITH_I_PREFIX,
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
            "Enter sequence (e.g. GAGN5CTC). IUPAC codes and T/U are supported."
        )
        self.search_input.setMinimumHeight(70)
        self.search_input.setMaximumHeight(110)
        self.search_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.search_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.search_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.search_input.textChanged.connect(self.update_search_sequence_info)

        self.search_sequence_info_text = QTextEdit()
        self.search_sequence_info_text.setReadOnly(True)
        self.search_sequence_info_text.setMaximumHeight(92)
        self.search_sequence_info_text.setPlaceholderText(
            "Search sequence info will appear here."
        )
        self.search_sequence_info_text.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )

        self.include_complementary_checkbox = QCheckBox(
            "Include complementary matches (same direction; red)"
        )
        self.include_complementary_checkbox.setChecked(False)
        self.include_complementary_checkbox.setToolTip(
            "Complementary uses the base-by-base complement in the same direction. "
            "Reverse-complementary also reverses the sequence."
        )
        self.iupac_table_button = QPushButton("IUPAC code && complement")
        self.iupac_table_button.clicked.connect(self.show_iupac_code_table)
        search_options_row = QHBoxLayout()
        search_options_row.addWidget(self.include_complementary_checkbox)
        search_options_row.addStretch()
        search_options_row.addWidget(self.iupac_table_button)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_sequence_info_text)
        search_layout.addLayout(search_options_row)
        self.search_group.setLayout(search_layout)

        # Hairpin controls, hidden except in Find hairpins mode.
        self.hairpin_group = QGroupBox("Find Hairpins Options")
        hairpin_layout = QVBoxLayout()

        hairpin_param_row = QHBoxLayout()
        self.hairpin_min_stem_spin = QSpinBox()
        self.hairpin_min_stem_spin.setRange(1, 10000)
        self.hairpin_min_stem_spin.setValue(3)
        self.hairpin_min_loop_spin = QSpinBox()
        self.hairpin_min_loop_spin.setRange(1, 10000)
        self.hairpin_min_loop_spin.setValue(3)
        self.hairpin_index_base_combo = QComboBox()
        self.hairpin_index_base_combo.addItems(["1-based positions", "0-based positions"])
        self.hairpin_index_base_combo.setMinimumWidth(145)
        hairpin_param_row.addWidget(QLabel("Min stem length:"))
        hairpin_param_row.addWidget(self.hairpin_min_stem_spin)
        hairpin_param_row.addWidget(QLabel("Min loop length:"))
        hairpin_param_row.addWidget(self.hairpin_min_loop_spin)
        hairpin_param_row.addWidget(QLabel("Positions:"))
        hairpin_param_row.addWidget(self.hairpin_index_base_combo)

        hairpin_rtf_row = QHBoxLayout()
        self.hairpin_write_rtf_checkbox = QCheckBox("Write RTF file")
        self.hairpin_rtf_path_input = QLineEdit("hairpins_output.rtf")
        self.hairpin_rtf_path_input.setPlaceholderText("RTF output filename")
        self.hairpin_browse_button = QPushButton("Browse...")
        self.hairpin_browse_button.clicked.connect(self.browse_hairpin_rtf_output)
        hairpin_rtf_row.addWidget(self.hairpin_write_rtf_checkbox)
        hairpin_rtf_row.addWidget(self.hairpin_rtf_path_input)
        hairpin_rtf_row.addWidget(self.hairpin_browse_button)

        self.hairpin_module_status_label = QLabel("")
        self.hairpin_module_status_label.setWordWrap(True)
        if not HAIRPIN_MODULE_AVAILABLE:
            self.hairpin_module_status_label.setText(
                "Hairpin support is unavailable because lib/find_hairpins.py "
                "could not be imported."
            )

        hairpin_layout.addLayout(hairpin_param_row)
        hairpin_layout.addLayout(hairpin_rtf_row)
        hairpin_layout.addWidget(self.hairpin_module_status_label)
        self.hairpin_group.setLayout(hairpin_layout)

        # Buttons.
        button_layout = QHBoxLayout()
        self.run_button = QPushButton("Convert")
        self.run_button.clicked.connect(self.run_selected_mode)
        self.clear_button = QPushButton("Clear Output")
        self.clear_button.clicked.connect(self.clear_output)
        self.copy_output_button = QPushButton("Copy Output")
        self.copy_output_button.clicked.connect(self.copy_output)
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.copy_output_button)

        # Output field.
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        self.output_summary = QLabel("")
        self.output_summary.setTextFormat(Qt.RichText)
        self.output_summary.setWordWrap(True)
        self.output_text = QTextEdit()
        self.output_text.setFont(sequence_font)
        self.output_text.setReadOnly(True)
        self.output_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.output_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.output_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.output_text.viewport().installEventFilter(self)
        self.output_text.textChanged.connect(self.reset_output_position_status)
        self.output_text.selectionChanged.connect(self.show_output_selection_position)
        self.output_position_status = QLabel()
        self.output_position_status.setFrameShape(QFrame.StyledPanel)
        self.output_position_status.setContentsMargins(8, 4, 8, 4)
        self.reset_output_position_status()
        output_layout.addWidget(self.output_summary)
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)

        main_layout.addWidget(input_group)
        main_layout.addWidget(mode_row_widget)
        main_layout.addWidget(self.convert_group)
        main_layout.addWidget(self.search_group)
        main_layout.addWidget(self.hairpin_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(output_group)
        main_layout.addWidget(self.output_position_status)
        self.setLayout(main_layout)

    def eventFilter(self, watched, event) -> bool:
        if (
            watched is self.output_text.viewport()
            and event.type() == QEvent.MouseButtonPress
            and event.button() == Qt.LeftButton
        ):
            self.show_output_letter_position(event.pos())
        return super().eventFilter(watched, event)

    def reset_output_position_status(self) -> None:
        self.output_position_status.setText(
            "Click a letter or select a region in Output for 1-based positions "
            "(spaces ignored)."
        )

    def show_output_selection_position(self) -> None:
        """Report the inclusive letter range and length of a text selection."""
        selection = self.output_text.textCursor()
        if not selection.hasSelection():
            return

        document = self.output_text.document()
        selection_start = selection.selectionStart()
        start_position = 0
        if self._hairpin_output_sequence:
            first_block = document.findBlock(selection_start)
            last_block = document.findBlock(selection.selectionEnd() - 1)
            if (
                first_block != last_block
                or first_block.text() != self._hairpin_output_sequence
            ):
                self.reset_output_position_status()
                return
            start_position = first_block.position()

        selected_text = selection.selectedText()
        selected_letter_count = sum(char.isalpha() for char in selected_text)
        if not selected_letter_count:
            self.reset_output_position_status()
            return

        prefix = QTextCursor(document)
        prefix.setPosition(start_position)
        prefix.setPosition(selection_start, QTextCursor.KeepAnchor)
        preceding_letters = sum(char.isalpha() for char in prefix.selectedText())
        first_position = preceding_letters + 1
        last_position = preceding_letters + selected_letter_count
        self.output_position_status.setText(
            f"Selected positions: {first_position}-{last_position}; "
            f"length: {selected_letter_count} letters (1-based)"
        )

    def show_output_letter_position(self, point) -> None:
        """Report the letter under a mouse click, even beside a cursor boundary."""
        document = self.output_text.document()
        nearest_position = self.output_text.cursorForPosition(point).position()
        for position in (nearest_position - 1, nearest_position):
            if position < 0 or position >= document.characterCount() - 1:
                continue

            character_cursor = QTextCursor(document)
            character_cursor.setPosition(position)
            left_edge = self.output_text.cursorRect(character_cursor)
            character_cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
            character = character_cursor.selectedText()
            if not character.isalpha():
                continue

            right_edge = self.output_text.cursorRect(character_cursor)
            if right_edge.y() == left_edge.y() and right_edge.x() > left_edge.x():
                right_x = right_edge.x()
            else:
                # The following cursor can be on the next visual line after wrapping.
                right_x = left_edge.x() + self.output_text.fontMetrics().horizontalAdvance(character)
            if not (
                left_edge.y() <= point.y() < left_edge.y() + left_edge.height()
                and left_edge.x() <= point.x() < right_x
            ):
                continue

            start_position = 0
            if self._hairpin_output_sequence:
                block = character_cursor.block()
                if block.text() != self._hairpin_output_sequence:
                    break
                start_position = block.position()

            prefix_cursor = QTextCursor(document)
            prefix_cursor.setPosition(start_position)
            prefix_cursor.setPosition(
                character_cursor.position(), QTextCursor.KeepAnchor
            )
            letter_position = sum(char.isalpha() for char in prefix_cursor.selectedText())
            self.output_position_status.setText(
                f"Output letter position: {letter_position} (1-based)"
            )
            return

        self.reset_output_position_status()

    def update_visible_controls(self) -> None:
        """Show only controls related to the selected mode."""
        mode = self.mode_combo.currentText()
        is_convert = mode == MODE_CONVERT
        is_search = mode == MODE_SEARCH
        is_add = mode == MODE_ADD
        is_find_hairpins = mode == MODE_FIND_HAIRPINS

        self.convert_group.setVisible(is_convert or is_add)
        self.convert_group.setTitle("Add Options" if is_add else "Convert Options")
        self.convert_to_row_widget.setVisible(is_convert)
        self.search_group.setVisible(is_search)
        self.hairpin_group.setVisible(is_find_hairpins)
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
        elif is_search:
            self.run_button.setText("Search")
            self.output_summary.setText(
                "Search output: exact matches = yellow; reverse-complementary matches = "
                "light blue; optional complementary matches = red."
            )
        else:
            self.run_button.setText("Find hairpins")
            self.output_summary.setText(
                "Hairpin output: stem nucleotides = red; wobble pairs = underlined; "
                "maximal-stem hairpins = bold."
            )

    def update_sequence_info(self) -> None:
        """Display essential statistics for the expanded original sequence."""
        sequence, used_i_prefix_reverse = self.get_processed_original_sequence()
        self.sequence_info_text.setPlainText(
            format_original_sequence_info(sequence, used_i_prefix_reverse)
        )

    def update_search_sequence_info(self) -> None:
        """Display essential statistics for the expanded search sequence."""
        raw_sequence = self.search_input.toPlainText()
        expanded_sequence = expand_repeat_notation(raw_sequence)
        info = get_original_sequence_info(expanded_sequence)
        searchable_length = sum(char in NA_LETTERS for char in expanded_sequence)
        degenerate_count = sum(
            char in NA_LETTERS and not is_standard_base(char)
            for char in expanded_sequence
        )
        self.search_sequence_info_text.setPlainText(
            format_sequence_info(info, "Search sequence")
            + f" Searchable length={searchable_length}; Degenerate codes={degenerate_count}."
        )

    def show_iupac_code_table(self) -> None:
        """Show the possible bases and DNA/RNA complements for each search code."""
        dialog = QDialog(self)
        dialog.setWindowTitle("IUPAC code & complement")
        dialog.resize(600, 510)
        layout = QVBoxLayout(dialog)
        layout.addWidget(
            QLabel(
                "T and U are equivalent in Search. Complementary keeps the code "
                "order; reverse-complementary also reverses it."
            )
        )
        table = QTableWidget(len(IUPAC_CODE_ORDER), 4, dialog)
        table.setHorizontalHeaderLabels(
            ["Code", "Possible bases", "DNA complement", "RNA complement"]
        )
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        for row, code in enumerate(IUPAC_CODE_ORDER):
            bases = IUPAC_BASES[canonicalize_base(code)]
            possible_bases = ", ".join(
                "T/U" if base == "T" else base for base in sorted(bases)
            )
            for column, value in enumerate(
                (
                    code,
                    possible_bases,
                    DNA_COMPLEMENT_UPPER[code],
                    RNA_COMPLEMENT_UPPER[code],
                )
            ):
                table.setItem(row, column, QTableWidgetItem(value))
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)
        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=dialog)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec_()

    def run_selected_mode(self) -> None:
        """Run conversion, text addition, or search for the selected mode."""
        self.update_sequence_info()
        self.update_search_sequence_info()
        mode = self.mode_combo.currentText()
        if mode == MODE_SEARCH:
            self.search_sequence()
        elif mode == MODE_ADD:
            self.add_sequence()
        elif mode == MODE_FIND_HAIRPINS:
            self.find_hairpins_sequence()
        else:
            self.convert_sequence()

    def clear_input(self) -> None:
        """Clear the original sequence input."""
        self.sequence_input.clear()

    def clear_output(self) -> None:
        self._hairpin_output_sequence = ""
        self.output_summary.setText("")
        self.output_text.clear()
        self.output_text.setCurrentCharFormat(QTextCharFormat())

    def copy_output(self) -> None:
        """Copy the output text without search-highlight formatting."""
        QApplication.clipboard().setText(self.output_text.toPlainText())

    def set_output_plain_text(self, text: str) -> None:
        """Set unhighlighted output text and clear any previous search formatting."""
        self._hairpin_output_sequence = ""
        self.output_text.clear()
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.output_text.setTextCursor(cursor)
        self.output_text.setCurrentCharFormat(QTextCharFormat())
        self.output_text.setPlainText(text)

    def get_processed_original_sequence(self) -> Tuple[str, bool]:
        """Return the expanded original sequence, optionally applying i-prefix handling."""
        expanded_sequence = expand_repeat_notation(self.sequence_input.toPlainText())
        if not self.i_prefix_reverse_checkbox.isChecked():
            return expanded_sequence, False
        return apply_i_prefix_reverse_handling(expanded_sequence)

    def browse_hairpin_rtf_output(self) -> None:
        """Choose an RTF file path for optional hairpin export."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save hairpin RTF file",
            self.hairpin_rtf_path_input.text().strip() or "hairpins_output.rtf",
            "RTF files (*.rtf);;All files (*)",
        )
        if filename:
            self.hairpin_rtf_path_input.setText(filename)

    def convert_sequence(self) -> None:
        sequence, used_i_prefix_reverse = self.get_processed_original_sequence()
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
        elif operation == CONVERT_REVERSE_WITH_I_PREFIX:
            reversed_sequence = reverse_sequence(cleaned_sequence)
            result = add_text_before_each_base(
                apply_case_mode(reversed_sequence, case_mode), "i"
            )
        elif operation == CONVERT_TO_DNA:
            result = rna_to_dna_with_case(cleaned_sequence)
        elif operation == CONVERT_TO_RNA:
            result = dna_to_rna_with_case(cleaned_sequence)
        else:
            result = cleaned_sequence

        if operation != CONVERT_REVERSE_WITH_I_PREFIX:
            result = apply_case_mode(result, case_mode)
        self.output_summary.setText(
            "Conversion complete. "
            + format_original_sequence_info(sequence, used_i_prefix_reverse)
        )
        self.set_output_plain_text(result)

    def add_sequence(self) -> None:
        """Add the entered text before each standard base in the expanded sequence."""
        sequence, used_i_prefix_reverse = self.get_processed_original_sequence()
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
            + format_original_sequence_info(sequence, used_i_prefix_reverse)
        )
        self.set_output_plain_text(result)

    def search_sequence(self) -> None:
        self._hairpin_output_sequence = ""
        original_sequence, used_i_prefix_reverse = self.get_processed_original_sequence()
        query_sequence = self.search_input.toPlainText()
        include_complementary = self.include_complementary_checkbox.isChecked()

        (
            highlighted_html,
            exact_count,
            complementary_count,
            reverse_complementary_count,
            warnings,
        ) = highlight_search_matches(
            original_sequence,
            query_sequence,
            include_complementary=include_complementary,
            circular=self.circular_checkbox.isChecked(),
        )
        complementary_summary = (
            f"Complementary matches: {complementary_count}"
            if include_complementary
            else "Complementary matches: not searched"
        )

        def styled_count(style: str, label: str) -> str:
            return f'<span style="{MATCH_STYLE_CSS[style]}">{html.escape(label)}</span>'

        warning_text = " " + html.escape(" ".join(warnings)) if warnings else ""
        self.output_summary.setText(
            "<html><body>"
            + styled_count("exact", f"Exact matches: {exact_count}")
            + "; "
            + styled_count(
                "reverse_complementary",
                f"reverse-complementary matches: {reverse_complementary_count}",
            )
            + "; "
            + styled_count("complementary", complementary_summary)
            + ". "
            + html.escape(
                format_original_sequence_info(original_sequence, used_i_prefix_reverse)
            )
            + warning_text
            + "</body></html>"
        )
        self.output_text.setHtml(highlighted_html)

    def find_hairpins_sequence(self) -> None:
        """Find hairpin candidates in the expanded original sequence."""
        if not HAIRPIN_MODULE_AVAILABLE:
            self.output_summary.setText("Hairpin finder is unavailable.")
            self.set_output_plain_text(
                "Hairpin support requires lib/find_hairpins.py to be available."
            )
            return

        original_sequence, _ = self.get_processed_original_sequence()
        hairpin_sequence = prepare_sequence_for_hairpin_finding(original_sequence)
        if not hairpin_sequence:
            self.output_summary.setText("Please enter a sequence before finding hairpins.")
            self.set_output_plain_text("No sequence was provided.")
            return

        min_stem = self.hairpin_min_stem_spin.value()
        min_loop = self.hairpin_min_loop_spin.value()
        index_base = 0 if self.hairpin_index_base_combo.currentIndex() == 1 else 1

        hairpins = find_hairpins(
            hairpin_sequence,
            min_stem=min_stem,
            min_loop=min_loop,
            index_base=index_base,
        )
        self._hairpin_output_sequence = hairpin_sequence
        self.output_text.setHtml(
            hairpin_results_to_html(hairpin_sequence, hairpins, index_base=index_base)
        )

        max_stem_text = "N/A"
        if hairpins:
            max_stem_text = str(max(hairpin["stem_length"] for hairpin in hairpins))

        saved_text = ""
        if self.hairpin_write_rtf_checkbox.isChecked():
            filename = self.hairpin_rtf_path_input.text().strip() or "hairpins_output.rtf"
            self.hairpin_rtf_path_input.setText(filename)
            try:
                write_hairpins_rtf(
                    hairpin_sequence,
                    hairpins,
                    filename,
                    index_base=index_base,
                )
            except OSError as error:
                saved_text = f" RTF export failed: {error}"
            else:
                saved_text = f" RTF written to {filename}."

        self.output_summary.setText(
            f"Hairpins found: {len(hairpins)}; min stem={min_stem}; "
            f"min loop={min_loop}; max stem={max_stem_text}; "
            f"position indexing={index_base}-based.{saved_text}"
        )



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

    Single-character expansion is applied to IUPAC DNA/RNA letters, including
    degenerate codes such as N. Parenthesized groups can contain bases, whitespace, or other
    characters; their contents are recursively expanded before repetition.
    Digits that do not immediately follow an IUPAC letter or a parenthesized
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

        if char in NA_LETTERS:
            repeat_count, next_index = read_repeat_number(sequence, index + 1)
            if next_index != index + 1:
                result.append(char * repeat_count)
                index = next_index
                continue

        result.append(char)
        index += 1

    return "".join(result)


def apply_i_prefix_reverse_handling(sequence: str) -> Tuple[str, bool]:
    """
    Interpret single-i-prefixed bases as reverse-order notation.

    Example:
        iAiTiCiG -> GCTA

    Only one letter i immediately before a standard A/C/G/T/U base is removed.
    If no such prefixed base is found, the sequence is returned unchanged.
    """
    tokens: List[str] = []
    found_i_prefixed_base = False
    index = 0
    while index < len(sequence):
        char = sequence[index]
        if (
            char.lower() == "i"
            and index + 1 < len(sequence)
            and is_standard_base(sequence[index + 1])
        ):
            tokens.append(sequence[index + 1])
            found_i_prefixed_base = True
            index += 2
            continue

        tokens.append(char)
        index += 1

    if not found_i_prefixed_base:
        return sequence, False
    return "".join(reversed(tokens)), True


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


def format_sequence_info(
    info: Dict[str, object], sequence_label: str = "Original sequence"
) -> str:
    """Format sequence statistics as one compact line for the GUI."""
    gc_percent = info["gc_percent"]
    gc_text = "N/A" if gc_percent is None else f"{gc_percent:.2f}%"
    return (
        f"{sequence_label} info after repeat expansion: "
        f"DNA/RNA length={info['recognized_bases']}; Total length={info['total_length']}; "
        f"A={info['A']}; T/U={info['T_or_U']}; C={info['C']}; G={info['G']}; "
        f"Space/whitespace={info['whitespace']}; Other={info['other']}; "
        f"GC%={gc_text}."
    )


def format_original_sequence_info(
    sequence: str,
    used_i_prefix_reverse: bool = False,
) -> str:
    """Format original sequence stats, naming i-prefix reverse handling when used."""
    info_text = format_sequence_info(get_original_sequence_info(sequence))
    if used_i_prefix_reverse:
        return info_text.replace(
            "Original sequence info after repeat expansion:",
            "Original sequence info after repeat expansion and "
            "i-prefix reverse handling:",
        )
    return info_text


def prepare_sequence_for_hairpin_finding(sequence: str) -> str:
    """Match the standalone hairpin GUI by removing whitespace and uppercasing."""
    return "".join(char for char in sequence.upper() if not char.isspace())


def hairpin_results_to_html(
    sequence: str,
    hairpins: Sequence[Dict[str, object]],
    index_base: int = 1,
) -> str:
    """Render hairpin results with red stems, underlined wobble positions, and bold max stems."""
    escaped_sequence = html.escape(sequence)
    parts = ['<html><body style="font-family: Arial, Helvetica, sans-serif;">']

    if not hairpins:
        parts.append("<p>No hairpins found with these parameters.</p>")
        parts.append(f"<pre>{escaped_sequence}</pre>")
        parts.append("</body></html>")
        return "".join(parts)

    max_stem = max(int(hairpin["stem_length"]) for hairpin in hairpins)
    parts.append(
        '<p><b>Legend:</b> stem nucleotides are red; wobble-pair nucleotides '
        "are underlined; maximal-stem hairpins are bold.</p>"
    )

    for index, hairpin in enumerate(hairpins, start=1):
        stem_length = int(hairpin["stem_length"])
        loop_length = int(hairpin["loop_length"])
        stem1_start = int(hairpin["stem1_start"])
        stem2_start = int(hairpin["stem2_start"])
        wobble_pairs = int(hairpin["wobble_pairs"])
        gc_pairs = int(hairpin["gc_pairs"])
        at_au_pairs = int(hairpin["at_au_pairs"])
        wobble_positions = hairpin.get("wobble_positions", [])

        parts.append(
            "<p>"
            f"<b>Hairpin {index}</b>: stem length={stem_length}; "
            f"loop length={loop_length}; stem1 start={stem1_start}; "
            f"stem2 start={stem2_start}; wobble pairs={wobble_pairs}; "
            f"GC pairs={gc_pairs}; AT/AU pairs={at_au_pairs}; "
            f"wobble positions={html.escape(str(wobble_positions))}."
            "</p>"
        )
        parts.append(
            '<pre style="font-family: Courier New, Menlo, Consolas, monospace; '
            'white-space: pre-wrap;">'
        )
        if stem_length == max_stem:
            parts.append("<b>")
        parts.append(
            hairpin_sequence_to_html(
                sequence,
                hairpin,
                index_base=index_base,
            )
        )
        if stem_length == max_stem:
            parts.append("</b>")
        parts.append("</pre>")

    parts.append("</body></html>")
    return "".join(parts)


def hairpin_sequence_to_html(
    sequence: str,
    hairpin: Dict[str, object],
    index_base: int = 1,
) -> str:
    """Render one hairpin's sequence line with stem and wobble formatting."""
    stem_length = int(hairpin["stem_length"])
    stem1_start = int(hairpin["stem1_start"]) - index_base
    stem2_start = int(hairpin["stem2_start"]) - index_base
    stem_positions = set(range(stem1_start, stem1_start + stem_length)) | set(
        range(stem2_start, stem2_start + stem_length)
    )

    wobble_positions_list = hairpin.get("wobble_positions", [])
    if index_base == 1:
        wobble_positions = {int(position) - 1 for position in wobble_positions_list}
    else:
        wobble_positions = {int(position) for position in wobble_positions_list}

    parts = []
    for position, char in enumerate(sequence):
        is_stem = position in stem_positions
        is_wobble = position in wobble_positions

        styles = []
        if is_stem:
            styles.append("color:#d32f2f")
        if is_wobble:
            styles.append("text-decoration: underline")

        escaped_char = html.escape(char)
        if styles:
            parts.append(f'<span style="{"; ".join(styles)};">{escaped_char}</span>')
        else:
            parts.append(escaped_char)
    return "".join(parts)


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


def find_all_overlapping(
    haystack: str, needle: str, circular: bool = False
) -> List[int]:
    """Return starts of IUPAC-compatible matches, including boundary matches if circular."""
    if not haystack or not needle or len(needle) > len(haystack):
        return []

    # A circular match may cross the boundary once, but may not make a full lap.
    # Preserve literal matching for callers that pass non-sequence characters.
    original_bases = [
        IUPAC_BASES[char] if char in IUPAC_BASES else frozenset(char)
        for char in haystack
    ]
    pattern_bases = [
        IUPAC_BASES[char] if char in IUPAC_BASES else frozenset(char)
        for char in needle
    ]
    start_count = len(haystack) if circular else len(haystack) - len(needle) + 1
    return [
        start
        for start in range(start_count)
        if all(
            original_bases[(start + offset) % len(haystack)] & bases
            for offset, bases in enumerate(pattern_bases)
        )
    ]


def collect_match_styles(
    searchable_original: str,
    raw_indices: Sequence[int],
    exact_pattern: str,
    reverse_complementary_pattern: str,
    complementary_pattern: str,
    circular: bool = False,
) -> Tuple[Dict[int, str], int, int, int]:
    """Collect separate highlight styles and counts for the three match classes."""
    styles: Dict[int, str] = {}

    complementary_starts = find_all_overlapping(
        searchable_original, complementary_pattern, circular=circular
    )
    for start in complementary_starts:
        for offset in range(len(complementary_pattern)):
            styles[raw_indices[(start + offset) % len(raw_indices)]] = "complementary"

    reverse_complementary_starts = find_all_overlapping(
        searchable_original, reverse_complementary_pattern, circular=circular
    )
    for start in reverse_complementary_starts:
        for offset in range(len(reverse_complementary_pattern)):
            # Reverse-complementary matches take priority over complementary matches.
            styles[raw_indices[(start + offset) % len(raw_indices)]] = "reverse_complementary"

    exact_starts = find_all_overlapping(searchable_original, exact_pattern, circular=circular)
    for start in exact_starts:
        for offset in range(len(exact_pattern)):
            # Exact matches take priority over both transformed match classes.
            styles[raw_indices[(start + offset) % len(raw_indices)]] = "exact"

    return (
        styles,
        len(exact_starts),
        len(complementary_starts),
        len(reverse_complementary_starts),
    )


def text_to_highlighted_html(raw_sequence: str, styles: Dict[int, str]) -> str:
    """Convert raw text to HTML with distinct colors for each match class."""
    span_for_style = {
        style: f'<span style="{css}">'
        for style, css in MATCH_STYLE_CSS.items()
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


def highlight_search_matches(
    raw_sequence: str,
    query_sequence: str,
    include_complementary: bool = False,
    circular: bool = False,
) -> Tuple[str, int, int, int, List[str]]:
    """
    Highlight exact, reverse-complementary, and optional complementary matches.

    Search expands compact repeats, ignores non-sequence characters, treats T
    and U as equivalent, and interprets IUPAC codes as compatible base sets.
    Circular searches allow a
    match to cross the end/start boundary once. Exact query matches are yellow,
    reverse-complementary matches are light blue, and complementary matches are
    red when include_complementary is True.
    """
    searchable_original, raw_indices = extract_searchable_sequence(raw_sequence)
    exact_pattern, _ = extract_searchable_sequence(
        expand_repeat_notation(query_sequence)
    )
    warnings: List[str] = []

    if not exact_pattern:
        warnings.append("Please enter a search sequence containing nucleic-acid letters.")
        return text_to_highlighted_html(raw_sequence, {}), 0, 0, 0, warnings

    complement_pattern = complement_canonical_dna(exact_pattern)
    reverse_complement_pattern = reverse_complement_canonical_dna(exact_pattern)
    reverse_complementary_search_pattern = reverse_complement_pattern
    complementary_search_pattern = ""

    if reverse_complement_pattern == exact_pattern:
        reverse_complementary_search_pattern = ""
        warnings.append(
            "The reverse-complementary pattern is identical to the exact pattern, so "
            "those matches are counted and shown as yellow exact matches."
        )

    if include_complementary:
        if complement_pattern == exact_pattern:
            warnings.append(
                "The complementary pattern is identical to the exact pattern, so those "
                "matches are counted and shown as yellow exact matches."
            )
        elif complement_pattern == reverse_complement_pattern:
            warnings.append(
                "The complementary pattern is identical to the reverse-complementary "
                "pattern, so those matches are counted and shown as light-blue "
                "reverse-complementary matches."
            )
        else:
            complementary_search_pattern = complement_pattern

    (
        styles,
        exact_count,
        complementary_count,
        reverse_complementary_count,
    ) = collect_match_styles(
        searchable_original,
        raw_indices,
        exact_pattern,
        reverse_complementary_search_pattern,
        complementary_search_pattern,
        circular=circular,
    )
    return (
        text_to_highlighted_html(raw_sequence, styles),
        exact_count,
        complementary_count,
        reverse_complementary_count,
        warnings,
    )


def parse_command_line(arguments: Sequence[str]) -> None:
    """Parse command-line options, including terminal version reporting."""
    parser = argparse.ArgumentParser(
        description="Convert, annotate, and search nucleic-acid sequence text."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{APP_NAME} v{APP_VERSION}",
    )
    parser.parse_args(arguments)


def main() -> None:
    """Start the GUI application."""
    parse_command_line(sys.argv[1:])
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    if APP_RESOURCES_AVAILABLE:
        app.setWindowIcon(QIcon(APP_ICON_RESOURCE))
    gui = NAToolsGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
