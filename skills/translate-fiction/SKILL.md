---
name: translate-fiction
description: |
  Translates fiction or instructional nonfiction into a target language, preserving
  meaning, voice and domain terminology with one translation call and proportional
  self-checks. Keeps correct natural variants, avoids cosmetic rewriting and loads
  literary guidance only for genuinely difficult passages. Discovers existing
  glossaries and style examples. Use when the user
  asks to "translate chapter", "translate this text into [language]", "translate
  this file", or "/translate-fiction".
---

1. **Resolve input and execution.** Accept `file=<path>` or `text="<text>"`,
  `language=<target-language>`, and optional `glossary=` / `style-guide=`.
  Explicit paths take precedence. Respect the selected model and effort; default
  to medium, never raise effort automatically. Under translate-end-to-end, inherit
  its model selection, immutable source, candidate path and publication contract.
  Do not overwrite the source or publish the orchestrator's target from a worker.

2. **Identify genre and audience.** For instructional nonfiction, prioritize faithful
  explanations, terminology, examples, logical relations and natural target prose.
  Do not invent literary difficulty in ordinary exposition. For fiction, preserve
  narrator/character voice, intentional ambiguity and emotional effect. Mixed
  texts keep the appropriate register for quoted scenes and explanatory passages.

3. **Load bounded context.** Read the complete assigned source, target glossary,
  conventions and 2-4 available verified style pairs. Do not claim human approval
  unless recorded. Use the existing context index to load only relevant bible
  entries; do not reread the whole bible or all earlier chapters by default.
  Retrieve earlier passages when a recurring voice, callback, term or ambiguity
  needs checking; widen that read when evidence is missing or inconsistent.
  With no context, proceed from the source and record genuine unresolved risks.

4. **Translate once (Step 1).** Use one prompt with five ordered blocks:
  (1) genre, audience and register; (2) style pairs; (3) scoped glossary;
  (4) explicit exceptions and real untranslatable effects; (5) unchanged source.
  Keep stable context first for possible cache reuse, without claiming a cache hit.
  Ordinary idioms, exonyms and synonyms need a natural choice, not alternatives
  or a decision essay. Read memory-and-glossary when a persistent term decision
  is needed. Fixed terms cover domain concepts, recurring ambiguity and explicit
  exceptions, not every word. Do not insert undecided-term markers into prose.

5. **Verify and correct in the same call (Step 2).** Cover the entire assigned
  source/target for facts, omissions, additions, negation, intensity, conditions,
  causality, examples and explicit exercise constraints. Perform 2a: preserve
  subtext/ambiguity where present; 2b: read the target alone for actual calques
  and register defects; 2c: copyedit grammar, agreement, spelling and conventions;
  2d: check continuity using verified context and targeted prior passages.
  Scope the depth, not fidelity coverage. Keep correct, natural wording unchanged.
  A less literal equivalent or repeated word is not itself a defect. Rebuild real
  wordplay for its effect without changing facts or explaining implicit meaning.
  Group confirmed corrections; do not launch separate polishing or synonym calls.

6. **Check structure and hand off.** Run required mechanical gates and inspect
  alerts before fixing; read failure-modes or review-heuristics for relevant
  anomalies. Keep source paragraph/heading alignment when required by the
  orchestrator. Independent judgment, coverage, scores, bounded correction loops
  and audit remain the orchestrator's responsibility and must not be bypassed.
  Self-checks and back-translation are not substitutes for independent review;
  neither is a guarantee of human publication-level approval.

7. **Save concise results and stop.** Deliver the complete translation and a
  Markdown handoff with candidate path/hash, scope, 2a-2d check status and gate
  results. Summarize grouped corrections once. Record only decisions that future
  chapters need, genuinely difficult effects and unresolved issues, outside prose.
  No per-paragraph commentary, routine synonym rationale or empty decision lists.
  A clean check needs one short status, not an essay. Preserve traceability and
  do not mark unperformed checks as passed. Stop after the required checks pass.

| Reference | When to read | Contents |
|---|---|---|
| `references/memory-and-glossary.md` | Defining a persistent term or updating shared context | Sense-scoped terminology, naming policy and durable decisions |
| `references/review-heuristics.md` | Interpreting mechanical or stylistic alerts | Evidence before correction; reliable and unreliable signals |
| `references/failure-modes.md` | Investigating a specific gate failure or suspect passage | Symptoms, causes and focused repairs |
