# Interface verification — 21 October 2026

Linear-inspired dark triage layout with original Relay branding. Only functional
labels and report content are visible by default. Model and policy controls moved
to Evaluation. The existing review workbook and data files are unchanged.

Verified in the real browser at 1440, 1024, 768 and 390 px:

- No page-level horizontal overflow. The list and detail scroll independently.
- Desktop/tablet: navigation, report list and detail pane.
- Phone: list opens a full-width report; Back returns to the list.
- Search narrows the queue and updates the selected report and count.
- Evaluation Apply changes the live model/policy; restored Rules/Standard after QA.
- Created a temporary report, corrected its team, added a note and confirmed it.
  It left Inbox, appeared in Done, and persisted after reload.
- The temporary report and its own decision were removed after QA. Human reviews
  and existing records were not changed.
- Blind review starts with empty labels. Guide and report selector are on demand.
- JavaScript syntax check passed. No extra dependencies or paid API calls.

Follow-up checks after the owner's queue feedback:

- Urgent and Needs review now have disjoint membership. Urgent review cases keep
  their review flag and appear only in Urgent. Inbox remains all open reports.
- Actual browser counts with Rules/Standard: Inbox 48, Urgent 10, Needs review 12.
  The 12 review rows contained no urgent markers; the API exposes the same
  priority assignment. Counts reflect the revised rules, not human test labels.
- Evaluation prices every row under the same selected penalty: Rules/Standard
  costs 525 and Rules/Sensitive 55 with penalty 100. Standard was restored after
  testing. Unknown scores render as unavailable, not zero.
- Mobile filter sizing was widened so Needs review remains readable. Updated
  queues and Evaluation were checked at desktop/tablet/mobile widths.
- The user's original workbook and saved reviews were not edited by QA.

Fresh-container corpus, behavioral, model-reproduction and real HTTP checks are
recorded in `evidence/runtime-verification.json`. This verifies local packaging,
not GitHub publication, assessment submission or production deployment.

## Completed review and final test

A separate reviewer has now completed all 60 judgments. The default Label review is read-only and shows 60/60 with original reports, labels and reasons. Next/Previous navigation works; Guide retains actual agent attribution and opens a separate editable manual review. The manual view remained at 0/60 during QA and no judgment was saved. Returning to Label review restores the frozen labels. Workbook and CSV downloads contain all 60 judgments with provenance.

The completed review and Final test view were visually inspected at 1440, 1024, 768 and 390 px. No page-level horizontal overflow occurred; the wide evaluation table scrolls within its own region. No browser console warnings/errors were recorded. Final test shows the actual frozen scores and miss denominator of 16; collapsed Methodology explains the 56 known-label denominators and reviewer limitations. Primary review titles/columns contain no AI label.

Screenshots: `evidence/ui/completed-review-desktop.png`, `completed-review-mobile.png`, `final-test-desktop.png`, `final-test-mobile.png`. Original source reports, initial blank workbook and manual records are preserved. Publication and Q11 save are tracked in `DELIVERABLES.md`.

## Temperature revision - 22 October 2026

Verified by Codex in the actual browser at 1440, 1024, 768 and 390 px. Manual prototype testing/feedback is credited separately to dansyar (author-reported).

- RLY-82374 appears in Urgent with Cold-chain quality, Urgent and human review required. The prediction is correct under every method/policy combination. No confirmation was saved for this incident during QA.
- Text/Sensitive is the new default for new use and was applied through Evaluation for the current preview; model/policy controls remain outside the incident pane. Explicitly saved choices remain selectable.
- Retest selects the current diagnostic; Original test displays the unchanged v1 results. The collapsed methodology explains prior case exposure. All table rows use the same selected cost penalty.
- Both revised views have no page-level horizontal overflow; the table scrolls within its region. Mobile incident details retain Back. Screenshots are in `evidence/ui/temperature-v3/`.
- Label review still displays 60/60 read-only judgments with actual agent attribution. The manual review remains separate. No browser warnings/errors were recorded.
- A cached old HTML entry point was detected during verification. The index now uses no-store caching and versioned assets; a refresh loads the revised interface.
- The prior RLY-27213 demonstration decision remains in Done; local manual labels and history were unchanged.

The 26 behavioral checks, 32 temperature scenarios and isolated Linux/HTTP reproductions are recorded in `evidence/iterations/temperature-v3/runtime-verification.json`. Reused reference cases remain a diagnostic, not new independent validation.

## Fresh-set results and labels - 22 October

Verified by Codex against the running local app after the classifier and all fresh labels were frozen. Manual prototype testing and feedback remain credited to dansyar (author-reported).

- Evaluation defaults to Fresh test, showing all four configurations, n=60 and the retained Text/Sensitive miss (1/15), 50/60 abstentions and F1 0.600. Original test remains selectable and displays its unchanged v1 results.
- Labels opens the fresh read-only judgments and reasons. The set selector switches between Fresh, Original and the separate Own review workflow. All 60 new source texts match frozen input. CSV exports all 60 with actual agent attribution, including six unclear urgencies.
- Inspected Evaluation and Fresh labels at 1440, 1024, 768 and 390 px. Tables scroll within a labeled region; no page overflow. The mobile review header was revised to keep its count, selector and actions readable, then rechecked. Original review was also inspected at 390 px.
- No browser warnings or errors were recorded. The entry point remains no-store; assets are version 10. Temporary viewport reset was called; the final tab remains on Fresh test.
- Saved-state counts remain unchanged: zero custom incidents, one prior decision, zero manual review labels/history. Fresh reports do not enter training or the operations queue. The known fire-alarm failure was reproduced through the real HTTP API without saving it.
- Local Linux reproduction matched all 240 per-report predictions and all quality/cost counts, excluding machine-dependent timing. All 31 checks passed locally and in the container. The refreshed business summary is one page and was rendered/visually inspected.

