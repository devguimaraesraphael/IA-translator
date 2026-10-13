# Action handlers

The exact flags of every command are shown by
`python3 "$SCRIPTS/e2e_controller.py" <command> --help`. Commands below use:

```bash
C="python3 $SCRIPTS/e2e_controller.py"
```

Every call also takes `--workspace "$WS" --lang "$LANG_TAG"`.

After every handler, call `next --file <name>` again. Edit only what the action
names. The controller detects your edits from the files on disk.

The parent session owns controller calls and worker dispatch. Follow
`references/model-handoffs.md` for explicit model selection and Markdown results.
Workers never need nested subagents. Translators write immutable candidates
covering the named scope; the parent publishes via `single-writer.md`. Judges
never edit manuscripts. Apply `consolidated-review.md` to reuse full reviews.

## translate

Payload: `source_path`, `target_path`. Follow `translate-fiction` Step 1 (blocks
1 to 5, prefix identical across files) and Step 2 (subtext, naturalness,
copyedit, continuity), reading the glossary, conventions, style guide and
`decisions/` from the workspace. Write the whole chapter to a new candidate with
the same paragraph structure as the source: one paragraph per line, headings kept,
same paragraph count. Record non-trivial choices for `decisions/<file>.md`, never
in the manuscript.

## repair_parity

Payload: `source_paragraphs`, `target_paragraphs`. Compare source and target
paragraph by paragraph, find the merged, split, dropped or added paragraphs, and
fix them in a candidate so the counts match. Re-translate only a missing
paragraph; do not rewrite the others.

## repair_gates

Payload: `findings`, `gate_rounds`. Apply the `translation-gates` reading rules
(`skills/translation-gates/references/gates.md`): read each finding with source
and target side by side and fix only confirmed defects. For an inspected number
false positive, call
`allow-number --workspace "$WS" --lang "$LANG_TAG" --file <name> --value <v>`
instead of editing. Never silence a number without reading it.

## judge

Payload: `passages`, `sample`, `prompts_dir`, `batches`, `prompt_files`. Combine
the chapter's prompt files into one fresh review when they fit, preserving all
passage IDs. Split only at semantic boundaries when needed. The judge receives
the consolidated prompt content (it contains the
support texts and rubric), its output contract and no translator reasoning.
Select the judge model resolved in preflight explicitly. Require a Markdown
result in a unique `state/handoffs/<stem>/<round>/judge-NN.md` path, containing
exactly one `json` fenced block with the required array covering every passage id.
The parent verifies that file exists, parses the block, validates exact ID
coverage and associates it with the dispatched prompt hash. Convert the parsed
array to `judge-NN.json` alongside that result, then register ONLY the explicit
JSON paths from this dispatch (never a wildcard of older batches):

```bash
$C record-judgments --workspace "$WS" --lang "$LANG_TAG" --file <name> --judgments <round_dir>/judge-01.json <round_dir>/judge-02.json
```

Read `restored`, `missing`, `unresolved`; do nothing about them, the controller
decides what follows.

## retranslate

Payload: `reason` (`fail` or `polish`) and `passages`, each with `id`, `index`,
`attempt`, `strategy`, `source`, `current`, `notes`, `context_before`,
`context_after`, `best_score`, `paragraph_count`, `line_numbers`. For each
passage, build the prompt from `references/retranslation-prompt.md`, apply the
strategy, and change only the lines in `line_numbers` in a new candidate:

- `targeted_notes`: fix exactly what the judge notes name.
- `widen_context`: reread the context lines, the glossary and the style anchors,
  and rewrite the passage as a whole.
- `multi_candidate`: write 3 candidates, pick the best against the notes, the
  source and the glossary, and keep the paragraph count.

Never repeat the mistake of a rejected earlier attempt listed in `notes`. Keep
numbers and `Preserve` terms. For `polish`, make only the changes the notes ask
for; do not rework passages that are fine. Editing several passages in one pass is
fine; passages do not share lines.

If a note demonstrably contradicts a recorded convention or misreads available
source context, do not distort the translation to satisfy it. Request one
reconsideration with a concrete reason, then call `next` and dispatch its judge
prompt to a fresh independent judge using the Markdown handoff contract:

```bash
$C reconsider --workspace "$WS" --lang "$LANG_TAG" --file <name> --passages <id> --reason "<specific source or convention evidence>"
```

This keeps the same text, preserves the prior verdict, consumes a normal attempt
and is permitted once per failing passage. It does not approve the passage or
relax thresholds. Supply context neutrally; never instruct the judge to approve.

## chapter_checks

Payload: `round`. Before recording clean checks, require completed batch
reconciliation against the current chapter versions. Keep this action pending
while independent reviews/reconciliation finish; do not advance to audit merely
because the individual chapter review is clean. Merge confirmed findings into
one scoped correction round, using `efficient-dispatch.md` for exact mechanical
replacements. Reuse a consolidated report matching the current version.
After scoped corrections, check changed passages, affected cross-chapter terms
and known issues, retaining baseline coverage evidence. If no matching report
exists, run against previous translated chapters:

1. `check-consistency` in translation mode (fact, term, voice, convention).
2. `review-writing-tics` on the target text, applying its intentionality test.
3. `update-story-bible` translation mode: add new recurring terms to the target
   glossary and record cross-chapter decisions in `decisions/<file>.md`.

Fix real issues in a candidate, publish through the parent, then:

```bash
$C record-chapter-checks --workspace "$WS" --lang "$LANG_TAG" --file <name> --issues <n> --note "<short summary>"
```

`<n>` is the number of issues you fixed (0 when none).

## audit

Payload like `judge` plus `audit: true`. Same as `judge`, with a separate
fresh-context subagent per prompt file. Honor the resolved audit model; do not
override an explicit user choice merely to diversify models. Save Markdown
results as `audit-NN.md` in a new round directory and convert validated arrays
to `audit-NN.json`. Register only this dispatch's explicit paths:

```bash
$C record-judgments --workspace "$WS" --lang "$LANG_TAG" --file <name> --judgments <round_dir>/audit-01.json --audit
```

`audit_reopened` lists passages sent back to retranslation.

## finalize

```bash
$C finalize --workspace "$WS" --lang "$LANG_TAG" --file <name>
```

Read `restored` and `unresolved`; then call `next` once more to get `done`.

## done

Payload: `manifest_status`, `score`, `unresolved`. Update the manifest row, write
`decisions/<file>.md` and `verification/<file>.md` (SKILL.md step 5), then move
to the next file.

## stop

Payload: `reason` (`budget` or `max_steps`). Stop that file. Mark its manifest row
`drafted`, note the reason, continue with the remaining files only if the reason
was `max_steps`; on `budget`, stop the run and go to the report.
