---
description: Spawn a review subagent, get prioritized suggestions, then implement all of them
---

You will run a three-phase loop: **review → propose → implement-all**. Target of the review: $ARGUMENTS (if empty, review the most relevant deliverable(s) in this repo — ask which only if genuinely ambiguous).

## Phase 1 — Review (subagent)
Spawn ONE general-purpose subagent to critique the target. In its prompt include:
- **Project context & goal**: what the artifact is and who it serves (state the end-user and the single job the artifact must do).
- **What to read**: the exact source-of-truth files (generators/templates), the rendered output, and the data model — with absolute paths. Tell it to read generators FULLY.
- **Already-done list**: every improvement from prior rounds, with an explicit "do NOT re-propose these" so suggestions don't overlap.
- **Optional screenshot** instructions if the target is a webpage (headless Chrome at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` → `--headless=new --screenshot=/tmp/rev.png ... "file://<abs>"`, then view it).
- **Deliverable**: at least 5 (aim 6–8) NEW, concrete, non-overlapping suggestions. For each: title + which deliverable + which goal (attract / help-beginner / both) + the specific problem (cite code: element/class/function/behavior) + a concrete implementable change (which existing data fields, roughly how) + Effort (S/M/L) + Impact (high/med/low). End with a prioritized list and the single highest-leverage change. Tell it to look for second-order gaps (trust signals, shareability/SEO, accessibility, content quality, dedup, navigation, mobile, empty states) and to prefer changes needing no new manual data. **Report only — do not edit files.**

## Phase 2 — Relay
Summarize the suggestions to me as a compact prioritized table (number, title, deliverable, goal, problem) and name the highest-leverage one. Keep it tight.

## Phase 3 — Implement ALL
Implement **every** suggestion, in priority order — **skip none**.
- Create a task (TaskCreate) per suggestion; set it in_progress when you start it.
- After each change, **verify it actually landed** (grep the generated output for the new element/string; re-render; for pages, screenshot headlessly and look at it).
- Mark each task **completed** only after it's verified. If the data can't show a feature yet (cold-start), say so honestly — implement the mechanism, don't fake data.
- Keep edits consistent with the surrounding code's style and the established visual identity.
- Regenerate all derived artifacts so they stay in parity.
- Clean up any temp/preview files (e.g. screenshots) before committing.
- Commit on the working branch (branch first if on the default branch) with a message listing what each numbered item did; end the message with the Co-Authored-By trailer.

## Final report
Show all suggestions as a checklist with each marked ✅ (implemented & verified), and note anything intentionally empty at cold-start. Do not skip any item.