Evidence: `evidence/fresh-20261022/runtime-verification.json`; screenshots in `evidence/ui/fresh-20261022/`. These checks confirm the implementation/evidence flow; the synthetic results still include material failures and do not establish operator performance. No publication or assessment save occurred.

## Routing-v4 and Fresh 2

Verified by Codex on the running local app, after the final classifier and new independent labels were frozen. Manual prototype testing and feedback remain credited to dansyar (author-reported).

- Evaluation defaults to Fresh 2 and includes Team accuracy. All four rows match the frozen result: Text/Sensitive 89.1% team accuracy, F1 0.904, zero misses among 13 labeled urgent cases, 43/60 abstentions and cost 59 at either priority penalty.
- Labels opens the second fresh-context agent's read-only judgments. All 60 texts/reasons remain intact; eight unknown urgencies are retained. CSV has the actual agent name/type. Fresh 1 can still be selected in both results and labels without applying current code to its historical freeze.
- Inspected Evaluation and new labels at 1440, 1024, 768 and 390 px. No page overflow; the results table scrolls inside its labeled region. The compact mobile set selector and actions remain readable. No console warnings/errors were recorded. Temporary viewport reset was called; the output tab remains on Fresh 2.
- The original fire-alarm controller text returns Safety & security/Urgent with review through the real HTTP API under Rules/Text and Standard/Sensitive. No report was added to the user's queue. Saved incident, decision and review rows are identical to the pre-restart snapshot.
- All 40 automated checks passed locally and in clean Linux. All 240 new predictions, all 240 preserved first-fresh predictions, quality/cost counts and the paired version comparison reproduce, excluding machine-dependent timing. The new one-page summary was rendered and visually inspected.

Evidence: `evidence/fresh2-20261022/runtime-verification.json`, `FRESH2-VALIDATION.md`, screenshots in `evidence/ui/routing-v4/`. The evidence retains six team disagreements, five false urgent alerts and one wrong eligible team. Three team disagreements concern the guide's critical-system ownership boundary. The classifier and labels were not changed after scoring. Everything stays local; no submission or publication occurred.

## 24 October — UI polish, complete reviews and bug audit

The current interface keeps the compact Linear-inspired layout, with clearer typography, quieter navigation, more consistent spacing and a readable completed-review view. Model and evaluation controls remain outside incident details. Explanations use short, report-specific sentences. The Guide and CSV retain actual agent attribution.

Reviews now opens Latest review: **60/60 Fresh 2 reports completed** by `review_all_sixty`. Category and urgency agree with the frozen references on all 60; RLY-920024 additionally needs clarification because its delivery record conflicts with the recipient's account. This supplemental second pass saw the earlier labels and does not replace independent labels or change benchmark scores. Five unclear categories and eight unclear urgencies remain explicit.

Fixed during this pass:

- Old network responses could overwrite the active incident, review or evaluation set.
- A review save could switch the displayed source after the user navigated away.
- Successful creation followed by a failed refresh could encourage duplicate creation.
- Pending saves could discard later edits; pending creation could be dismissed and replace a new draft.
- Done search used the predicted team rather than the confirmed team.
- Urgent incidents without a review flag displayed Open.
- Empty review sets and shortcuts during loading could fail.
- Paging discarded keyboard focus. View Done on mobile opened the list rather than the saved incident.
- Padded report text bypassed the meaningful length check. Database connections were not explicitly closed. Invalid evidence files produced unhelpful errors, and CSV formulas were not escaped.

Verification completed by Codex:

- **47 Python checks and 12 JavaScript regression checks passed**. The JavaScript checks exercise actual event handlers with controlled response ordering; they are not a substitute for browser rendering checks.
- The rebuilt local Linux container passed all 47 backend checks. Its real supplemental review, all five result sets and CSV export returned successfully. The container contains the completed review artifact.
- Operations, Reviews and Evaluation were visually inspected at **1440, 1024, 768 and 390 px**. All 12 views fit their viewport width; the wide results table scrolls within its own region. The mobile incident view, report selector and guide were also checked.
- Created a report, confirmed it, followed View Done, changed its note, reloaded and verified persistence. Checked corrected-team search, empty-search recovery, required review reasons, manual-review saving, model/policy application and all five result selectors. These writes used a separate local test database, never the user's database.
- Opened all 60 completed review pages: 60 unique IDs, 60 nonempty reasons, and Next disabled on the last report. Checked the one disagreement, original/fresh source selection, Guide attribution and the browser CSV download. Downloaded contents exactly match the 60-row export.
- No browser console warnings or errors were recorded. The container emitted a dependency deprecation notice for the test client; tests and endpoints still passed.
- The exact earlier fire-alarm report still routes to Safety & security / Urgent with review under all four configurations. Classifier and frozen Fresh 2 label hashes match the earlier freeze. The user's saved rows are identical before and after this work.

Screenshots: `evidence/ui/quality-20261024/`. Machine-readable scope: `evidence/quality-20261024/verification.json`. Completed export: `output/review/review_latest_60.csv`. Earlier verification entries remain historical records.

The 180 independent reference judgments remain unchanged, and this new 60-row second pass is recorded separately. Automated testing, assisted browser actions and supplemental review were performed by Codex and its agents. Prior manual prototype testing and feedback remain credited to dansyar as author-reported. No external operator validation, publishing or assessment submission occurred.
