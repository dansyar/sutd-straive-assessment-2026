# Demo walkthrough

Target: five minutes, then questions. All reports are fictional and all saved decisions are local. No completed interview or operator trial is claimed.

## Frame the task

Relay helps a coordinator choose a receiving team, urgency and when facts need human review. Show Inbox and the exclusive Urgent/Needs review queues. Done means a recorded routing decision, not that delivery or remediation has finished.

## Demonstrate the corrected incident

Open Urgent and select RLY-82374: cold cargo at 19 C against a stated 2–8 C range, with immediate isolation needed. The proposed team is Cold-chain quality and urgency is Urgent. Human confirmation remains required. Explain that the original rules model suggested Transport operations/Routine, which the author's walkthrough exposed. The correction uses readings, actual limits and current consequences, not the report ID.

Inspect team/urgency and add a note requesting exposure duration, logger readings and isolation confirmation. Confirm a route only when demonstrating a local decision; open Done and reload to show persistence. The earlier delay walkthrough RLY-27213 is already saved in Done with a clearly marked demo note. No actual team is contacted.

## Compare the approaches

Open Evaluation. New use defaults to Text/Sensitive; saved choices can be changed here. Rules is the explicit baseline. Text fits TF-IDF centroids only on the 240 training reports. Both use the documented cold-chain protection. Similarity is not calibrated probability.

Retest shows the current diagnostic: category F1 0.683 for Text versus 0.601 for Rules, using 56 known category labels. There are 16 urgent cases. Text/Sensitive misses zero but raises six false urgent flags and reviews 45/60; Rules/Sensitive misses one. Two wrong eligible Text/Sensitive routes and one bypassed required review remain. Do not present this as unseen validation.

Select Original test to show the preserved first v1 evaluation. Its code and labels were frozen before scoring. The current correction followed inspection of cases and mistakes, so the reused-case improvement is diagnostic. The subsequent Fresh test uses 60 new reports labeled by another fresh-context agent after classifier selection was frozen.

## Change the requirement

Compare Standard and Sensitive under a common missed-urgent penalty of 100. Revised Text changes 3 to 0 misses, 24 to 45 reviews and cost 398 to 69. Rules changes 11 to 1 misses, 32 to 56 reviews and cost 1188 to 198. Extra review and false alerts are explicit costs. Apply a policy to show the live queue change.

USD 0 means no paid classifier inference calls; computing, development/review service costs and labor are excluded. Warm inference timing does not measure human capacity or resolution time. Costs are relative assumptions, not prices or measured savings.

## Show provenance and testing roles

Label review contains all 60 unchanged agent judgments and reasons. Guide identifies the separate fresh-context reviewer and its limited inputs. This is not human domain-expert validation. `DATA.md`, `EVALUATION.md`, source hashes, per-report mistakes and the one-page summary support inspection.

Manual prototype testing and feedback are credited to dansyar (author-reported). Codex performed the assisted walkthrough clicks, automated checks and benchmarks. The 31-check suite includes 32 temperature scenarios across four configurations. Full attribution is in `ATTRIBUTION.md`. No outside tester feedback is invented.

## Next evidence

Collect representative operator reports, obtain domain judgments, test on a new set and measure review workload/escalation outcomes before integration. Publication and Q11 save are deferred because the owner requested local delivery.

## Fresh test

Evaluation defaults to Fresh test. The preregistered Text/Sensitive candidate catches 14/15 urgent reports, with F1 0.600, seven false urgent alerts and 50/60 reviews. Team accuracy is 34/56; six unknown urgencies remain unknown. RLY-910052 incorrectly gets routine customs review despite a disabled building fire alarm. Do not hide this miss. The previous diagnostic used exposed cases; this set was authored and independently labeled after the classifier was frozen, with no tuning after scoring.

Open Labels to inspect new judgments and reasons, or switch the Label review set to Fresh. They are read-only and retain agent attribution in Guide/CSV. The original 60 remain under Original; Own review preserves the separate editable original-set workflow. See FRESH-VALIDATION.md for limitations: synthetic reports, author knowledge, shared model family and no operator trial.

## Latest routing-v4 evidence

Evaluation now defaults to Fresh 2. Team accuracy is 49/55 (89.1%), F1 0.904, urgent misses 0/13, false urgent five and review 43/60. Click Labels for the independent judgments; the selector also retains Fresh 1 and Original. Some primary-team choices differ across reviewers on urgent safety-system blockers; their labels remain unchanged. The original missed fire-alarm case now receives Safety/Urgent review in all four configurations.

The same-report old/new comparison is 46/55 to 49/55 teams correct, with seven to five false urgent alerts and 41 to 43 reviews. That comparison was added after primary scoring and did not tune the candidate. Earlier set improvements are development diagnostics. The current 40-check suite and Linux replay pass; synthetic/shared-model evidence still requires operator validation. See FRESH2-VALIDATION.md.
