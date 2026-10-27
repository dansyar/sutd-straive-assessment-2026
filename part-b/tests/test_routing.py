"""Authored development regressions; never count these as unseen evidence."""
import unittest

from corpus import load_corpus
from engine import TextModel, triage


class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = TextModel(load_corpus()[0])

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
