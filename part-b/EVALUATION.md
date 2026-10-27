# Evaluation and decision

## Current routing-v4 and Fresh 2

The latest preregistered test contains 60 new reports labeled by a new fresh-context agent after routing-v4 was frozen. Text/Sensitive gets **49/55 clear team labels correct (89.1%)**, Macro F1 **0.904**, **0/13 urgent misses**, **five false urgent alerts** and **43/60 model abstentions**. Eight unknown urgencies remain unknown; all ten reference-required reviews are caught. One wrong team remains among 17 reports outside abstention, so every route still needs confirmation.

On these same reports, preserved v3 gets 46/55 teams correct (83.6%), F1 0.839, zero urgent misses, seven false urgent alerts and 41 reviews. This paired comparison was added after primary scoring, without tuning or candidate selection. It supports three more correct teams; comparing 89.1% directly with the earlier set's 60.7% would confound case mix and reviewers.

The original fire-alarm case RLY-910052 now routes to Safety & security/Urgent with review in all four configurations. It is an authored regression and exposed-case correction, not part of the second fresh test. The new reviewer chose operational teams plus urgent priority for three critical-system blockers; the earlier reviewer used Safety/Urgent. Those disagreements and all other errors are retained, without prediction-led relabeling.

Both methods share new primary-issue, custody and consequence checks; training data and metric definitions are unchanged. Sensitive is not the cheapest observed choice on Fresh 2: cost is 59 versus Standard's 54, but it catches ten versus eight required reviews. It remains the preregistered demo default. See [FRESH2-VALIDATION.md](FRESH2-VALIDATION.md) for full methods, known-label denominators, adverse results, paired comparison, provenance and limits. Fresh 2 is the app default; earlier results remain separately selectable. Everything remains local.

The following sections preserve preceding test history.

**Keep all routes human-confirmed.** The new 60-report confirmation set caught 14/15 urgent cases with the preregistered Text/Sensitive candidate, but team accuracy was 34/56 (60.7%) and 50/60 reports required model abstention. Original tests, diagnostic iterations, source code and judgments remain preserved.

## Fresh confirmation set - 22 October

The existing temperature-v3 classifier and Text/Sensitive choice were frozen before 60 new fictional reports were authored. Another fresh-context agent labeled them using only their text and the unchanged guide. All judgments were frozen before predictions; no model tuning followed. This tests new wording and scenarios beyond the original 60. The author knew the classifier and the reviewer shares its development tool's model family; it is not operator validation.

| Configuration | Macro F1 | Urgent misses /15 | False urgent | Review /60 | Wrong eligible teams | Required review bypasses | Cost at 100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Rules / Standard | 0.571 | 12 | 0 | 39 | 5 | 3 | 1281 |
| Rules / Sensitive | 0.571 | 6 | 12 | 51 | 2 | 0 | 687 |
| Text / Standard | 0.600 | 3 | 1 | 34 | 6 | 2 | 384 |
| **Text / Sensitive** | **0.600** | **1** | **7** | **50** | **0** | **0** | **164** |

Denominators: 56 known categories; 54 known urgencies (15 urgent, 39 routine); four unclear categories and six unclear urgencies retained; 21 reference-required reviews. Text/Sensitive reviews all 21, but still misses urgent priority for RLY-910052: a customs-held replacement fire-alarm controller while the building has no operating alarm. It suggests Documents & customs/Routine instead of Safety/Urgent, with ordinary review. All 22 wrong known-category suggestions and other errors remain in the evidence.

Text/Sensitive F1 is lower than on the exposed diagnostic set (0.600 vs 0.683); these are different case mixes, not paired observations. Zero wrong eligible teams is based on only ten eligible cases and does not establish reliable automatic routing. Changed requirement at a common penalty of 100: Text Standard to Sensitive costs 384 to 164, misses 3 to 1, reviews 34 to 50. Human review does not erase the priority penalty. Warm Text/Sensitive p95 was 0.059 ms; fit 4.643 ms, excluding HTTP, UI, startup and humans.

See [FRESH-VALIDATION.md](FRESH-VALIDATION.md) for protocol, full comparison, failures, attribution and limits. First results are in `evidence/fresh-20261022/`; original raw review is in `evidence/reviews/fresh-20261022/`. Reproduce with `python fresh_evaluate.py --output evidence/reproduced-fresh`. Evaluation defaults to Fresh test; Labels opens the new judgments. Earlier tests remain selectable.

