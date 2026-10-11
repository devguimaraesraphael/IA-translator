---
name: review-writing-tics
description: |
  Detects and fixes language tics and repeated structures in fiction prose: words, gesture verbs,
  connectives, looks and speech formulas that recur out of writing reflex instead of deliberate
  choice (intentional motif or echo). Separates functional repetition (anchor symbol, refrain,
  callback, world rule) from accidental repetition before suggesting any cut. Use PROACTIVELY
  after a chapter has been written and reviewed, or when the user asks to "find language tics",
  "find repeated words", "spot a writing crutch", "diversify vocabulary", "review structural
  repetition", "/review-writing-tics", or asks whether the text has "tics or repeated structures".
---

# Skill: Review Writing Tics

Scans a chapter (or a block of chapters) counting the frequency of words, gesture verbs,
connectives and speech formulas, and proposes varied rewrites without losing the original meaning
or breaking the project's authorial voice.

Unlike a general chapter-review skill (voice, rhythm and show-don't-tell as broad, qualitative
categories), this skill is **quantitative and lexical**: it counts how many times each word or
gesture recurs across the whole text. This kind of problem only shows when reading the chapter in
one pass, not sentence by sentence, so it deserves its own dedicated pass.

The catalog's example words are English. For a text in another language, swap them for that
language's equivalents of each category (see the note at the top of the catalog).

## When to use

- After the chapter's voice and rhythm have been adjusted: tics are easier to count in stable
  prose, and counting repetitions in a draft that will still change is wasted work
- When the author feels "this text tastes repetitive" but cannot point to where
- Before treating a chapter as ready for consolidation or export
- On blocks of chapters (not just one), to catch tics that cross chapters and go unnoticed in an
  isolated read

## How to use

```
/review-writing-tics chapter=<number> [category=connective|gesture-verb|contact-verb|gesture-noun|adverb|closing-formula|sentence-opening|hypothetical-comparison|all]
/review-writing-tics chapters=<range>
```

**Examples:**
- `/review-writing-tics chapter=55`: full scan of chapter 55
- `/review-writing-tics chapter=55 category=gesture-verb`: only physical-gesture verbs (grip,
  clutch, grab...)
- `/review-writing-tics chapters=50-55`: scan a block to catch tics that cross chapters

## Prerequisites

- The chapter text already in near-final prose (a very unstable draft yields false positives: a
  repetition in a passage that will be rewritten is not worth cataloguing)
- The project's author-voice guide (`notes/author-voice.md`), so an established motif (a symbolic
  object, a world rule that demands the same gesture) is not mistaken for an accidental tic
- The story bible (`bible/`), when the repetition involves a specific item or rule (e.g. a pendant
  that "warms when the character decides something": a squeeze gesture may be a world rule, not a
  tic)

## Process

### 1. Frequency count (mechanical, before judging)
For each category in "Categories covered", count by **lemma** (group conjugations and inflections:
"gripped/grips/gripping" count together), not only the exact form. Separate narration from
dialogue: character speech has its own rules (catalog section C). Apply the thresholds in
`references/tics-catalog.md` section B.

### 2. Intentionality test (before suggesting any cut)
For each word or structure above its threshold, apply the test in `references/tics-catalog.md`
section C before reporting it as a tic. Repetition that **evolves**, is **anchored by an
established world rule**, or works as a **deliberate rhetorical echo** (refrain, callback, a
character's signature line) is not a tic: it is a motif. Report only static, functionless
repetition.

### 3. Rewrite with variation
For each occurrence confirmed as a tic, propose a rewrite following the recipes in
`references/tics-catalog.md` section D:
- Do not invent an action or gesture that was not implied in the original: vary the word, not the
  event.
- Do not introduce a new tic in place of the old one (replacing every "gripped" with "grabbed"
  only moves the problem: vary for real, do not substitute 1:1).
- When it makes sense, prefer removing the connective or verb over swapping it for a synonym: a
  cut is usually stronger than a substitution (e.g. split the sentence in two instead of using
  "but" again).

## Categories covered

1. **Contrast connectives** (but, yet, however, still) in narration, used as a reflex at every
   emotional or physical turn until the turn loses impact through predictability.
2. **Gesture verbs** (grip, clutch, grab, touch, pull): the same physical gesture returning as the
   default reflex for tension, affection or control.
3. **Eye-contact or default speech verbs** (stare, gaze, say): the stock verb for every exchange
   of looks or every speech attribution.
4. **Repeated gesture nouns** (raised chin, clenched fist, set jaw): the same body detail used
   several times to convey the same emotional state.
5. **Redundant manner adverbs** (slowly, quickly, quietly): they reinforce an idea already in the
   verb, or repeat the same adverb in close proximity for different characters or events.
6. **Closing formulas for speech or paragraphs** ("he said at last"; "and smiled"; "without
   another word"): the same sentence tail closing different scenes or lines, draining the weight
   of each.
7. **Fixed sentence or paragraph openings** (always "Name + verb", the same syntactic
   construction opening consecutive paragraphs).
8. **Hypothetical comparative structures** ("as if", "as though", "like"): used as a stock crutch
   for any gesture or reaction, even when the narrator already knows the real cause (the test
   differs from the other categories: see catalog section B.8).

## Review output

Report by **cluster** (all occurrences of the same word or structure together), never by isolated
line: the problem is the repetition, not the individual occurrence.

```
TIC: <word/structure, e.g. "grip (gesture verb)">
OCCURRENCES: <N> in <M> words, lines <list>
CLASSIFICATION: accidental tic | intentional motif (justify) | borderline (justify the doubt)
ORIGINAL (each occurrence confirmed as a tic): "..."
SUGGESTION: "..."
REASON: <why this specific variation, and why it does not introduce a new tic>
```

Close with an objective summary: how many tics were confirmed and rewritten, how many stayed as
"intentional motif, kept" (with a short justification), and a self-check: does any suggested
substitution recur as often as the original tic?

## What NOT to do

- Do not suggest variation just for variety: if the repetition is a motif (catalog section C),
  leave it intact and say why. Not every repetition is a tic.
- Do not swap one tic verb for another that becomes the new tic: before closing the review, check
  that the replacement word was not already used in the other fixes of the same pass.
- Do not apply the same repetition standard to dialogue and narration. Repeated speech can be a
  character's voice trait (verbal habit, rhetorical insistence), not a narrator tic: report
  dialogue repetition only if it seems neither deliberate nor consistent with the speaker.
- Do not review general authorial voice, sentence rhythm, show-don't-tell, semantic field or scene
  structure here: that belongs to the project's chapter-review and scene-editing skills, if they
  exist. This skill covers only countable lexical and structural repetition.
- Do not fix a chapter that is still an unstable draft: wait for the prose to settle so
  everything is not recounted on the next pass.

## References

| File | When to read | What it contains |
|---|---|---|
| `references/tics-catalog.md` | Steps 1-3 of the process | Categories, thresholds, examples, intentionality test, rewrite recipes, common mistakes and reference metrics |

Related skills in this repo:
- `check-consistency`: for repetition that crosses multiple chapters, run this skill with
  `chapters=<range>` and cross-check with its narrative-style dimension.
- `create-style-guide`: to learn whether a repetition is an established motif of the project's
  voice (and must not be cut), see its "Distinctive Elements" section.
