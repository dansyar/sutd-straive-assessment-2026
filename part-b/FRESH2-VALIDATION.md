# Routing-v4 and a second fresh test

**The revised Text/Sensitive candidate gets 49/55 clear team labels correct (89.1%) and catches all 13 labeled urgent cases on 60 new reports. Keep routes human-confirmed:** six team disagreements, five false urgent alerts and one wrong team outside model abstention remain.

## What changed

The primary-issue checks now distinguish lost goods from missing documents, confirmed custody from an allegation, physical cargo damage from a vehicle problem, and a closed incident from a current hazard. Active physical/security consequences take priority over temperature handling. An unavailable critical safety system gets urgent Safety & security review even when paperwork or transport is the immediate blocker. Base-model scores stay heuristic; an override does not invent a probability.

RLY-910052, the previously missed customs-held fire-alarm controller, now receives **Safety & security/Urgent with review in all four configurations**. Its text and labels were not changed. The correction covers fire pumps, medical-gas alarms, emergency stops, ventilation and communications, and includes negation/restoration checks. Both Rules and Text share these explicit checks; the improvement is not solely a change in the trained text model. Training remains the same 240 reports.

The first fresh set was used for development and now has 56/56 correct known team suggestions and zero urgent misses under Text/Sensitive. This is an exposed-case diagnostic, **not unseen validation**. It is recorded separately in `evidence/iterations/routing-v4/fresh1-retest.json`. A pretest draft's regression failures and superseded registration are preserved; the final candidate was frozen only after those checks, before fresh-2 report authoring.

## Fresh-2 protocol

- `evidence/fresh2-20261022-registration.json` froze routing-v4 and selected Text/Sensitive before the new reports existed. Code copies are under `evidence/versions/routing-v4-pre-fresh2/`.
- `generate_fresh2.py` authored another 60 fictional reports. Text/ID uniqueness was checked against all preceding 420 reports. No exact/normalized duplicate or ID overlap was found; maximum word-trigram Jaccard similarity was 0.1111. Shared issue types and some scenario themes remain; lexical checks do not establish semantic independence.
- A new agent, `fresh2_report_review`, started with **no inherited conversation** and received only the new reports and the unchanged guide. No previous labels, reports, classifier, predictions or results were supplied. It labeled every report and gave reasons. Raw output is preserved unchanged in `evidence/reviews/fresh2-20261022/review.raw.json`.
- All 60 labels were frozen before first scoring. `fresh2_evaluate.py` and its source manifest were frozen before reviewer output was accessed. The evaluator reuses unchanged metric functions and checks report, label, raw-review, candidate, training, guide and driver hashes. No classifier, threshold, taxonomy, training data or judgment changed after fresh-2 labels/results were seen.
- The new set never enters training or the initial operations queue. Earlier source files, judgments and results remain unchanged; the previous fresh test can be reproduced using its preserved v3 implementation.

## Results and denominators

There are **55 known categories**, **52 known urgencies** (13 urgent, 39 routine), **five unclear categories**, **eight unclear urgencies**, and **ten reference-required reviews**. Unknowns remain unknown. Team accuracy/F1 use 55; urgency errors use 52; urgent recall uses 13; review and cost use all 60.

| Configuration | Team accuracy | Macro F1 | Urgent misses /13 | False urgent | Review /60 | Wrong eligible teams | Required review bypasses | Cost at 30 | Cost at 100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Rules / Standard | 78.2% | 0.768 | 4 | 0 | 36 | 2 | 1 | 174 | 454 |
| Rules / Sensitive | 78.2% | 0.768 | 2 | 9 | 54 | 0 | 0 | 132 | 272 |
| Text / Standard | 89.1% | 0.904 | 0 | 3 | 30 | 1 | 2 | 54 | 54 |
| **Text / Sensitive (preregistered)** | **89.1%** | **0.904** | **0** | **5** | **43** | **1** | **0** | **59** | **59** |

Text/Sensitive reviews all ten reference-required reports, but still reviews 71.7% of the entire set. Of 17 reports outside model abstention, one has the wrong team. The demo requires human confirmation for every route, including those outside abstention. Catching 13/13 urgent synthetic examples does not establish perfect recall in operation. Eight unknown urgencies are not counted as safe or correct routine decisions.

## Same-report version comparison

After primary scoring, the preserved temperature-v3 classifier was also scored on the exact same fresh-2 reports and frozen labels. Both classifier versions predate these reports. This paired comparison was added **after** primary results, did not select a candidate and involved no tuning. Full old/new metrics, per-report outputs and hashes are under `evidence/iterations/routing-v4/paired-fresh2-versions.json` and adjacent files.

| Text / Sensitive | Preserved v3 | Revised v4 |
| --- | ---: | ---: |
| Correct team /55 | 46 | 49 |
| Team accuracy | 83.6% | 89.1% |
| Macro F1 | 0.839 | 0.904 |
| Urgent misses /13 | 0 | 0 |
| False urgent | 7 | 5 |
| Review /60 | 41 | 43 |
| Cost at miss penalty 100 | 67 | 59 |

