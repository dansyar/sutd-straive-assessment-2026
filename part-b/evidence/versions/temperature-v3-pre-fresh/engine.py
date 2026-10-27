"""Two reproducible local approaches. Similarity scores are not probabilities."""
from __future__ import annotations

import math
import re
import time
from collections import Counter, defaultdict

from taxonomy import CATEGORIES, POLICIES

ENGINE_VERSION = "temperature-v3"

KEYWORDS = {
    "delay": ["late", "delay", "traffic", "queue", "reschedul", "window", "wrong turn", "missed", "arrival", "connection"],
    "missing": ["missing", "short", "cannot find", "can't find", "no scan", "trace", "not received", "denies receipt", "absent", "empty sealed", "unaccounted", "cannot locate"],
    "damage": ["damage", "crush", "dent", "crack", "broken", "torn", "scratch", "shatter", "split", "scuff", "fragments", "water entered"],
    "temperature": ["temperature", "refrigerat", "chilled", "cold room", "cold-chain", "logger", "reefer", "thaw", "freezer", "cooling", "cold storage"],
    "safety": ["smoke", "leaking", "chemical", "injur", "hijack", "suspicious", "fire", "security", "hazard", "collapse", "spill", "pedestrian"],
    "documentation": ["customs", "invoice", "packing list", "tariff", "declaration", "proof of delivery", "bill of lading", "certificate", "permit", "transport document"],
}
URGENT_PATTERNS = [
    r"smoke is", r"leak(?:ing)?.*hazard", r"has been injured", r"hijack", r"happening now",
    r"could collapse", r"\bnot\b[^.!?]*(?:isolated|contained|cordoned)", r"still nearby",
    r"(?:protection|safety system|fire suppression|fire pump).*(?:offline|disabled|outage)",
    r"(?:offline|disabled|outage).*(?:protection|safety system|fire pump)",
    r"(?:cold|refrigerat|freezer|reefer).*(?:lost power|stopped|failed|rising|unpowered)",
    r"(?:thawing|warming rapidly|backup.*failing|running out|immediate isolation)",
]
CLARIFY = [r"unknown", r"unclear", r"cannot confirm", r"\bnot\b[^.!?]*(?:provided|checked|identified)",
           r"do not know", r"may have", r"says.*but", r"unreadable", r"unmarked", r"may also"]
SENSITIVE_SIGNALS = [r"emergency", r"protection", r"unusual.*smell", r"unrefrigerated",
                     r"security", r"heat", r"fumes", r"trapped", r"threat", r"warming", r"hissing",
                     r"ventilation.*failed", r"could.*collapse", r"safety system"]

STOP_WORDS = set("a an the is are was were be been being of to at in on into for from with and or but as by it its this that these those our their has have had will please advise next team message receiving operations note dispatch update report".split())

def content_text(text):
    return re.sub(r" Please advise the next team\.$", "", re.sub(
        r"^(?:Dispatch update: |Please check this report\. |Message from the receiving team: |Operations note — )", "", text))

def tokens(text):
    words = [w for w in re.findall(r"[a-z]+", content_text(text).lower()) if w not in STOP_WORDS]
    return words + [a + "_" + b for a, b in zip(words, words[1:])]

def dot(a, b):
    return sum(value * b.get(key, 0) for key, value in a.items())

def normalize(vector):
    norm = math.sqrt(sum(v * v for v in vector.values())) or 1
    return {key: value / norm for key, value in vector.items()}

class TextModel:
    """TF-IDF class centroids, fitted ONLY to the train split (240 reports)."""
    def __init__(self, rows):
        train = [row for row in rows if row["split"] == "train"]
        dfs = Counter()
        for row in train:
            dfs.update(set(tokens(row["text"])))
        self.idf = {token: math.log((1 + len(train)) / (1 + df)) + 1 for token, df in dfs.items()}
        buckets = defaultdict(Counter)
        for row in train:
            vector = self.vector(row["text"])
            buckets[row["category"]].update(vector)
            buckets["__urgent" if row["urgent"] else "__routine"].update(vector)
        self.centroids = {label: normalize(counts) for label, counts in buckets.items()}
        self.train_count = len(train)

    def vector(self, text):
        counts = Counter(tokens(text))
        return normalize({t: (1 + math.log(c)) * self.idf[t] for t, c in counts.items() if t in self.idf})

    def predict(self, text):
        vector = self.vector(text)
        scores = sorted(((cat, dot(vector, self.centroids[cat])) for cat in CATEGORIES),
                        key=lambda item: item[1], reverse=True)
        urgent_margin = dot(vector, self.centroids["__urgent"]) - dot(vector, self.centroids["__routine"])
        evidence = sorted(((t.replace("_", " "), v * self.centroids[scores[0][0]].get(t, 0))
                           for t, v in vector.items()), key=lambda x: x[1], reverse=True)
        return {"category": scores[0][0], "score": scores[0][1], "margin": scores[0][1] - scores[1][1],
                "urgent_margin": urgent_margin, "signals": [t for t, v in evidence[:5] if v > 0],
                "alternatives": [{"category": c, "score": round(s, 4)} for c, s in scores[:3]]}

