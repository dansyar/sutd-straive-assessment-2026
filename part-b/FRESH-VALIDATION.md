# Fresh-set validation - 22 October 2026

Historical temperature-v3 result. The subsequent correction, same-report comparison and second fresh test are in [FRESH2-VALIDATION.md](FRESH2-VALIDATION.md). No original evidence below was replaced.

**The frozen Text/Sensitive candidate caught 14/15 urgent incidents, but missed a critical fire-alarm blocker. Keep every route human-confirmed.** This is useful evidence beyond the original 60, with substantial remaining team-classification and review-workload limitations.

## What was kept independent

1. Before authoring new reports, `evidence/fresh-20261022-registration.json` selected the existing Text/Sensitive default and froze engine, taxonomy, evaluator, corpus loader and training hashes. Copies are in `evidence/versions/temperature-v3-pre-fresh/`.
2. `generate_fresh.py` authored 60 new fictional scenarios covering all six teams, active and resolved conditions, mixed consequences, alternative wording, numeric units and unknown facts. It contains no reference labels. `data/fresh_reports_20261022.jsonl` contains only ID, text and channel.
3. Source text and the existing guide were frozen before labeling. None of the 60 IDs or normalized texts duplicates the original 360. Maximum word-trigram Jaccard similarity to an old report was 0.075. This is a lexical check, not proof of semantic independence.
4. Another agent, `fresh_report_review`, started with **no inherited conversation**. It received only the fresh reports and unchanged guide. It saw no classifier, author labels, original reviews, predictions or results. It independently labeled all 60 and wrote a reason for each.
5. The returned raw review is preserved byte-for-byte in `evidence/reviews/fresh-20261022/review.raw.json`. `data/fresh_labels_20261022.jsonl` adds actual reviewer attribution without changing any judgment or reason. Its adjacent freeze records input, label, raw-review, implementation and driver hashes. Freeze time was 02:02:39 UTC; first scoring was 02:02:44 UTC.
6. `fresh_evaluate.py` reuses the unchanged metric functions and both methods/policies. The scoring driver was frozen before accessing the review. No classifier, thresholds, taxonomy, training data or judgments were changed after the test. Earlier evidence remains unchanged.

## Results

The reviewer supplied **56 known categories**, **54 known urgencies** (15 urgent, 39 routine), **4 unclear categories**, **6 unclear urgencies**, and **21 reports requiring clarification/review**. Unknowns remain unknown. Category scores use 56; urgency errors use the 54 known urgencies; urgent recall uses 15. Review, coverage and cost use all 60.

| Configuration | Team accuracy | Macro F1 | Urgent misses /15 | False urgent | Review /60 | Wrong eligible teams | Required review bypasses | Cost at 30 | Cost at 100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Rules / Standard | 58.9% | 0.571 | 12 | 0 | 39 | 5 | 3 | 441 | 1281 |
| Rules / Sensitive | 58.9% | 0.571 | 6 | 12 | 51 | 2 | 0 | 267 | 687 |
| Text / Standard | 60.7% | 0.600 | 3 | 1 | 34 | 6 | 2 | 174 | 384 |
| **Text / Sensitive (preregistered)** | **60.7%** | **0.600** | **1** | **7** | **50** | **0** | **0** | **94** | **164** |

Text/Sensitive's urgent recall is 93.3%. It reviews all 21 reference-required cases and 50/60 overall (83.3%), leaving only 10 reports eligible for automatic routing. Those ten have correct reference teams, but ten synthetic cases cannot establish automatic-routing reliability; the app still requires confirmation for every decision. Raw team accuracy includes reviewed cases and is only 34/56 correct.

Compared with the diagnostic rerun of the already-seen set, Text/Sensitive falls from F1 0.683 to 0.600, misses rise from 0/16 to 1/15, and reviews rise from 45/60 to 50/60. The sets have different case mixes and denominators, so this is evidence of remaining generalization limits, not a paired estimate of regression.

