# Parallel chapter batches

1. Schedule up to four independent chapters per batch. Keep each chapter's
   translate, validate, judge, correct, chapter-check and audit dependencies in
   order, but do not wait for another chapter to finish before dispatching ready
   work. Use the runtime's parallel tool wrapper, not nested worker delegation.
2. Freeze the shared glossary, conventions and style guide into an immutable
   batch context. Each compact chapter context is derived from that same revision
   and records its selected entries and source hashes; include recurring entities
   relevant to the batch, not just exact glossary string matches. Before
   the first chapter verifies, mark the anchors provisional; reconcile the batch
   against the verified anchors afterwards. Workers write only their assigned
   immutable candidate and unique Markdown handoffs. They propose glossary changes in their
   handoffs; only the parent merges shared context.
3. Inspect source segmentation before creating passage state. PDF line wraps are
   not paragraphs. For unstarted chapters only, preserve the original bytes in
   an immutable copy, prepare complete paragraphs with one paragraph per line,
   and record source line spans. Check that ordered non-whitespace characters
   are identical; additionally review headings, lists, quotes and paragraph
   boundaries. This mechanical check detects content changes but does not prove
   correct segmentation. Do not repair OCR wording during preparation. Do not
   change an active chapter's segmentation or reset its judgment history. An
   existing active chapter uses bilingual context until it completes.
4. The parent is the sole controller writer. Run controller commands serially,
   including across chapters: they share the pipeline budget and configuration.
   If input preparation is required, complete and validate it before the first
   `next` for that chapter. Obtain each translate action before dispatching its
   translation worker. Never let workers run controller commands.
5. Translate ready chapters in parallel with the selected translator. Immediately
   validate candidates and publish via `single-writer.md` before judging. Follow
   `consolidated-review.md` with one fresh independent judge per chapter when
   it fits, using complete semantic passages and read-only bilingual context.
   Do not alter active passage IDs merely to reduce dispatch count.
6. Before closing any chapter in the batch, reconcile terminology, voice and
   explicit conventions across the available full chapter reviews and source/target
   occurrences. Run this alongside independent full reviews once drafts exist.
   Distinguish stable full names from valid generic descriptions and source-side
   variants. Record inherited differences outside the requested scope without
   silently reopening earlier chapters. Adjudicate findings against evidence and
   the frozen policies, preserving original verdicts. Hold chapters at the
   chapter-check boundary until this batch reconciliation is recorded.
   Collect all confirmed defects for a chapter into one correction dispatch per
   controller round. Preserve best-of tracking, thresholds, full coverage, audit
   fraction and attempt caps. Stylistic alternatives without a concrete defect
   are not errors. Use the existing bounded reconsideration for demonstrable
   false positives; do not approve them manually or retry until a favorable vote.
7. After grouped corrections and independent delta review, record current clean
   chapter checks, then run the required audit and finalize each chapter. Recheck
   changed recurring terms against the batch's occurrence evidence; no second full
   review is needed for untouched text. Run whole-work consistency at the end. Any
   changed manuscript re-enters controller validation. A chapter blocked by a
   local issue does not prevent other independent ready chapters from progressing;
   global budget stops still stop the run.
   This ordering is an orchestration requirement: the controller may return an
   audit/finalize action before cross-chapter reconciliation is complete. Do not
   execute it prematurely or change controller budgets to bypass a blocked chapter.
8. Keep execution focused on translation. Record tool improvements for a separate
   maintenance pass unless they block correctness. Report elapsed time and real
   chapter states when available, not projected speedups or promises of background
   execution. A completed draft is not a verified chapter.