# Dataset provenance and review

## Source

Original fictional English-language logistics incidents authored with OpenAI Codex on 21 October 2026. No confidential operator records, real shipment IDs, customer records or personal data are used. Messages simulate dispatch, drivers, depots and receiving teams. `generate_data.py` records the scenario banks and deterministic seed 20261021. It is an authoring record, not verified truth.

The dataset supports a demonstrable work sample, not an estimate of real incident prevalence, error rates, labor savings or service capacity.

## Grain and split

| File / split | Reports | Scenario families | Labels | Purpose |
| --- | ---: | ---: | --- | --- |
| `development.jsonl` train | 240 | 48 | Synthetic author drafts | Fit text classifier, construct rules |
| `development.jsonl` validation | 60 | 12 | Synthetic author drafts | Development comparison/debugging |
| `review_reports.jsonl` | 60 | 60 distinct scenarios | Blind input, text only | Separate review |
| `reviewed_labels.jsonl` | Same 60 | Same 60 | Frozen separate-agent judgments | First independent test |
| `fresh_reports_20261022.jsonl` | 60 new | 60 distinct authored scenarios | Blind input, text only | Fresh confirmation set |
| `fresh_labels_20261022.jsonl` | Same new 60 | Same new 60 | Frozen new separate-agent judgments | Preregistered temperature-v3 confirmation |
| `fresh2_reports_20261022.jsonl` | Another new 60 | Newly authored report scenarios | Blind input, text only | Fresh-2 confirmation |
| `fresh2_labels_20261022.jsonl` | Same second 60 | Same second 60 | Frozen third separate-agent judgments | Preregistered routing-v4 test |

Development has 60 base scenarios with five message wrappers each, 50 reports per category. Family splitting prevents paraphrases of a scenario crossing train/validation. Wrappers add count, not independent operational diversity. The balanced synthetic mix is not production prevalence.

Test reports are separately authored, shuffled and assigned opaque IDs. Blind records contain only `id`, `text`, `channel`. IDs and exact text are unique across all 360 reports. Test reports do not enter training, development scoring or the initial queue. The queue displays 48 training examples, one per family.

## Labels

| Primary category | Receiving team |
| --- | --- |
| Delivery delay | Transport operations |
| Missing shipment | Shipment tracing |
| Cargo damage | Claims & recovery |
| Temperature issue | Cold-chain quality |
| Safety & security | Safety & security |
| Documents & customs | Trade compliance |

Urgency is separate: active hazards, uncontrolled temperature exposure or a critical safety-system blocker require immediate attention. Customer emphasis alone is insufficient. Clarification covers material missing/conflicting facts or multiple issues. Greatest immediate consequence guides the primary issue. The complete guide is in `taxonomy.py` and `evidence/reviews/guide.txt`.

Unclear category and urgency are valid completed judgments and require reasons. They remain unknown rather than being forced into a category or routine label. Category/urgency each has 56 known test labels; 16 urgent, 40 routine, 4 unknown urgency; 4 unknown categories and 12 required-review cases. Evaluation retains all 60 for review, coverage and cost.

## Separate review and freeze

At the user's explicit request, another Codex agent (`independent_report_review`) received a fresh context with only original report text and the written guide. No parent history, draft labels, prior review, model, predictions or results were supplied. It judged all 60 cases independently and wrote a reason for each. Original output is `evidence/reviews/independent-review.raw.json`; enriched provenance and input hashes are in `independent-review.json`. This is agent review, not human or domain-expert validation.

Before receiving labels, `evidence/pretest-registration.json` recorded Rules/Sensitive as the candidate and froze classifier/corpus hashes. All returned judgments, uncertainty and six guide-ambiguity notes were preserved unchanged. Import added exact original texts and actual reviewer attribution. `reviewed_labels.freeze.json` records label/source/implementation hashes and timestamp. The first scoring ran after this freeze, without classifier tuning or prediction-led adjudication. The original code and inputs are preserved under `evidence/versions/v1/`.

The earlier same-assistant second pass in `evidence/ai-review-20261021.json` is retained only as iteration history. It was not the separate reference, never populated human review and was not used for fitting. Its 17 urgent judgments differ from the independent review's 16; these disagreements were not reconciled to favor either classifier.

The original blank workbook and manual database remain intact. The completed workbook has neutral title/columns with true attribution in Provenance; frozen browser judgments are read-only. CSV exports retain reviewer type. The importer rejects agent workbooks/CSV as human labels. A later human reviewer exposed to existing judgments must disclose that exposure; do not call such a review blind.

