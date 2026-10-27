"""Behavioral checks. Test reviews use temporary databases, never the user's work."""
import copy
import csv
import importlib
import io
import json
import os
import shutil
import sqlite3
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx

from corpus import load_corpus, sha256
from engine import TextModel, rule_prediction, routing_queue, tokens, triage
from evaluate import reviewed_rows, summarize
from review import freeze_labels, normalize_reviews, read_agent_review, sheet_values


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.development, _, _ = load_corpus()
        cls.model = TextModel(cls.development)

    def test_group_split_and_training_only_vocabulary(self):
        self.assertEqual(self.model.train_count, 240)
        modified = copy.deepcopy(self.development)
        for row in modified:
            if row["split"] == "validation":
                row["text"] = "unseenvalidationcanary"
        other = TextModel(modified)
        self.assertEqual(self.model.idf, other.idf)
        self.assertEqual(self.model.centroids, other.centroids)
        self.assertNotIn("unseenvalidationcanary", other.idf)

    def test_word_boundaries_and_negation(self):
        result = rule_prediction("Operations note — This incident is isolated and resolved.")
        self.assertNotIn("dent", result["signals"])
        self.assertNotIn("late", result["signals"])
        self.assertLess(result["urgent_margin"], 0)
        self.assertGreater(rule_prediction("The area is not isolated; smoke is spreading.")["urgent_margin"], 0)
        self.assertIn("not", tokens("This parcel is not missing."))

    def test_wrapper_does_not_change_text_features(self):
        text = "The pallet has cracked boards and torn wrapping."
        self.assertEqual(tokens(text), tokens("Operations note — " + text))
        self.assertEqual(tokens(text), tokens(text + " Please advise the next team."))

    def test_unknown_report_defers(self):
        for method in ["rules", "learned"]:
            pred = triage("qwerty zzzxxx bbbccc", self.model, method)
            self.assertTrue(pred["review"])
            self.assertTrue(pred["review_reasons"])

    def test_exclusive_priority_queues_preserve_review_flag(self):
        pred = {"urgent": True, "review": True}
        self.assertEqual(routing_queue(pred), "urgent")
        self.assertTrue(pred["review"])
        self.assertEqual(routing_queue({"urgent": False, "review": True}), "review")
        self.assertEqual(routing_queue({"urgent": False, "review": False}), "routine")
        self.assertEqual(routing_queue(pred, confirmed=True), "done")


