# Models and durable handoffs

## Preflight

1. Resolve translator, judge, audit judge and effort before the first draft.
   Use explicit user choices first, then recorded preferences. Otherwise select
   available translator and independent judge models and disclose the selection.
   Honor the user's effort limit. Do not silently upgrade effort or switch models.
2. Resolve display names against the runtime's actual model identifiers. An
   unavailable-model response may supply the valid spelling; correct spelling
   without choosing a different model. If the requested model is unavailable,
   stop that role and report the blocker rather than using the default.
3. Pass the model identifier explicitly to every worker. A product name such as
   GitHub Copilot is not a model identifier. A worker's self-identification is
   not proof of routing; use the dispatch configuration and tool response.
4. Record the plan in `targets/<lang>/verification/_execution.md`: requested
   names, resolved identifiers, effort, parallelism, role, first successful
   dispatch and any unconfirmed routing. Mark planned roles as not yet executed.
   Record actual translator and judge IDs via `set-models` once used. On resume,
   document any earlier draft with unknown provenance instead of relabeling it.
5. Check which tools are available to the parent and workers. The parent runs
   `next`, conversion, registration and validation. Translators translate;
   judges judge. Do not delegate orchestration to a worker that cannot spawn
   model-selected subagents. Parallelize independent judge batches only through
   the environment's supported parallel dispatch mechanism.

## Every worker writes Markdown

Give each dispatch an explicit, unique output path under
`targets/<lang>/state/handoffs/<chapter-stem>/<round>/`. Never use the same file
as both input prompt and output. Never overwrite a prior round's result.

The parent records the input prompt path and SHA-256 with each dispatch. The
result is associated with that prompt, not just a reused batch number. After an
interruption, inspect saved files before retrying; an unknown tool outcome is
neither success nor proof that no write occurred.

- Translator: read the manuscript as a baseline, but write only a new
   `candidate.md` plus `translation.md` in the assigned handoff directory.
   Include scope, decisions, checks actually run and blockers. Never edit official
   manuscripts, shared context or state. The parent publishes via `single-writer.md`.
- Judge or auditor: write `judge-NN.md` or `audit-NN.md` with exactly one fenced
  `json` block containing the required array. Include every requested ID exactly
  once. Do not include translator reasoning, additional prose or manuscript edits.
- Chapter checker: write `chapter-checks.md` with checks performed, verified
  findings, source/target references and proposed corrections. Do not manufacture
  a clean result when a required check could not run.

Workers return a short message pointing to the saved file. The parent verifies
the artifact before relying on it. A missing artifact is an incomplete dispatch;
retry that dispatch or report the write-capability blocker.

## Markdown to controller JSON

The Markdown artifact is the durable worker result. The controller still expects
JSON; do not change its API or pass Markdown directly to `record-judgments`.

1. Read the current prompt and result from the recorded dispatch.
2. Require exactly one JSON fence and parse its contents using a JSON parser.
3. Require an array, exact ID-set equality with the dispatched passages, no
   duplicate IDs and valid error entries under the prompt's rubric.
4. Serialize the parsed value to the round's matching `.json` sidecar. Never
   synthesize an absent judgment, erase a negative finding or repair semantics
   during conversion. Ask the judge to correct an invalid result instead.
5. Register explicit sidecar paths for that round only. The controller reuses
   prompt filenames; globbing earlier `batch-*.json` files can mix old and new
   judgments. Keep older Markdown/JSON results as evidence, not current input.

## Resume and source layout

Validate candidates after worker writes, and manuscripts after parent publication.
If the worker lacks a terminal, the parent performs that validation. Executing
the existing controller is not a request to refactor Python or reconfigure its
environment.

An editor edit is not proof that a disk-based controller sees the new text.
Verify expected changed text on disk before generating prompts. If a worker's
editor buffer and disk disagree, report the mismatch and use a supported,
file-scoped save operation; never force-save every open document or overwrite
unrelated user edits. Do not claim validation of a buffer from an old disk copy.

On resume, verify the source paths recorded in the pipeline still exist. A
missing source or changed source corpus is a blocker, not permission to recreate
deleted files, silently include newly added chapters or reset the pipeline.
Preserve state and ask for the intended recovery when user changes prevent
continuation. Record any unjudged manuscript edits in a durable handoff.

PDF line wraps, form feeds and isolated drop capitals are not semantic
paragraphs. Before initializing a new corpus, inspect segmentation. Do not claim
byte-identical copies have normalized paragraphs. Preserve originals; any
normalization must be checked for omissions and recorded separately. Once a
pipeline is active, do not silently resegment sources or reset passage history.
Report a boundary that prevents a faithful scoped correction instead of forcing
bad prose to satisfy a line counter.

For an active line-fragment pipeline, snapshot each generated judge prompt into
the round directory before dispatch and append read-only bilingual context that
completes the sentences crossing its passage boundaries. Use the full source
and target chapter when sentence boundaries cannot be recovered reliably. Label
this material context-only: judge only the requested IDs, do not count normal
cross-line word-order changes as additions or omissions, and attribute a defect
to the passage containing the defective target wording, not its neighbor.
Include no translator rationale or proposed verdict. Hash this complete snapshot
as the dispatch input; the original generated prompt and passage IDs stay intact.