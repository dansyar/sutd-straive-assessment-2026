"""Active routing policy using the frozen model and safety checks."""
from __future__ import annotations

import re
import time

from engine import (
    CLARIFY, SENSITIVE_SIGNALS, TEMPERATURE_RANGE, TEMPERATURE_READING,
    TextModel, celsius, content_text, issue_check, routing_queue, rule_prediction,
    temperature_check,
)
from taxonomy import CATEGORIES, POLICIES

ENGINE_VERSION = "routing-v6"

CARGO = r"(?:parcel|shipment|consignment|cargo|pallet|load|carton|case|goods|stock|freight)"
DOCUMENT = (r"(?:commercial invoice|invoice number|invoice|air ?waybill|airway bill|bill of lading|packing list|"
            r"customs declaration|clearance document|delivery receipt|proof of delivery|"
            r"transport document|shipping document|customs document|document|waybill|"
            r"cargo paperwork|shipping paperwork|paperwork|certificate|licen[cs]e|permit|manifest)")
MISSING_DOCUMENT = re.compile(
    rf"\b(?P<subject>{DOCUMENT})\b(?: (?:for|of) (?:the |this |that )?{CARGO}\b)?"
    rf" (?:is |are |was |were |has gone |remains? )?(?:still )?"
    rf"(?:(?P<denial>not )?(?:missing|absent)|not attached|not supplied)\b"
    rf"|\b(?:missing|absent|(?:cannot|can't|could not|unable to) (?:find|locate)) "
    rf"(?:the |a |an |its |our )?(?P<object>{DOCUMENT})\b"
)
CARGO_CARRYING_DOCUMENT = re.compile(rf"\b{CARGO} (?:with|without|carrying|holding|containing) (?:the |a |an |its )?$")
CARGO_JOINED_TO_DOCUMENT = re.compile(rf"\b{CARGO}s?\s*,?\s+and (?:its |their |the |an? )?$")
CARGO_EXPLICIT_LOSS = re.compile(
    rf"\b{CARGO}s?(?: (?:with|without|carrying|holding|containing) (?:the |its )?paperwork)? "
    rf"(?:still |currently )?(?:(?:(?:cannot|can't|could not) (?:yet )?be|"
    rf"(?:has|have) not (?:yet )?been) (?:found|located|accounted for)|"
    rf"(?:was|were|has been|have been) stolen)\b"
    rf"|\bneither\b[^.!?;\n]{{0,90}}\bnor (?:the |our |its )?{CARGO}s?(?: itself)? "
    rf"(?:can|could) be (?:found|located|accounted for)\b"
)
READING_BOUNDARY = re.compile(r"[!?;\n]|\.(?!\d)|\b(?:but|however|while)\b")
EARLIER_READING = re.compile(r"\b(?:yesterday|earlier|last (?:night|week|month)|previous(?:ly)?|historical)\b")


def document_issue(text):
    """Keep named paperwork gaps out of the cargo-loss heuristics."""
    lower = content_text(text).lower()
    document = None

    def mask(match):
        nonlocal document
        prefix = lower[max(0, match.start() - 55):match.start()]
        if match["subject"] and (CARGO_CARRYING_DOCUMENT.search(prefix) or CARGO_JOINED_TO_DOCUMENT.search(prefix)):
            return match[0]
        if not (match["denial"] or re.search(r"\b(?:not|never) $", prefix)):
            document = document or match["subject"] or match["object"]
        return "paperwork"

    # Reassess the remaining facts without treating missing paperwork as cargo loss.
    masked = MISSING_DOCUMENT.sub(mask, lower)
    if document:
        masked = CARGO_EXPLICIT_LOSS.sub("cargo is missing", masked)
    issue = issue_check(masked if masked != lower else text)
    if not document or (issue and (issue["active_safety"] or issue["category"] == "missing")):
        return issue

    return {"category": "documentation", "urgent": False, "active_safety": False, "reasons": [],
            "signals": [f"Missing {document}"]}


def temperature_excursion(text):
    """Describe the same reported reading and limit that triggered escalation."""
    lower = content_text(text).lower().replace("–", "-").replace("—", "-").replace("−", "-")
    lower = re.sub(r"\bminus\s+(?=\d)", "-", lower)
    ranges = list(TEMPERATURE_RANGE.finditer(lower))
    bounds = []
    for limits in ranges:
        low_unit = limits["low_unit"] or limits["high_unit"]
        low = celsius(limits["low"], low_unit)
        high = celsius(limits["high"], limits["high_unit"])
        if low <= high:
            bounds.append((limits, low, high, low_unit))
    different_limits = len({(round(low, 6), round(high, 6)) for _, low, high, _ in bounds}) > 1

    def degrees(value, unit):
        return f"{value}°{'F' if 'f' in unit else 'C'}"

    for reading in TEMPERATURE_READING.finditer(lower):
        if any(reading.start() < limits.end() and reading.end() > limits.start() for limits in ranges):
            continue
        value = celsius(reading["value"], reading["unit"])
        for limits, low, high, low_unit in bounds:
            if value < low - 1e-8:
                direction, limit, unit = "is below", limits["low"], low_unit
            elif value > high + 1e-8:
                direction, limit, unit = "exceeds", limits["high"], limits["high_unit"]
            else:
                continue

            measured = degrees(reading["value"], reading["unit"])
            if ("f" in reading["unit"]) != ("f" in unit):
                equivalent = round(value * 9 / 5 + 32 if "f" in unit else value, 2)
                if equivalent != float(limit):
                    measured += f" (≈{degrees(f'{equivalent:g}', unit)})"
            context = (READING_BOUNDARY.split(lower[:reading.start()])[-1] + " " +
                       READING_BOUNDARY.split(lower[reading.end():], maxsplit=1)[0])
            earlier = EARLIER_READING.search(context)
            if earlier:
                measured = f"Earlier reading of {measured}"
            bound = degrees(limit, unit)
            if different_limits:
                return f"{measured} {direction} one stated limit of {bound}", "Check which limits apply"
            return f"{measured} {direction} the {bound} limit", "Confirm exposure history" if earlier else None
    return "Reading outside stated limits", None


