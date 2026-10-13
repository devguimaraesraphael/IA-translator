# MQM rubric for translation

Deliberately short list: long lists lead the judge to category-shopping (stacking labels on the same problem). One problem, one category.

## Defect test (before scoring)

Evaluate fidelity throughout the assigned text, using its actual genre and audience.
Act as a verifier, not a second translator. Keep correct, natural variants unchanged.
Before reporting an error, identify the source/target wording and the concrete
defect: changed meaning, lost information, incorrect language, demonstrably
unnatural phrasing, or a broken applicable convention. Include that evidence and
impact concisely in the existing note field; do not add output fields.

- A preferable synonym, closer literal wording or an alternative interpretation
	that readers are unlikely to make is not sufficient evidence of error.
- Repetition alone is not a defect. Show the actual disruption, not a frequency.
- Apply glossary entries to their defined sense. An ordinary use of a word is not
	automatically a collision with its technical meaning. Allow grammatical inflection.
- Implicit grammatical information and idiomatic reformulation are not omissions
	unless a relevant distinction is actually lost in context.
- Preserve source-supported nuance when it matters to the fact, instruction,
	argument, voice or intended effect. Do not ignore real defects merely to save work.
- Objective spelling, agreement and punctuation errors remain reportable even
	when the sentence is understandable. Group duplicates; do not inflate severity.
- Do not invent an error quota or explain clean lexical choices. If no concrete
	defect is established, return an empty error list for that passage.

## Categories

| Category | Question |
|---|---|
| `accuracy/mistranslation` | Did the meaning change relative to the source? |
| `accuracy/omission` | Did anything from the source disappear? |
| `accuracy/addition` | Is there content the source does not have? |
| `accuracy/untranslated` | Is there leftover source-language text that should have been translated? (embedded language kept on purpose does not count) |
| `fluency/grammar` | Grammar, agreement, spelling or punctuation error? |
| `fluency/calque` | Correct sentence, but reads like a literal translation? |
| `fluency/register` | Formality, dialect or tone does not fit the speaker or the scene? |
| `terminology/glossary` | Contradicts the project glossary or wavers between passages? |
| `style/voice` | Was the narrator's or character's voice flattened or swapped? |
| `style/subtext` | Did the implicit become explicit, or was a deliberate ambiguity resolved? |
| `typography/convention` | Quotation marks, dashes, italics or the target editorial convention broken? |

## Severities (weight)

- **minor (1):** a demonstrable local defect while the passage remains usable, such as a spelling error, missing required article or clearly unnatural collocation. Mere repetition or a less-preferred synonym does not qualify.
- **major (5):** substantially changes meaning, breaks an important voice/effect or seriously impedes comprehension. E.g. "she didn't say a word" rendered as "she said a word"; a dry character turned warm; a joke that stops working. An untranslated familiar place name or a capitalization mismatch is not automatically major; assess its actual impact.
- **critical (10):** reverses or destroys a central meaning, loses a fact the plot uses, or leaves the passage unusable. E.g. a lost negation that swaps who did what; a reveal rendered so the reader understands the opposite.

When unsure between two severities, pick the lower one and give the reason in the note.

## Score

`100 - (sum of penalties ÷ evaluated target words) × 100`, floored at 0. Only evaluated passages enter the divisor.

## Guidance for the judge (against bias)

- Do not reward what "sounds beautiful" if the meaning changed; always compare with the source.
- Do not punish a deliberate choice recorded in `decisions/` or in the glossary (embedded language kept, adapted term, target punctuation). If the choice is not recorded and breaks the meaning, it is an error.
- Do not punish a structural difference that preserves meaning, voice and rhythm.
- Do not invent errors to "justify" the evaluation: a clean passage has an empty list.
- Do not stack categories on the same problem; choose the one that best describes the cause.
- A source ambiguity resolved without need is `style/subtext`, not `accuracy/mistranslation`.
- Answer only with the requested JSON, covering every id; omitting a passage excludes it from the score.
