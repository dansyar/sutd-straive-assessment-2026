# Part B requirement coverage

Checked against the authenticated [assessment brief](https://exam.sanand.workers.dev/sutd-2026-10-internship) on 21 October 2026. Deadline: **27 October 2026, 11:59 pm SGT**.

Relay is a logistics incident triage work sample: an internal coordinator's workbench plus separate evaluation. A commercial SaaS business, paid AI model or hosted service is not required.

| Requirement | Concrete evidence | State |
| --- | --- | --- |
| Demonstrable classification, urgency and human review | `app.py`, `engine.py`, `web/`, corrections/persistent decisions, `UI-VERIFICATION.md` | Working locally |
| At least 300 documented non-confidential reports | 300 development + 60 original test + 60 first fresh + 60 second fresh reports; `DATA.md`, source/hash checks | Complete: 480 fictional reports |
| Independently review at least 50 labels | 180 judgments across three separate fresh-context agents; text/guide-only inputs and unchanged raw judgments preserved | Complete separate-agent review; human expertise not claimed |
| At least two approaches, including simple baseline | Rules and trained TF-IDF centroids, unchanged during test | Complete |
| Quality, costly misroutes, latency, cost, mistakes and abstention | `evaluate.py`, `fresh2_evaluate.py`, version comparisons, frozen result files, `EVALUATION.md`, `FRESH-VALIDATION.md` | Complete: original first test, disclosed diagnostics and two fresh preregistered tests; failures and unknowns retained |
| Changed requirement | Missed-urgent penalty 30 to 100, stricter policy, common-matrix cost/workload comparison | Complete on development, original test, diagnostic and fresh test |
| Public repository; demo or reproducible instructions | Root/Part B README, pinned dependencies, Dockerfile, automated checks | Reproducible local instructions and source are included |
| Data provenance, evaluation scripts/results | `DATA.md`, `corpus.py`, `review.py`, `evaluate.py`, frozen inputs/hashes | Complete |
| One-page business summary | `output/pdf/business-summary.pdf` | Updated from second fresh test; preceding summaries preserved; one page |
| AI/collaborator attribution | `ATTRIBUTION.md`, review provenance | Complete |
| Feedback, if possible | `FEEDBACK.md` records actual owner feedback and fixes | Obtained; no outside operator study |
| Project repository | `https://github.com/dansyar/sutd-straive-assessment-2026` | Submit the public URL through the assessment |

The brief allows agents/collaboration and does not explicitly mandate human label review. The separate reviewer received only text and guide, retaining uncertainty. Shared tooling and lack of domain-expert validation are disclosed. The prior same-assistant pass is historical and not the independent reference.

## Submission

The public repository contains the runnable project, data, evaluation evidence, business summary and attribution. The assessment requests its repository URL in Question 11. Submission status should be verified on the assessment page.

The project evidence addresses the requested deliverables; completeness does not guarantee marks, production performance or a follow-up invitation.

## Manual marking

| Area | Marks | Evidence |
| --- | ---: | --- |
| Problem framing | 10 | Business summary, operating assumptions, urgency/route costs and human ownership |
| Correctness | 10 | Working flow, behavioral checks, frozen independent judgments, failures and limitations |
| Reproducibility and cost | 10 | Source/freeze hashes, group split, scripts, per-report results, timings and cost matrices |
| Working demo | 10 | Usable queues, inference, correction, persistence, review and changed-policy interaction |

Q11's URL checker awards zero automatic project marks. Part B's 40 marks are manual and separate from Part A's displayed score. The site also mentions a separate 10-mark walkthrough; `WALKTHROUGH.md` prepares it without claiming an invitation or awarded marks.

## Temperature correction and testing roles - 22 October

RLY-82374 receives Cold-chain quality/Urgent, with human confirmation, under all four configurations. Diagnostic, original and fresh tests are separately selectable. The cold-chain correction followed exposure to the original cases. A subsequent preregistered fresh test uses 60 new reports, a newly independent reviewer context and unchanged classifier/labels. It caught 14/15 urgent cases but retained a critical fire-alarm miss. See `FRESH-VALIDATION.md`; synthetic convenience selection and shared model-family bias remain limitations. Original code, results and labels are preserved.

Manual prototype testing and feedback are credited to **dansyar (author-reported)**. **Codex** authored and executed automated checks and benchmarks; separate agents retain credit for both sets of independent labels. The suite has 40 checks including 32 temperature scenarios across four configurations. The benchmark and manual feedback were recorded before publication.

## Routing-v4 and second fresh test

The fire-alarm blocker is corrected under all four configurations. A new candidate/selection freeze preceded another 60 reports and a new independent reviewer context. Text/Sensitive gets 49/55 known teams correct (89.1%), catches 13/13 known urgent cases and reviews 43/60, with five false urgent alerts and one wrong eligible team retained. On the same reports the frozen old version gets 46/55 teams correct. Critical-system team-policy disagreements are preserved. Full protocol and limits: FRESH2-VALIDATION.md. The 40-check suite, all new predictions, historical replay and paired comparison reproduce in local Linux. The benchmark was recorded before publication.

## Latest local quality review — 24 October

Completed: quieter UI, clearer review reading view, 60/60 supplemental Fresh 2 reviews, concise reasons, and fixes for stale navigation, save-state handling, confirmed-team search, urgent status, validation, database connections and export safety. There are now 47 backend checks and 12 frontend checks. The earlier 40-check result above records the 22 October run. Original independent labels, model scores and user records are preserved. The supplemental review is attributed to its agent, with one clarification disagreement disclosed. `UI-VERIFICATION.md` records the browser verification. This describes the local verification completed on 24 October.
