# Relay incident desk

An internal operations workbench for a fictional logistics operator. The primary
user is a duty coordinator who needs to identify time-sensitive incidents, choose
the receiving team and send ambiguous reports for review. This is an assessment
prototype with synthetic data, not a connected dispatch system.

## Experience

- Operations: queue → original report → proposed route and urgency → reasons →
  human confirmation/correction. No automatic messages to external teams.
- Evidence: fresh test, current development, a disclosed diagnostic retest,
  preserved original test, costs and policy experiment. Never mix these versions.
- Reviews: Latest review shows a completed second pass over all 60 Fresh 2 reports. Original, Fresh 1 and Fresh 2 keep their frozen judgments.
  Reviewer provenance is available on demand. Completed reviews use readable text, not disabled form controls. A separate manual review remains
  editable; neither review view exposes classifier predictions.
- New report: paste text, run real local inference, inspect the result.

## Composition and visual system

The user selected Linear's compact triage interface and explicitly requested:
"Remove ALL descriptors, reduce words on the screen." Use the reference for
density and composition, with original Relay branding. Charcoal surfaces, neutral
gray typography, a muted violet action color, and orange reserved for urgency.
System sans typography, 5 px corners, thin rules, and no decorative shadows.

Desktop fills the viewport with a narrow navigation rail, a compact report list,
and a detail pane. Use functional labels only. No hero, slogan, subtitle,
description, summary strip, explanatory paragraph, redundant metadata, or footer.
The report's first sentence becomes its heading; the remaining report is the body.
Only non-substantive generation wrappers are omitted; the original data is intact.
Team, urgency, note, and confirmation remain in the incident pane. Model/policy
controls, inference details, metrics and methodology belong in Evaluation.

At 1024/768 px reduce rail and list widths. At 390 px show a full-width queue,
then a full-width report with an explicit back button. Do not stack a long queue
above the report. Keep review instructions behind Guide, and the report index
behind the current position button. Use labeled horizontal scrolling for tables.
Check 1440, 1024, 768 and 390 px and inspect all three views visually.

## Accessibility and honest states

Semantic navigation, visible keyboard focus, explicit labels, text alongside
status colors, live feedback for saves and errors, and reduced-motion support.
Keep the compact Demo indicator in the navigation. Counts come from actual records.
Human actions are stored only in this local demo. Model similarity is not a
probability. Never present development estimates as independently verified test
performance. Show an actionable unavailable/error state rather than a fake zero.
