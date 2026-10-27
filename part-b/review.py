"""Validate attributed human or separate-agent reviews; freeze without guessing."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from corpus import ROOT, load_corpus, sha256
from taxonomy import CATEGORIES

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

def sheet_values(xml, strings):
    cells = {}
    for cell in ET.fromstring(xml).findall(".//s:sheetData/s:row/s:c", NS):
        address = cell.attrib["r"]
        if cell.find("s:f", NS) is not None:
            # Independent labels must be literal judgments, not calculated cells.
            cells[address] = {"formula": True}
            continue
        kind = cell.attrib.get("t", "")
        value = cell.find("s:v", NS)
        if kind == "inlineStr":
            cells[address] = "".join(t.text or "" for t in cell.findall(".//s:t", NS))
        elif kind == "s" and value is not None:
            cells[address] = strings[int(value.text)]
        else:
            cells[address] = value.text if value is not None else ""
    return cells

def read_workbook(path):
    with zipfile.ZipFile(path) as archive:
        if sum(f.file_size for f in archive.infolist()) > 40_000_000:
            raise ValueError("Review workbook is unexpectedly large.")
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(t.text or "" for t in si.findall(".//s:t", NS)) for si in root]
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {r.attrib["Id"]: r.attrib["Target"] for r in relationships}
        sheets = {}
        for sheet in ET.fromstring(archive.read("xl/workbook.xml")).findall("s:sheets/s:sheet", NS):
            target = targets[sheet.attrib[f"{{{NS['r']}}}id"]]
            filename = target.lstrip("/") if target.startswith("/") else "xl/" + target
            sheets[sheet.attrib["name"]] = sheet_values(archive.read(filename), strings)
    if "Review" not in sheets:
        raise ValueError("Expected the original Review worksheet.")
    if sheets.get("Provenance", {}).get("B6") == "agent":
        raise ValueError("This workbook contains agent judgments. Import its original provenance JSON with --agent-review, not as human labels.")
    cells = sheets["Review"]
    if cells.get("A6") != "Report ID" or cells.get("B6") != "Original report":
        raise ValueError("Keep the original review-sheet headers and report columns.")
    rows = []
    for i in range(7, 67):
        values = [cells.get(f"{col}{i}", "") for col in "ABCDEF"]
        if any(isinstance(value, dict) for value in values):
            raise ValueError(f"Row {i}: use literal values, not formulas.")
        rows.append(dict(zip(["report_id", "report", "category", "urgency", "needs_clarification", "reason"], values)))
    reviewer = sheets.get("Guide", {}).get("B4", "")
    if isinstance(reviewer, dict):
        raise ValueError("Enter the reviewer name as a literal value.")
    return rows, {"reviewer": reviewer, "review_date": sheets.get("Guide", {}).get("B5", "")}

def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"report_id", "report", "category", "urgency", "needs_clarification", "reason"} <= set(reader.fieldnames or []):
            raise ValueError("Expected the original CSV column names.")
        rows = list(reader)
        if any(r.get("reviewer_type") == "agent" or r.get("label_source") == "independent agent review" for r in rows):
            raise ValueError("This CSV contains agent judgments. Use --agent-review with the original provenance JSON.")
        return rows, {}

def browser_rows(state_dir):
    path = Path(state_dir) / "relay.sqlite3"
    if not path.exists():
        raise ValueError("No browser review database was found.")
    _, reports, _ = load_corpus()
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        saved = {r["report_id"]: dict(r) for r in db.execute("SELECT * FROM reviews")}
    rows = []
    for report in reports:
        label = saved.get(report["id"], {})
        rows.append({"report_id": report["id"], "report": report["text"],
            "category": label.get("category", ""), "urgency": label.get("urgency", ""),
            "needs_clarification": ("Yes" if label["clarification"] else "No") if label else "",
            "reason": label.get("reason", ""), "reviewer": label.get("reviewer", ""),
            "reviewed_at": label.get("updated_at", "")})
    return rows, {"source": "browser review snapshot"}

def normalize_reviews(rows, reports, reviewer="", reviewer_type="human"):
    if reviewer_type not in {"human", "agent"}:
        raise ValueError("Reviewer type must be human or agent.")
    expected = {r["id"]: r["text"] for r in reports}
    mapping = {key.casefold(): key for key in CATEGORIES}
    mapping.update({value["label"].casefold(): key for key, value in CATEGORIES.items()})
    mapping["unclear"] = "unclear"
    seen, labels, pending, errors = set(), [], [], []
    for row in rows:
        ident = str(row.get("report_id", "")).strip()
        if ident in seen:
            errors.append(f"Duplicate report ID: {ident}")
            continue
        seen.add(ident)
        if ident not in expected:
            errors.append(f"Unknown report ID: {ident}")
            continue
        if str(row.get("report", "")).replace("\r\n", "\n") != expected[ident]:
            errors.append(f"Original report was changed: {ident}")
            continue
        category = str(row.get("category", "")).strip().casefold()
        urgency = str(row.get("urgency", "")).strip().casefold()
        clarify = str(row.get("needs_clarification", "")).strip().casefold()
        author = str(row.get("reviewer") or reviewer).strip()
        reason = str(row.get("reason", "")).strip()
        if not category or not urgency or not clarify or not author:
            pending.append(ident)
            continue
        if category not in mapping or urgency not in {"urgent", "routine", "unclear"} or clarify not in {"yes", "no", "true", "false", "1", "0"}:
            errors.append(f"Invalid label: {ident}")
            continue
        clarification = clarify in {"yes", "true", "1"}
        if (category == "unclear" or urgency == "unclear" or clarification) and not reason:
            errors.append(f"Explain the missing facts: {ident}")
            continue
        labels.append({"id": ident, "category": mapping[category],
            "urgent": None if urgency == "unclear" else urgency == "urgent",
            "clarification": clarification, "reason": reason, "reviewer": author,
            "reviewed_at": row.get("reviewed_at") or None,
            "reviewer_type": reviewer_type,
            "label_source": f"independent {reviewer_type} review"})
    for ident in expected.keys() - seen:
        pending.append(ident)
    labels.sort(key=lambda r: r["id"])
    return labels, {"total": len(expected), "completed": len(labels),
        "pending": sorted(pending), "errors": errors,
        "unclear_category": sum(r["category"] == "unclear" for r in labels),
        "unclear_urgency": sum(r["urgent"] is None for r in labels)}

def freeze_labels(labels, status, output, source):
    if status["total"] != 60 or status["completed"] != 60 or status["pending"] or status["errors"]:
        raise ValueError("All 60 independent reviews must be complete and valid before freezing. Unclear labels are allowed.")
    types = {r.get("reviewer_type", "human") for r in labels}
    if len(labels) != 60 or len(types) != 1 or any(r.get("label_source") != f"independent {r.get('reviewer_type', 'human')} review" for r in labels):
        raise ValueError("All labels must retain their actual reviewer type and independent source.")
    if types == {"agent"} and (source.get("kind") != "independent agent" or not source.get("fresh_context") or not source.get("blind_inputs")):
        raise ValueError("Agent reviews require recorded fresh-context, blind-input provenance.")
    output = Path(output)
    manifest_path = output.with_suffix(".freeze.json")
    if output.exists() or manifest_path.exists():
        raise ValueError("Preserve existing labels. Choose a new output path for an explicitly documented revision.")
    text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in labels)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(text)
    manifest = {"status": "frozen independent review", "count": 60,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "labels_sha256": sha256(output), "reports_sha256": sha256(ROOT / "data/review_reports.jsonl"),
        "implementation_sha256": {name: sha256(ROOT / name) for name in ["engine.py", "taxonomy.py", "evaluate.py"]},
        "source": source, "reviewers": sorted({r["reviewer"] for r in labels}),
        "reviewer_types": sorted(types),
        "unclear_category": status["unclear_category"], "unclear_urgency": status["unclear_urgency"]}
    with manifest_path.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    return manifest

def read_agent_review(path, reports):
    document = json.loads(Path(path).read_text())
    if (document.get("reviewer_type") != "agent" or document.get("independent_human_review") is not False or
        not document.get("reviewer") or not document.get("method") or not document.get("input_files")):
        raise ValueError("Expected an attributed separate-agent review with a documented blind method.")
    expected = {r["id"]: r["text"] for r in reports}
    judgments = document.get("judgments", [])
    if not isinstance(judgments, list) or len(judgments) != 60:
        raise ValueError("Expected exactly 60 separate-agent judgments.")
    rows = []
    for r in judgments:
        if type(r.get("clarification")) is not bool:
            raise ValueError("Agent clarification must be a boolean.")
        rows.append({"report_id": r.get("id", ""), "report": expected.get(r.get("id"), ""),
            "category": r.get("category", ""), "urgency": r.get("urgency", ""),
            "needs_clarification": "Yes" if r["clarification"] else "No", "reason": r.get("reason", ""),
            "reviewer": document["reviewer"], "reviewed_at": document.get("completed_at")})
    metadata = {"kind": "independent agent", "reviewer_type": "agent", "reviewer": document["reviewer"],
        "file": Path(path).name, "sha256": sha256(path), "method": document["method"],
        "fresh_context": document.get("fresh_context", False), "blind_inputs": document.get("blind_inputs", {}),
        "guide_notes": document.get("guide_notes", [])}
    return rows, metadata

def main(argv=None):
    parser = argparse.ArgumentParser()
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--file", type=Path, help="completed original XLSX or exported CSV")
    sources.add_argument("--browser", action="store_true", help="read saved browser reviews without changing them")
    sources.add_argument("--agent-review", type=Path, help="separate-agent JSON with fresh-context provenance")
    parser.add_argument("--reviewer", default="", help="reviewer alias when absent from the file")
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "data/reviewed_labels.jsonl")
    args = parser.parse_args(argv)
    _, reports, _ = load_corpus()
    if args.agent_review:
        rows, metadata = read_agent_review(args.agent_review, reports)
        source = metadata
    elif args.browser:
        rows, metadata = browser_rows(os.environ.get("RELAY_STATE_DIR", str(ROOT / ".local")))
        source = metadata
    else:
        rows, metadata = read_workbook(args.file) if args.file.suffix.lower() == ".xlsx" else read_csv(args.file)
        source = {"file": args.file.name, "sha256": sha256(args.file), **metadata}
    labels, status = normalize_reviews(rows, reports, args.reviewer or metadata.get("reviewer", ""), metadata.get("reviewer_type", "human"))
    print(json.dumps(status, indent=2))
    if args.freeze:
        manifest = freeze_labels(labels, status, args.output, source)
        print(f"Frozen {manifest['count']} labels: {args.output}")
    return status

if __name__ == "__main__":
    main()
