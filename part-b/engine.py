"""Two reproducible local approaches. Similarity scores are not probabilities."""
from __future__ import annotations

import math
import re
import time
from collections import Counter, defaultdict

from taxonomy import CATEGORIES, POLICIES

ENGINE_VERSION = "routing-v4"

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
           r"do not know", r"may have", r"says.*but", r"unreadable", r"unmarked", r"may also",
           r"cannot establish", r"conflict", r"neither.{0,30}(?:confirmed|verified|checked)",
           r"(?:inspection|assessment|count).{0,30}(?:not yet|has not|not been)", r"not.{0,20}(?:provided|supplied).{0,25}(?:count|photo)"]
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
    cold = bool(re.search(r"\b(?:cold|chill|refrigerat|reefer|freez|froz|temperature|logger|cooling|compressor|ice cream|warm hold|warm-hold)", lower))
    limits_mentioned = bool(re.search(r"\b(?:range|limits?|requirement|required|allowed|against|between|permitted|specified|specification)\b", lower) or
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
    controlled = controlled or re.search(r"\b(?:batch|goods|product|cargo|shipment|stock|it|they).{0,25}(?:now|already).{0,20}isolated.{0,55}(?:verified|controlled).{0,30}(?:stor|cool|freez)", lower)
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


def issue_check(text):
    """Bounded evidence rules for the primary issue, before similarity fallback.

    These checks use reported consequences and custody, never report IDs. Both
    methods share these checks; independent performance must be measured again.
    An override does not replace the base score with a probability.
    """
    lower = re.sub(r"[-–—]", " ", content_text(text).lower())
    clauses = re.split(r"[.!?;\n]|\b(?:but|however|whereas|although)\b", lower)

    def has(pattern):
        return bool(re.search(pattern, lower))

    def positive(pattern):
        for clause in clauses:
            for match in re.finditer(pattern, clause):
                scope = clause[max(0, match.start() - 55):match.end()]
                negation = r"\b(?:no|not|without|never)\s+(?:(?:yet|been|being|currently|actively|ever|any|reported|a|an|of|signs?|evidence)\s+){0,4}(?:smok\w*|leak\w*|injur\w*|trapped|threat\w*|hissing|spreading|armed threat|forced entry|spill\w*|hazard\w*|confirm\w*|located|accounted|found|intact|sealed)\b|\b(?:nobody|no one|neither)\b.{0,30}(?:confirm\w*|locate|find|account)"
                if not re.match(r"\s*(?:no|without|there (?:is|are) no)\b", clause) and not re.search(negation, scope):
                    return True
        return False

    def result(category, urgent, signal, review=False, active=False):
        return {"category": category, "urgent": urgent, "signals": [signal],
                "reasons": [signal + "; human confirmation is required."] if review else [],
                "active_safety": active}

    systems = r"\b(?:fire (?:alarm|pump|water|suppression|protection)|medical gas (?:alarm|system)|emergency (?:stop|shutdown|alarm|ventilation|communications)|safety (?:interlock|system)|gas (?:detector|alarm))\b"
    unavailable = r"\b(?:out of (?:service|action)|offline|disabled|unavailable|failed|not (?:working|operating|operational)|cannot (?:be )?restor\w*|cannot isolate|no (?:working|operating|backup|temporary) (?:\w+ ){0,3}(?:alarm|pump|protection|monitoring))\b"
    restored = r"\b(?:now (?:fully )?(?:working|operational)|back in service|has been restored|is restored|no longer (?:offline|disabled|out of service))\b"
    still_unavailable = r"\b(?:still|remains?|currently).{0,35}(?:out of service|offline|disabled|unavailable|not working)|\bnot (?:yet )?(?:been )?restored\b"
    if has(systems) and has(unavailable) and (not has(restored) or has(still_unavailable)):
        return result("safety", True, "A critical safety system remains unavailable", True, True)

    # Closed incidents retain their subject team, but not a new urgent alarm.
    controlled = has(r"\b(?:incident|near miss|spill|leak|breach|theft).{0,70}(?:closed|resolved|contained|cleaned|secured)|\b(?:area|site).{0,30}(?:now secure|is secure|made safe)|\b(?:lock|guard).{0,90}(?:replaced|secure)")
    active = positive(r"\b(?:still|currently|now|continues?|remains?)\b.{0,55}(?:leaking|spreading|hissing|smok\w*|threat\w*|occupied|uncontained)")
    current_hazard = (
        positive(r"\b(?:smoke (?:is|continues?)|(?:battery|batteries|power bank).{0,60}(?:hissing|expanding|swelling|venting|sparking)|(?:person|worker|driver).{0,35}(?:injured|trapped|threatened)|(?:struck|hit).{0,25}(?:person|pedestrian))\b") or
        positive(r"\b(?:chemical|acid|solvent|gas|hazardous).{0,55}(?:leak\w*|drip\w*|spill\w*|vent\w*|spreading)|\b(?:liquid|puddle|fluid).{0,55}(?:spreading|live|electrical|walkway)|\bwater.{0,40}entering.{0,45}(?:electrical|energized|live)|\b(?:odour|odor|fumes).{0,70}(?:occupied|staff|people)|\b(?:itchy eyes|breathing difficult|hijacked|hijacking|armed threat|forced.{0,25}(?:gate|entry)|threatened.{0,40}(?:cab|driver))\b") or
        positive(r"\b(?:suspicious person|intruder|unauthori[sz]ed person).{0,70}(?:removing|inside|entering|loading)|\b(?:load|stack).{0,35}(?:could collapse|collapsing)")
    )
    if current_hazard and (not controlled or active):
        return result("safety", True, "An ongoing physical or security hazard takes priority", True, True)

    # Location evidence outranks allegations that the same goods are lost.
    located = positive(r"\b(?:know exactly where|all.{0,25}accounted for|(?:full|complete) (?:shipment|load).{0,45}(?:at our|at the|on the|is back|is intact)|confirms?\b.{0,35}(?:sealed|intact|still)|we have (?:its|the) scan|(?:all|full|complete).{0,30}(?:on (?:his|the|our) (?:truck|vehicle)|at (?:our|the) depot))\b")
    lost = has(r"\b(?:cannot|can't|could not) (?:find|locate|account for)|\b(?:unlocated|unaccounted|disappeared|disappears)|\b(?:not|never).{0,18}(?:found|located|appeared)|\b(?:neither|nobody|no one).{0,35}(?:locate|find|account for)|\b(?:no confirmed|unconfirmed) (?:delivery )?location|\b(?:parcel|shipment|consignment|cargo|sack|pallet|case|insert|instrument|component|kit|contents?).{0,35}(?:missing|absent)|\b(?:space for|contents?).{0,55}empty")
    lost = lost or has(r"\b(?:short (?:count|delivery)|one (?:sack|carton|pallet|case|item) short|not (?:all|every).{0,20}(?:arrived|received)|not received|denies? (?:receipt|receiving)|cannot confirm who received)\b")
    cargo_description = re.sub(r"\bpunctured (?:tyre|tire)\b", "", lower)
    physical = bool(re.search(r"\b(?:crush\w*|dented|cracked|snapped|scuff\w*|stained|soaked|shattered|torn|scratched|fractured|buckled|smashed|punctured|split boards|split panels|broken glass|water entered|rain (?:entered|soaked)|oil marks|shock indicator)\b", cargo_description))
    documents = has(r"\b(?:invoice|customs|clearance|declaration|tariff|permit|licen[cs]e|proof of delivery|bill of lading|certificate|shipping document|paperwork|packing list|manifest|consignment note|delivery receipt)\b")
    doc_problem = has(r"\b(?:reject\w*|incorrect\w*|correct\w*|amend\w*|currency|wrong|error|mismatch|missing from.{0,30}(?:packet|form)|cannot (?:open|close)|will not open|won't open|attachment.{0,15}(?:missing|corrupt)|(?:needs to|does not|doesn't|must).{0,18}match|(?:invoice|permit|licen[cs]e|certificate|paperwork|document|field|number).{0,30}(?:missing|absent|expired)|missing.{0,30}(?:licen[cs]e|document|field|number))\b")
    cargo_loss = has(r"\b(?:parcel|shipment|consignment|cargo|sacks?|pallet|cases?|insert|instrument|component|kits?|contents?).{0,40}(?:missing|absent|unlocated|not received|empty)|\b(?:missing|absent|unlocated).{0,25}(?:parcel|cargo|consignment|sack|pallet|insert|instrument|component|kit)\b")
    if documents and doc_problem and not cargo_loss:
        return result("documentation", False, "The reported blocker is a document or clearance record")
    if lost and not located:
        return result("missing", False, "The reported goods or contents cannot be accounted for")
    if documents and doc_problem:
        return result("documentation", False, "The reported blocker is a document or clearance record")
    if physical:
        return result("damage", False, "The primary reported issue is physical cargo or packaging damage")
    if controlled and positive(r"\b(?:security|near miss|theft|spill|lock|breach)\b"):
        return result("safety", False, "The request concerns a contained or closed safety incident")
    delay = has(r"\b(?:delay\w*|late|later|reschedul\w*|redelivery|revised.{0,15}(?:arrival|eta|forecast)|cancelled.{0,25}(?:sailing|departure|flight)|next departure|new appointment|booking.{0,25}(?:slot|closing)|tyre puncture|tire puncture|missed.{0,20}(?:delivery|collection)|waiting.{0,30}(?:unload|vehicle))\b")
    if located or delay:
        return result("delay", False, "The goods are located and the reported issue is timing or handover")
    return None

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
    issue = issue_check(text)
    # A live safety consequence outranks cold-chain handling; a live thermal
    # exposure outranks an ordinary cargo or paperwork issue. Otherwise use the
    # stated operational problem rather than incidental temperature vocabulary.
    if issue and (issue["active_safety"] or not checked or checked["urgent"] is not True):
        checked = issue
        if checked["category"] != pred["category"]:
            reasons.append("The stated issue differs from the base model's strongest word match.")
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
            "explanation": ("Reported issue and consequence check" if checked else "Keyword matches" if method == "rules" else "Words shared with training examples") +
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
