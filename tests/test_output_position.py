"""GUI checks for click-to-position behavior in the output editor."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from NA_text_converter_finder import NAToolsGUI, MODE_SEARCH, hairpin_results_to_html


class OutputPositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.gui = NAToolsGUI()
        self.gui.show()
        self.app.processEvents()

    def tearDown(self):
        self.gui.close()

    def click_character(self, position):
        editor = self.gui.output_text
        cursor = QTextCursor(editor.document())
        cursor.setPosition(position)
        left = editor.cursorRect(cursor)
        cursor.setPosition(position + 1)
        right = editor.cursorRect(cursor)
        width = (
            right.x() - left.x()
            if right.y() == left.y() and right.x() > left.x()
            else editor.fontMetrics().horizontalAdvance("A")
        )
        point = QPoint(left.x() + max(1, width // 2), left.y() + left.height() // 2)
        QTest.mouseClick(editor.viewport(), Qt.LeftButton, pos=point)
        self.app.processEvents()
        return self.gui.output_position_status.text()

    def test_plain_output_skips_spaces_and_newlines(self):
        self.gui.set_output_plain_text("AC GT\nTTA")
        self.assertIn("position: 4", self.click_character(4))
        self.assertIn("Click a letter", self.click_character(2))
        self.assertIn("position: 5", self.click_character(6))

    def test_wrapped_output_uses_sequence_position(self):
        self.gui.set_output_plain_text("A" * 200)
        editor = self.gui.output_text
        document = editor.document()
        first_line_y = editor.cursorRect(QTextCursor(document)).y()
        wrap_position = next(
            position
            for position in range(1, 200)
            if editor.cursorRect(self.cursor_at(position)).y() != first_line_y
        )
        self.assertIn(
            f"position: {wrap_position}", self.click_character(wrap_position - 1)
        )
        self.assertIn(
            f"position: {wrap_position + 1}", self.click_character(wrap_position)
        )

    def cursor_at(self, position):
        cursor = QTextCursor(self.gui.output_text.document())
        cursor.setPosition(position)
        return cursor

    def select_range(self, start, end):
        cursor = self.cursor_at(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        self.gui.output_text.setTextCursor(cursor)
        self.app.processEvents()
        return self.gui.output_position_status.text()

    def test_selection_reports_inclusive_letter_range_and_length(self):
        self.gui.set_output_plain_text("AC GT\nTTA")
        self.assertIn(
            "Selected positions: 2-5; length: 4 letters",
            self.select_range(1, 7),
        )

    def test_highlighted_search_output(self):
        self.gui.mode_combo.setCurrentText(MODE_SEARCH)
        self.gui.sequence_input.setPlainText("AC GT")
        self.gui.search_input.setPlainText("CGT")
        self.gui.search_sequence()
        self.assertIn("position: 3", self.click_character(3))
        self.assertIn(
            "Selected positions: 2-3; length: 2 letters",
            self.select_range(1, 4),
        )

    def test_hairpin_sequence_starts_at_one(self):
        sequence = "GGGAAACCC"
        self.gui._hairpin_output_sequence = sequence
        self.gui.output_text.setHtml(hairpin_results_to_html(sequence, [], 1))
        self.app.processEvents()
        description = self.gui.output_text.document().firstBlock()
        self.assertIn("Click a letter", self.click_character(description.position()))
        sequence_block = description.next()
        self.assertIn("position: 5", self.click_character(sequence_block.position() + 4))
        self.assertIn(
            "Selected positions: 3-7; length: 5 letters",
            self.select_range(sequence_block.position() + 2, sequence_block.position() + 7),
        )


if __name__ == "__main__":
    unittest.main()
