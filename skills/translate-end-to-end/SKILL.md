---
name: translate-end-to-end
description: |
  Translates a whole work, a single file or a folder of files forming one book,
  from start to finish with no questions and no human approval gate: automatic
  workspace bootstrap, draft, mechanical gates, independent full-coverage judging,
  focused retranslation, chapter-level checks, an audit by a second judge and a
  final report. A deterministic controller keeps state and decides the next action.
  Use when the user asks to "translate end to end", "translate this book/folder/file
  fully", "fully automatic translation", "translate and verify until high quality",
  or "/translate-end-to-end".
---

# translate-end-to-end

## Steps

0. **Resolve models and execution capabilities before translating.** Read
    `references/model-handoffs.md` and `references/quality-policy.md`. Honor the user's requested translator, judge
   and parallelism; record requested versus actually selected models separately.
   On resume, preserve earlier provenance. The parent session owns the controller
   and launches workers; every worker saves its result as a Markdown artifact.
1. **Resolve scripts and inputs.**
   Accept `language=<language-tag> path=<file-or-folder>` with no approval gate.
   If either input is missing, the language is not BCP 47, or the path contains
   no Markdown source, stop with
   `Usage: /translate-end-to-end language=<language-tag> path=<file-or-folder>`.
   ```bash
   REPO=$(dirname "$(dirname "$(readlink -f ~/.claude/skills/translate-end-to-end)")")
   SCRIPTS="$REPO/scripts"
   ```
   If the skill was copied rather than symlinked, locate the script with
   `find ~ -name e2e_controller.py -path '*/scripts/*' 2>/dev/null`.
   `LANG_TAG` is the tag (never use `LANG`, a system variable). If `path` is a folder, the source dir is that folder and
   the files are its `*.md` files in name order; if it is a file, the source dir
   is its parent and only that file is translated. The workspace is
   `WS=<source_dir>/translation`, never treated as source.
2. **Bootstrap the workspace** with no questions: `references/bootstrap.md`.
3. **Initialise the controller.**
   ```bash
   python3 "$SCRIPTS/e2e_controller.py" init --source "<source_dir>" --workspace "$WS" --lang "$LANG_TAG" --files <file1> <file2> ...
   ```
   If the translator and judge model names are known, record them:
   `set-models --translator-model <X> --judge-model <Y>`.
4. **Process independent files in batches of four.** Read
   `references/parallel-batches.md`; keep controller writes serial and worker
   outputs disjoint. Apply `references/single-writer.md` for publication and
   `references/consolidated-review.md` for full/delta reviews. Use
   `references/efficient-dispatch.md` for compact context, mechanical corrections,
   consolidated validation and timing. Reconcile the batch before recording final
   clean chapter checks or starting audits. Within each file,
   loop on `next`. Call
   `next --workspace "$WS" --lang "$LANG_TAG" --file <name>`, handle the returned
   `action` as described in `references/action-handlers.md`, and call `next`
   again until it returns `done` or `stop`. Quality thresholds and the meaning of
   each outcome are in `references/quality-policy.md`.
5. **After each file**: set its row in `translation/manifest.md` to `verified`
   only if the controller returned `manifest_status: verified`, else `drafted`;
   never write `human reviewed`. Fill `decisions/<file>.md` and
   `verification/<file>.md` from `translation/templates/`, recording what the
   `chapter_checks` and retranslation rounds actually corrected.
6. **After the first file verifies**, enrich `context/style-guide.md` and the
   target's style anchors with the top-scoring passage pairs (source and target,
   score 100, no notes), marked `auto-approved`, using `create-style-guide`.
   Later files read the enriched guide.
7. **After all files**: run `check-consistency` in translation mode across the
   whole work (facts, terms, voice, conventions); fix real issues through new
   candidates and parent publication, then re-enter step 4 for each touched file. Then
   `report --workspace "$WS" --lang "$LANG_TAG"`.
8. **Final message**: report path; per-file status and score; unresolved
   passages with their last judge notes; residual risk (`references/quality-policy.md`);
   and the statement that the output is machine-verified and not human reviewed.

## Reference files

| File | When to read | What it contains |
|---|---|---|
| `references/model-handoffs.md` | Before starting or resuming; dispatching any worker | Model selection, capability boundaries, Markdown results, JSON conversion, stale-result prevention |
| `references/parallel-batches.md` | Scheduling a corpus or preparing PDF-wrapped input | Four-file batches, frozen context, source preparation, serialized state and reconciliation |
| `references/single-writer.md` | Dispatching or publishing a translation | Immutable candidates, version guards, scope and conflict handling |
| `references/consolidated-review.md` | Reviewing a chapter or corrections | Full/delta reviews, editorial rules, decisions and measurements |
| `references/efficient-dispatch.md` | Preparing dispatches, corrections and measurements | Context selection, exact replacements, validation and timing contracts |
| `references/bootstrap.md` | Step 2 | Building source profile, glossary, conventions and style guide without questions; `auto-decided` records |
| `references/action-handlers.md` | Step 4 | One section per controller action: what to do, which skill to apply, which command to call next |
| `references/retranslation-prompt.md` | Handling `retranslate` | Dense prompt template for fixing a single passage |
| `references/quality-policy.md` | Handling scores, stagnation, unresolved passages; writing the final message | Thresholds, best-of tracking, noise floor, caps, audit, independence of the judge, meaning of `verified` |
