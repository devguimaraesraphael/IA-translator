# Automatic review heuristics for literary text

Core rule: **inspect before acting.** An alert is a question, not a sentence. Never
delete or retranslate in bulk because of an alert; read a sample of the flagged
passages and decide. A heuristic that flags too much is worse than none: it teaches
people to ignore every warning.

## Table

| Check | Reliable? | Correct use |
|---|---|---|
| Number of paragraphs, headings and sections (output vs. source) | Yes, as a clue | A mismatch means reading the point of misalignment; legitimate paragraph merges exist. |
| Numbers and dates (set in the source vs. in the output) | Yes | A changed number **fails**. Consider spelled-out forms and the target language's notation ("1.000" vs. "1,000"). |
| Paragraph identical to the source | Yes, with a floor | Only consider paragraphs with a minimum number of content words (e.g. 5 or more, excluding names and Preserve passages); below that, names, interjections and short lines create noise. The floor is adjustable per project. |
| High word overlap with the source | Medium | Flags partial copying (item 2 of `failure-modes.md`); in close languages, cognates raise the rate. Compare content words only and exclude Preserve terms. |
| Output/source length ratio | Weak; calibrate per language pair | English→Portuguese tends to grow, other languages shrink. A single fixed threshold gives false positives. Use only to find a chapter far off the book's own curve (compared with the other chapters), never as an acceptance criterion. |
| Last sentence ending in punctuation | Yes | Clue for truncation; confirm by reading the ending. |
| Glossary terms missing or in variant forms | Warning only | Inflection (gender, number, conjugation) breaks exact matching; never fails. |
| Wrong-variant markers (e.g. en-GB in an en-US project) | Medium | Short word list; warning and reading. |
| Repetition of adjacent words ("the the", "that that") | Weak | Only detects typing errors; fiction has intentional repetition (refrains, echoes). List for the copyedit, with no automatic correction. |
| Replacement rule with zero matches | Yes | Always warn; zero matches may indicate a wrong pattern. |

## Procedure

1. Run the checks and group the alerts by type.
2. For each type, read 3 to 5 flagged passages (or all of them, if there are few).
3. Classify: real defect, false positive or doubt for human review.
4. Fix only the affected passage. If most of the sample is false positives, adjust or
   discard the heuristic instead of acting on the alerts.
5. Record in the Step 2 log what was flagged, what was real and what was discarded.

## What the floor and the sample protect

- Passages legitimately identical to the source (names, verses in another language,
  acronyms) stay out of the count.
- A short or lyrical chapter with an atypical length ratio is not rejected without
  reading.
- A warning without reading never triggers automatic retranslation.
