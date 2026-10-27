"""Measure development behavior; final testing requires frozen human labels."""
from __future__ import annotations

import argparse
import json
import platform
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from corpus import ROOT, load_corpus, read_jsonl, sha256
from engine import TextModel, triage
from taxonomy import CATEGORIES, COSTS, POLICIES

def percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    i = int(position)
    return values[i] + (values[min(i + 1, len(values) - 1)] - values[i]) * (position - i)

def requires_review(row):
    return bool(row["clarification"] or row["category"] == "unclear" or row["urgent"] is None)

def summarize(rows, predictions, policy):
    if not rows or len(rows) != len(predictions):
        raise ValueError("Metrics require matching, non-empty truth and prediction lists.")
    pairs = list(zip(rows, predictions))
    known_category = [(r, p) for r, p in pairs if r["category"] in CATEGORIES]
    known_urgency = [(r, p) for r, p in pairs if type(r["urgent"]) is bool]
    urgent_total = sum(r["urgent"] for r, _ in known_urgency)
    misses = sum(r["urgent"] and not p["urgent"] for r, p in known_urgency)
    false_urgent = sum(not r["urgent"] and p["urgent"] for r, p in known_urgency)
    auto = [(r, p) for r, p in pairs if not p["review"]]
    auto_known = [(r, p) for r, p in auto if r["category"] in CATEGORIES]
    auto_wrong = sum(r["category"] != p["category"] for r, p in auto_known)
    auto_urgent_misses = sum(r["urgent"] is True and not p["urgent"] for r, p in auto)
    auto_unclear = sum(r["category"] == "unclear" or r["urgent"] is None for r, _ in auto)
    review_count = sum(p["review"] for _, p in pairs)
    review_required = sum(requires_review(r) for r, _ in pairs)
    review_caught = sum(requires_review(r) and p["review"] for r, p in pairs)
    required_auto = sum(requires_review(r) and not p["review"] for r, p in pairs)
    confusion = {cat: {pred: 0 for pred in CATEGORIES} for cat in CATEGORIES}
    for actual, pred in known_category:
        confusion[actual["category"]][pred["category"]] += 1
    fs = []
    for cat in CATEGORIES:
        tp = confusion[cat][cat]
        fp = sum(confusion[a][cat] for a in CATEGORIES if a != cat)
        fn = sum(confusion[cat][p] for p in CATEGORIES if p != cat)
        fs.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0)
    # A missed urgent flag causes a priority delay even if ordinary review later
    # finds the error. Do not erase that cost by assuming perfect human review.
    route_errors = sum((r["category"] in CATEGORIES and r["category"] != p["category"])
                       or requires_review(r) for r, p in auto)
    common_cost = (review_count * COSTS["human_review"] + route_errors * COSTS["wrong_route"] +
                   false_urgent * COSTS["false_urgent"])
    costs = {name: common_cost + misses * config["urgent_miss_cost"]
             for name, config in POLICIES.items()}
    n = len(rows)
    return {"n": n, "category_n": len(known_category), "urgency_n": len(known_urgency),
        "category_accuracy": sum(r["category"] == p["category"] for r, p in known_category) / len(known_category) if known_category else None,
        "macro_f1": sum(fs) / len(fs) if known_category else None,
        "urgent_total": urgent_total, "urgent_misses": misses,
        "urgent_recall": (urgent_total - misses) / urgent_total if urgent_total else None,
        "false_urgent": false_urgent, "review_count": review_count, "review_rate": review_count / n,
        "review_required_n": review_required, "review_recall": review_caught / review_required if review_required else None,
        "review_precision": review_caught / review_count if review_count else None,
        "required_review_automated": required_auto,
        "automation_coverage": len(auto) / n, "unsafe_auto_urgent_misses": auto_urgent_misses,
        "wrong_auto_routes": auto_wrong, "unknown_labels_automated": auto_unclear,
        "auto_route_accuracy": (len(auto_known) - auto_wrong) / len(auto_known) if auto_known else None,
        "auto_category_n": len(auto_known), "cost_units_standard": costs["standard"],
        "cost_units_sensitive": costs["sensitive"], "weighted_cost_units": costs[policy],
        "cost_units_per_report": costs[policy] / n, "api_cost_usd": 0, "confusion": confusion}

