# Consolidated, risk-based review

1. Before dispatch, distinguish real personal names and original titles from
   geographic exonyms, descriptive fictional names and meaningful joke labels.
   Record concrete Preserve/Translate examples in shared conventions instead of
   "preserve all proper nouns". Reconcile previously affected chapters.
2. One translator produces the chapter and performs translate-fiction Step 2.
   One independent judge per chapter covers all controller passage IDs, factual
   fidelity, conventions, voice and relevant repetition checks. Combine prompt
   batches without duplicating shared context. Split only for actual context or
   output limits, at semantic boundaries, with documented coverage.
   State genre and audience in dispatch: instructional prose needs accurate,
   natural explanation; literary depth is for actual subtext, wordplay and voice.
   Respect selected models and effort. Require full coverage, not an error quota.
   Include the impact filter below in both judge and chapter-check instructions;
   do not rely on workers discovering it independently.
3. Save `judge.md` containing one JSON fence with all requested IDs and c/s/n
   errors. Also save `chapter-checks.md` with source/target/context hashes,
   coverage and issue IDs. Both artifacts may come from that single review.
   Register only this dispatch's validated JSON. Missing judgments are not clean.
4. Use three outcomes, not an open-ended request to improve the prose:
   **material defect**: source/target evidence demonstrates lost meaning, a wrong
   instruction, a plausible misunderstanding or genuine unnaturalness; fix and
   recheck. **objective copyedit**: spelling, agreement, punctuation or an applicable
   naming convention needs correction; group it with other confirmed fixes and
   recheck affected IDs. **acceptable variant**: correct and natural, even if a
   reviewer prefers another synonym; retain it without a correction call.
   Explain each error briefly in the existing c/s/n note, with wording and impact.
   Do not create new JSON fields, inflate severity for a policy mismatch, or ignore
   legitimate minor errors. Source-supported nuance and exercise constraints count.
   Repetition alone and ordinary uses of glossary words are not violations. A
   contextually adequate pronoun is not wrong merely because a noun is more explicit.
   Record conflicting editorial policies separately and resolve them once before
   more dispatches. Preserve existing negative verdicts; use bounded reconsideration
   only for demonstrated false positives, never repeated voting until approval.
5. Merge individual-review and batch-reconciliation findings before dispatching
   corrections. Group confirmed fixes into one candidate per chapter per round.
   Use the exact-replacement path in `efficient-dispatch.md` for fully adjudicated
   mechanical changes; otherwise use the selected translator. Rejudge only
   changed IDs with adjacent context. Missing sections, systematic errors,
   resegmentation or broad rewrites require a new full review. Keep thresholds,
   full coverage and attempt caps unchanged.
   No standalone call for each accent, familiar exonym or synonym. A confirmed
   isolated error still gets fixed; batching is not permission to leave it behind.
   No generic polish after a clean review. Handoffs retain candidate/hash, scope,
   check status and exceptional decisions, without per-paragraph narration.
6. At `chapter_checks`, reuse a full-review artifact only when hashes match.
   After correction, record delta coverage and the final manuscript hash; verify
   every known issue against persisted text, especially after restoration.
   Record corrections performed during a check with their actual count. If
   corrections were already published and independently rechecked before this
   handler, record zero for the final clean check and retain the earlier fix
   count in its note and issue ledger. Never claim an unperformed check or use
   zero while known issues remain in the checked version.
7. Reconcile terminology and voice before final clean chapter checks and audits,
   not after chapters have been finalized. Keep the separate fresh-context
   seeded 10% audit and whole-work final consistency check. Do not add another
   full review for reassurance after the required gates pass.
8. Record actual elapsed time, review/delta counts, confirmed issues, rejected
   preferences, reversions and audit escapes when measurable. Do not reconstruct
   unknown timing or present a numerical score gain as proof of quality. Compare
   time per chapter and fixes surviving audit before claiming improvement.
   Capture worker start/end when available; dispatch preparation is not execution
   time and file modification time is not completion time. Record token/cost data
   only if provided by the runtime. Prompt bytes are not tokens or elapsed time.
   Use paired stage/dispatch markers and distinguish parallel wall time from summed
   worker duration; interrupted or unpaired markers cannot establish execution time.