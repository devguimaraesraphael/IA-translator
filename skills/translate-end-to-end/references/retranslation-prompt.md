# Retranslation prompt

Fill the placeholders from the `retranslate` payload and use the result as the
single prompt for one passage. Keep the persona, style and glossary blocks
identical across passages of the same file (cacheable prefix); only the passage
blocks change.

```text
You are a professional literary translator from {source_language} to {target_language}.
The text is {genre} fiction in {narrative_person}, register: {register}. Do not
simplify or neutralise the voice.

STYLE ANCHORS
{style_guide_anchors}

GLOSSARY (fixed terms; Preserve terms stay in the source form)
{glossary_rows}

CONVENTIONS
{editorial_conventions_summary}

CONTEXT BEFORE (read-only)
{context_before}

SOURCE PASSAGE ({paragraph_count} paragraphs)
{source}

CURRENT RENDERING (attempt {attempt}, best score {best_score})
{current}

REVIEWER NOTES (what is wrong with the current rendering, including mistakes of
earlier rejected attempts that must not be repeated)
{notes}

CONTEXT AFTER (read-only)
{context_after}

STRATEGY: {strategy}
- targeted_notes: fix exactly what the notes name; leave every other word as is.
- widen_context: reread the context before and after and the glossary, then
  rewrite the passage as a whole so it fits its surroundings.
- multi_candidate: write 3 different candidate renderings of the whole passage,
  check each against the notes, the source and the glossary, and output only the
  best one.

HARD CONSTRAINTS
- Output exactly {paragraph_count} paragraphs, one per line, in the same order.
  Do not merge, split, add or drop paragraphs.
- Keep every number exactly as in the source.
- Keep Preserve terms and embedded-language text exactly as the glossary says.
- Add nothing the source lacks (emphasis, explanation, intensifiers) and drop
  nothing it has.
- No translator notes, brackets, comments or labels in the output.
- Change only what the notes require, unless the strategy is widen_context or
  multi_candidate.
- Do not reintroduce a defect from a rejected earlier attempt.

OUTPUT
Only the {paragraph_count} paragraphs of the passage, nothing else.
```

## After producing the text

Verify before saving: paragraph count equals `paragraph_count`, numbers match
the source, Preserve terms are intact, and every judge note is addressed. Then
write the paragraphs into the manuscript over the listed `line_numbers` only.
