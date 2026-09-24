"""Regression checks for degenerate and circular sequence search."""

import unittest

from NA_text_converter_finder import (
    CANONICAL_DNA_COMPLEMENT,
    DNA_COMPLEMENT_UPPER,
    IUPAC_BASES,
    IUPAC_CODE_ORDER,
    RNA_COMPLEMENT_UPPER,
    canonicalize_base,
    expand_repeat_notation,
    find_all_overlapping,
    highlight_search_matches,
)


class SearchTests(unittest.TestCase):
    def test_every_iupac_complement_preserves_possible_bases(self):
        for code in IUPAC_CODE_ORDER:
            with self.subTest(code=code):
                bases = IUPAC_BASES[canonicalize_base(code)]
                expected = frozenset(CANONICAL_DNA_COMPLEMENT[base] for base in bases)
                for complement_map in (DNA_COMPLEMENT_UPPER, RNA_COMPLEMENT_UPPER):
                    complement_code = canonicalize_base(complement_map[code])
                    self.assertEqual(IUPAC_BASES[complement_code], expected)

    def test_degenerate_repeats_and_matching(self):
        self.assertEqual(expand_repeat_notation("GAGN5CTC"), "GAGNNNNNCTC")
        self.assertEqual(
            highlight_search_matches("GAGAAAAACTC", "GAGN5CTC")[1:4], (1, 0, 0)
        )
        self.assertEqual(expand_repeat_notation("(RY)2"), "RYRY")
        self.assertEqual(find_all_overlapping("ACGT", "RYSW"), [0])
        self.assertEqual(find_all_overlapping("AGCT", "RYSW"), [])

    def test_original_degenerate_codes_and_t_u_equivalence(self):
        self.assertEqual(highlight_search_matches("aR u", "AGT")[1:4], (1, 0, 0))
        self.assertEqual(highlight_search_matches("aR u", "ACT")[1:4], (0, 0, 1))

    def test_circular_exact_match_highlights_both_ends(self):
        self.assertEqual(find_all_overlapping("ACGT", "GTAC"), [])
        self.assertEqual(find_all_overlapping("ACGT", "GTAC", circular=True), [2])
        highlighted, exact, _, _, _ = highlight_search_matches(
            "AC GT", "GTAC", circular=True
        )
        self.assertEqual(exact, 1)
        self.assertEqual(highlighted.count("background-color:#fff176"), 2)
        self.assertEqual(
            highlight_search_matches("ACGT", "GTAC", circular=False)[1], 0
        )

    def test_reverse_complement_can_cross_boundary(self):
        self.assertEqual(
            highlight_search_matches("AACTG", "TTCA", circular=True)[1:4],
            (0, 0, 1),
        )
        self.assertEqual(
            highlight_search_matches("AACTG", "TTCA", circular=False)[1:4],
            (0, 0, 0),
        )

    def test_degenerate_complementary_match_can_cross_boundary(self):
        self.assertEqual(
            highlight_search_matches(
                "ACGT", "CATN", include_complementary=True, circular=True
            )[1:4],
            (0, 1, 0),
        )

    def test_query_cannot_span_more_than_one_turn(self):
        self.assertEqual(find_all_overlapping("ACG", "ACGA", circular=True), [])

    def test_plain_text_matcher_remains_usable(self):
        self.assertEqual(find_all_overlapping("banana", "ana"), [1, 3])


if __name__ == "__main__":
    unittest.main()
