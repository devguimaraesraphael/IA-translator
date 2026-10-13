# Quality policy

Defaults live in `state/pipeline.json` under `config`; the controller applies
them. You never change them mid-run.

## Workflow invariants

- The controller owns state, budgets and stop conditions. Never improvise loops.
- Missing judgments are not clean; never synthesize them from a score or omission.
- Preserve source paragraph parity, numbers and explicit glossary Preserve terms.
- Keep translator notes in decisions, never inside manuscripts.
- Use fresh-context judges without translator reasoning; honor selected models.
- Workers write new candidates only; the parent publishes and runs the controller.
- Register only version-bound artifacts for the current dispatch.

## Thresholds

| Setting | Default | Meaning |
|---|---|---|
| `passage_min` | 98.0 | A passage passes with score >= this and no major or critical error |
| `chapter_min` | 99.0 | Words-weighted chapter score needed; below it a polish loop runs |
| `window` | 3 | Paragraphs per judged passage |
| `noise_floor` | 0.5 | A score gain must exceed this to count as an improvement |
| `max_retranslations` | 10 | Per passage; the draft does not count |

Score per passage: `100 - penalty / words * 100`, floored at 0, with severity
weights minor 1, major 5, critical 10 (see `skills/translation-mqm/references/mqm-rubric.md`).
Full coverage: every passage is judged, not a sample.

## Best-of tracking

Every attempt is saved. An attempt is better than the best when
`(critical, major, penalty)` is lexicographically lower. On an equal tuple, keep
the latest independently judged attempt only if its normalized score is not
lower. This tie still increments stagnation; it is not evidence of improvement.
A worse attempt is rejected and the best text is written back.

Numerical ties do not prove semantic equivalence. After any restoration, check
that confirmed defects were not reintroduced before recording clean chapter
checks. Preserve old verdicts and corrected candidates for reconciliation.

On resume, a matching historical text can become best if its attempt is later,
already judged, equally ranked and not lower-scoring. Its original rejection
flag stays in history; `retained_on_resume` records the new selection. An older
attempt or a worse judged version is not promoted by this rule.

## Stagnation strategies

Consecutive attempts without a gain beyond the noise floor raise the strategy:
`targeted_notes` (fewer than 2), `widen_context` (fewer than 4), `multi_candidate`
(4 or more). A gain smaller than the noise floor is treated as noise, since two
runs of the same judge differ by about that much.

## Unresolved

A demonstrably invalid judgment may be reconsidered once with `reconsider` and
a concrete reason. The original text and verdict remain in attempt history, the
new judgment consumes the existing attempt and judgment budgets, and a fresh
judge must still apply the same thresholds. This is not a score-shopping loop.

A passage still failing after 10 retranslations, or never returned by the judge
`judge_misses_max` times (`unjudged`), is `unresolved`. It keeps its best text,
is listed with its last notes in the report, and does not block the next chapter.
A file with any unresolved passage, or with gates unresolved, is `drafted`, not
`verified`.

## Chapter polish and checks

If all passages pass but the chapter is below `chapter_min`, passages with
penalty are retranslated in descending penalty order while retranslations
remain; if none remain the chapter proceeds and the report records
`chapter_min_unmet`. Chapter checks run at most twice per chapter.

## Audit by a second judge

After the loop, a seeded random subset of passed passages (about 10%, at least 1,
at most 20) is judged again by an independent judge. A major or critical error, or
a score below `passage_min`, reopens the passage with the audit notes. This
catches a lenient first judge.

## Why the judge must be independent

A model grades its own text generously and shares its blind spots. The judge runs
in a fresh context that has not seen the translator's reasoning, and on a
different model when possible. Record both models; if the judge model is missing
or equals the translator's, the report warns and the residual risk is higher.

## What `verified` means

`verified` means: gates pass, every passage was judged and passed the thresholds,
the audit found nothing, and chapter checks are clean, all by machine. It does not
mean a native speaker read it. The status `human reviewed` is never set here.

## Residual risk wording for the final message

State, in a few lines: the judge's model and whether it differed from the
translator's; the number of unresolved passages and `auto-decided` records;
anything flagged by the report (`chapter_min_unmet`, unresolved gates, unjudged
passages); and that subtle calques, cultural nuance and deliberate ambiguity can
pass an automated judge, so a bilingual human review is still advised before
publication.
