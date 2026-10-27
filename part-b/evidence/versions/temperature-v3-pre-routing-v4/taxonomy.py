"""Scenario assumptions, not a real operator's service-level agreements."""
CATEGORIES = {
    "delay": {"label": "Delivery delay", "team": "Transport operations"},
    "missing": {"label": "Missing shipment", "team": "Shipment tracing"},
    "damage": {"label": "Cargo damage", "team": "Claims & recovery"},
    "temperature": {"label": "Temperature issue", "team": "Cold-chain quality"},
    "safety": {"label": "Safety & security", "team": "Safety & security"},
    "documentation": {"label": "Documents & customs", "team": "Trade compliance"},
}
REVIEW_CATEGORY = "unclear"
POLICIES = {
    "standard": {"label": "Standard", "urgent_miss_cost": 30,
                 "similarity_floor": .12, "margin_floor": .035, "urgent_margin": .025},
    "sensitive": {"label": "Higher urgency sensitivity", "urgent_miss_cost": 100,
                  "similarity_floor": .17, "margin_floor": .065, "urgent_margin": -.025},
}
COSTS = {"wrong_route": 6, "false_urgent": 2, "human_review": 1}

GUIDE = [
    ("Delivery delay", "Shipment is located and intact, but arrival or handover is late. Transport operations."),
    ("Missing shipment", "Cargo or contents cannot be found, are short, or were delivered to an unconfirmed place. Shipment tracing."),
    ("Cargo damage", "Physical damage is the main issue and there is no continuing hazard. Claims & recovery."),
    ("Temperature issue", "Cold-chain performance, excursion evidence or temperature records are the main issue. Cold-chain quality."),
    ("Safety & security", "Injury, unsafe conditions, hazardous substances, fire, theft, threats or site security. Safety & security."),
    ("Documents & customs", "Invoices, permits, declarations, clearance or proof of delivery. Trade compliance."),
    ("Unclear", "Not enough information to identify a primary category. Do not guess."),
    ("Urgent", "Immediate attention: an ongoing physical/security hazard, uncontained temperature excursion, or a shipment blocking restoration of a critical safety system."),
    ("Routine", "No immediate threat is described. A loud subject line or a customer's inconvenience alone does not make a report urgent."),
    ("Unclear urgency", "The report lacks the facts needed to judge urgency. Do not treat missing information as proof of safety."),
    ("Needs clarification: Yes", "Material facts are missing, accounts conflict, or multiple issues need separate handling. Urgency alone does not imply missing information."),
    ("Multiple issues", "Choose the issue with the greatest immediate consequence. Prefer an active safety hazard to a temperature issue, then the main operational cause. Mark Yes if separate handling or facts are needed."),
]
