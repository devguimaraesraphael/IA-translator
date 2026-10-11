---
name: translate-fiction
description: |
  Translates loose text or a file (chapter, scene, excerpt) into a target language,
  preserving authorial voice, fixed terminology and register — using a single dense
  prompt (persona + style guide + glossary + untranslatable-element rules) for the
  translation itself, followed by a mandatory verification step (subtext/
  ambiguity, naturalness/calque, copyedit, cross-chapter continuity) that edits the
  result before it is considered done. Automatically discovers the glossary (project
  bible) and the style guide (author-voice notes) when available. Use when the user
  asks to "translate chapter", "translate this text into [language]", "translate
  this file", or "/translate-fiction".
---

# Skill: Translate

Translates fiction (loose text or a file) into a target language, preserving
authorial voice, fixed terminology and register. The process has two distinct steps:

1. **Translation** — a single dense prompt (persona + style guide + glossary +
   untranslatable-element rules): **specificity beats complexity** — a well-built prompt consistently
   outperforms a pipeline that asks for the same task again across several calls
   ("translate" → "refine" → "review" the same lexical choice repeatedly tends to
   produce only cosmetic adjustments).
2. **Verification** (mandatory, see its own section below) — a different class of
   problem, which the single prompt structurally does not catch: idiom calques,
   added emphasis, inconsistent formatting between chapters and character drift
   between chapters. These defects only become visible by rereading the target text
   in isolation (without the original beside it) or by comparing chapter with
   chapter — not by comparing the target text with the source sentence by sentence,
   which is what Step 1 already does. It is not the same anti-pattern as the
   "refine/review" pipeline mentioned above: it is a checklist of specific defects,
   not a second generic request to "improve the translation".

## How to use

```
/translate-fiction file=<path> language=<target-language> [glossary=<path>] [style-guide=<path>]
/translate-fiction text="<loose text>" language=<target-language>
```

**Examples:**
- `/translate-fiction file=manuscript/chapters/ch56.the_book_that_reads.md language=English`
- `/translate-fiction text="He slammed the door." language=Spanish`
- `/translate-fiction file=ch01.md language=French glossary=glossary-fr.md` — own glossary, skips automatic discovery

## Automatic context discovery (glossary and style guide)

Before assembling the translation prompt, check what already exists in the project —
do not ask the user to provide manually what is already available:

1. **Fixed-term glossary.** If a `bible/` folder exists in the project, read all the
   files in it (`bible/characters/*.md`, `bible/world/*.md`, `bible/factions/*.md`
   etc.) and extract proper names, world-system terms (magic, factions, unique
   objects) and titles — these **cannot vary** from translation to translation
   within the same project. Without this, "Crystal" may come out as "Cristal" in
   one chapter and "The Crystal" in another.
2. **Style guide with paired examples.** If `notes/author-voice.md` (or equivalent)
   exists, use the validated passages there as register calibration — abstract tone
   rules ("dark", "dense") work worse than a real excerpt annotated with what works.
3. **If neither exists** (loose text, outside a writing project, or the project's
   first translation): ask the user for a quick glossary of terms that cannot vary,
   and — if any passage of the same text has already been translated — ask for 1-2
   examples to calibrate register. Do not stall on this: if the user has nothing,
   proceed with the source text itself as the only voice reference.
4. Explicit `glossary=` / `style-guide=` parameters always take priority over
   automatic discovery.

## Step 1 — Translation (a single prompt, not a pipeline)

Assemble **a single dense prompt** with the blocks below, in this order (order
matters for prompt caching when the same session translates several chapters — see
"Multiple chapters" below). Do not split the translation itself into separate
"translate", "refine" and "review" calls — asking for the same
lexical choice again several times adds little value over a prompt well built from
the start. This does not remove Step 2 (verification), which is a different kind
of check — see below.

### Block 1 — Persona and register
Explicitly define the role and the type of text, do not leave it implicit:
> "You are a professional literary translator from [source] to [target]. The text is
> [genre] fiction in [narrative person], with [prose characteristics — e.g. dense,
> variable rhythm, subtext in dialogue]. It is not technical or journalistic text —
> do not simplify or neutralize the register."

### Block 2 — Style guide (paired examples, not abstract rules)
Include 2-4 real passages from the source text with an annotation of what works in
the original prose (from `notes/author-voice.md` when it exists), and — if any
earlier passage in the same target language already has an approved translation —
the full original→translation pair as direct calibration. A concrete pair corrects
the model more reliably than "preserve the dark tone".

### Block 3 — Fixed-term glossary
Explicit list: original term → fixed translation. Every proper name, world-system
term and title extracted from the project bible goes here. If a term has no
translation decided yet, mark it as `[TO DECIDE — suggest an option and keep it
consistent within this text]` instead of letting the model choose silently at each
occurrence.

### Block 4 — Explicit rules for untranslatables
Never leave implicit what to do with puns, alliteration, sentence rhythm, idiomatic
expressions or wordplay with no direct equivalent — the model's default behavior
tends toward surface semantic translation, losing exactly this kind of nuance.
Instruct explicitly, for example:
> "When there is no direct equivalent (pun, alliteration, idiomatic expression),
> prioritize effect over literalness — rebuild the same effect in the target
> language, even if the literal image changes. Flag each of these decisions in the
> notes list at the end; do not insert a note inside the text."

### Block 5 — The text to translate
The content of the `file=` or `text=` parameter, unedited.

## Step 2 — Mandatory verification (post-translation)