class MetricTests(unittest.TestCase):
    def test_urgent_miss_cost_survives_ordinary_review(self):
        truth = [{"category": "delay", "urgent": True, "clarification": False}]
        pred = [{"category": "delay", "urgent": False, "review": True}]
        standard = summarize(truth, pred, "standard")
        sensitive = summarize(truth, pred, "sensitive")
        self.assertEqual(standard["urgent_misses"], 1)
        self.assertEqual(standard["cost_units_standard"], 31)
        self.assertEqual(standard["cost_units_sensitive"], 101)
        self.assertEqual(standard["cost_units_sensitive"], sensitive["cost_units_sensitive"])
        self.assertEqual(standard["unsafe_auto_urgent_misses"], 0)

    def test_unclear_is_not_routine_or_a_forced_category(self):
        truth = [{"category": "unclear", "urgent": None, "clarification": False}]
        pred = [{"category": "damage", "urgent": True, "review": False}]
        metrics = summarize(truth, pred, "standard")
        self.assertIsNone(metrics["category_accuracy"])
        self.assertIsNone(metrics["urgent_recall"])
        self.assertEqual(metrics["urgency_n"], 0)
        self.assertEqual(metrics["false_urgent"], 0)
        self.assertEqual(metrics["required_review_automated"], 1)
        self.assertEqual(metrics["unknown_labels_automated"], 1)
        self.assertEqual(metrics["cost_units_standard"], 6)

    def test_wrong_route_and_bypassed_review_are_not_double_counted(self):
        truth = [{"category": "delay", "urgent": False, "clarification": True}]
        pred = [{"category": "damage", "urgent": True, "review": False}]
        self.assertEqual(summarize(truth, pred, "standard")["cost_units_standard"], 8)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.reports = [{"id": "FIXTURE-1", "text": "Fictional unit test text."}]
        self.row = {"report_id": "FIXTURE-1", "report": self.reports[0]["text"],
            "category": "Delivery delay", "urgency": "Routine", "needs_clarification": "No", "reason": ""}

    def test_blank_reviews_remain_pending(self):
        row = {**self.row, "category": ""}
        labels, status = normalize_reviews([row], self.reports, "Test fixture")
        self.assertEqual(labels, [])
        self.assertEqual(status["pending"], ["FIXTURE-1"])

    def test_display_names_and_unknowns_are_preserved(self):
        labels, status = normalize_reviews([self.row], self.reports, "Test fixture")
        self.assertEqual(labels[0]["category"], "delay")
        self.assertEqual(status["errors"], [])
        row = {**self.row, "category": "Unclear", "urgency": "Unclear", "reason": "The relevant facts are absent."}
        labels, status = normalize_reviews([row], self.reports, "Test fixture")
        self.assertEqual(labels[0]["category"], "unclear")
        self.assertIsNone(labels[0]["urgent"])
        self.assertEqual(status["unclear_urgency"], 1)

    def test_missing_reason_and_source_changes_are_rejected(self):
        for altered in [{"urgency": "Unclear"}, {"needs_clarification": "Yes"}, {"report": "Changed text"}]:
            _, status = normalize_reviews([{**self.row, **altered}], self.reports, "Test fixture")
            self.assertTrue(status["errors"])
        _, status = normalize_reviews([self.row, self.row], self.reports, "Test fixture")
        self.assertTrue(any("Duplicate" in error for error in status["errors"]))

    def test_xlsx_literals_shared_strings_and_formula_detection(self):
        xml = '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="7"><c r="C7" t="s"><v>0</v></c><c r="D7" t="inlineStr"><is><t>Routine</t></is></c><c r="E7"><f>1+1</f><v>2</v></c></row></sheetData></worksheet>'
        cells = sheet_values(xml, ["Delivery delay"])
        self.assertEqual(cells["C7"], "Delivery delay")
        self.assertEqual(cells["D7"], "Routine")
        self.assertEqual(cells["E7"], {"formula": True})

    def test_separate_agent_import_retains_actual_source(self):
        reports = [{"id": f"FIXTURE-{i}", "text": f"Unit test report {i}"} for i in range(60)]
        document = {"reviewer_type": "agent", "reviewer": "Separate fixture agent", "independent_human_review": False,
            "method": "Isolated fixture", "input_files": ["reports.jsonl", "guide.txt"], "fresh_context": True,
            "blind_inputs": {"reports_sha256": "fixture"}, "judgments": [{"id": r["id"], "category": "unclear",
                "urgency": "unclear", "clarification": True, "reason": "Fixture, not a real review"} for r in reports]}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "agent.json"
            path.write_text(json.dumps(document))
            rows, metadata = read_agent_review(path, reports)
            labels, status = normalize_reviews(rows, reports, metadata["reviewer"], metadata["reviewer_type"])
            self.assertEqual(status["completed"], 60)
            self.assertTrue(all(r["label_source"] == "independent agent review" and r["reviewer_type"] == "agent" for r in labels))
            self.assertTrue(all(r["urgent"] is None for r in labels))
            document["independent_human_review"] = True
            path.write_text(json.dumps(document))
            with self.assertRaises(ValueError):
                read_agent_review(path, reports)

    def test_freeze_requires_complete_reviews_and_protects_source_and_code(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").mkdir()
            (root / "data/review_reports.jsonl").write_text("test-only source fixture")
            for name in ["engine.py", "taxonomy.py", "evaluate.py"]:
                (root / name).write_text("test-only implementation fixture")
            output = root / "labels.jsonl"
            with self.assertRaises(ValueError):
                freeze_labels([], {"total": 60, "completed": 0, "pending": ["x"], "errors": []}, output, {})
            reports = [{"id": f"FIXTURE-{i}", "text": f"Unit test report {i}"} for i in range(60)]
            labels = [{"id": r["id"], "category": "unclear", "urgent": None,
                "clarification": True, "reason": "Test fixture", "reviewer": "Unit test fixture",
                "label_source": "independent human review"} for r in reports]
            status = {"total": 60, "completed": 60, "pending": [], "errors": [], "unclear_category": 60, "unclear_urgency": 60}
            with patch("review.ROOT", root), patch("evaluate.ROOT", root), patch("evaluate.load_corpus", return_value=([], reports, {})):
                freeze_labels(labels, status, output, {"kind": "isolated unit test fixture"})
                self.assertEqual(len(reviewed_rows(output)), 60)
                archive = root / "preserved"
                archive.mkdir()
                for filename in ["engine.py", "taxonomy.py", "evaluate.py"]:
                    shutil.copyfile(root / filename, archive / filename)
                with self.assertRaises(ValueError):
                    freeze_labels(labels, status, output, {})
                (root / "engine.py").write_text("changed implementation fixture")
                with self.assertRaisesRegex(ValueError, "implementation changed"):
                    reviewed_rows(output)
                self.assertEqual(len(reviewed_rows(output, implementation_root=archive)), 60)
                (archive / "engine.py").write_text("tampered archive fixture")
                with self.assertRaisesRegex(ValueError, "implementation changed"):
                    reviewed_rows(output, implementation_root=archive)
                (root / "engine.py").write_text("test-only implementation fixture")
                output.write_text(output.read_text() + "\n")
                with self.assertRaisesRegex(ValueError, "labels or source reports changed"):
                    reviewed_rows(output)


class ApiTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        with patch.dict(os.environ, {"RELAY_STATE_DIR": str(Path(cls.folder.name) / "isolated/state")}):
            cls.module = importlib.import_module("app")

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    async def asyncSetUp(self):
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.module.app), base_url="http://relay.test")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_real_triage_correction_and_persistence(self):
        result = await self.client.post("/api/triage", json={"text": "A pallet has crushed cartons and broken glass. No active hazard remains.", "save": True})
        self.assertEqual(result.status_code, 200)
        created = result.json()
        self.assertEqual(created["prediction"]["method"], "learned")
        self.assertEqual(created["prediction"]["policy"], "sensitive")
        response = await self.client.post(f"/api/incidents/{created['id']}/decision", json={"category": "damage", "urgent": False, "note": "Test fixture confirmed"})
        self.assertEqual(response.status_code, 200)
        rows = (await self.client.get("/api/incidents")).json()
        row = next(r for r in rows if r["id"] == created["id"])
        self.assertEqual(row["queue"], "done")
        self.assertEqual(row["decision"]["note"], "Test fixture confirmed")
        for row in rows:
            if not row["decision"] and row["prediction"]["urgent"]:
                self.assertEqual(row["queue"], "urgent")

    async def test_report_length_uses_trimmed_text_and_does_not_save_invalid_reports(self):
        with self.module.connection() as db:
            before = db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        for text in [" " * 12, "         short         ", "\n\t tiny \n\t"]:
            response = await self.client.post("/api/triage", json={"text": text, "save": True})
            self.assertEqual(response.status_code, 422)
        with self.module.connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0], before)
        text = "A document is missing from the clearance packet."
        with patch.object(self.module, "triage", wraps=self.module.triage) as classifier:
            response = await self.client.post("/api/triage", json={"text": "  " + text + "\n", "save": True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], text)
        self.assertEqual(classifier.call_args.args[0], text)

    async def test_database_connections_close_and_failed_writes_roll_back(self):
        with self.module.connection() as db:
            self.assertEqual(db.execute("SELECT 1").fetchone()[0], 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            db.execute("SELECT 1")
        with self.assertRaisesRegex(RuntimeError, "rollback fixture"):
            with self.module.connection() as failed:
                failed.execute("INSERT INTO incidents VALUES(?,?,?,?)", ("ROLLBACK-FIXTURE", "Isolated fixture", "Test", "2026-10-24"))
                raise RuntimeError("rollback fixture")
        with self.module.connection() as check:
            self.assertIsNone(check.execute("SELECT id FROM incidents WHERE id='ROLLBACK-FIXTURE'").fetchone())
        with self.assertRaises(sqlite3.ProgrammingError):
            failed.execute("SELECT 1")

    async def test_temperature_excursion_is_urgent_for_each_method_and_policy(self):
        text = "The cold compartment is at 19 C with sensitive cargo still inside. Product limits are 2 to 8 C and immediate isolation is needed."
        for method in ["rules", "learned"]:
            for policy in ["standard", "sensitive"]:
                result = await self.client.post("/api/triage", json={"text": text, "method": method, "policy": policy})
                self.assertEqual(result.status_code, 200)
                pred = result.json()["prediction"]
                self.assertEqual(pred["team"], "Cold-chain quality")
                self.assertTrue(pred["urgent"])
                self.assertTrue(pred["review"])

    async def test_blind_review_and_revision_history(self):
        response = await self.client.get("/api/review?source=human")
        rows = response.json()
        self.assertEqual(len(rows), 60)
        self.assertTrue(all(set(r) == {"id", "text", "review"} for r in rows))
        self.assertTrue(all("prediction" not in r for r in rows))
        ident = rows[0]["id"]
        body = {"category": "unclear", "urgency": "unclear", "clarification": True,
                "reason": "Isolated API fixture; not a human review", "reviewer": "Unit test fixture"}
        self.assertEqual((await self.client.post(f"/api/review/{ident}", json=body)).status_code, 200)
        body["reason"] = "Revised isolated API fixture"
        self.assertEqual((await self.client.post(f"/api/review/{ident}", json=body)).status_code, 200)
        with self.module.connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM review_history WHERE report_id=?", (ident,)).fetchone()[0], 2)
        export = await self.client.get("/api/review/export?source=human")
        self.assertIn("Revised isolated API fixture", export.text)
        self.assertNotIn("prediction", export.text)

    async def test_independent_view_is_readonly_and_exports_attribution(self):
        fixture = [{"id": "FIXTURE-READONLY", "text": "Isolated source fixture.", "category": "unclear",
            "urgent": None, "clarification": True, "reason": "Fixture reason", "reviewer": "Separate fixture agent",
            "reviewer_type": "agent", "label_source": "independent agent review"}]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").mkdir()
            (root / "data/reviewed_labels.jsonl").write_text("fixture placeholder")
            with patch.object(self.module, "ROOT", root), patch.object(self.module, "reviewed_rows", return_value=fixture):
                result = (await self.client.get("/api/review")).json()
                self.assertTrue(result[0]["readonly"])
                self.assertEqual(result[0]["review"]["urgency"], "unclear")
                self.assertEqual(result[0]["review"]["reviewer_type"], "agent")
                export = await self.client.get("/api/review/export")
                self.assertIn("independent agent review", export.text)
                manual = (await self.client.get("/api/review?source=human")).json()
                self.assertTrue(all(not r.get("readonly") for r in manual))

    async def test_invalid_labels_and_missing_final_test_are_explicit(self):
        self.assertEqual((await self.client.post("/api/triage", json={"text": "short"})).status_code, 422)
        body = {"category": "unclear", "urgency": "unclear", "clarification": True, "reason": "", "reviewer": "Fixture"}
        self.assertEqual((await self.client.post("/api/review/not-real", json=body)).status_code, 422)
        body["reason"] = "Fixture"
        self.assertEqual((await self.client.post("/api/review/not-real", json=body)).status_code, 404)
        if not (self.module.ROOT / "evidence/final-test.json").exists():
            self.assertEqual((await self.client.get("/api/evidence?dataset=test")).status_code, 503)
        self.assertEqual((await self.client.get("/data/private_draft_labels.jsonl")).status_code, 404)

    async def test_fresh_evidence_labels_and_exports_preserve_attribution(self):
        result = await self.client.get("/api/evidence?dataset=fresh")
        self.assertEqual(result.status_code, 200)
        evidence = result.json()
        self.assertEqual(evidence["status"], "fresh independently reviewed test")
        self.assertFalse(evidence["evaluation_protocol"]["previously_exposed_cases"])
        self.assertEqual((await self.client.get("/api/config")).json()["default_evidence_dataset"], "fresh2")
        rows = (await self.client.get("/api/review?source=fresh")).json()
        self.assertEqual(len(rows), evidence["evaluation_n"])
        self.assertTrue(all(r["readonly"] and "prediction" not in r for r in rows))
        self.assertTrue(all(r["review"]["reviewer_type"] == "agent" for r in rows))
        self.assertTrue(any(r["review"]["urgency"] == "unclear" for r in rows))
        export = await self.client.get("/api/review/export?source=fresh")
        self.assertIn("relay-fresh-review.csv", export.headers["content-disposition"])
        self.assertIn("independent agent review", export.text)
        self.assertNotIn("prediction", export.text)
        body = {"category": "delay", "urgency": "routine", "clarification": False,
                "reason": "Isolated fixture", "reviewer": "Unit test fixture"}
        self.assertEqual((await self.client.post(f"/api/review/{rows[0]['id']}", json=body)).status_code, 404)

    async def test_stale_fresh_labels_show_an_explicit_error(self):
        with patch.object(self.module, "fresh1_rows", side_effect=ValueError("Frozen labels changed")):
            for path in ["/api/evidence?dataset=fresh", "/api/review?source=fresh"]:
                response = await self.client.get(path)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["detail"], "Frozen labels changed")

    async def test_missing_or_corrupt_evaluation_records_return_actionable_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "evidence").mkdir()
            with patch.object(self.module, "ROOT", root):
                for dataset in ["fresh", "fresh2"]:
                    response = await self.client.get(f"/api/evidence?dataset={dataset}")
                    self.assertEqual(response.status_code, 503)
                    self.assertIn("does not have a saved evaluation", response.json()["detail"])
                (root / "evidence/current.json").write_text("not valid JSON")
                self.assertEqual((await self.client.get("/api/config")).status_code, 503)
                (root / "evidence/current.json").write_text(json.dumps({"development": "evidence/development.json"}))
                for content in ["not valid JSON", "[]", "{}"]:
                    (root / "evidence/development.json").write_text(content)
                    response = await self.client.get("/api/evidence?dataset=development")
                    self.assertEqual(response.status_code, 503)
                    self.assertIn("evaluation", response.json()["detail"].lower())
                (root / "evidence/development.json").write_text(json.dumps({"evaluation_n": 60, "methods": [{}],
                    "implementation_sha256": {"engine.py": "missing fixture"}}))
                response = await self.client.get("/api/evidence?dataset=development")
                self.assertEqual(response.status_code, 503)
                self.assertIn("stale", response.json()["detail"])

    async def test_original_review_integrity_errors_are_explicit(self):
        with patch.object(self.module, "reviewed_rows", side_effect=ValueError("Frozen labels changed")):
            for path in ["/api/review?source=independent", "/api/review/export?source=independent"]:
                response = await self.client.get(path)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["detail"], "Frozen labels changed")

    async def test_csv_quotes_fields_and_keeps_formula_text_inert(self):
        fixture = [{"id": "FIXTURE", "text": "An isolated fixture, with a comma.", "review": {
            "category": "delay", "urgency": "routine", "clarification": False,
            "reason": "=1+1", "reviewer": "  @SUM(1,2)", "updated_at": "2026-10-24"}}]
        with patch.object(self.module, "review", return_value=fixture):
            response = await self.client.get("/api/review/export?source=human")
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(io.StringIO(response.text)))
        self.assertEqual(rows[0]["report"], fixture[0]["text"])
        self.assertEqual(rows[0]["reason"], "'=1+1")
        self.assertEqual(rows[0]["reviewer"], "'  @SUM(1,2)")

    def quality_fixture(self):
        reports = [{"id": f"QUALITY-{i:02}", "text": f"Original report {i}.", "category": "delay",
                    "urgent": False, "clarification": False} for i in range(60)]
        document = {"reviewer": "review_all_sixty", "reviewer_type": "agent",
            "label_source": "post-test assistant review", "blind": False, "reviewed_at": "2026-10-24T08:00:00+00:00",
            "rows": [{"id": report["id"], "text": "This must never replace the source report.",
                "category": "delay", "urgency": "routine", "clarification": False,
                "reason": "The shipment is late and its location is known.", "agrees_with_reference": True,
                "disagreement_note": ""} for report in reports]}
        document["rows"][0].update({"category": "unclear", "urgency": "unclear", "clarification": True,
            "reason": "The report omits the current location and impact.", "agrees_with_reference": False,
            "disagreement_note": "The reference chose routine delay; this fixture leaves both labels open."})
        return reports, document

    async def test_completed_review_is_readonly_attributed_and_joins_original_text(self):
        reports, document = self.quality_fixture()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "evidence/reviews/quality-20261024/review.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(document))
            with patch.object(self.module, "ROOT", root), patch("fresh2_evaluate.fresh_rows", return_value=(reports, {}, {}, [], {})):
                response = await self.client.get("/api/review?source=quality")
                self.assertEqual(response.status_code, 200)
                rows = response.json()
                self.assertEqual(len(rows), 60)
                self.assertEqual(rows[0]["text"], reports[0]["text"])
                self.assertTrue(all(row["readonly"] for row in rows))
                self.assertEqual(rows[0]["review"]["reviewer_type"], "agent")
                self.assertEqual(rows[0]["review"]["label_source"], "post-test assistant review")
                self.assertFalse(rows[0]["review"]["agrees_with_reference"])
                export = await self.client.get("/api/review/export?source=quality")
                self.assertIn("relay-completed-review.csv", export.headers["content-disposition"])
                exported = list(csv.DictReader(io.StringIO(export.text)))
                self.assertEqual(len(exported), 60)
                self.assertEqual(exported[0]["agrees_with_reference"], "No")
                self.assertEqual(exported[0]["label_source"], "post-test assistant review")
                self.assertEqual(exported[0]["disagreement_note"], document["rows"][0]["disagreement_note"])
                body = {"category": "delay", "urgency": "routine", "clarification": False,
                        "reason": "Attempt to overwrite a read-only review.", "reviewer": "Unit test fixture"}
                self.assertEqual((await self.client.post(f"/api/review/{reports[0]['id']}", json=body)).status_code, 404)

    async def test_completed_review_rejects_incomplete_labels_and_false_attribution(self):
        reports, original = self.quality_fixture()
        mutations = [lambda row: row["rows"].pop(),
            lambda row: row["rows"].__setitem__(1, copy.deepcopy(row["rows"][0])),
            lambda row: row.update({"reviewer_type": "human"}),
            lambda row: row.update({"blind": True}),
            lambda row: row.update({"reviewed_at": "not a date"}),
            lambda row: row["rows"][0].update({"category": []}),
            lambda row: row["rows"][0].update({"reason": " "}),
            lambda row: row["rows"][0].update({"agrees_with_reference": True}),
            lambda row: row["rows"][0].update({"disagreement_note": ""})]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "evidence/reviews/quality-20261024/review.json"
            path.parent.mkdir(parents=True)
            with patch.object(self.module, "ROOT", root), patch("fresh2_evaluate.fresh_rows", return_value=(reports, {}, {}, [], {})):
                for mutation in mutations:
                    candidate = copy.deepcopy(original)
                    mutation(candidate)
                    path.write_text(json.dumps(candidate))
                    self.assertEqual((await self.client.get("/api/review?source=quality")).status_code, 503)

    async def test_second_fresh_set_and_original_fire_alarm_regression(self):
        response = await self.client.get("/api/evidence?dataset=fresh2")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["revision"], "routing-v4")
        self.assertEqual(payload["experiment"], "fresh2-20261022")
        self.assertFalse(payload["evaluation_protocol"]["previously_exposed_cases"])
        rows = (await self.client.get("/api/review?source=fresh2")).json()
        self.assertEqual(len(rows), payload["evaluation_n"])
        self.assertTrue(all(r["readonly"] and "prediction" not in r for r in rows))
        self.assertTrue(all(r["review"]["reviewer"] == "fresh2_report_review" for r in rows))
        export = await self.client.get("/api/review/export?source=fresh2")
        self.assertIn("relay-fresh2-review.csv", export.headers["content-disposition"])
        self.assertIn("independent agent review", export.text)
        text = "A licence number is missing from the clearance packet for the replacement fire-alarm controller. The building's alarm remains out of service with no temporary alarm, and customs will not release the controller until the licence is supplied."
        for method in ["rules", "learned"]:
            for policy in ["standard", "sensitive"]:
                response = await self.client.post("/api/triage", json={"text": text, "method": method, "policy": policy})
                result = response.json()["prediction"]
                self.assertEqual(result["team"], "Safety & security")
                self.assertTrue(result["urgent"] and result["review"])
        with patch("fresh2_evaluate.fresh_rows", side_effect=ValueError("Fresh-2 labels changed")):
            for path in ["/api/evidence?dataset=fresh2", "/api/review?source=fresh2"]:
                self.assertEqual((await self.client.get(path)).status_code, 503)


if __name__ == "__main__":
    unittest.main()
