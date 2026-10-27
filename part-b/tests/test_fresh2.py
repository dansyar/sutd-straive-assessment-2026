"""Protect fresh-set independence and integrity without changing its judgments."""
import copy
import unittest
from unittest.mock import patch

import fresh2_evaluate as fresh


class Fresh2IntegrityTests(unittest.TestCase):
    def test_complete_frozen_review_preserves_returned_judgments_and_unknowns(self):
        rows, freeze, registration, _, _ = fresh.fresh_rows()
        self.assertEqual(len(rows), registration["planned_n"])
        self.assertEqual(freeze["count"], len(rows))
        self.assertTrue(any(r["urgent"] is None for r in rows))
        self.assertTrue(any(r["category"] == "unclear" for r in rows))
        self.assertTrue(all(r["reviewer_type"] == "agent" for r in rows))

    def test_changed_candidate_or_labels_cannot_be_scored(self):
        original = fresh.sha256
        for target in [fresh.ROOT / "engine.py", fresh.LABELS]:
            with self.subTest(target=target.name), patch.object(
                fresh, "sha256", side_effect=lambda path: "tampered" if path == target else original(path)
            ), self.assertRaises(ValueError):
                fresh.fresh_rows()

    def test_missing_duplicate_or_invalid_judgments_are_rejected(self):
        _, _, _, reports, _ = fresh.check_candidate()
        labels = fresh.read_jsonl(fresh.LABELS)
        duplicate = [*labels[:-1], labels[0]]
        invalid = copy.deepcopy(labels)
        invalid[0]["urgent"] = "false"
        for candidate in [labels[:-1], duplicate, invalid]:
            with self.assertRaises(ValueError):
                fresh.validate_judgments(candidate, reports)


if __name__ == "__main__":
    unittest.main()
