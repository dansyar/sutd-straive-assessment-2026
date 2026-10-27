"""Disclosed exposed-case diagnostic and post-hoc paired frozen-version check."""
import argparse
import importlib.util
import json
import platform
from datetime import datetime, timezone

from corpus import ROOT, load_corpus, sha256
from engine import TextModel, triage
from evaluate import run_benchmark, requirement_change
from historical_review import fresh1_rows
from fresh2_evaluate import fresh_rows, write_new


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=lambda value: ROOT / value,
                        default=ROOT / "evidence/iterations/routing-v4")
    args = parser.parse_args()
    first_rows, first_freeze, _, development, _ = fresh1_rows()
    second_rows, second_freeze, registration, _, _ = fresh_rows()
    original_second = json.loads((ROOT / "evidence/fresh2-20261022/fresh-test.json").read_text())
    if original_second["implementation_sha256"] != registration["implementation_sha256"]:
        raise ValueError("The primary fresh-2 result does not match the frozen candidate.")
    model = TextModel(development)
    metrics, mistakes, predictions = run_benchmark(first_rows, model)
    trigger = next(row for row in first_rows if row["id"] == "RLY-910052")
    trigger_results = [triage(trigger["text"], model, method, policy)
                       for method in ["rules", "learned"] for policy in ["standard", "sensitive"]]
    assert all(r["category"] == "safety" and r["urgent"] and r["review"] for r in trigger_results)
    diagnostic = {"status": "post-test diagnostic rerun", "revision": "routing-v4", "dataset": "fresh1",
                  "generated_at": datetime.now(timezone.utc).isoformat(), "evaluation_n": len(first_rows),
                  "test_labels_sha256": first_freeze["labels_sha256"],
                  "implementation_sha256": registration["implementation_sha256"],
                  "evaluation_protocol": {"previously_exposed_cases": True,
                                          "limitation": "These labels and errors informed routing-v4; this is development evidence only."},
                  "methods": metrics, "requirement_change": requirement_change(metrics),
                  "trigger_case": {"id": trigger["id"], "all_four_configurations": trigger_results}}
    write_new(args.output / "fresh1-retest.json", diagnostic)
    write_new(args.output / "fresh1-retest-predictions.json", predictions)
    write_new(args.output / "fresh1-retest-mistakes.json", mistakes)

    archive = ROOT / "evidence/versions/temperature-v3-pre-routing-v4"
    old_engine = module_at("relay_compare_v3_engine", archive / "engine.py")
    old_evaluator = module_at("relay_compare_v3_evaluator", archive / "evaluate.py")
    old_evaluator.triage = old_engine.triage
    old_model = old_engine.TextModel(load_corpus(archive)[0])
    old_metrics, old_mistakes, old_predictions = old_evaluator.run_benchmark(second_rows, old_model)
    comparison = {"status": "paired frozen-version comparison", "generated_at": datetime.now(timezone.utc).isoformat(),
                  "python": platform.python_version(), "reports": len(second_rows),
                  "labels_sha256": second_freeze["labels_sha256"],
                  "primary_fresh_test": "evidence/fresh2-20261022/fresh-test.json",
                  "comparison_added_after_primary_results": True,
                  "protocol": "Both classifier versions were frozen before these reports were authored. Score exactly the same unchanged reports and labels; no retraining or tuning follows. This paired comparison was added after primary scoring and did not select a candidate.",
                  "old": {"revision": "temperature-v3", "engine_sha256": sha256(archive / "engine.py"), "methods": old_metrics},
                  "new": {"revision": "routing-v4", "engine_sha256": sha256(ROOT / "engine.py"), "methods": original_second["methods"]}}
    write_new(args.output / "paired-fresh2-versions.json", comparison)
    write_new(args.output / "fresh2-v3-predictions.json", old_predictions)
    write_new(args.output / "fresh2-v3-mistakes.json", old_mistakes)
    selected = lambda records: next(r for r in records if r["method"] == "learned" and r["policy"] == "sensitive")
    keys = ["category_accuracy", "macro_f1", "urgent_misses", "urgent_total", "false_urgent", "review_count", "cost_units_sensitive"]
    print(json.dumps({"fresh1_exposed_diagnostic": {k: selected(metrics)[k] for k in keys},
                      "same_fresh2_old_version": {k: selected(old_metrics)[k] for k in keys},
                      "same_fresh2_new_version": {k: selected(original_second["methods"])[k] for k in keys}}, indent=2))


if __name__ == "__main__":
    main()
