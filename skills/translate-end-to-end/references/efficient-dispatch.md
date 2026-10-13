# Efficient dispatch without reduced coverage

## Compact context

Freeze the complete shared policies once per batch. Build each dispatch from the
complete rubric, genre/audience, all applicable conventions, relevant glossary
entries (including inflections and ordinary/technical sense distinctions), recurring
entities and at most two useful paired style examples. Store the selected entries,
selection reason and upstream hashes. A filename reference alone does not put its
contents in a worker's context. When relevance is uncertain, retain the entry.

For a delta, include complete changed passage pairs, adjacent bilingual context
needed to understand them, the applicable policy subset and known issue IDs.
Reference the immutable full-review baseline for coverage bookkeeping; do not
claim a fresh full review. Never remove source/target passages, required rules or
an unresolved exception just to meet a token target. Reviewers must not receive
translator reasoning or other judges' verdicts except the explicit correction
issues needed for a delta check. Keep a separate independent audit.

## Grouped corrections and exact replacements

Wait for both chapter review and batch reconciliation, then adjudicate the union
of findings once. Fix actual meaning/naturalness defects and explicit convention
violations; retain correct variants and ordinary generic references. A majority
spelling is evidence of local consistency, not proof of a published translation.

No translator call is needed when every requested edit has an already approved,
unambiguous exact replacement, such as a title apostrophe or a fixed name at known
occurrences. The parent may run a deterministic transformation with this contract:

1. Freeze source, baseline target and context hashes before transformation.
2. Record issue ID, zero-based nonempty block index (including headings), exact
   before/after strings and expected occurrence count per replacement.
3. Require the baseline hash and counts to match. Reject overlapping/cascading
   replacements, zero matches and out-of-scope changes; never use a global blind
   search-and-replace. Create a new immutable complete candidate and short handoff.
4. Validate parity, candidate hash and unchanged blocks, then use
   `publish_candidate.py` with the frozen spec and allowed blocks. Run controller
   `next` immediately, then independently judge changed IDs even for punctuation.

If meaning, register, inflection or the intended replacement is still undecided,
use the selected translator. In a mixed semantic/mechanical correction, send one
grouped request rather than two calls. Never reinterpret a negative review as
clean merely because a script performed the edit.

## Consolidated local validation

Use one reusable, file-scoped validation command per publication/review stage
instead of repeated ad hoc shell snippets. Resolve absolute paths once and
enumerate only the requested Markdown files, excluding locks and handoffs.
Validate persisted bytes, source/target/context hashes, exact judgment ID sets,
schema, parity, changed blocks and known issue resolutions. Fail closed before
registering a stale or malformed result. Keep controller writes serial even
when read-only checks run together. Do not force-save unrelated editor buffers.

After a later scoped correction, an earlier audit can be reused only when all
selected audited passage texts are proven unchanged against its frozen baseline
and the controller does not require a new audit. The current sample file may
contain only delta IDs; it is not a full historical audit record. Changed audit
passages need fresh independent audit evidence before finalization.

## Measurements

Record immutable paired start/end markers for preparation, dispatch, publication,
review, reconciliation, correction, delta, audit and final validation. Give each
worker and parallel wave distinct IDs. Keep UTC timestamps plus monotonic elapsed
time where supported; write end markers on completion/error, not from file mtimes.
Record interruption/resume events without overwriting earlier markers. Missing or
cross-interruption intervals are unknown execution time, not zero.

Report elapsed batch wall time separately from summed worker durations, local
validation time, retries and orchestration. Count translation, semantic correction,
mechanical transformation, review, delta and audit calls separately. Record prompt
bytes and output bytes as sizes only. Record input/output/cached tokens and cost
only when the runtime supplies them, with model, pricing source/date and currency
for any cost calculation; otherwise mark unavailable, never estimate from bytes.

Compare only matched workloads, models, effort and concurrency when claiming a
gain. Reduced calls or shorter prompts are useful observations, not demonstrated
cost or latency savings. Keep full fidelity coverage, thresholds, attempt history,
independent audits and human-review caveats unchanged.