def rule_prediction(text):
    lower = content_text(text).lower()
    # Match a word/stem at its beginning. "dent" must not match "incident".
    hits = {cat: [word for word in words if re.search(r"\b" + re.escape(word), lower)] for cat, words in KEYWORDS.items()}
    ranked = sorted(CATEGORIES, key=lambda c: len(hits[c]), reverse=True)
    best, second = len(hits[ranked[0]]), len(hits[ranked[1]])
    return {"category": ranked[0], "score": min(.65, best * .13),
            "margin": max(0, best - second) * .08,
            "urgent_margin": .1 if any(re.search(p, lower) for p in URGENT_PATTERNS) else -.1,
            "signals": hits[ranked[0]], "alternatives": [], "no_match": best == 0}

NUMBER = r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)"
UNIT = r"(?:°\s*)?(?:degrees?\s*)?(?:c(?:elsius)?|f(?:ahrenheit)?)\b"
TEMPERATURE_RANGE = re.compile(rf"(?P<low>{NUMBER})\s*(?P<low_unit>{UNIT})?\s*(?:to|through|-)\s*(?P<high>{NUMBER})\s*(?P<high_unit>{UNIT})")
TEMPERATURE_READING = re.compile(rf"(?<![\w.])(?P<value>{NUMBER})\s*(?P<unit>{UNIT})")

def celsius(value, unit):
    value = float(value)
    return (value - 32) * 5 / 9 if "f" in unit else value

def temperature_check(text):
    """Shared, explicit cold-chain checks; never infer an unstated safe range.

    Category scores remain those of each base method. This policy can override
    the proposed route/priority, and records the actual evidence and review need.
    It is deliberately a bounded language/number check, not a calibrated model.
    """
    lower = content_text(text).lower().replace("–", "-").replace("—", "-").replace("−", "-")
    lower = re.sub(r"\bminus\s+(?=\d)", "-", lower)
    ranges = list(TEMPERATURE_RANGE.finditer(lower))
    readings = [m for m in TEMPERATURE_READING.finditer(lower)
                if not any(m.start() < r.end() and m.end() > r.start() for r in ranges)]
    cold = bool(re.search(r"\b(?:cold|chill|refrigerat|reefer|freez|temperature|logger|cooling|compressor|ice cream)", lower))
    limits_mentioned = bool(re.search(r"\b(?:range|limits?|requirement|required|allowed|against|between|permitted)\b", lower) or
        (ranges and re.search(r"\b(?:product|cargo|goods|shipment|consignment)\b", lower)))
    if not cold and not (readings and (limits_mentioned or re.search(r"\b(?:probes?|sensor|display)\b", lower))):
        return None
    result = {"category": "temperature", "urgent": None, "reasons": [], "signals": ["Cold-chain context"]}
    hazard_text = re.sub(r"\b(?:no|not|without)\b[^.!?;]*(?:smoke|injur\w*|trapped|armed threat)[^.!?;]*", "", lower)
    if re.search(r"\b(?:smoke is (?:coming|spreading|rising)|(?:worker|person|driver).{0,25}(?:injured|trapped)|(?:acid|chemical|gas).{0,25}(?:venting|spreading)|armed threat)\b", hazard_text):
        return {"category": "safety", "urgent": True,
                "reasons": ["An active physical hazard takes priority over cold-chain handling."], "signals": ["Active physical hazard"]}
    no_cargo = re.search(r"\b(?:empty return trip|no (?:product|cargo|goods|stock) (?:was|were|is|are)?\s*(?:on|inside|aboard|present))\b", lower)
    corrected_sensor = re.search(r"\b(?:faulty|false|sensor error)\b", lower) and re.search(
        r"(?:independent probes verified|second.{0,30}probe confirms|sensor has been replaced)", lower)
    controlled = re.search(r"(?:quarantined.{0,60}(?:control|quality)|(?:resolved|closed).{0,40}(?:incident|excursion)|(?:incident|excursion).{0,40}(?:resolved|closed))", lower)
    archival = re.search(r"\b(?:archive|records?|logger file|paperwork)\b", lower) and re.search(
        r"\b(?:last week|last month|previous|already|resolved|closed|all measurements|all readings)\b", lower)
    new_exposure = re.search(r"\b(?:currently|now|still)\b.{0,50}(?:warming|softening|exposed|at\s*[-+\d])", lower)
    if no_cargo or corrected_sensor or ((controlled or archival) and not new_exposure):
        result.update(urgent=False, signals=["No exposed cargo, verified sensor correction, or controlled historical record"])
        return result
    normal_packaging_claim = re.search(r"(?:cosmetic tear|claim concerns (?:the )?packaging only|claim is (?:only )?for (?:the )?packaging)", lower) and re.search(
        r"(?:temperature.{0,30}(?:in range|normal)|seal is intact|recorded temperature stayed in range)", lower)
    if normal_packaging_claim:
        return {"category": "damage", "urgent": False, "reasons": [], "signals": ["Packaging claim with controlled temperature and intact contents"]}
    values = [celsius(m["value"], m["unit"]) for m in readings]
    permitted = []
    if limits_mentioned:
        for match in ranges:
            lo = celsius(match["low"], match["low_unit"] or match["high_unit"])
            hi = celsius(match["high"], match["high_unit"])
            if lo > hi:
                result["reasons"].append("The stated temperature limits are reversed; confirm them.")
            else:
                permitted.append((lo, hi))
    active_failure = bool(re.search(r"\b(?:thawing|softening|warming rapidly|continues warming|cargo is warming)\b", lower) or
        re.search(r"(?:cold|reefer|chill|refrigerat|compartment|compressor|cooling).{0,90}(?:failed|unpowered|lost power|stopped|without (?:working )?cooling)", lower) or
        re.search(r"\b(?:immediate isolation|without working cooling|no working cooling)\b", lower))
    outside = bool(values and permitted and any(v < lo - 1e-8 or v > hi + 1e-8 for v in values for lo, hi in permitted))
    if outside or active_failure:
        result.update(urgent=True)
        result["signals"].append("Reading outside stated limits" if outside else "Ongoing loss of cooling or immediate isolation")
        result["reasons"].append("Possible active temperature exposure requires urgent human confirmation.")
    elif values and permitted and not result["reasons"]:
        result.update(urgent=False, signals=["Current readings are within the stated limits"])
    if len(set(round(v, 4) for v in values)) > 1:
        result["reasons"].append("Multiple temperature readings need reconciliation.")
    if not values:
        result["reasons"].append("A usable current temperature reading is missing.")
    if not permitted:
        result["reasons"].append("Usable product temperature limits are missing.")
    return result

