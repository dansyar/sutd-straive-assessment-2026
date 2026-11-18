"""Authored development regressions; never count these as unseen evidence."""
import unittest

from corpus import load_corpus
from live_engine import TextModel, triage


class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.development, _, _ = load_corpus()
        cls.model = TextModel(cls.development)

    def check_cases(self, cases, review=False):
        for text, category, urgent in cases:
            for method in ["rules", "learned"]:
                for policy in ["standard", "sensitive"]:
                    with self.subTest(text=text, method=method, policy=policy):
                        result = triage(text, self.model, method, policy)
                        self.assertEqual(result["category"], category)
                        self.assertEqual(result["urgent"], urgent)
                        if review:
                            self.assertTrue(result["review"])

    def test_critical_system_consequence_overrides_paperwork_and_transport(self):
        self.check_cases([
            ("A licence number is missing from the clearance packet for the replacement fire-alarm controller. The building's alarm remains out of service with no temporary alarm, and customs will not release the controller until the licence is supplied.", "safety", True),
            ("The permit for a replacement fire pump motor has expired. The fire pump is offline and there is no backup protection.", "safety", True),
            ("A delayed control board is needed for the medical gas alarm. The alarm remains disabled while the supplier arranges delivery.", "safety", True),
            ("The emergency stop is unavailable. A missing actuator is preventing restoration, even though the carrier calls it a delivery delay.", "safety", True),
            ("The vehicle carrying a replacement emergency ventilation motor is delayed. The destination's ventilation has failed and staff cannot remain safely.", "safety", True),
        ], review=True)

    def test_operational_cause_and_confirmed_location_win_over_incidental_words(self):
        self.check_cases([
            ("The customer alleges theft, but the depot confirms the sealed carton is still in the dispatch cage. Arrange its delayed departure.", "delay", False),
            ("A punctured tyre delayed the vehicle. The complete load is intact at our depot for redelivery; no safety system is affected.", "delay", False),
            ("The chilled cartons are scuffed. Product temperature remained within 2 to 5 C at 4 C throughout; the claim concerns packaging damage only.", "damage", False),
            ("A shipping invoice attached to the case shows the value of the cracked picture frame. The fragments are secured; the request is a cargo repair claim.", "damage", False),
            ("We cannot find the commercial invoice. All goods arrived intact; customs needs a corrected copy of the document.", "documentation", False),
        ])

    def test_document_absence_and_cargo_loss_route_separately(self):
        original = next(row["text"] for row in self.development if row["id"] == "RLY-27397")
        self.check_cases([
            (original, "documentation", False),
            ("The consignment remains at customs. Please send the missing bill of lading.", "documentation", False),
            ("The invoice for this shipment is missing. The goods are on the loading dock.", "documentation", False),
            ("Customs held the cargo because the airway bill is missing. The cargo is still at the terminal.", "documentation", False),
            ("The consignment remains at customs as it is missing cargo paperwork.", "documentation", False),
            ("We could not locate the packing list for this cargo. The cargo remains in our warehouse.", "documentation", False),
            ("The invoice is missing. The pallet could not be located earlier, but the full shipment is intact at the depot.", "documentation", False),
            ("The invoice is attached. Our warehouse cannot locate the shipment.", "missing", False),
            ("The paperwork has arrived, but one pallet is missing from the consignment.", "missing", False),
            ("The invoice is missing. Nobody can locate the cargo.", "missing", False),
            ("The shipment has a missing invoice but the pallet cannot be found.", "missing", False),
            ("The chilled shipment and its commercial invoice are missing. No one can confirm its location or temperature.", "missing", False),
            ("The parcel containing the missing invoice was stolen from the warehouse yesterday.", "missing", False),
            ("Neither the missing paperwork nor the cargo itself could be located.", "missing", False),
            ("The parcel containing the paperwork is missing. The warehouse cannot find it.", "missing", False),
            ("A parcel with a commercial invoice is missing. The warehouse cannot find it.", "missing", False),
            ("The invoice is not missing. The warehouse cannot locate the shipment.", "missing", False),
        ])
        for method in ("rules", "learned"):
            prediction = triage(original, self.model, method)
            self.assertEqual(prediction["rationale"]["team"], "Missing commercial invoice")

    def test_document_gap_cannot_hide_live_cold_chain_or_safety_consequences(self):
        self.check_cases([
            ("Customs cannot release the crate due to a missing invoice. The fire alarm is offline until its contents are installed.", "safety", True),
            ("Customs held the refrigerated shipment because the invoice is missing. The reefer now reads 25 C against the allowed 2 to 8 C.", "temperature", True),
        ], review=True)

    def test_rationale_quotes_actual_temperature_limit_and_explains_review(self):
        original = next(row["text"] for row in self.development if row["id"] == "RLY-82374")
        for text, urgency_reason in [
            (original, "19°C exceeds the 8°C limit"),
            (original.replace("19 C", "-0.5 C"), "-0.5°C is below the 2°C limit"),
            (original.replace("19 C", "8.1 C"), "8.1°C exceeds the 8°C limit"),
        ]:
            for method in ("rules", "learned"):
                for policy in ("standard", "sensitive"):
                    with self.subTest(text=text, method=method, policy=policy):
                        prediction = triage(text, self.model, method, policy)
                        self.assertTrue(prediction["urgent"] and prediction["review"])
                        why = prediction["rationale"]
                        self.assertEqual(why["urgency"], urgency_reason)
                        self.assertEqual(why["review"], "Confirm current exposure")
                        self.assertTrue(all(not reason.endswith(".") for reason in why.values() if reason))

    def test_temperature_rationale_keeps_units_history_and_uncertainty(self):
        cases = [
            ("The reefer is at 58 F against the required 2 C to 8 C range. Cargo remains on board.",
             "58°F (≈14.44°C) exceeds the 8°C limit", "Confirm current exposure"),
            ("The current cargo temperature is 12 C. The consignee says the permitted range is 2 to 8 C, but the sender lists a range of 10 to 15 C.",
             "12°C exceeds one stated limit of 8°C", "Check which limits apply"),
            ("Yesterday the refrigerated cargo reached 19 C. The current verified temperature is 4 C. The permitted limits are 2 to 8 C.",
             "Earlier reading of 19°C exceeds the 8°C limit", "Confirm exposure history"),
        ]
        for text, urgent, review in cases:
            for method in ("rules", "learned"):
                with self.subTest(text=text, method=method):
                    prediction = triage(text, self.model, method)
                    self.assertTrue(prediction["urgent"] and prediction["review"])
                    self.assertEqual(prediction["rationale"]["urgency"], urgent)
                    self.assertEqual(prediction["rationale"]["review"], review)

        reversed_limits = "Current cargo temperature is 19 C. The specified product range is 8 to 2 C."
        cleared = "A faulty display flashed 30 C, but two independent probes verified stable 5 C. The sensor has been replaced."
        for method in ("rules", "learned"):
            predicted = triage(reversed_limits, self.model, method)
            self.assertEqual(predicted["rationale"]["review"], "Check the stated temperature limits")
            self.assertNotIn("exceeds", predicted["rationale"]["urgency"] or "")
            predicted = triage(cleared, self.model, method)
            self.assertFalse(predicted["urgent"])
            self.assertIsNone(predicted["rationale"]["urgency"])
            self.assertEqual(predicted["rationale"]["team"], "Sensor replaced")

    def test_unconfirmed_cold_chain_custody_is_not_a_routine_delay(self):
        text = "A chilled load may have been left unrefrigerated overnight. The logger is unreadable and nobody has confirmed whether the stock is still exposed."
        for method in ["rules", "learned"]:
            result = triage(text, self.model, method, "sensitive")
            self.assertEqual(result["category"], "temperature")
            self.assertTrue(result["urgent"])
            self.assertTrue(result["review"])

    def test_live_physical_hazard_precedes_temperature_or_missing_goods(self):
        self.check_cases([
            ("A sweet-smelling puddle from the chilled pallet is spreading toward live electrical equipment. People remain beside it.", "safety", True),
            ("The driver reports being threatened in the cab. The chilled cargo also has an incomplete temperature log.", "safety", True),
            ("A power bank carton is hissing and expanding beside the packing workers.", "safety", True),
            ("The isolation valve is missing. Water is still entering an electrical service room while staff wait for the replacement.", "safety", True),
        ], review=True)

    def test_closed_or_negated_hazards_do_not_create_a_new_emergency(self):
        self.check_cases([
            ("The fire alarm has been restored and is now fully operational. The incorrect invoice for its replacement controller needs correction.", "documentation", False),
            ("No person has been injured and no smoke is coming from the load. The dented cargo is secured and the claim concerns cosmetic damage.", "damage", False),
            ("The frozen batch briefly exceeded specification during transit. It is now isolated in a verified -18 C store; quality needs the recorded excursion for disposition.", "temperature", False),
            ("The site is secure after last week's lock incident. The lock was replaced and the security incident is closed; file the final report.", "safety", False),
        ])


if __name__ == "__main__":
    unittest.main()