def run_benchmark(rows, model, passes=5):
    metrics, mistakes, predictions = [], [], []
    for method in ["rules", "learned"]:
        for policy in POLICIES:
            for row in rows:
                triage(row["text"], model, method, policy)
            timed = [triage(row["text"], model, method, policy) for _ in range(passes) for row in rows]
            first_pass = timed[:len(rows)]
            result = summarize(rows, first_pass, policy)
            result.update({"method": method, "policy": policy,
                "p50_ms": round(percentile([p["latency_ms"] for p in timed], .5), 4),
                "p95_ms": round(percentile([p["latency_ms"] for p in timed], .95), 4),
                "latency_samples": len(timed)})
            metrics.append(result)
            for row, pred in zip(rows, first_pass):
                issues = []
                if row["category"] in CATEGORIES and row["category"] != pred["category"]:
                    issues.append("wrong_category")
                if type(row["urgent"]) is bool and row["urgent"] != pred["urgent"]:
                    issues.append("urgent_miss" if row["urgent"] else "false_urgent")
                if requires_review(row) and not pred["review"]:
                    issues.append("required_review_bypassed")
                record = {"id": row["id"], "text": row["text"], "family": row.get("family", row["id"]),
                    "method": method, "policy": policy, "actual_category": row["category"],
                    "actual_urgent": row["urgent"], "actual_review_required": requires_review(row),
                    "prediction": pred, "issues": issues}
                predictions.append(record)
                if issues:
                    mistakes.append(record)
    return metrics, mistakes, predictions

def reviewed_rows(path):
    _, reports, _ = load_corpus()
    path = Path(path)
    freeze_path = path.with_suffix(".freeze.json")
    if not freeze_path.exists():
        raise ValueError("Freeze independent labels with review.py before final testing.")
    freeze = json.loads(freeze_path.read_text())
    if freeze.get("labels_sha256") != sha256(path) or freeze.get("reports_sha256") != sha256(ROOT / "data/review_reports.jsonl"):
        raise ValueError("Frozen labels or source reports changed.")
    implementation = freeze.get("implementation_sha256", {})
    if freeze.get("status") != "frozen independent review" or freeze.get("count") != 60 or set(implementation) != {"engine.py", "taxonomy.py", "evaluate.py"}:
        raise ValueError("Invalid label freeze manifest. Freeze reviews with review.py.")
    if any(sha256(ROOT / name) != expected for name, expected in implementation.items()):
        raise ValueError("The implementation changed after label freeze. Preserve the original evaluation before a documented new version.")
    labels = read_jsonl(path)
    ids = [r["id"] for r in labels]
    if len(ids) != 60 or len(set(ids)) != 60 or set(ids) != {r["id"] for r in reports}:
        raise ValueError("Final testing requires all 60 original report IDs, once each.")
    for row in labels:
        reviewer_type = row.get("reviewer_type", "human")
        if (row.get("category") not in {*CATEGORIES, "unclear"} or
            not (type(row.get("urgent")) is bool or row.get("urgent", "missing") is None) or
            type(row.get("clarification")) is not bool or not row.get("reviewer") or
            reviewer_type not in {"human", "agent"} or row.get("label_source") != f"independent {reviewer_type} review"):
            raise ValueError("Invalid independent label or reviewer attribution.")
    if any(r.get("reviewer_type") == "agent" for r in labels):
        source = freeze.get("source", {})
        if (source.get("kind") != "independent agent" or source.get("fresh_context") is not True or
            source.get("blind_inputs", {}).get("reports_sha256") != sha256(ROOT / "data/review_reports.jsonl")):
            raise ValueError("Independent agent labels require recorded blind review provenance.")
    by_id = {r["id"]: r for r in labels}
    # Join only labels; a review file cannot override original report text.
    return [{**report, **{k: v for k, v in by_id[report["id"]].items() if k != "text"}} for report in reports]

