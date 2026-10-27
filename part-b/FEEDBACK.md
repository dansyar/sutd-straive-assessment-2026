# Prototype feedback

This records actual owner feedback during use of the local demo on 21–22 October
2026. It is product feedback from the assessment author, not an independent
logistics-operator usability study.

| Feedback | Change | Verification |
| --- | --- | --- |
| The initial interface looked AI-generated; the user wanted simpler navigation and a Linear-style layout | Replaced decorative summaries/cards with a compact queue/detail workbench | Visually checked at 1440, 1024, 768 and 390 px |
| Move model controls and evaluation out of the incident view; remove descriptors | Dedicated Evaluation view; functional labels only in operations; Guide on demand | Operations contains team, urgency, note and confirmation; no model controls |
| "Looks better" after the redesign | Retained the accepted visual direction | Owner's direct response; no quantitative usability improvement claimed |
| Why are urgent reports also inside Needs review? | Exclusive priority queues: urgent review cases stay in Urgent, ordinary Needs review excludes them; detail can show Urgent review | Browser queue checks and API/unit checks; Inbox intentionally remains the all-open overview |

The author is also trying the independent review workflow. No completed review
feedback or outside tester result has been invented. If an outside tester becomes
available, record their role/permission, task, observed difficulty, exact feedback
and resulting change here. Feedback is optional in the brief; it does not replace
the required independent label review or final correctness evidence.

The owner subsequently requested a separate agent review and removal of the AI label. All 60 reports were independently judged in a fresh context. The completed review uses neutral titles and columns, with actual authorship retained in Guide/Provenance and exported metadata. It is read-only to preserve the frozen test; manual review remains separate. Desktop/mobile visual checks and API tests verified this flow.

## Manual testing credit and triage correction

Manual prototype testing and feedback: **dansyar (as reported by the author)**. Codex executed the assisted walkthrough clicks and automated tests; this distinction is recorded in `ATTRIBUTION.md`.

On 22 October the author requested walkthroughs for a normal delay and a Needs review incident. The cold-chain case RLY-82374 exposed an incorrect rules suggestion: Transport operations/Routine despite 19 C cargo with a 2–8 C limit. The author requested better triage and another local test. The correction recognizes explicit readings and limits, ongoing cooling failure, controlled historical cases and sensor corrections. Active excursions keep urgent human review. Text/Sensitive is the new default; explicitly saved model preferences remain available.

The revised system was tested with 26 automated checks and a disclosed rerun of the same 60 reference cases. Detailed results are in `evidence/iterations/temperature-v3/`. These were Codex-run checks, not an independent human or operator study.

## Routing improvement and second fresh evaluation

The author requested improved team accuracy, correction of the missed fire-alarm case, and another fresh test with a separate agent, keeping everything local. The new checks address stated primary issues, confirmed custody and critical consequences. The corrected case passes in all four configurations. Fresh 2 and the paired comparison retain remaining errors and differences in reviewer interpretation. No operator feedback is invented.

## 24 October request

The author requested a neater website, natural explanations, another functional review and completion of all 60 reviews. The response adds a readable completed-review view, clearer spacing and typography, short report-specific reasons and a separate second-pass record for all 60 Fresh 2 reports. One clarification difference is visible without replacing frozen labels. Navigation, save, search and error-handling issues found during the audit were corrected. Testing was carried out by Codex and its agents; the author's prior manual-testing credit remains separate.