After producing the Step 1 draft, **before considering the chapter done**, edit the
translated text itself, fixing whatever the four steps below find. It is not
optional and it is not a second human invocation — it is part of the same skill
call. Record each correction made in a short log (see "Output").

### 2a. Subtext and intentional ambiguity
Reread the translated passage side by side with the source looking specifically for:
dialogue in which the original's subtext became explicit in the translation (the
"translated" character says what they feel, not what they would say); ambiguity the
author left open on purpose that the translation resolved into a single reading
without need. Where found, rewrite preserving the same openness/opacity as the
original — do not "fix" the ambiguity.

### 2b. Naturalness (calque and odd words)
Reread the translated text **in isolation, without opening the source** — as a
native reader of the target language who has never seen the original. Mark every
sentence that is grammatically correct but sounds "translated": idiom calques (e.g.
a source idiom rendered word for word as *"laughed in his beard"* is not natural
English; the right effect is something like *"he chuckled to himself"*), word
collocations a native would not use, sentence order that betrays the source
language's syntax. After marking, compare with the source only to confirm that the
fix did not lose meaning, and rewrite.

### 2c. Copyedit
Standardize within the chapter and — when other chapters are already translated into
the same language — across chapters: punctuation, dependent formatting (quotation
marks vs. italics for inner thought, for example — decide once and record the
convention in the chapter notes if it is not yet documented anywhere), capitalization
of glossary terms, form of dialogue dashes/quotation marks. Do not introduce an
intensifier, adverb or clarity that the source lacks (e.g. a source phrase
translated with an added "little" that does not exist in the original) — this is the
same kind of addition that Block 4 already prohibits within the translation, but it
goes unnoticed on the first pass and only shows up when rereading with this specific
focus.

### 2d. Cross-chapter continuity (in the target language)
When more than one chapter is already translated in the same work block, reread the
previous chapters **in the target language** (not the term glossary — a check of tone
and characterization) looking for adjectives or character traits that the
translation made inconsistent between chapters, even when the source originals are
consistent with each other. Translation can introduce a new inconsistency that does
not exist in the source; the fixed-term glossary (Block 3) does not cover this.

## Step 3 — Mechanical gates and evaluation

After Step 2, compare the output with the source by mechanical means: run the
`translation-gates` skill (paragraph parity, numbers, preserved passages, glossary).
Alerts are clues: read samples before fixing (see
`references/review-heuristics.md`). When a quality score is wanted, run
`translation-mqm`. When closing the chapter, record decisions and glossary (see
`references/memory-and-glossary.md`) for the next chapter.

## Recommended model parameters

- **Effort:** `high` or `xhigh` — literary translation is work of lexical choice and
  subtext preservation, not mechanical extraction; do not use `low`.
- **Thinking:** on (adaptive) — helps especially with verse, puns and passages with
  intentional ambiguity, letting the model "think" the choice through before
  committing the final prose.
- **One chapter/scene per call.** Even with a large context, translating by
  narrative unit gives more quality control than asking for the monolithic
  translation of an entire manuscript at once.

## Multiple chapters (prompt caching)

When translating several chapters in the same session, keep Blocks 1-4 (persona,
style guide, glossary, untranslatable-element rules) fixed as the prompt prefix and
vary only Block 5 (the chapter text). This prefix is cacheable — resending it
identically between calls reduces cost and ensures the same glossary is applied
without retyping for each chapter.

For step 2d (cross-chapter continuity) of Step 2, this means each new chapter must
be checked against **all** the chapters already translated in the block, not only
the previous one.

## Output

- **Translated text**, complete, with Step 2 already applied (not a pre-verification
  draft).
- **List of non-trivial decisions** at the end, separate from the text — rebuilt
  puns, terms with no direct equivalent, ambiguities resolved in a specific way.
  Never embed these notes inside the translation.
- **Step 2 correction log**, separate from the decisions above: what was corrected in
  each of the 4 steps (2a-2d) and why. If a step found nothing to correct, say so
  explicitly — do not omit the step.

## What this skill does not do

- **Does not use back-translation as an acceptance criterion.** Back-translation
  preserves surface semantics but often loses metaphorical
  structure, cultural intent and emotional nuance — it is an inadequate test of
  literary fidelity (it works better for technical terminology). If the user asks for
  back-translation as QA, warn about this limitation before proceeding.
- **Does not replace a native human reader of the target language reading without
  the original.** Step 2 (step 2b) is the automated approximation of that, but an LLM
  rereading its own text does not catch everything a human does — mainly subtle
  calques that sound natural enough not to trigger the check. The output of this
  skill remains material for bilingual human review before publication, only with one
  less step of manual work than before Step 2 existed.

## References

- To review voice/rhythm/show-don't-tell of the **original** before translating: use
  the project's chapter-review skill, if one exists — translating a chapter with
  unresolved voice problems propagates the problem into the target language.
- To consolidate/export after translation: `export-manuscript`.

## Reference files

| File | When to read | What it contains |
|---|---|---|
| `references/failure-modes.md` | When closing Step 2 or investigating a suspect chapter | Failure modes (Symptom → Cause → Fix → How to detect): skipped paragraphs or paragraphs in the source language, wrong variant, truncation, data that is not translated, glossary drift |
| `references/review-heuristics.md` | When interpreting Step 3 alerts | Reliable and unreliable automatic checks, and the "inspect before acting" rule |
| `references/memory-and-glossary.md` | When assembling Block 3 and when closing each chapter | Preserve/Translate glossary, matching order, warning vs. failure, passage role, per-chapter decision log |
