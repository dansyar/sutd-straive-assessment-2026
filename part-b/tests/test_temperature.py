"""Authored regression cases, not an independent or operational test set."""
import unittest

from corpus import load_corpus
from engine import TextModel, triage, routing_queue


class TemperatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.development, _, _ = load_corpus()
        cls.model = TextModel(cls.development)

    def predictions(self, text):
        for method in ["rules", "learned"]:
            for policy in ["standard", "sensitive"]:
                yield method, policy, triage(text, self.model, method, policy)

    def test_active_excursions_use_actual_limits_and_keep_review(self):
        cases = [
            "The cold compartment is at 19 C with sensitive cargo still inside. Product limits are 2 to 8 C and immediate isolation is needed.",
            "Cargo is currently at 11°C; its required range is 1–6°C. The shipment remains in the compartment.",
            "The freezer cargo is now at -2 C against a required -20 to -15 C range. Goods are still inside.",
            "The product is at 29 F. Its required range is 35 to 46 F. Cargo remains on board.",
            "The cold compartment is at 8.1 C, just outside the required 2-8 C range. Cargo is still exposed.",
            "The reefer is at 58 F against a required 2 C to 8 C range. Cargo is still inside.",
            "The cold compartment is at -0.5 C; product limits are +1 to +5 C. Goods remain inside.",
            "A 1 to 5 C product is now at 12 C after the door was left open. Stock has not been isolated.",
            "A 35 to 46 F shipment is at 59 F and remains in the vehicle.",
        ]
        for text in cases:
            for method, policy, pred in self.predictions(text):
                with self.subTest(text=text, method=method, policy=policy):
                    self.assertEqual(pred["category"], "temperature")
                    self.assertTrue(pred["urgent"])
                    self.assertTrue(pred["review"])
                    self.assertEqual(routing_queue(pred), "urgent")

    def test_contained_or_normal_temperature_is_not_a_new_emergency(self):
        cases = [
            "The cold compartment is at 4 C and cargo is still inside. Product limits are 2 to 8 C.",
            "The refrigerated cargo is at 41 F against a required 35 to 46 F range.",
            "The freezer is at -18 C against a required -20 to -15 C range. Goods are stable.",
            "The cold compartment is at 2 C. Product limits are 2 to 8 C; readings are stable.",
            "The refrigerated cargo is at 8 C. Product limits are 2 to 8 C; readings are stable.",
            "Last week's cold-chain excursion reached 19 C against a 2 to 8 C limit. The goods are now quarantined under the quality team's control. This request is for archive records only.",
            "A faulty display flashed 30 C, but two independent probes verified stable 5 C. The sensor has been replaced.",
            "A temperature warning occurred during an empty return trip. No product was on the vehicle.",
            "The temperature monitor battery is low. Current probes confirm 4 C against a required 2 to 8 C range.",
        ]
        for text in cases:
            for method, policy, pred in self.predictions(text):
                with self.subTest(text=text, method=method, policy=policy):
                    self.assertEqual(pred["category"], "temperature")
                    self.assertFalse(pred["urgent"])

    def test_missing_or_conflicting_measurements_require_review(self):
        cases = [
            "The cold compartment contains cargo at 19 C. No product limits were provided.",
            "The cold compartment has a required 2 to 8 C range. The current logger reading is unreadable.",
            "The cold compartment has two readings, 5 C and 19 C, against a required 2 to 8 C range. Neither sensor has been verified.",
            "The cold compartment is at 19 C. Product limits are 8 to 2 C.",
            "The refrigerated cargo is at 293 K. Its permitted limits are 275 to 281 K.",
        ]
        for text in cases:
            for method, policy, pred in self.predictions(text):
                with self.subTest(text=text, method=method, policy=policy):
                    self.assertEqual(pred["category"], "temperature")
                    self.assertTrue(pred["review"])

    def test_loss_of_cooling_and_current_hazards_take_priority(self):
        cases = [
            ("Ice cream is softening in a trailer whose compressor has failed. The goods remain on board without working cooling.", "temperature"),
            ("The chilled cargo is warming and the backup chiller has failed. There is no spare cold room.", "temperature"),
            ("Smoke is coming from a battery beside the refrigerated cargo. The cold compartment reads 19 C against a required 2 to 8 C range.", "safety"),
        ]
        for text, category in cases:
            for method, policy, pred in self.predictions(text):
                with self.subTest(text=text, method=method, policy=policy):
                    self.assertEqual(pred["category"], category)
                    self.assertTrue(pred["urgent"])
                    self.assertTrue(pred["review"])

    def test_trigger_report_is_generalized_not_matched_by_identifier(self):
        original = next(r for r in self.development if r["id"] == "RLY-82374")
        for text in [original["text"], original["text"].replace("19 C", "13 C"), original["text"].replace("19 C", "-3 C")]:
            for method, policy, pred in self.predictions(text):
                with self.subTest(method=method, policy=policy, text=text):
                    self.assertEqual(pred["team"], "Cold-chain quality")
                    self.assertTrue(pred["urgent"])
                    self.assertTrue(pred["review"])

    def test_controlled_temperature_does_not_override_a_packaging_claim(self):
        cases = [
            "The chilled carton has a cosmetic tear. The seal is intact, the recorded temperature stayed in range and the claim concerns the packaging only.",
            "The refrigerated cargo has scuffed packaging. The temperature is normal and the claim is only for the packaging.",
        ]
        for text in cases:
            for method, policy, pred in self.predictions(text):
                with self.subTest(text=text, method=method, policy=policy):
                    self.assertEqual(pred["category"], "damage")
                    self.assertFalse(pred["urgent"])

    def test_negated_physical_hazard_does_not_override_temperature_evidence(self):
        text = "No smoke is coming from the unit. The cold compartment is at 19 C against a required 2 to 8 C range, with cargo still inside."
        for method, policy, pred in self.predictions(text):
            with self.subTest(method=method, policy=policy):
                self.assertEqual(pred["category"], "temperature")
                self.assertTrue(pred["urgent"])
