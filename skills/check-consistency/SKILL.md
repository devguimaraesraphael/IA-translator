---
name: check-consistency
description: |
  Checks for contradictions in character, world, timeline and style across multiple
  chapters of a fiction manuscript. Use PROACTIVELY before exporting a manuscript, when closing
  an arc or block of chapters, or when the user asks to "check consistency",
  "find contradictions", "validate the timeline", or "review continuity". Slash
  form: `/check-consistency`.
---

# Skill: Check Consistency

Scans a range of chapters for plot, character, world and style contradictions —
comparing against the project's bible and against each other.

## How to use

```
/check-consistency chapters=<range> [dimension=timeline|character|world|factual|style|all] [incremental=true]
```

**Examples:**
- `/check-consistency chapters=1-8` — full check of the first 8 chapters
- `/check-consistency chapters=23 dimension=character` — character inconsistencies in chapter 23
- `/check-consistency chapters=1-55 dimension=timeline` — the complete timeline
- `/check-consistency chapters=54-56 incremental=true` — only compares the new/changed chapters against the previous report, not the whole manuscript

**Respect the requested range.** When the author asks for a specific `chapters=<range>`, restrict
both the reading and the conclusions to that range — even if reports/data from chapters
outside it are available. Using information from outside the range contaminates the diagnosis with
payoffs or developments that only become clear later, and the author loses the reading of what that
block delivers on its own. If a thread is only resolved outside the range, it is fine to note that
it "remains open as of this point" — but do not use the content of the resolving chapter to judge the
requested range. Obvious exception: when the request explicitly asks for a view of the whole book or a
comparison between blocks (`chapters=1-55`, for example).

## Verification Dimensions

### 1. Timeline / Plot
- Does the sequence of events match across chapters?
- Is diegetic time (hours/days) consistent?
- Do narrative promises (setups) have payoffs in the right chapters?

### 2. Character
- Are motivations consistent with the profile in the bible?
- Does the emotional arc progress without unjustified regression?
- Character knowledge: does the character know only what they could know up to that point?
- Are physical descriptions consistent?

### 3. World / World-building
- Are the rules of the magic/technological/social system respected?
- Geography: are distances and places coherent?
- Do factions/groups behave consistently?
- Are details established once not contradicted later?

### 4. Factual
A dimension of its own (previously treated as a sub-case of "world", now explicit) for
concrete, verifiable — not interpretive — contradictions: an object that changes
place without explanation, a character who knows something the scene did not show, a date
that does not add up arithmetically. Practical difference from the other dimensions:
here the contradiction is binary (it matches or it does not), not a matter of tone or nuance.

### 5. Narrative Style
- Unjustified shifts in voice?
- Abrupt deviations in tone?
- Narrator inconsistency (internal vs. external)?
- A writing tic that runs through several chapters (the same word/gesture/closing formula
  reappearing chapter after chapter without a function)? A single occurrence per chapter can go
  unnoticed in a chapter-by-chapter review — delegate the counting and the intentionality test
  to `review-writing-tics chapters=<range>` instead of estimating by eye.

### 6. Genre Conventions (Obligatory Scenes & Conventions)
Applies mainly to action/combat chapters (battles, duels, fights).
Check whether the chapter fulfills the obligatory scenes expected of the Story Grid
Action genre when the scene sets out to be an action scene:
- [ ] The hero faces a clearly more powerful antagonistic force (Villain/Monster).
- [ ] There is a "hero at the mercy of the villain" moment (the hero loses the advantage before regaining it).
- [ ] The scene's climax resolves the confrontation through direct physical action, not exposition.
- [ ] The cost of victory (wound, loss, debt) is shown, not dismissed.
If the chapter does not set out to be an action scene, skip this dimension.

## Evidence Step (before reporting)

Before listing an inconsistency, build the chain of evidence: passage A (with
chapter/location), passage B (with chapter/location) and the exact reason for the
contradiction between the two. Do not report an inconsistency without both passages
quoted — "seems contradictory" without a quote is not an inconsistency, it is a
suspicion; in that case, mark it as "to verify" instead of reporting it as a finding.

## Incremental Mode

With `incremental=true`, do not repeat the full scan of the manuscript: read the
most recent previous report in `analysis/consistency/inconsistencies.md`,
identify which chapters in the requested range are new or have changed since the
last scan (compare against `state/current/progress.md`), and check only
those chapters against the bible and against neighboring chapters — not against the whole
manuscript. Append the new findings to the existing report instead of rewriting it
from scratch; keep the old findings intact unless the chapter that originated them
has been rewritten.

## Output

```
INCONSISTENCY #<N>
Dimension: <type>
Chapters involved: ch<A> × ch<B>
Evidence A: "<quoted passage>" (ch<A>)
Evidence B: "<quoted passage>" (ch<B>)
Description: <what contradicts what>
Severity: low | medium | high
Suggested fix: <how to resolve>
```

If no inconsistency is found: confirm which facts were verified.

## Translation mode (source × target)

When the project is a translation (`translation/targets/<locale>/` exists), the question changes:
does the target text contradict the source or itself? Use `chapters=<range>` over the files in
`manuscript/` and compare against the same-named file in the source.

1. First run the `translation-gates` skill; an open GATE (missing paragraph, altered
   number) is a certain finding and needs no reading. Treat the WARNINGS as leads.
2. Dimensions in this mode, all with the chain of evidence (source passage + target passage):
   - **Fact:** a name, number, date, place or object that changed in translation.
   - **Term:** the same fixed term translated in different ways across chapters, or outside
     the target's `glossary.md` (inflection does not count as variation).
   - **Voice and characterization:** adjectives or character traits that the translation made
     inconsistent across chapters, even when the source is consistent.
   - **Convention:** quotation marks, dashes, treatment of embedded language and italics
     diverging from `editorial-conventions.md`.
3. There is no bible here: the reference is the target's glossary and decisions
   (`glossary.md`, `decisions/<file>.md`). A deliberate choice recorded in `decisions/`
   is not an inconsistency.

## What NOT to Do

- Do not fix the text automatically — only report. Fixes are up to the author
  or the project's chapter-review skill, on demand.

## References

- Order of calls within the full workflow: see the project's writing workflow, if one exists
- Run before `export-manuscript`
- For writing tics that run through several chapters (item 5 above): `review-writing-tics`