The earlier 60.7% result belongs to a different set and reviewer. Do not subtract it from 89.1% as a paired improvement. On this same set the gain is three additional correct teams (5.5 percentage points). The small synthetic sample and label ambiguity limit inference.

## Failures and rubric disagreement retained

The second reviewer interprets critical-system restoration blockers as their operational category **with urgent priority**. The previous reviewer instead used Safety/Urgent for these cases. Neither was shown predictions, and no labels were changed to favor the code. These are independent agent interpretations of an ambiguous boundary, not adjudicated expert truth.

| Report | New independent judgment | Revised Text/Sensitive | Interpretation |
| --- | --- | --- | --- |
| RLY-920010: missing export licence blocks fire-suppression restoration | Documents & customs/Urgent | Safety & security/Urgent, review | Team-policy disagreement; urgent consequence caught. |
| RLY-920023: bridge delays emergency ventilation fan while room is unsafe | Delay/Urgent | Safety & security/Urgent, review | Same routing boundary; priority caught. |
| RLY-920036: absent medical-gas alarm sensor blocks restoration | Missing/Urgent | Safety & security/Urgent, review | Same routing boundary; priority caught. |
| RLY-920039: all goods delivered, signed proof is missing | Documents & customs/Routine | Delay/Routine, review | Confirmed cargo location can still outweigh the actual record issue. |
| RLY-920008: located wagon waits for the next rail service | Delay/Routine | Safety & security/Urgent, review | Wrong team and false urgency. |
| RLY-920012: driver awaits receiving staff at a locked gate | Delay/Routine | Safety & security/Urgent, no abstention | Wrong eligible team; human confirmation remains essential. |

Two additional delayed routine loads (RLY-920002 and RLY-920049) and the completed drill record (RLY-920050) receive false urgent alerts. All errors are retained in `evidence/fresh2-20261022/fresh-test-mistakes.json`; predictions are adjacent. Rules/Sensitive still misses two urgent cases. No post-test fix was applied to make these scores look better.

## Requirement change, timing and economics

The common missed-urgent penalty rises from 30 to 100 without changing the metric definition. On fresh-2, Text Standard to Sensitive increases reviews 30 to 43 and cost 54 to 59; both catch all 13 known urgent cases. Sensitive catches all ten required reviews versus eight under Standard. It is **not the cheapest observed configuration on this set**; it remains the preregistered conservative demo default. Rules Standard to Sensitive reduces misses four to two and cost at 100 from 454 to 272, at the price of 18 additional reviews and nine false urgent flags.

Relative costs remain review 1, automatic wrong team OR bypassed required review 6 once, false urgency 2, and every urgent miss 30 or 100 even in ordinary review. These are scenario assumptions, not prices, staffing feasibility or measured savings. Both classifiers make zero external inference calls; compute, conversation/review services and human labor are unpriced.

Local warm p95 was 0.205/0.195 ms for Rules Standard/Sensitive and 0.109/0.110 ms for Text, 300 samples per configuration after warm-up. Excludes startup, HTTP, rendering, queue time and human decisions. Timings vary by machine. All 40 behavioral/integrity tests pass, including 32 temperature and 19 authored routing scenarios; those regression fixtures are not additional independent reports.

## Inspect and reproduce locally

Evaluation defaults to **Fresh 2**, with Team accuracy, Macro F1, urgency, workload and costs. Labels opens the new read-only judgments. Fresh 1 and Original remain available; Own review remains a separate editable original-set workflow. CSV exports preserve actual reviewer attribution.

From `part-b/`, using Python 3.12 and the pinned application dependencies:

```sh
python generate_fresh2.py
python fresh2_evaluate.py --output evidence/reproduced-fresh2
python compare_versions.py --output evidence/reproduced-version-comparison
python evidence/versions/temperature-v3-pre-routing-v4/fresh_evaluate.py --output evidence/reproduced-fresh1
python -m unittest discover -s tests -v
```

Existing result files and label freezes cannot be overwritten. Clean local Linux reproduction matches all 240 fresh-2 predictions, all 240 preserved fresh-1 predictions and all quality/cost counts, excluding machine-dependent timing. The paired version comparison reproduces too. See `evidence/fresh2-20261022/runtime-verification.json` for the precise scope.

Manual prototype testing and feedback are credited to **dansyar (author-reported)**. Automated checks, benchmarks, browser verification and implementation are credited to **OpenAI Codex**. New reference judgments belong to the separate **fresh2_report_review** agent. No human logistics-expert review, representative operational sample, field trial, publication, repository push or assessment save is claimed.

Next: have an operator clarify the primary-team rule for critical-system blockers, obtain representative noisy reports and measure review capacity. Any further tuned candidate requires another untouched test. Current results support the local work sample and expose remaining failures; they do not establish production reliability.