def triage(text, model, method="learned", policy="sensitive"):
    started = time.perf_counter()
    config = POLICIES[policy]
    pred = rule_prediction(text) if method == "rules" else model.predict(text)
    lower = content_text(text).lower()
    urgent = pred["urgent_margin"] >= config["urgent_margin"]
    sensitive_signal = any(re.search(p, lower) for p in SENSITIVE_SIGNALS)
    reasons = []
    if pred["score"] < config["similarity_floor"]:
        reasons.append("Too little matching evidence to route automatically.")
    if pred["margin"] < config["margin_floor"]:
        reasons.append("More than one category has similar evidence.")
    if any(re.search(p, lower) for p in CLARIFY):
        reasons.append("The report contains missing or conflicting facts.")
    if policy == "sensitive" and sensitive_signal and not urgent:
        urgent = True
        reasons.append("The stricter policy escalates a possible critical consequence for human confirmation.")
    if not text.strip() or pred.get("no_match"):
        # Lack of category keywords must not erase an explicit urgency signal.
        urgent = urgent or policy == "sensitive"
    checked = temperature_check(text)
    if checked:
        if checked["urgent"] is not None:
            urgent = checked["urgent"]
        reasons.extend(checked["reasons"])
    review = bool(reasons)
    category = checked["category"] if checked else pred["category"]
    signals = checked["signals"] if checked else pred["signals"]
    return {"category": category, "category_label": CATEGORIES[category]["label"],
            "team": CATEGORIES[category]["team"], "urgent": urgent, "review": review,
            "review_reasons": list(dict.fromkeys(reasons)), "signals": signals,
            "explanation": ("Cold-chain evidence check" if checked else "Keyword matches" if method == "rules" else "Words shared with training examples") +
                (": " + ", ".join(signals[:5]) + "." if signals else " are insufficient."),
            "similarity": round(pred["score"], 4), "margin": round(pred["margin"], 4),
            "alternatives": pred["alternatives"], "policy": policy, "method": method,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3), "api_cost_usd": 0,
            "action": "Priority review" if urgent and review else "Escalate now" if urgent else
                      "Human review" if review else "Ready to route"}

def routing_queue(prediction, confirmed=False):
    """Exclusive priority queues; Inbox in the UI is the combined open view."""
    if confirmed:
        return "done"
    if prediction["urgent"]:
        return "urgent"
    return "review" if prediction["review"] else "routine"
