# Collaboration and AI assistance

## Human author

The repository owner, dansyar, chose the product direction, requested the Linear-inspired redesign, reviewed the prototype, identified overlapping priority queues and authorized the separate reviewer. Manual prototype testing and product feedback are credited to dansyar, as reported by the author. Feedback and observed walkthroughs are recorded in `FEEDBACK.md`. This credit covers manual user-flow testing, not execution of the automated checks, model benchmarks, or independent label judgments. No completed human label review or logistics domain expertise is claimed.

## OpenAI Codex

Codex assisted with assessment interpretation, architecture, software, original synthetic scenarios and development labels, workbook creation, model/rules implementation, evaluation, tests, browser QA and documentation/business-summary authoring. Generated development labels remain author assumptions.

At the user's request, the same assistant first performed a second-pass annotation in `evidence/ai-review-20261021.json`. That is preserved as history only and was not used as the independent reference or to tune classifiers. The assistant helped author the reports and therefore did not claim that pass as a separate reviewer.

The user then requested another agent. A separate Codex agent, `independent_report_review`, was started with a fresh context and no inherited conversation. It received only 60 original report texts and the written guide. It did not receive draft annotations, previous reviews, models, predictions or evaluation results. It independently assigned every judgment and reason. The raw returned record, input hashes, enriched provenance and preregistered candidate are in `evidence/reviews/` and `evidence/pretest-registration.json`. Unknown values and guide ambiguities were retained unchanged. The first evaluation ran without test-driven model tuning; its implementation and results are preserved. On 22 October the author requested improved triage. Subsequent changes and reruns are explicitly recorded as post-test diagnostics; no reference judgment was relabeled.

This is independent agent review, not human or operator validation. Same-tool/model-family biases and a shared guide limit independence. The primary workbook title and columns are neutral at the user's request; its Provenance sheet, CSV fields and freeze records retain actual agent attribution. Removing a presentation label does not change authorship.

Both Part B classifiers run locally and make zero paid inference API calls. Codex development and review use conversation service resources whose monetary cost is unmeasured. The USD 0 inference figure excludes those resources, local compute and human labor. No LLM classifier comparison or invented outside-user feedback is claimed.

Part A used separately authorized AIPipe calls and GitHub publication. Those are separate from Part B inference results.

## Software and design

- Python, FastAPI/Pydantic, Uvicorn, SQLite and httpx support the app and checks. Classifiers are small project implementations in `engine.py`.
- HTML, CSS, JavaScript and original SVG icons implement the interface. [Linear](https://linear.app/) was the user's reference for compact queues and restrained navigation. Relay uses its own name and assets.
- Codex's bundled spreadsheet artifact library authored the optional XLSX; ReportLab, pypdf and Poppler support the PDF.
- Synthetic reports are original project material, not scraped operator records or a third-party benchmark.

The owner remains responsible for the submitted work and explaining it. No operator study, field trial or production activation has occurred.

## Testing roles and the 22 October revision

| Activity | Credit and evidence |
| --- | --- |
| Manual prototype testing and feedback | dansyar, as reported by the author; product choices, queue feedback and walkthrough requests are documented |
| Assisted walkthrough actions | Codex operated the local app at dansyar's request; one example routing decision was saved locally |
| Automated behavioral and regression tests | Authored and executed by OpenAI Codex; 26 checks including 32 temperature scenarios across four configurations |
| Model benchmarks and diagnostic reruns | Executed by OpenAI Codex; commands, hashes and machine-readable results retained |
| Independent reference labels | Separate fresh-context Codex agent; original 60 judgments remain unchanged |

The user's testing credit is not a claim that they personally executed the automated suite or authored the separate agent's labels. No external operator test or production trial is claimed.

## Fresh-set testing - 22 October

At dansyar's request, Codex froze temperature-v3 and Text/Sensitive before authoring 60 new fictional reports. A second independent reviewer, `fresh_report_review`, started without inherited conversation and received only the new text and unchanged guide. Its complete raw output, all 60 reasons and actual agent attribution are preserved under `evidence/reviews/fresh-20261022/` and `data/fresh_labels_20261022*`. No judgment was changed after scoring.

Codex executed the fresh benchmark, 31 automated behavioral/integrity checks, local container reproduction and browser verification. Manual prototype testing and feedback remain credited to dansyar (author-reported); those credits do not imply human execution of these automated runs or authorship of agent labels. The new reviewer shares a model family with the authoring tool, and the author knew the classifier. This is fresh synthetic evidence, not human domain-expert validation. `FRESH-VALIDATION.md` records adverse results and remaining limitations. No publication or submission occurred.

## Routing-v4 and second fresh set

At the author's request, Codex improved routing using earlier exposed failures and authored regression fixtures. A superseded pretest draft and its regression failures are archived. The final routing-v4 candidate and Text/Sensitive selection were frozen before 60 further reports were authored. Another agent, fresh2_report_review, started with no inherited history and saw only new text and the unchanged guide. Its 60 judgments/reasons are preserved byte-for-byte in the raw record and without relabeling in the frozen reference. Its operational-team interpretation of urgent restoration blockers differs from the prior reviewer; those disagreements remain.

Codex executed the second fresh benchmark, the disclosed post-hoc paired comparison against preserved v3, all 40 automated checks, local Linux reproduction and browser verification. Manual prototype testing and product feedback remain credited to dansyar (author-reported). This does not attribute automated execution or agent labels to the human author. All 180 judgments across three separate agents retain true provenance. No classifier or independent judgment changed after Fresh 2 scoring. No outside operator study, deployment, publication or assessment save occurred.

## 24 October UI, reliability and completed review

At dansyar's request, Codex refined the interface and wording, audited the website, and ran 47 backend tests, 12 frontend regression tests and browser checks. `backend_audit` checked validation, storage and evidence loading; `frontend_audit` checked navigation and save behavior.

A further agent, `review_all_sixty`, reviewed all 60 Fresh 2 reports with the guide and earlier labels available. This was a post-test second opinion, not a blind review. It supplied short, report-specific reasons and changed only the clarification judgment for RLY-920024 in its own supplemental record. Frozen reference labels and classifier scores remain unchanged. The app calls this Latest review and keeps attribution in Guide and Export.

Manual prototype testing and feedback remain credited to dansyar as author-reported. These new automated runs, browser actions and supplemental reviews were performed by Codex and its agents. No human authorship, human label review or operator validation is implied by the plain-language wording. All work remains local.
