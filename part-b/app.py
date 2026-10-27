"""Local Relay demo. No dispatch integration; all decisions remain local."""
from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator

from engine import ENGINE_VERSION, TextModel, routing_queue, triage
from corpus import load_corpus, sha256
from evaluate import reviewed_rows
from historical_review import fresh1_rows
from taxonomy import CATEGORIES, COSTS, GUIDE, POLICIES

ROOT = Path(__file__).resolve().parent
LOCAL = Path(os.environ.get("RELAY_STATE_DIR", str(ROOT / ".local")))
LOCAL.mkdir(parents=True, exist_ok=True)
DB = LOCAL / "relay.sqlite3"
development, review_reports, _ = load_corpus()
review_ids = {r["id"] for r in review_reports}
model = TextModel(development)

@contextmanager
def connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()

with connection() as db:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS incidents(id TEXT PRIMARY KEY, text TEXT, channel TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY AUTOINCREMENT, report_id TEXT,
            category TEXT, urgent INTEGER, note TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS reviews(report_id TEXT PRIMARY KEY, category TEXT, urgency TEXT,
            clarification INTEGER, reason TEXT, reviewer TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS review_history(id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT, category TEXT, urgency TEXT, clarification INTEGER, reason TEXT,
            reviewer TEXT, updated_at TEXT);
    """)

app = FastAPI(title="Relay incident desk", docs_url="/api/docs")

class TriageInput(BaseModel):
    text: str = Field(min_length=12, max_length=6000)
    method: Literal["rules", "learned"] = "learned"
    policy: Literal["standard", "sensitive"] = "sensitive"
    save: bool = False

    @field_validator("text", mode="before")
    @classmethod
    def trim_report(cls, value):
        return value.strip() if isinstance(value, str) else value

class DecisionInput(BaseModel):
    category: Literal["delay", "missing", "damage", "temperature", "safety", "documentation"]
    urgent: bool
    note: str = Field(default="", max_length=1000)

class ReviewInput(BaseModel):
    category: Literal["delay", "missing", "damage", "temperature", "safety", "documentation", "unclear"]
    urgency: Literal["urgent", "routine", "unclear"]
    clarification: bool
    reason: str = Field(default="", max_length=1000)
    reviewer: str = Field(min_length=1, max_length=80)

    @model_validator(mode="after")
    def meaningful(self):
        if not self.reviewer.strip():
            raise ValueError("Enter your reviewer name.")
        if (self.category == "unclear" or self.urgency == "unclear" or self.clarification) and not self.reason.strip():
            raise ValueError("Explain the missing or conflicting facts.")
        return self

def now():
    return datetime.now(timezone.utc).isoformat()

def current_evaluation():
    path = ROOT / "evidence/current.json"
    return read_record(path, "The evaluation index could not be read.") if path.exists() else {}

def read_record(path, detail):
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise HTTPException(503, detail) from error
    if not isinstance(payload, dict):
        raise HTTPException(503, detail)
    return payload

def project_path(relative):
    if not isinstance(relative, str) or not relative:
        raise HTTPException(503, "Invalid evaluation record path.")
    try:
        path = (ROOT / relative).resolve()
    except (ValueError, OSError) as error:
        raise HTTPException(503, "Invalid evaluation record path.") from error
    if not path.is_relative_to(ROOT.resolve()):
        raise HTTPException(503, "Invalid evaluation record path.")
    return path

def seed_incidents():
    seen, rows = set(), []
    for row in development:
        if row["split"] != "train" or row["family"] in seen:
            continue
        seen.add(row["family"])
        rows.append({k: row[k] for k in ["id", "text", "channel"]})
    return rows

def all_incidents():
    with connection() as db:
        custom = [dict(r) for r in db.execute("SELECT * FROM incidents ORDER BY created_at DESC")]
    return custom + seed_incidents()

@app.get("/api/health")
def health():
    return {"status": "ok", "dataset": "synthetic", "train": model.train_count}

@app.get("/api/config")
def config():
    return {"categories": CATEGORIES, "policies": POLICIES, "costs": COSTS, "guide": GUIDE,
            "development_n": 300, "train_n": 240, "validation_n": 60, "review_n": 60,
            "default_evidence_dataset": "fresh2" if current_evaluation().get("fresh2") else "fresh" if current_evaluation().get("fresh") else "retest" if current_evaluation().get("retest") else "development",
            "revision": ENGINE_VERSION}

@app.get("/api/incidents")
def incidents(method: Literal["rules", "learned"]="learned", policy: Literal["standard", "sensitive"]="sensitive"):
    with connection() as db:
        decisions = {r["report_id"]: dict(r) for r in db.execute("SELECT * FROM decisions ORDER BY id")}
    rows = []
    for report in all_incidents():
        prediction = triage(report["text"], model, method, policy)
        decision = decisions.get(report["id"])
        rows.append({**report, "prediction": prediction, "decision": decision,
                     "queue": routing_queue(prediction, bool(decision))})
    rows.sort(key=lambda r: (bool(r["decision"]), not r["prediction"]["urgent"], not r["prediction"]["review"], r["id"]))
    return rows

@app.post("/api/triage")
def classify(body: TriageInput):
    if not body.text.strip():
        raise HTTPException(422, "Enter an incident report.")
    result = {"prediction": triage(body.text, model, body.method, body.policy)}
    if body.save:
        import secrets
        ident = "NEW-" + secrets.token_hex(3).upper()
        with connection() as db:
            db.execute("INSERT INTO incidents VALUES(?,?,?,?)", (ident, body.text.strip(), "Demo entry", now()))
        result.update({"id": ident, "text": body.text.strip()})
    return result

@app.post("/api/incidents/{report_id}/decision")
def save_decision(report_id: str, body: DecisionInput):
    if report_id not in {r["id"] for r in all_incidents()}:
        raise HTTPException(404, "Report not found.")
    stamp = now()
    with connection() as db:
        db.execute("INSERT INTO decisions(report_id,category,urgent,note,created_at) VALUES(?,?,?,?,?)",
                   (report_id, body.category, int(body.urgent), body.note.strip(), stamp))
    return {"saved": True, "scope": "local demo", "created_at": stamp}

@app.get("/api/audit")
def audit():
    with connection() as db:
        return [dict(r) for r in db.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT 10")]

@app.get("/api/evidence")
def evidence(dataset: Literal["development", "test", "retest", "fresh", "fresh2"]="development"):
    active = current_evaluation()
    if dataset in {"fresh", "fresh2"} and not active.get(dataset):
        raise HTTPException(503, "This report set does not have a saved evaluation.")
    relative = "evidence/final-test.json" if dataset == "test" else active.get(dataset, "evidence/development.json" if dataset == "development" else "evidence/retest.json")
    path = project_path(relative)
    if not path.exists():
        raise HTTPException(503, "Complete and freeze independent reviews before final testing." if dataset == "test"
                            else "Run evaluate.py to create the development benchmark.")
    payload = read_record(path, "The saved evaluation could not be read.")
    if (type(payload.get("evaluation_n")) is not int or payload["evaluation_n"] < 1
            or not isinstance(payload.get("methods"), list) or not payload["methods"]
            or not isinstance(payload.get("implementation_sha256"), dict)
            or not payload["implementation_sha256"]):
        raise HTTPException(503, "The saved evaluation is incomplete.")
    if dataset in {"fresh", "fresh2"}:
        from fresh2_evaluate import fresh_rows
        if not isinstance(payload.get("review_provenance"), dict):
            raise HTTPException(503, "The saved evaluation is missing its review attribution.")
        try:
            _, freeze, _, _, _ = fresh1_rows() if dataset == "fresh" else fresh_rows()
            if payload.get("test_labels_sha256") != freeze["labels_sha256"]:
                raise ValueError("The fresh results do not match frozen labels.")
        except (ValueError, OSError, KeyError, TypeError) as error:
            raise HTTPException(503, str(error)) from error
    implementation = project_path("evidence/versions/temperature-v3-pre-routing-v4") if dataset == "fresh" else ROOT
    if dataset != "test" and active:
        try:
            stale = any(name not in {"engine.py", "taxonomy.py", "evaluate.py", "corpus.py"}
                        or not isinstance(expected, str)
                        or not (implementation / name).is_file()
                        or sha256(implementation / name) != expected
                        for name, expected in payload["implementation_sha256"].items())
        except OSError as error:
            raise HTTPException(503, "The saved evaluation could not be verified.") from error
        if stale:
            raise HTTPException(503, "The active evaluation is stale. Rerun the current implementation into a new output folder.")
    test_path = ROOT / "evidence/final-test.json"
    test = read_record(test_path, "The original evaluation could not be read.") if test_path.exists() else None
    if test and (type(test.get("evaluation_n")) is not int
                 or not isinstance(test.get("review_provenance"), dict)):
        raise HTTPException(503, "The original evaluation is incomplete.")
    with connection() as db:
        count = db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    payload["independent_review"] = {"completed": max(count, test["evaluation_n"] if test else 0), "total": 60,
        "reviewer_types": test.get("review_provenance", {}).get("reviewer_types", []) if test else [],
        "final_test": "available" if test else "pending review and label freeze"}
    if dataset in {"fresh", "fresh2"}:
        payload["independent_review"] = {"completed": payload["evaluation_n"], "total": payload["evaluation_n"],
            "reviewer_types": payload["review_provenance"]["reviewer_types"], "final_test": "available"}
    payload["available_datasets"] = [{"id": "fresh2", "label": "Fresh 2"}] if active.get("fresh2") else []
    if active.get("fresh"):
        payload["available_datasets"].append({"id": "fresh", "label": "Fresh 1"})
    if active.get("retest"):
        payload["available_datasets"].append({"id": "retest", "label": "Retest"})
    payload["available_datasets"].append({"id": "development", "label": "Development"})
    if test:
        payload["available_datasets"].append({"id": "test", "label": "Original test"})
    return payload

def quality_reviews():
    from fresh2_evaluate import fresh_rows

    document = read_record(ROOT / "evidence/reviews/quality-20261024/review.json",
                           "The completed review could not be read.")
    if (document.get("reviewer") != "review_all_sixty" or document.get("reviewer_type") != "agent"
            or document.get("label_source") != "post-test assistant review" or document.get("blind") is not False
            or not isinstance(document.get("reviewed_at"), str) or not document["reviewed_at"].strip()):
        raise HTTPException(503, "The completed review has invalid attribution.")
    try:
        datetime.fromisoformat(document["reviewed_at"].replace("Z", "+00:00"))
        reports, _, _, _, _ = fresh_rows()
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise HTTPException(503, "The completed review source could not be verified.") from error
    by_id = {row["id"]: row for row in reports}
    judgments = document.get("rows")
    if (not isinstance(judgments, list) or len(judgments) != 60 or len(by_id) != 60
            or any(not isinstance(row, dict) or not isinstance(row.get("id"), str) for row in judgments)
            or len({row["id"] for row in judgments}) != 60 or {row["id"] for row in judgments} != set(by_id)):
        raise HTTPException(503, "The completed review must contain all 60 reports exactly once.")
    result = []
    for row in judgments:
        reference = by_id[row["id"]]
        if (not isinstance(row.get("category"), str) or row["category"] not in {*CATEGORIES, "unclear"}
                or not isinstance(row.get("urgency"), str) or row["urgency"] not in {"urgent", "routine", "unclear"}
                or type(row.get("clarification")) is not bool
                or not isinstance(row.get("reason"), str) or not row["reason"].strip()
                or type(row.get("agrees_with_reference")) is not bool
                or not isinstance(row.get("disagreement_note"), str)
                or (not row["agrees_with_reference"] and not row["disagreement_note"].strip())):
            raise HTTPException(503, "The completed review contains an invalid judgment.")
        reference_urgency = "unclear" if reference["urgent"] is None else "urgent" if reference["urgent"] else "routine"
        agrees = (row["category"] == reference["category"] and row["urgency"] == reference_urgency
                  and row["clarification"] == reference["clarification"])
        if row["agrees_with_reference"] != agrees:
            raise HTTPException(503, "A review agreement flag does not match the reference labels.")
        result.append({"id": row["id"], "text": reference["text"], "readonly": True,
            "review": {key: row[key] for key in ["category", "urgency", "clarification", "reason",
                                                  "agrees_with_reference", "disagreement_note"]}})
        result[-1]["review"].update({"reviewer": document["reviewer"], "reviewer_type": document["reviewer_type"],
                                    "label_source": document["label_source"], "updated_at": document["reviewed_at"]})
    return result

@app.get("/api/review")
def review(source: Literal["auto", "human", "independent", "fresh", "fresh2", "quality"]="auto"):
    if source == "quality":
        return quality_reviews()
    path = ROOT / "data/reviewed_labels.jsonl"
    if source in {"fresh", "fresh2"} or (source != "human" and path.exists()):
        if source in {"fresh", "fresh2"}:
            from fresh2_evaluate import fresh_rows
            try:
                labels, _, _, _, _ = fresh1_rows() if source == "fresh" else fresh_rows()
            except (ValueError, OSError, KeyError, TypeError) as error:
                raise HTTPException(503, str(error)) from error
        else:
            preserved = project_path(current_evaluation().get("frozen_implementation", "evidence/versions/v1"))
            try:
                labels = reviewed_rows(path, implementation_root=preserved if preserved.exists() else ROOT)
            except (ValueError, OSError, KeyError, TypeError) as error:
                raise HTTPException(503, str(error)) from error
        return [{"id": r["id"], "text": r["text"], "readonly": True,
            "review": {"category": r["category"], "urgency": "unclear" if r["urgent"] is None else "urgent" if r["urgent"] else "routine",
                "clarification": r["clarification"], "reason": r["reason"], "reviewer": r["reviewer"],
                "reviewer_type": r.get("reviewer_type", "human"), "label_source": r["label_source"],
                "updated_at": r.get("reviewed_at") or ""}} for r in labels]
    if source == "independent":
        raise HTTPException(503, "The independent review has not been frozen.")
    with connection() as db:
        saved = {r["report_id"]: dict(r) for r in db.execute("SELECT * FROM reviews")}
    # Deliberately no prediction, channel, family, generated label or urgency.
    return [{"id": r["id"], "text": r["text"], "review": saved.get(r["id"])} for r in review_reports]

@app.post("/api/review/{report_id}")
def save_review(report_id: str, body: ReviewInput):
    if report_id not in review_ids:
        raise HTTPException(404, "Review report not found.")
    values = (report_id, body.category, body.urgency, int(body.clarification),
              body.reason.strip(), body.reviewer.strip(), now())
    with connection() as db:
        db.execute("INSERT OR REPLACE INTO reviews VALUES(?,?,?,?,?,?,?)", values)
        db.execute("INSERT INTO review_history(report_id,category,urgency,clarification,reason,reviewer,updated_at) VALUES(?,?,?,?,?,?,?)", values)
    return {"saved": True}

@app.get("/api/review/export")
def export_review(source: Literal["auto", "human", "independent", "fresh", "fresh2", "quality"]="auto"):
    rows = review(source)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    headers = ["report_id", "report", "category", "urgency", "needs_clarification", "reason", "reviewer", "reviewed_at", "reviewer_type", "label_source"]
    if source == "quality":
        headers.extend(["agrees_with_reference", "disagreement_note"])
    writer.writerow(headers)
    for row in rows:
        label = row["review"] or {}
        cells = [row["id"], row["text"], label.get("category", ""), label.get("urgency", ""),
            ("Yes" if label["clarification"] else "No") if label else "", label.get("reason", ""),
            label.get("reviewer", ""), label.get("updated_at", ""), label.get("reviewer_type", "human") if label else "",
            label.get("label_source", "independent human review") if label else ""]
        if source == "quality":
            cells.extend(["Yes" if label["agrees_with_reference"] else "No", label["disagreement_note"]])
        # CSV quoting alone does not stop spreadsheet applications evaluating formulas.
        writer.writerow(["'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@"))
                         else value for value in cells])
    filename = "relay-completed-review.csv" if source == "quality" else "relay-fresh2-review.csv" if source == "fresh2" else "relay-fresh-review.csv" if source == "fresh" else "relay-independent-review.csv"
    return Response(buffer.getvalue(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})

@app.get("/review-workbook")
def workbook(source: Literal["auto", "human"]="auto"):
    path = ROOT / "output/review/review_60_reports.xlsx" if source != "human" and (ROOT / "data/reviewed_labels.jsonl").exists() else ROOT / "output/review/review_template.xlsx"
    if source == "human" and not path.exists():
        path = ROOT / "outputs/relay-review-20261021/review_60_reports.xlsx"
    if not path.exists():
        raise HTTPException(404, "Use the browser review or CSV export.")
    return FileResponse(path, filename="review_60_reports.xlsx")

app.mount("/assets", StaticFiles(directory=ROOT / "web"), name="assets")

@app.get("/")
def home():
    return FileResponse(ROOT / "web/index.html", headers={"Cache-Control": "no-store"})