REVIEW_HINTS = {
    "Multiple temperature readings need reconciliation.": "Check conflicting temperature readings",
    "The stated temperature limits are reversed; confirm them.": "Check the stated temperature limits",
    "A usable current temperature reading is missing.": "Current temperature missing",
    "Usable product temperature limits are missing.": "Product temperature limits missing",
    "The report contains missing or conflicting facts.": "Missing or conflicting facts",
    "Possible active temperature exposure requires urgent human confirmation.": "Confirm current exposure",
    "Too little matching evidence to route automatically.": "Limited routing evidence",
    "More than one category has similar evidence.": "More than one team fits",
    "The stated issue differs from the base model's strongest word match.": "Reported issue outweighs the word match",
}


def rationale(text, checked, signals, urgent, reasons, method, policy_escalated):
    if checked:
        team = signals[0].rstrip(".")
        if "Reading outside stated limits" in signals:
            team = "Temperature reading and stated limit"
        elif team == "No exposed cargo, verified sensor correction, or controlled historical record":
            lower = content_text(text).lower()
            if "empty return trip" in lower:
                team = "Empty return trip"
            elif "sensor has been replaced" in lower:
                team = "Sensor replaced"
            else:
                team = "Temperature record"
    elif signals:
        matches = " and ".join(f"“{signal}”" for signal in signals[:2])
        team = f"Matches {matches}"
    else:
        team = "Limited routing evidence"

    urgency = temperature_review = None
    if urgent:
        if "Reading outside stated limits" in signals:
            urgency, temperature_review = temperature_excursion(text)
        elif checked and checked["urgent"] is True:
            urgency = signals[-1].rstrip(".")
        elif policy_escalated:
            urgency = "Possible urgent consequence under Sensitive"
        else:
            urgency = "Urgency terms in the report" if method == "rules" else "Wording matches urgent examples"

    review = temperature_review or next((hint for reason, hint in REVIEW_HINTS.items() if reason in reasons), None)
    if not review and checked and checked.get("active_safety"):
        review = "Verify the reported hazard"
    if not review and reasons:
        review = "Check the reported consequences"
    return {"team": team, "urgency": urgency, "review": review}


def triage(text, model, method="learned", policy="sensitive"):
    started = time.perf_counter()
    config = POLICIES[policy]
    pred = rule_prediction(text) if method == "rules" else model.predict(text)
    lower = content_text(text).lower()
    urgent = pred["urgent_margin"] >= config["urgent_margin"]
    policy_escalated = False
    reasons = []
    if pred["score"] < config["similarity_floor"]:
        reasons.append("Too little matching evidence to route automatically.")
    if pred["margin"] < config["margin_floor"]:
        reasons.append("More than one category has similar evidence.")
    missing_facts = re.search(r"\b(?:nobody|no one) knows (?:whether|if|what|where|who|how)\b|\bno information (?:is available )?(?:about|on|regarding)\b", lower)
    if missing_facts or any(re.search(p, lower) for p in CLARIFY):
        reasons.append("The report contains missing or conflicting facts.")
    if policy == "sensitive" and not urgent and any(re.search(p, lower) for p in SENSITIVE_SIGNALS):
        urgent = policy_escalated = True
        reasons.append("The stricter policy escalates a possible critical consequence for human confirmation.")
    if not text.strip() or pred.get("no_match"):
        # The Sensitive policy also sends unclassified reports for urgent review.
        policy_escalated = policy_escalated or (not urgent and policy == "sensitive")
        urgent = urgent or policy_escalated

    checked = temperature_check(text)
    issue = document_issue(text)
    if issue and (issue["active_safety"] or not checked or checked["urgent"] is not True):
        checked = issue
        if checked["category"] != pred["category"]:
            reasons.append("The stated issue differs from the base model's strongest word match.")
    if checked:
        if checked["urgent"] is not None:
            urgent = checked["urgent"]
        reasons.extend(checked["reasons"])

    category = checked["category"] if checked else pred["category"]
    signals = checked["signals"] if checked else pred["signals"]
    why = rationale(text, checked, signals, urgent, reasons, method, policy_escalated)
    return {"category": category, "category_label": CATEGORIES[category]["label"],
            "team": CATEGORIES[category]["team"], "urgent": urgent, "review": bool(reasons),
            "review_reasons": list(dict.fromkeys(reasons)), "signals": signals,
            "rationale": why, "explanation": why["team"],
            "similarity": round(pred["score"], 4), "margin": round(pred["margin"], 4),
            "alternatives": pred["alternatives"], "policy": policy, "method": method,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3), "api_cost_usd": 0,
            "action": "Priority review" if urgent and reasons else "Escalate now" if urgent else
                      "Human review" if reasons else "Ready to route"}