## Current temperature revision — diagnostic retest

The author requested a local correction after the RLY-82374 walkthrough. Its report states 19 C against a 2–8 C product limit and calls for immediate isolation. The old rules engine recognized neither a category phrase nor a robust numeric limit, and a no-keyword fallback could erase an urgency signal. The new check routes it to Cold-chain quality/Urgent, with human confirmation, under every method/policy combination. It generalizes values and wording rather than matching an ID.

The original 60 reference cases have already been seen. Results below are a **post-test diagnostic**, not an unseen evaluation. All original labels, first-test results and v1 code remain unchanged. The v2 diagnostic also exposed implicit product-range phrasing; v3 covers it. Earlier iteration records are retained.

| Configuration | Original F1 → revised F1 | Urgent misses /16 | False urgent | Review /60 | Cost at 100 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rules / Standard | 0.551 → 0.601 | 15 → 11 | 1 → 1 | 27 → 32 | 1601 → 1188 |
| Rules / Sensitive | 0.551 → 0.601 | 2 → 1 | 19 → 18 | 54 → 56 | 310 → 198 |
| Text / Standard | 0.648 → 0.683 | 6 → 3 | 1 → 1 | 19 → 24 | 717 → 398 |
| Text / Sensitive | 0.648 → 0.683 | 0 → 0 | 8 → 6 | 42 → 45 | 76 → 69 |

Category and urgency still each have 56 known labels, including 16 urgent cases; review/cost uses all 60. Revised Text/Sensitive has 69.6% category accuracy, two wrong eligible routes and one bypassed required review. Rules/Sensitive still misses the spreading unidentified liquid near a break area (RLY-17064). These failures remain in the evidence. New defaults are Text/Sensitive; all decisions remain human-confirmed.

The price of the cold-chain protection is more review: Text/Sensitive rises from 42 to 45/60. On the reused set, its six false urgent alerts and 45 reviews produce 69 cost units under either urgency penalty, including two eligible-route/bypass failures counted per report. This is a scenario proxy, not savings. Current warm p95 is approximately 0.045 ms for Text/Sensitive and 0.127 ms for Rules/Sensitive; model fit is 4.694 ms on Python 3.12.14/Darwin arm64.

Changed requirement on the revised version, under a common miss penalty of 100: Rules/Standard to Sensitive changes 11 to 1 misses, 32 to 56 reviews and cost 1188 to 198. Text changes 3 to 0 misses, 24 to 45 reviews and cost 398 to 69. Shared temperature protection applies in both policies.

Manual prototype testing and feedback are credited to **dansyar (author-reported)**. Codex authored/executed 26 automated checks, including 32 temperature scenarios across all four configurations, and ran the model benchmarks. Independent labels remain attributed to the separate agent. These roles are recorded in `ATTRIBUTION.md`; no human execution of Codex-run checks is claimed.

Diagnostic evidence: `evidence/iterations/temperature-v3/`. Reproduce with `python evaluate.py --reviewed data/reviewed_labels.jsonl --diagnostic --output evidence/reproduced-retest`. The subsequent fresh confirmation set is described above; representative operator evidence is still needed.

## Approaches

**Rules baseline:** explicit category words/stems; greatest match count wins. Consequence patterns set urgency. Weak evidence, close category margins and missing/conflicting facts trigger review. Taxonomy order resolves ties, sometimes producing a weak Delay suggestion; review is essential.

**Text model:** word/bigram TF-IDF with normalized category and urgent/routine centroids. Vocabulary and centroids use only 240 training reports from 48 scenario families. Greatest cosine similarity chooses the category; urgency uses a similarity margin. Message wrappers/common stop words are removed, negation retained. Similarity is not calibrated probability. No LLM classifier benchmark was run.

Both methods share the taxonomy, review policy and explicit cold-chain checks. The current temperature checks compare measurements to the report's stated limits, recognize active cooling failure, preserve missing/conflicting facts, and distinguish verified sensor corrections and controlled historical records. Shared checks can override category/urgency and require human confirmation; base-method similarity scores remain heuristic and do not become calibrated confidence in the override. Standard and Sensitive change escalation/abstention thresholds without retraining. Every actual demo routing decision requires human confirmation, even when the metric says a report is eligible for automation.

