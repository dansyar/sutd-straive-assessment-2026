# Run and reproduce Relay

Relay is an internal coordinator's workbench. Six categories propose receiving teams; urgency and review are separate decisions. Every route still needs human confirmation. All reports are fictional, and no real dispatch or alert is sent.

## Start

From the repository root, using Python 3.12:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r part-b/requirements.txt
cd part-b
python corpus.py
python -m unittest discover -s tests -v
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Stop with Ctrl-C. State persists in `part-b/.local/`. Set `RELAY_STATE_DIR` to another directory for an isolated demo. Keep loopback binding; this prototype has no authentication or production integration.

From `part-b/`, Docker is an alternative:

```sh
docker build -t relay-demo .
docker run --rm -p 127.0.0.1:8000:8000 -v relay-demo-state:/state relay-demo
```

The application needs only the pinned packages in `requirements.txt`. A clean Linux container verifies installation and 47 backend behavioral/integrity checks. The new fresh test reproduces all 240 predictions and quality/cost counts in Linux. See `evidence/fresh2-20261022/runtime-verification.json` for the classifier reproduction scope; preceding verification remains in `evidence/runtime-verification.json`.

## Use it

1. Inbox shows all open incidents. Initial examples are 48 training reports, one per family, not test evidence.
2. Urgent contains urgent reports, including those needing review. Needs review contains non-urgent review reports. These priority queues are exclusive. Done contains confirmed decisions.
3. Select a report; change Team or Urgency if needed, add a note, then Confirm route. Reload and open Done to inspect the saved local decision.
4. New report runs the selected classifier and can add the report to the queue.
5. Evaluation holds model and policy controls. Fresh 2 defaults to the latest 60-report test; Fresh 1 retains the preceding version; Retest shows the exposed-case diagnostic; Original test preserves v1 results. Every row uses the same selected miss penalty.
6. Reviews opens Latest review: all 60 Fresh 2 reports checked again, with short reasons. Fresh 2, Fresh 1 and Original preserve the frozen reference labels. Your review opens the separate editable original-set workflow. Guide explains attribution, and Export downloads the selected set. The latest second pass is not another blind benchmark.

Text/Sensitive is the default for new use; explicitly saved model/policy choices remain available. Rules remains the baseline comparator. Both approaches share explicit cold-chain protection. Changing approach/policy updates the queue without retraining; every decision still needs human confirmation.

## Reproduce the evidence

With the virtual environment active, from `part-b/`:

```sh
python evaluate.py --output evidence/reproduced-development
python evidence/versions/v1/evaluate.py --reviewed data/reviewed_labels.jsonl --output evidence/reproduced-original
python evaluate.py --reviewed data/reviewed_labels.jsonl --diagnostic --output evidence/reproduced-retest
python evidence/versions/temperature-v3-pre-routing-v4/fresh_evaluate.py --output evidence/reproduced-fresh1
python fresh2_evaluate.py --output evidence/reproduced-fresh2
python compare_versions.py --output evidence/reproduced-version-comparison
```

Use new output prefixes. Original `evidence/final-test*.json` files are the first frozen test and must be preserved. Quality counts and costs reproduce; latency varies with machine/load. Training reads only 240 reports from 48 scenario families. The reviewed test is never used for fitting.

The test checks corpus, frozen label and implementation hashes. The preserved reviewer source is `evidence/reviews/independent-review.json`; the unmodified returned output is `independent-review.raw.json`. The review used only original report text and `guide.txt`, with no parent history, prior labels or classifier predictions. `evidence/pretest-registration.json` records Rules/Sensitive selection before judgments were received. The first model was not tuned on those labels. The later temperature correction followed user walkthroughs and inspection of original mistakes. Its reused-case results are explicitly diagnostic, not new independent validation; original judgments are unchanged.

Unknown category/urgency remains unknown. The original set uses 56 known labels in each field and 16 urgent cases. Fresh 1 uses 56 known categories, 54 known urgencies and 15 urgent cases; Fresh 2 uses 55 known categories, 52 known urgencies and 13 urgent cases; review/cost uses all 60. See [EVALUATION.md](EVALUATION.md) and [FRESH2-VALIDATION.md](FRESH2-VALIDATION.md).

## Additional human review

The optional manual workflow, CSV and initial blank workbook remain available. Once someone has seen the completed judgments, disclose that exposure rather than calling a later review blind. Do not overwrite or silently replace the frozen test.

```sh
python review.py --file /path/to/completed-review.xlsx --reviewer REVIEWER
python review.py --browser
```

These validate without writing. Freeze accepts only complete, attributed judgments with unchanged text and required reasons. It refuses an existing freeze. Agent annotations must use the `--agent-review` JSON path and cannot be imported as human labels, including through the neutral workbook/CSV.

## Files

| Purpose | Files |
| --- | --- |
| App and interface | `app.py`, `web/` |
| Methods and policy | `engine.py`, `taxonomy.py` |
| Source and frozen labels | `data/`, `corpus.py` |
| Import and freeze | `review.py` |
| Metrics, predictions and costs | `evaluate.py`, `evidence/` |
| Business summary and review | `output/pdf/`, `output/review/` |
| Data, conclusions and authorship | `DATA.md`, `EVALUATION.md`, `ATTRIBUTION.md` |

The XLSX authoring script uses Codex's bundled artifact library; the PDF script uses ReportLab/pypdf. Both are optional authoring tools, unnecessary for running the app or reproducing classifier results. No secrets or paid inference services are required.

## Current revision and testing credit

The active implementation is `routing-v4`; `evidence/current.json` identifies current development/diagnostics, the preserved first fresh test and the second fresh test. Primary-issue, custody and consequence checks now override incidental word matches. The missed RLY-910052 fire-alarm controller receives Safety & security/Urgent review in all four configurations. Both methods share the new checks; the same 240 training rows and thresholds remain unchanged.

Fresh 2 gets 49/55 teams correct, F1 0.904, zero known urgent misses out of 13, five false urgent alerts and 43/60 model abstentions. The frozen v3 on the same reports gets 46/55 teams correct. One wrong eligible team and three critical-system primary-team disagreements remain. No classifier or judgment changed after Fresh 2 scoring. See FRESH2-VALIDATION.md for protocol and limitations.

Manual prototype testing and feedback: **dansyar (author-reported)**. Automated checks, benchmarks and assisted walkthroughs: **OpenAI Codex**. All 180 reference judgments retain separate-agent attribution. There are 47 backend checks and 12 frontend regression checks, including 32 temperature and 19 authored routing scenarios. These fixtures are not extra independent reports.

Original results and implementations remain preserved and reproducible. Historical labels are validated using their preserved candidate; current results are checked against active code. The new and older sets remain separately selectable. Synthetic agent evidence does not establish operational performance.

## UI and reliability review — 24 October

The app has a quieter layout, readable completed reviews, clearer save feedback and a direct View Done link. All 60 Fresh 2 reports received a second pass. Category and urgency agree with the frozen reference; one report, RLY-920024, also needs clarification because the delivery record and recipient disagree. The original reference remains unchanged.

Run the frontend race and save tests with Node 24:

```sh
node --test tests/test_frontend.mjs
```

This is 12 additional checks, alongside the 47 Python checks. Browser testing uses a separate local state directory, including creation, confirmation, saved updates and manual-review fixtures. See `UI-VERIFICATION.md` and `evidence/quality-20261024/verification.json`. Actual user records are preserved.