def requirement_change(results):
    changes = []
    for method in ["rules", "learned"]:
        before = next(m for m in results if m["method"] == method and m["policy"] == "standard")
        after = next(m for m in results if m["method"] == method and m["policy"] == "sensitive")
        changes.append({"method": method, "requirement": "Urgent priority miss penalty increases from 30 to 100 units.",
            "before": {k: before[k] for k in ["urgent_recall", "urgent_misses", "false_urgent", "review_count", "automation_coverage", "cost_units_sensitive"]},
            "after": {k: after[k] for k in ["urgent_recall", "urgent_misses", "false_urgent", "review_count", "automation_coverage", "cost_units_sensitive"]},
            "additional_reviews": after["review_count"] - before["review_count"],
            "urgent_misses_prevented": before["urgent_misses"] - after["urgent_misses"],
            "cost_reduction_under_new_requirement": before["cost_units_sensitive"] - after["cost_units_sensitive"]})
    return changes

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewed", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence")
    args = parser.parse_args(argv)
    development, _, manifest = load_corpus()
    started = time.perf_counter()
    model = TextModel(development)
    model_fit_ms = round((time.perf_counter() - started) * 1000, 4)
    rows = reviewed_rows(args.reviewed) if args.reviewed else [r for r in development if r["split"] == "validation"]
    review_manifest = json.loads(args.reviewed.with_suffix(".freeze.json").read_text()) if args.reviewed else None
    name = "final-test" if args.reviewed else "development"
    final_path = args.output / f"{name}.json"
    if args.reviewed and final_path.exists():
        raise ValueError("Final test was already run. Preserve the original result; use a new output directory only for an explicitly documented rerun.")
    results, mistakes, predictions = run_benchmark(rows, model)
    document = {"status": "independently reviewed test" if args.reviewed else "development estimates",
        "generated_at": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.machine()}", "train_n": model.train_count,
        "train_families": 48, "evaluation_n": len(rows), "evaluation_families": len({r.get("family", r["id"]) for r in rows}),
        "corpus_sha256": manifest["sha256"], "model_fit_ms": model_fit_ms,
        "implementation_sha256": {name: sha256(ROOT / name) for name in ["engine.py", "taxonomy.py", "evaluate.py"]},
        "test_labels_sha256": sha256(args.reviewed) if args.reviewed else None,
        "review_provenance": review_manifest,
        "methods": results, "requirement_change": requirement_change(results),
        "assumptions": {"cost_units": COSTS, "urgent_miss_by_policy": {k: v["urgent_miss_cost"] for k, v in POLICIES.items()},
            "priority_delay": "All missed urgent flags incur the priority penalty, including reports in ordinary human review.",
            "review": "Human review costs 1 relative unit. Automatic wrong routes or bypassed required review cost 6 once. False urgent flags cost 2. Human errors, staffing and elapsed queue time are unmeasured.",
            "api_cost": "Both approaches make zero paid API calls. Computing and human labor are excluded from USD figures.",
            "latency": "Warm inference only, 5 passes per report; excludes HTTP, UI and startup. Fit time is reported separately.",
            "quality": "Synthetic data. Development has 12 scenario families with 5 variants each, so 60 rows are not 60 independent scenarios.",
            "unclear": "Unclear category/urgency labels are not forced into known classes. Known-label denominators are explicit; required-review behavior is evaluated on all reports.",
            "thresholds": "Initial thresholds; development-only revisions. No tuning against independent review labels."}}
    args.output.mkdir(parents=True, exist_ok=True)
    final_path.write_text(json.dumps(document, indent=2) + "\n")
    for suffix, records in [("mistakes", mistakes), ("predictions", predictions)]:
        (args.output / f"{name}-{suffix}.json").write_text(json.dumps(records, indent=2) + "\n")
    (args.output / f"{name}-requirement-change.json").write_text(json.dumps(document["requirement_change"], indent=2) + "\n")
    print(json.dumps({"benchmark": name, "reports": len(rows), "families": document["evaluation_families"],
        "results": [{k: v for k, v in m.items() if k != "confusion"} for m in results]}, indent=2))
    return document

if __name__ == "__main__":
    main()
