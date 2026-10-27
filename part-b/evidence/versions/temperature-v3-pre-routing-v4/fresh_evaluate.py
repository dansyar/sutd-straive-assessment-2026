"""Freeze and score the preregistered, newly authored 60-report challenge set.

No classifier, training, policy, metric or original-label changes are made here.
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

from corpus import ROOT, load_corpus, read_jsonl, sha256
from engine import ENGINE_VERSION, TextModel
from evaluate import requirement_change, run_benchmark
from taxonomy import CATEGORIES, COSTS, POLICIES

REGISTRATION = ROOT / "evidence/fresh-20261022-registration.json"
SOURCE = ROOT / "evidence/fresh-20261022-source.json"
DRIVER = ROOT / "evidence/fresh-20261022-driver.json"
REPORTS = ROOT / "data/fresh_reports_20261022.jsonl"
LABELS = ROOT / "data/fresh_labels_20261022.jsonl"
FREEZE = LABELS.with_suffix(".freeze.json")
REVIEW_DIR = ROOT / "evidence/reviews/fresh-20261022"


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def check_candidate():
    registration = json.loads(REGISTRATION.read_text())
    source = json.loads(SOURCE.read_text())
    driver = json.loads(DRIVER.read_text())
    if (sha256(REGISTRATION) != source["registration_sha256"] or
            sha256(REPORTS) != source["reports_sha256"] or
            sha256(ROOT / "evidence/reviews/guide.txt") != source["guide_sha256"] or
            sha256(Path(__file__)) != driver["driver_sha256"] or
            sha256(SOURCE) != driver["source_manifest_sha256"]):
        raise ValueError("Preregistered source, guide or scoring driver changed.")
    for name, expected in registration["implementation_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise ValueError(f"Candidate changed after preregistration: {name}")
    if sha256(ROOT / "data/development.jsonl") != registration["training_sha256"]:
        raise ValueError("Training data changed after preregistration.")
    for name, expected in registration["original_results_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise ValueError("An earlier benchmark was changed.")
    development, original, manifest = load_corpus()
    reports = read_jsonl(REPORTS)
    if (len(reports) != registration["planned_n"] or
            len({r["id"] for r in reports}) != len(reports) or
            len({r["text"] for r in reports}) != len(reports) or
            any(set(r) != {"id", "text", "channel"} for r in reports) or
            {r["id"] for r in reports} & {r["id"] for r in development + original} or
            {r["text"] for r in reports} & {r["text"] for r in development + original}):
        raise ValueError("Invalid fresh source or overlap with the original corpus.")
    return registration, source, development, reports, manifest


def validate_judgments(judgments, reports):
    ids = [r.get("id") for r in judgments]
    if (len(ids) != len(reports) or len(set(ids)) != len(ids) or
            set(ids) != {r["id"] for r in reports}):
        raise ValueError("Every fresh report must be independently labeled exactly once.")
    for row in judgments:
        if (row.get("category") not in {*CATEGORIES, "unclear"} or
                not (type(row.get("urgent")) is bool or row.get("urgent", "missing") is None) or
                type(row.get("clarification")) is not bool or
                not isinstance(row.get("reason"), str) or not row["reason"].strip()):
            raise ValueError("Invalid independent judgment; preserve unknowns explicitly.")


def freeze_review(path):
    registration, source, _, reports, _ = check_candidate()
    raw = json.loads(path.read_text())
    if (raw.get("reviewer_type") != "agent" or raw.get("human_review") is not False or
            raw.get("fresh_context") is not True or not raw.get("reviewer") or
            set(raw.get("allowed_inputs", [])) != {
                str(Path(source["review_input_directory"]) / "reports.jsonl"),
                str(Path(source["review_input_directory"]) / "guide.txt")}):
        raise ValueError("Review must record its fresh-context, text-and-guide-only provenance.")
    judgments = raw.get("judgments", [])
    validate_judgments(judgments, reports)
    raw_path = REVIEW_DIR / "review.raw.json"
    if any(p.exists() for p in [LABELS, FREEZE, raw_path]):
        raise ValueError("Independent judgments are already frozen. Do not replace them.")
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    with raw_path.open("xb") as stream:
        stream.write(path.read_bytes())
    by_id = {r["id"]: r for r in judgments}
    labels = [{**by_id[r["id"]], "reviewer": raw["reviewer"], "reviewer_type": "agent",
               "label_source": "independent agent review"} for r in reports]
    with LABELS.open("x", encoding="utf-8") as stream:
        stream.write("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in labels))
    freeze = {"status": "frozen independent review", "frozen_at": datetime.now(timezone.utc).isoformat(),
              "count": len(labels), "reports_sha256": sha256(REPORTS), "labels_sha256": sha256(LABELS),
              "raw_review_sha256": sha256(raw_path), "registration_sha256": sha256(REGISTRATION),
              "source_manifest_sha256": sha256(SOURCE), "driver_sha256": sha256(Path(__file__)),
              "implementation_sha256": registration["implementation_sha256"],
              "reviewer_types": ["agent"], "human_review": False,
              "source": {"kind": "independent agent", "fresh_context": True, "reviewer": raw["reviewer"],
                         "blind_inputs": {"reports_sha256": source["reports_sha256"],
                                          "guide_sha256": source["guide_sha256"]},
                         "allowed_inputs": raw["allowed_inputs"]},
              "limitation": "Separate context and judgments, same model family; no domain-expert human review."}
    write_new(FREEZE, freeze)
    print(json.dumps({"frozen_labels": len(labels), "labels_sha256": freeze["labels_sha256"]}))


def fresh_rows():
    registration, source, development, reports, manifest = check_candidate()
    freeze = json.loads(FREEZE.read_text())
    if (freeze.get("status") != "frozen independent review" or
            freeze.get("count") != len(reports) or
            freeze.get("labels_sha256") != sha256(LABELS) or
            freeze.get("reports_sha256") != sha256(REPORTS) or
            freeze.get("registration_sha256") != sha256(REGISTRATION) or
            freeze.get("source_manifest_sha256") != sha256(SOURCE) or
            freeze.get("driver_sha256") != sha256(Path(__file__)) or
            freeze.get("raw_review_sha256") != sha256(REVIEW_DIR / "review.raw.json") or
            freeze.get("implementation_sha256") != registration["implementation_sha256"] or
            freeze.get("source", {}).get("blind_inputs") != {
                "reports_sha256": source["reports_sha256"], "guide_sha256": source["guide_sha256"]} or
            freeze.get("source", {}).get("fresh_context") is not True or freeze.get("human_review") is not False):
        raise ValueError("Fresh source, labels, review provenance or frozen candidate changed.")
    labels = read_jsonl(LABELS)
    validate_judgments(labels, reports)
    raw = json.loads((REVIEW_DIR / "review.raw.json").read_text())
    by_id = {r["id"]: r for r in labels}
    raw_by_id = {r["id"]: r for r in raw["judgments"]}
    for row in labels:
        if (row.get("reviewer_type") != "agent" or row.get("label_source") != "independent agent review" or
                row.get("reviewer") != freeze["source"]["reviewer"] or
                any(row[key] != raw_by_id[row["id"]][key]
                    for key in ["category", "urgent", "clarification", "reason"])):
            raise ValueError("A reference judgment or attribution differs from the returned independent review.")
    rows = [{**r, **{k: v for k, v in by_id[r["id"]].items() if k != "text"}} for r in reports]
    return rows, freeze, registration, development, manifest


def benchmark(output, activate=False):
    rows, freeze, registration, development, manifest = fresh_rows()
    paths = [output / f"fresh-test{suffix}.json"
             for suffix in ["", "-predictions", "-mistakes", "-requirement-change"]]
    if any(p.exists() for p in paths):
        raise ValueError("Preserve existing fresh results; reproduce into a new output folder.")
    started = time.perf_counter()
    model = TextModel(development)
    model_fit_ms = round((time.perf_counter() - started) * 1000, 4)
    results, mistakes, predictions = run_benchmark(rows, model)
    document = {
        "status": "fresh independently reviewed test", "revision": ENGINE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.machine()}", "train_n": model.train_count,
        "train_families": 48, "evaluation_n": len(rows), "evaluation_families": len(rows),
        "model_fit_ms": model_fit_ms, "corpus_sha256": manifest["sha256"],
        "reports_sha256": sha256(REPORTS), "test_labels_sha256": sha256(LABELS),
        "implementation_sha256": registration["implementation_sha256"],
        "review_provenance": freeze, "methods": results, "requirement_change": requirement_change(results),
        "evaluation_protocol": {
            "kind": "preregistered fresh synthetic challenge set", "previously_exposed_cases": False,
            "classifier_frozen_before_report_authoring": True, "labels_frozen_before_predictions": True,
            "selected_method": registration["selected_method"], "selected_policy": registration["selected_policy"],
            "registration": str(REGISTRATION.relative_to(ROOT)), "registration_sha256": sha256(REGISTRATION),
            "source_manifest": str(SOURCE.relative_to(ROOT)), "scoring_driver_sha256": sha256(Path(__file__)),
            "no_post_test_tuning": True, "limitations": registration["limitations"]},
        "assumptions": {
            "cost_units": COSTS,
            "urgent_miss_by_policy": {k: v["urgent_miss_cost"] for k, v in POLICIES.items()},
            "priority_delay": "Every missed urgent flag incurs the priority penalty, including ordinary review.",
            "review": "Human review 1; automatic wrong route OR bypassed required review 6 once; false urgent 2. Staffing, human errors and queue delays unmeasured.",
            "api_cost": "USD 0 in classifier inference API calls. Computing, development/review services and labor excluded.",
            "latency": "Warm inference, 5 passes per report; excludes startup, HTTP, UI and human handling.",
            "unclear": "Unknown category and urgency excluded only from their respective known-label scores; required-review behavior uses all reports.",
            "quality": "60 separately authored fictional scenarios; no exact overlap with the original 360. Not a random or representative production sample."},
        "testing_attribution": registration["testing_attribution"]}
    for path, value in zip(paths, [document, predictions, mistakes, document["requirement_change"]]):
        write_new(path, value)
    if activate:
        active_path = ROOT / "evidence/current.json"
        active = json.loads(active_path.read_text())
        active["fresh"] = str(paths[0].resolve().relative_to(ROOT))
        active_path.write_text(json.dumps(active, indent=2) + "\n")
    print(json.dumps({"reports": len(rows), "candidate": f"{registration['selected_method']}/{registration['selected_policy']}",
                      "results": [{k: v for k, v in result.items() if k != "confusion"} for result in results]}, indent=2))
    return document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-review", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/fresh-20261022")
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    if args.freeze_review:
        if args.activate:
            parser.error("Freeze judgments separately before scoring or activation.")
        freeze_review(args.freeze_review)
    else:
        benchmark(args.output, args.activate)


if __name__ == "__main__":
    main()