## Failures retained

| Report | Independent judgment | Frozen Text/Sensitive result | Consequence |
| --- | --- | --- | --- |
| RLY-910052 | Safety/Urgent; fire-alarm controller blocked by missing licence, building has no working alarm | Documents & customs/Routine, review | Ordinary review does not replace urgent escalation; the miss incurs the full priority penalty. |
| RLY-910058 | Safety/Urgent; leaking chilled pallet beside live charging equipment and people | Temperature/Urgent, review | Urgency caught, but the immediate physical hazard gets the wrong team. |
| RLY-910044 | Safety/Urgent; threatened driver and lost contact | Temperature/Urgent, review | Urgency caught; a serious team-routing error remains. |
| RLY-910033 | Temperature/Routine; past excursion, batch now isolated in verified storage | Temperature/Urgent, no model abstention | False urgency on a controlled historical event; user confirmation remains necessary. |
| RLY-910027 | Damage/Routine; packaging claim with verified in-range product | Temperature/Routine, review | A temperature mention outweighs the stated primary issue. |

All 22 wrong known-category suggestions, seven false urgent alerts and the one urgent miss for Text/Sensitive remain in `evidence/fresh-20261022/fresh-test-mistakes.json`; full per-report outputs are in the adjacent predictions file. Unknown urgency is not silently treated as correct routine behavior.

## Changed requirement, speed and cost

Using the common urgent-miss penalty of 100, Text/Standard to Sensitive changes misses 3 to 1, reviews 34 to 50, false alerts 1 to 7, and cost 384 to 164. Rules changes misses 12 to 6, reviews 39 to 51 and cost 1281 to 687. The original cost definitions remain review 1, an eligible wrong route OR bypassed required review 6 once, false urgency 2, missed urgency 30 or 100 even when in ordinary review. These are relative assumptions, not prices or savings.

Original local warm p95 timings were 0.154/0.160 ms for Rules Standard/Sensitive and 0.066/0.059 ms for Text; 300 samples/configuration after warm-up. Model fit was 4.643 ms on Python 3.12.14, Darwin arm64. Excludes startup, HTTP, UI, human handling and queue time. Inference makes zero external API calls; compute, review-agent service resources and labor are unpriced.

## Inspect and reproduce

- Local app: Evaluation defaults to **Fresh test**. **Labels** opens the new read-only judgments; the set selector switches between Fresh, Original and Own review. CSV export retains actual reviewer attribution.
- Reproduce the fixed report file: `python generate_fresh.py`.
- Validate frozen inputs and reproduce all metrics: `python evidence/versions/temperature-v3-pre-routing-v4/fresh_evaluate.py --output evidence/reproduced-fresh1`. Existing results and freezes cannot be overwritten. Quality/cost counts should match; timings vary.
- The local container includes the fresh source, frozen review, scoring driver and evidence. The local CI definition includes the same command; no remote CI run or publication is claimed.

## Interpretation and roles

This is a fresh **synthetic challenge set**, not a representative operational sample. The author knew the classifier when writing reports; the separate reviewer shares a model family and rubric. “Material facts missing” versus ordinary tracing work and safety consequences versus operational causes remain rubric boundaries. All judgments were retained; none was adjudicated using predictions. No human logistics expert or field trial validated these results.

Manual prototype testing and feedback: **dansyar (author-reported)**. Fresh independent labels: **fresh_report_review**, a separate Codex agent. Automated tests, model runs, browser verification and this report: **OpenAI Codex**. These credits do not attribute automated execution or agent labels to the human author.

The fresh evaluation supports a human-confirmed work sample and exposes specific remaining failures. Next work should clarify the safety-consequence guide with an operator, add critical-system and historical-context handling as a new version, and assess that candidate on another untouched set. Do not tune on this set and then reuse its scores as unseen validation. Everything remains local; no repository push or Q11 save occurred.