The assessment permits AI assistance and asks for independent review without expressly mandating a human. A fresh separate agent provides an independent reviewer check within that scope, with shared-tool/rubric limitations disclosed.

## Integrity and limits

`data/manifest.json` records source SHA-256 hashes. `python corpus.py` checks counts, IDs, exact uniqueness, family separation, valid development labels and no hidden labels in blind inputs. `review.py` checks every original report, valid literal judgments, reasons and authorship. An incomplete or changed review cannot freeze; existing freezes cannot be overwritten. Evaluation rejects changed labels or engine/taxonomy/evaluator hashes.

The generation code contains original draft annotations; an ignored local draft-label file also exists. Neither is final truth nor read by app/evaluation/import. The developer knows corpus authorship: this is not a concealed third-party benchmark. Exact uniqueness does not prove semantic independence.

The data is small, synthetic, balanced and mainly well-formed English. The independent agent shares model-family and guide biases with the authoring tool. Guide ambiguity around historical records, multi-issue safety routing and unknown urgency is preserved in the review record. No expert adjudication, multilingual/noisy-report study, live capacity test or production deployment has occurred. Obtain representative data and domain judgments before operational use.

## Revised implementation and reused test cases

The 22 October temperature correction does not alter any corpus text or reference judgment. The original first test remains `evidence/final-test*.json`; the active diagnostic is `evidence/iterations/temperature-v3/retest.json`. It reuses cases already inspected by the developer and must not be presented as new independent validation. `evidence/current.json` identifies active results and the original label-freeze implementation. The app checks label provenance against the preserved v1 code; the revised evaluator still rejects an implicit first-test rerun against changed code.

The 32 temperature scenarios in `tests/test_temperature.py` are authored regression fixtures across four method/policy combinations, not independent observations or added training reports. Their purpose is checking explicit limits, units, negative temperatures, unknowns, controlled records, false alarms and priority boundaries. The first correction's diagnostic exposed another product-range phrasing, which was then fixed and retested; earlier results remain in `evidence/iterations/`.

## Fresh confirmation set

On 22 October, the classifier and current Text/Sensitive choice were frozen before 60 additional reports were authored with `generate_fresh.py`. Total source is now 420 fictional reports, of which 120 have separate-agent judgments. New records contain only ID, text and channel, have no exact/normalized text or ID overlap with the original 360, and are excluded from training and the initial operations queue. Word-trigram overlap is recorded in `evidence/fresh-20261022-source.json`; this does not prove scenario independence.

Another agent, `fresh_report_review`, used no inherited conversation and received only new text plus the existing guide. Its 60 judgments and reasons were preserved unchanged and frozen before scoring. New denominators are 56 known categories, 54 known urgencies (15 urgent, 39 routine), four unclear categories, six unclear urgencies and 21 required-review cases. `fresh_evaluate.py` verifies original and new hashes, reviewer provenance, the frozen driver and candidate before every evaluation. Original source manifests/labels remain unchanged. See `FRESH-VALIDATION.md` for the protocol and limitations, including author knowledge of the implementation, synthetic case selection and shared model-family bias.

## Second fresh set

After exposed-case routing development, the final routing-v4 candidate and Text/Sensitive selection were frozen before `generate_fresh2.py` authored 60 further reports. Source now totals 480 fictional reports, with 180 reference judgments across three separate fresh-context agents. No exact/normalized text or ID overlaps the preceding 420, but themes/issue types overlap and the author knew the classifier. Do not equate lexical uniqueness with independent operational diversity.

`fresh2_report_review` saw only the new text and unchanged guide. All 60 judgments and reasons remain unchanged, including five unclear categories and eight unclear urgencies. There are 55 known categories, 52 known urgencies (13 urgent, 39 routine) and ten required-review cases. `fresh2_evaluate.py` was frozen before access to returned judgments and scoring. Neither independent labels nor classifier changed after scoring.

The new reviewer retained operational primary teams for urgent restoration blockers, unlike the preceding reviewer's Safety interpretation. Both applied the same guide; the ambiguity is disclosed rather than adjudicated using predictions. `FRESH2-VALIDATION.md` explains counts, frozen source/code/driver hashes and remaining biases. Earlier results reproduce under preserved implementations. Regression fixtures are separate from these reference reports and never counted as independent validation.
