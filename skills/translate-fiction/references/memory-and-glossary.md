# Memory and glossary

Translating a book takes many calls. Anything not written to a file is lost between
them. This file defines how to store terms, decisions and the role of each passage.

## Glossary with a per-term policy

Each entry has: source term, intended sense, policy, translation (when there is
one) and any necessary exception. Reserve entries for domain concepts, recurring
ambiguities and explicit naming decisions. Ordinary vocabulary, idioms and routine
exonyms do not need individual entries or decision notes.

| Policy | Meaning | Examples |
|---|---|---|
| **Preserve** | Stays as is under the project's explicit policy. | Real personal names, original work titles, intentional embedded language. |
| **Translate** | Uses the agreed equivalent for the specified sense. | Domain concepts, world terms, meaningful descriptive names. |

Use established target-language geographic exonyms and natural descriptive names
unless an explicit project convention says otherwise. "Proper noun" alone is not
a Preserve rule. Resolve contradictory naming conventions before dispatch.
Only genuinely unresolved recurring terms need a pending entry in the decision
ledger, never a marker in the manuscript. Settle routine choices without asking
for approval or generating synonym alternatives.

### How to match

1. By **word boundary**, never by substring (the term "Ana" does not match "banana").
2. **Longest term first**, so that "Old House" is matched before "House".
3. **Case-sensitive only when necessary** (proper name vs. homographic common word);
   otherwise, ignore case.
4. Mark the passage already matched, so that a short term does not match inside a
   long one.
5. Confirm the intended sense in context. A technical entry for "sequence" does
   not prohibit ordinary uses of "sequencia" or equivalent target vocabulary.

### What warns and what fails

| Situation | Effect |
|---|---|
| Translate term missing from the output or in a different form | **Warning.** Inflection, ellipsis and pronouns produce false positives. Read before fixing. |
| Preserve term altered or translated | **Strong warning**, to be read; fails if the passage is data (phrase in another language, name). |
| Number changed relative to the source | **Fails.** |
| Replacement rule with zero matches | **Warning**, never silence. |

Terminology only warns because the mechanical check does not understand inflection;
a changed number fails because it is an objective error.

## Data that is not translated

Explicit Preserve spans are data, not prose. Keep those spans and supply the same
items to the untranslated-text check (see item 4 of `failure-modes.md`). Names and
labels outside that policy still follow the naming rules above.

## Role of the passage

Tell the translator the role of each passage: chapter title, dialogue, epigraph, song
or verse, letter, narration. The role guides register and punctuation; it **does not
impose a length limit**: a title may grow, a verse may be rebuilt.

## Decision log per chapter

At the end of each chapter, append only new decisions that later chapters need;
do not repeat unchanged context or explain routine lexical choices:

- New terms and the policy chosen (Preserve/Translate).
- Fixed conventions (quotation marks, dashes, inner thought, language variant).
- Solutions for puns and untranslatables, with a short justification.
- Points for human review.

The decisions file and the updated glossary become part of the cacheable prefix
(Blocks 1-4) of the next chapter. In long chapters, save a resume point (last intact
paragraph) so that an interruption does not lose decisions already made.

## Reusing repeated passages

When the source repeats an identical passage (refrain, formula, recurring header),
reuse the translation already approved instead of generating another. Identify the
repetition by exact comparison of the normalized text (whitespace and case) and
record the approved pair next to the glossary.