## Independent test protocol

There are 300 development reports, with five wrappers per authored scenario and a family-disjoint 240/60 split. The 60 validation rows contain only 12 scenario families. Separately authored test reports comprise 60 distinct scenarios and never enter training or the initial demo queue.

Before receiving reviewer judgments, `evidence/pretest-registration.json` selected Rules/Sensitive from development evidence and recorded classifier/corpus hashes. A separate Codex agent ran with fresh context, receiving only the original test text and the written guide. It saw no parent history, draft annotations, earlier review, classifiers, predictions or results. Original output and enriched provenance are in `evidence/reviews/`.

All 60 returned judgments and reasons were preserved, including unknowns and six guide-ambiguity notes. Labels and engine/taxonomy/evaluator hashes were frozen before the first test. The test is `evidence/final-test.json`; predictions and mistakes are adjacent files. This is separate-agent verification, not human logistics-expert ground truth. Shared model-family bias and guide ambiguity remain limitations. Earlier same-assistant annotations are history only, unused as reference labels.

Category and urgency each have **56 known labels**; there are **16 urgent** and 40 routine judgments. Four category and four urgency judgments remain unknown. Twelve reports require review because of uncertainty or explicit clarification. Unknowns are excluded only from the corresponding known-label quality denominator; they remain in review, coverage and cost measures over all 60.

## Original v1 frozen test results

| Approach / policy | Category accuracy (n=56) | Macro F1 | Urgent misses (n=16) | False urgent | Review (n=60) | Eligible coverage | Wrong eligible routes | p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Rules / Standard | 53.6% | 0.551 | 15 | 1 | 27 | 55.0% | 6 | 0.1051 |
| Rules / Sensitive | 53.6% | 0.551 | 2 | 19 | 54 | 10.0% | 2 | 0.1011 |
| Text / Standard | 66.1% | 0.648 | 6 | 1 | 19 | 68.3% | 10 | 0.0240 |
| Text / Sensitive | 66.1% | 0.648 | 0 | 8 | 42 | 30.0% | 2 | 0.0240 |

Urgent recall is 6.25%, 87.5%, 62.5% and 100%, respectively. Rules/Sensitive reviews 11/12 required-review cases; Text/Sensitive reviews 10/12. Text/Sensitive's 18 eligible category routes contain two errors (16/18 correct). It also bypasses two required reviews. Wrong routes and bypasses can overlap and incur a single route penalty per report. Both Rules/Sensitive urgent misses enter ordinary review; that still delays priority, so both incur urgency-miss cost.

Macro F1 averages all six categories. Raw category quality includes reports sent for review. Review/abstention includes urgent review cases; the UI puts these in Urgent rather than ordinary Needs review. Zero-evidence/unknown input is withheld from automatic routing. Heuristic confidence thresholds and conservative flags do not guarantee correct escalation.

Latency is warm inference after warm-up, five passes per report (300 timings per configuration); quality uses the first deterministic pass. Python 3.12.14, Darwin arm64; text-model fitting took 4.0948 ms. HTTP, startup, rendering, queue delays and human decisions are excluded. Timings vary with hardware/load; exact quality and cost counts should reproduce. No population confidence interval or production accuracy claim is made from this small synthetic set.

## Costs and changed requirement

Explicit relative scenario assumptions: review 1 unit; an eligible wrong category or bypassed required review 6 once per report; false urgency 2; **every** missed urgent flag 30 or 100, including ordinary reviewed cases. Review does not instantly fix delayed priority. Human correction accuracy, staffing, time in queue and realized operational costs are unmeasured.

| Approach / policy | Cost at miss penalty 30 | Cost at miss penalty 100 | Classifier API spend |
| --- | ---: | ---: | ---: |
| Rules / Standard | 551 | 1601 | USD 0 |
| Rules / Sensitive | 170 | 310 | USD 0 |
| Text / Standard | 297 | 717 | USD 0 |
| Text / Sensitive | 76 | 76 | USD 0 |

Both classifiers make zero external inference calls. The USD figure excludes compute, development, review-agent conversation service costs and labor; those were not priced. Relative units are not prices or measured savings.

