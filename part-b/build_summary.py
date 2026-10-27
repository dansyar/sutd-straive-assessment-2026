"""Create the one-page business summary from actual benchmark JSON.

Optional authoring dependencies: reportlab and pypdf. Not needed by the demo.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
INK, MUTED, ACCENT = colors.HexColor("#20232c"), colors.HexColor("#5f6470"), colors.HexColor("#655bb0")

def pct(value):
    return "n/a" if value is None else f"{value:.0%}"

def name(row):
    return ("Rules" if row["method"] == "rules" else "Text") + " / " + ("Standard" if row["policy"] == "standard" else "Sensitive")

def build(path, output):
    data = json.loads(path.read_text())
    final = data["status"] == "independently reviewed test"
    diagnostic = data["status"] == "post-test diagnostic rerun"
    fresh = data["status"] == "fresh independently reviewed test"
    fresh2 = data.get("experiment") == "fresh2-20261022"
    rows = data["methods"]
    before = next(r for r in rows if r["method"] == "rules" and r["policy"] == "standard")
    after = next(r for r in rows if r["method"] == "rules" and r["policy"] == "sensitive")
    best = min(rows, key=lambda r: (r["cost_units_sensitive"], r["review_count"]))
    text_before = next(r for r in rows if r["method"] == "learned" and r["policy"] == "standard")
    text_after = next(r for r in rows if r["method"] == "learned" and r["policy"] == "sensitive")
    date = datetime.fromisoformat(data["generated_at"]).strftime("%d %B %Y")
    body = ParagraphStyle("Body", fontName="Helvetica", fontSize=10.2, leading=14.1, textColor=INK, spaceAfter=8)
    section = ParagraphStyle("Section", parent=body, fontName="Helvetica-Bold", fontSize=10.2, leading=13, textColor=ACCENT, spaceBefore=9, spaceAfter=4)
    caption = ParagraphStyle("Caption", parent=body, fontSize=8.4, leading=11.3, textColor=MUTED, spaceAfter=6)
    title = ParagraphStyle("Title", parent=body, fontName="Helvetica-Bold", fontSize=27, leading=31, spaceAfter=4)
    sub = ParagraphStyle("Subtitle", parent=body, fontSize=13, leading=18, spaceAfter=12)
    cell = ParagraphStyle("Cell", parent=caption, fontSize=9.2, leading=12, spaceAfter=0)
    cellright = ParagraphStyle("Numeric", parent=cell, alignment=TA_RIGHT)
    story = []
    def paragraph(text, style=body):
        story.append(Paragraph(text, style))
    paragraph("RELAY", title)
    paragraph("Incident triage for logistics", sub)
    label = 'FRESH 2 SYNTHETIC TEST' if fresh2 else 'FRESH SYNTHETIC TEST' if fresh else 'DIAGNOSTIC RETEST' if diagnostic else 'ORIGINAL SYNTHETIC TEST' if final else 'DEVELOPMENT EVIDENCE'
    paragraph(f"BUSINESS SUMMARY  /  {label}  /  {date.upper()}", caption)
    paragraph("The decision", section)
    paragraph("Keep routing <b>human-confirmed</b>. Text / Sensitive is the local demo default. " + (
        f"On the second new set, it gets 49/55 clear team labels correct ({pct(text_after['category_accuracy'])}) and catches all {text_after['urgent_total']} labeled urgent cases, while reviewing {text_after['review_count']}/{text_after['n']}. One wrong team outside model abstention remains."
        if fresh2 else
        f"On {data['evaluation_n']} new reports it caught {text_after['urgent_total']-text_after['urgent_misses']}/{text_after['urgent_total']} urgent cases, but missed a critical fire-alarm blocker and flagged {text_after['review_count']}/{text_after['n']} for review. This supports a work sample, not automatic operational routing."
        if fresh else
        "The revision corrects the observed cold-chain failure, but this retest reuses previously inspected cases. New independent validation is needed before operational use."
        if diagnostic else "The original test and its limited synthetic evidence remain preserved; operator validation is still needed."))
    paragraph("Problem and working prototype", section)
    paragraph("Relay proposes teams and urgency, flags uncertainty and records coordinator corrections. Compact queues lead from report to confirmation and Done; controls and evidence stay in Evaluation. The revision checks primary issues, cargo custody and active consequences. The missed fire-alarm controller now receives Safety/Urgent review in all four configurations. No real dispatch is sent." if fresh2 else "Relay proposes a receiving team and urgency for logistics incidents, flags uncertainty and records coordinator corrections. Compact queues lead from report to confirmation and Done; model controls and evidence stay in Evaluation. Shared checks compare stated temperature limits and readings and flag active exposures for review. No real dispatch is sent.")
    paragraph("Evidence", section)
    paragraph("Rules and TF-IDF centroids share the new evidence checks; training stays at 240 reports. There are 480 fictional reports, including three independently agent-labeled sets of 60. The revised classifier and Text/Sensitive choice were frozen before Fresh 2 was authored. A new fresh-context agent saw only new text and the unchanged guide. Labels were frozen before scoring; no tuning followed." if fresh2 else "Two approaches: rules and trained TF-IDF centroids, with shared cold-chain protection. There are 300 development reports (240 training, 48 families), 60 original test cases and 60 new scenarios. Before the new set was authored, the classifier and Text/Sensitive choice were frozen. Another fresh-context agent saw only new text and the unchanged guide. Labels were frozen before scoring; no tuning followed." if fresh else "Two approaches: rules and trained TF-IDF centroids, with shared cold-chain protection. There are 300 synthetic development reports (240 training, 48 training families) and 60 separate reference scenarios. A fresh-context agent judged the latter using only text and guide. The current rerun is diagnostic; original labels and results remain unchanged.", body)
    table_rows = [[Paragraph(t, cell if i == 0 else cellright) for i, t in enumerate([
        "Approach / policy", "Macro F1", "Urgent recall", "Review", "Cost*", "p95 ms"])] ]
    for row in rows:
        values = [name(row), "n/a" if row["macro_f1"] is None else f"{row['macro_f1']:.3f}", pct(row["urgent_recall"]),
                  f"{row['review_count']}/{row['n']}", str(row["cost_units_sensitive"]), f"{row['p95_ms']:.3f}"]
        table_rows.append([Paragraph(escape(v), cell if i == 0 else cellright) for i, v in enumerate(values)])
    width = A4[0] - 84
    table = Table(table_rows, colWidths=[width * p for p in [.32, .13, .17, .13, .12, .13]], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), .7, INK), ("LINEBELOW", (0, -1), (-1, -1), .4, colors.HexColor("#cdd0d7")),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(table)
    story.append(Spacer(1, 6))
    paragraph(f"*Relative cost with miss penalty 100 for every row. Category: {text_after['category_n']} known labels; urgency: {text_after['urgency_n']} known, including {text_after['urgent_total']} urgent. Unknowns remain unknown. Review uses all {text_after['n']}. Team accuracy is {pct(text_after['category_accuracy'])}; raw scores include reviewed cases. p95 excludes HTTP, startup and humans.", caption)
    paragraph("Changed requirement and workload", section)
    paragraph("On the same Fresh 2 reports, preserved v3 to v4 improves teams 46/55 to 49/55 (83.6% to 89.1%), F1 0.839 to 0.904 and false urgent alerts 7 to 5; reviews rise 41 to 43. Both catch all 13 urgent cases. This paired comparison was added after primary scoring, without tuning. Three remaining team disagreements concern operational versus Safety ownership of urgent blockers." if fresh2 else f"At a common missed-urgent penalty of 100, Text / Standard to Sensitive changes misses {text_before['urgent_misses']} to {text_after['urgent_misses']}, reviews {text_before['review_count']} to {text_after['review_count']}, and cost {text_before['cost_units_sensitive']} to {text_after['cost_units_sensitive']}. Text / Sensitive has {text_after['false_urgent']} false urgent alerts, {text_after['wrong_auto_routes']} wrong eligible teams and {text_after['required_review_automated']} bypassed required reviews. " + ("Only ten reports are eligible; this does not establish automatic-routing reliability. RLY-910052 still gets routine customs review despite a disabled building fire alarm." if fresh else f"Rules / Sensitive still misses {after['urgent_misses']} urgent cases."))
    paragraph("Economics, limits and next step", section)
    paragraph("At miss penalty 100, Text/Standard to Sensitive costs 54 to 59 and reviews 30 to 43, catching 8 to 10 required reviews. Sensitive is not cheapest on this set; it remains the preregistered conservative default. Review costs 1, wrong eligible team or bypassed review 6 once, false urgency 2, and every urgent miss 30 or 100 even in ordinary review. <b>USD 0 inference API calls</b> excludes compute, review/development services and labor; relative costs are assumptions, not savings." if fresh2 else "Both classifiers incur <b>USD 0 in inference API calls</b>; compute, development/review services and labor are excluded. Relative assumptions: review 1, wrong eligible route or bypassed required review 6 once, false urgency 2, missed priority 30 or 100 even during review. These are assumptions, not savings. Synthetic case selection, author knowledge of the classifier, shared model-family bias and guide ambiguity limit the fresh evidence." if fresh else "Both classifiers incur <b>USD 0 in inference API calls</b>; compute, development/review services and labor are excluded. Review 1, wrong eligible route or bypassed review 6 once, false urgency 2, missed priority 30 or 100 even during review. Reused cases, synthetic data and shared tooling limit this evidence.")
    paragraph("Synthetic selection, author knowledge, shared model-family bias and guide ambiguity limit the evidence. Next: operator guidance on critical-system team ownership, representative reports and measured review capacity. Any further tuned version needs another untouched set. No field trial has occurred." if fresh2 else "Next: clarify critical safety consequences with an operator, obtain representative reports and domain review, measure review capacity, and use another untouched set for any tuned version. No field trial has occurred.", body)
    paragraph("Evidence: " + str(path.relative_to(ROOT)) + ("; FRESH2-VALIDATION.md" if fresh2 else "; FRESH-VALIDATION.md") + "; EVALUATION.md. Manual prototype testing and feedback: dansyar (author-reported). Software, automated checks and evaluation: OpenAI Codex. Reference labels: separate Codex agents. Full roles in ATTRIBUTION.md.", caption)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=42, rightMargin=42,
        topMargin=34, bottomMargin=30, title="Relay - one-page business summary", author="dansyar, with OpenAI Codex assistance")
    doc.build(story)
    pages = len(PdfReader(output).pages)
    if pages != 1:
        raise ValueError(f"Business summary must be one page; got {pages}.")
    print(f"Created one-page business summary: {output}")

def main():
    parser = argparse.ArgumentParser()
    active = ROOT / "evidence/current.json"
    current = json.loads(active.read_text()) if active.exists() else {}
    default = ROOT / (current.get("fresh2") or current.get("fresh") or current.get("retest") or ("evidence/final-test.json" if (ROOT / "evidence/final-test.json").exists() else "evidence/development.json"))
    parser.add_argument("--evidence", type=Path, default=default)
    parser.add_argument("--output", type=Path, default=ROOT / "output/pdf/business-summary.pdf")
    args = parser.parse_args()
    build(args.evidence, args.output)

if __name__ == "__main__":
    main()
