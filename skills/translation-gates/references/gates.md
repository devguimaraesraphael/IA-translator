# Translation verification gates

Paragraph = non-empty line that is not a heading. Paragraphs are matched by position (index).

| Gate | Checks | Type | Known false positives | What to do |
|---|---|---|---|---|
| G1 pairing | Every source file has a target of the same name and vice versa | GATE | An overly broad `--glob` (README, notes) enters the count | Narrow `--glob`; otherwise translate the missing chapter or delete the orphan target after checking |
| G2 structural parity | Same number of headings and paragraphs (tolerance `--heading-tolerance`/`--para-tolerance`, default 0) | GATE | Target that merges or splits a paragraph on purpose (dialogue, verse) | Compare the surrounding positions; a skipped paragraph is a defect, a deliberate merge needs tolerance or a line-break adjustment. With G2 failing, G4 is skipped on that file |
| G3 numeric integrity | Multiset of digit numbers is equal in source and target; normalizes `1,000`/`1.000` and 12h/24h times (`8 p.m.` = `20h`) | GATE | Digit became a word (`6 p.m.` -> "six in the evening"); time without `p.m.` converted (`7.17` -> `19h17`); localized acronym (`M 4 M` -> `H p/ H`); list numbering | Read the passage. A genuinely changed number is a defect. Legitimate conversion: `--allow-number file.md:value` |
| G4 untranslated source text | Target paragraph with word overlap >= 0.8 of content words (4+ letters) with the source and >= 6 words, discounting Preserve terms | WARN (GATE with `--strict`) | Embedded Gaelic/Latin/other-language passage; proper names in a row; cognates in short text | If the passage should stay in the source language, record it in the glossary as `Preserve`; otherwise translate it |
| G5 truncation | Target ends without final punctuation when the source ends with it; target with under 40% of the source words (`--min-ratio`, `--end-chars`) | WARN | Source ends in punctuation the target omits for style; naturally tighter translation | Read the end of the chapter; if it was cut, complete it from the source |
| G6 glossary | `Preserve`: source term present in the target unchanged. `Translate`: target form present when the term appears in the source. Reports rules that matched 0 times | WARN (GATE with `--strict`) | Inflection and contraction (`do Minch` vs target form `o Minch`); term omitted by ellipsis; pronoun in place of the name | Tell valid inflection from unwanted variation; if the term changed for no reason, make it uniform; if the decision changed, update the glossary |

## Glossary notes

- Only tables with a `Source term` and `Policy` header are read. `Policy` counts as `Preserve` or
  `Translate` if it starts with that word; any other policy is ignored and counted.
- Rows with `TO DECIDE` or `TO ADD` in any cell are ignored and counted in the report.
- Alternatives separated by ` / ` in the source term each apply; capitalized terms (proper
  names) are case-sensitive; the rest are not. The longest term matches first.
- "Matched 0 times" = a valid rule with no occurrence in the source. It may be a mistyped term, a
  rule from another book, or a term that only appears in chapters outside `--glob`.
- If the glossary only has ignored rows, G6 passes without verifying anything: check the count
  of used rules in the G6 note.