The changed requirement increases the missed-urgent penalty from 30 to 100. Sensitive raises the evidence floor (0.12 to 0.17) and category-margin threshold (0.035 to 0.065), lowers the text urgency margin (0.025 to -0.025), and flags possible critical consequences. Compare both policies under the **same new penalty of 100**:

| Method | Standard cost | Sensitive cost | Misses prevented | Additional reviews | Additional false urgency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rules | 1601 | 310 | 13 | 27 | 18 |
| Text | 717 | 76 | 6 | 23 | 7 |

This demonstrates workload and escalation tradeoffs. Sensitive also costs less under the original assumptions; no newly optimal switching threshold, staffing feasibility or dollar ROI is inferred.

## Inspectable mistakes

| Report | Frozen observation | Implication |
| --- | --- | --- |
| RLY-17064: unknown liquid spreading near a break area | Rules/Sensitive chooses Safety but routine, with review; reviewer says urgent | A category/review flag does not replace timely escalation. |
| RLY-43963: softening ice cream, failed compressor, no backup cooling | Rules/Sensitive misses urgency despite temperature route and review | New wording/consequences expose incomplete patterns. |
| RLY-33429: crushed lamps, explicitly no smoke, leakage or ongoing hazard | Rules/Sensitive confidently routes Safety/Urgent; reviewer says Damage/Routine | Negation and contextual hazard terms cause costly over-escalation and misrouting. |
| RLY-25526: cosmetic tear, seals/temperature fine | Rules/Sensitive routes Temperature without review; reviewer says Damage | A temperature mention can outweigh the actual primary issue. |
| RLY-98271: vague cold-chain concern, no measures or limits | Text/Sensitive predicts Routine without review; reference urgency is unknown | Missing evidence must not be treated as proof of safety. This bypass is penalized even though unknown urgency is excluded from accuracy. |
| RLY-21862: faulty display contradicted by two stable probes, sensor replaced | Text/Sensitive marks urgent without review | Historical/resolved context can still trigger false alarms. |
| RLY-61963: delayed emergency ventilation motor, unsafe personnel conditions | Rules/Standard routes Delay/Routine without review | One message can require immediate safety and logistics handling; the independent reviewer documented the routing ambiguity. |

The guide has unresolved boundaries around active unsafe destinations versus transport causes, historical records, routine versus unknown urgency, and how much missing detail requires clarification. The reviewer documented its interpretation. Those disagreements were retained rather than adjudicated using predictions.

## Development history and generalization

| Approach / policy | Development macro F1 | Urgent misses /20 | Review /60 | Cost at 100 |
| --- | ---: | ---: | ---: | ---: |
| Rules / Standard | 0.911 | 5 | 25 | 525 |
| Rules / Sensitive | 0.911 | 0 | 45 | 55 |
| Text / Standard | 0.589 | 15 | 45 | 1575 |
| Text / Sensitive | 0.589 | 0 | 60 | 90 |

Rules' apparent development strength did not generalize. Validation repetition and author-generated labels limit that evidence. Earlier development-only changes fixed word boundaries (`dent`/`incident`, `late`/`isolated`, `not`/`note`) and removed wrapper/function-word noise, improving text F1 from 0.447 to 0.589. The initial record is retained under `evidence/iterations/`; its cost definition only counted automated urgency misses and is superseded. Do not compare those old costs to the current matrix.

The original v1 implementation was not tuned on independent review. The later temperature revision is a disclosed post-test change. Text/Sensitive was then preregistered for the fresh set above and remains the human-confirmed demo default. It is not a production-validated choice. Next: representative operator reports, domain review and clarified guidance, measured review capacity and escalation outcomes. Any further tuned version needs another untouched test. No field trial has occurred.

## Reproduce

From `part-b/`, run `python evaluate.py --output evidence/reproduced-development` and `python evidence/versions/v1/evaluate.py --reviewed data/reviewed_labels.jsonl --output evidence/reproduced-original`. Preserve the original output; the evaluator refuses overwriting final results and rejects changed inputs/code or invalid freezes. Clean Linux container evidence and real HTTP verification are in `evidence/container-*.json` and `runtime-verification.json`. Installed versions are in `container-dependencies.txt`. See `README.md` for setup and `DELIVERABLES.md` for publication status.
