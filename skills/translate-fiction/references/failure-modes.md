# Failure modes in LLM-assisted literary translation

Format: **Symptom → Cause → Fix → How to detect.** Use when closing Step 2 or when
investigating a suspect chapter.

## 1. Coverage is not completeness

- **Symptom:** every chapter is listed as translated, but paragraphs are missing or
  paragraphs remain in the source language.
- **Cause:** "file exists" was taken as proof of "file is complete". The model
  summarizes, skips or merges passages without warning, especially in long chapters.
- **Fix:** retranslate only the missing passage, leaving the rest intact.
- **Detect:** compare output and source: count of paragraphs, headings/sections and
  numbers. A paragraph mismatch is a clue, not a verdict: read the points where the
  sequence falls out of alignment.

## 2. Paragraph returned in the source language

- **Symptom:** a paragraph (or sentence) comes out nearly identical to the source,
  with one or two words swapped.
- **Cause:** the model "copies and adjusts" when the passage is short, full of names
  or looks already understandable.
- **Fix:** retranslate the paragraph in isolation, with the passage role.
- **Detect:** paragraphs identical or heavily overlapping with the source (see
  `review-heuristics.md`), then reading. Discard legitimate cases (see item 4).

## 3. Wrong variant of the target language

- **Symptom:** the text comes out in en-GB in an en-US project (or pt-PT/pt-BR,
  es-ES/es-419). Clues: "lorry", "whilst", "colour", "lift" where the project uses
  "truck", "while", "color", "elevator".
- **Cause:** the prompt named only the language, not the variant.
- **Fix:** declare the variant in Block 1 and in the glossary; retranslate the passage.
- **Detect:** a short list of markers for the unwanted variant, used as an alert, and
  reading a sample of the chapter.

## 4. Non-translatable data treated as an error (and the reverse)

- **Symptom:** the check flags "not translated" on passages in another language
  (phrases in another language or dialect, Latin, song), proper names or labels; or
  the translator "fixes" those passages into the target language.
- **Cause:** the rule for untranslatables was not given to the translator or to the
  verification.
- **Fix:** confirm that the passage actually requires preservation under the project
  policy before adding it to Preserve and excluding it from the untranslated check.
  Proper names and labels are not automatically Preserve: use the exonym and
  descriptive-name rules in `memory-and-glossary.md`.
- **Detect:** before flagging, consult the Preserve list; after translating, confirm
  that each Preserve item remains intact in the output.

## 5. Truncation by size limit

- **Symptom:** the chapter ends mid-word or mid-sentence, or without the final scene.
- **Cause:** the call's output limit was exhausted.
- **Fix:** resume from the last intact paragraph; in the future, split by scene.
- **Detect:** check the last character (expected final punctuation) and the last
  paragraph against the source's.

## 6. Subtext made explicit or ambiguity resolved

- **Symptom:** the character now says what they feel; an open reading gains a single
  interpretation.
- **Cause:** the model's tendency to clarify.
- **Fix:** rewrite preserving the opacity of the original (Step 2a).
- **Detect:** side-by-side reading of tense dialogue.

## 7. Calques and additions

- **Symptom:** a correct but "translated-sounding" sentence; an adverb or intensifier
  the source lacks.
- **Fix/Detect:** Step 2b (reading without the source) and 2c.

## 8. Glossary and convention drift

- **Symptom:** a fixed term in the same sense varies without an allowed inflection
  or contextual reason; quotation marks in one chapter, dashes in another.
- **Cause:** decisions stayed only in the conversation and were lost when switching
  calls.
- **Fix:** record each decision at the end of the chapter (see
  `memory-and-glossary.md`).
- **Detect:** search for the source term and for each translation variant across all
  chapters.

## 9. Numbers, dates and names altered

- **Symptom:** "1642" becomes "1624"; a name changes spelling.
- **Cause:** model copy error, or an unwarranted "correction".
- **Fix:** restore erroneous source values or spellings, retaining legitimate
  target notation, exonyms and explicit Translate entries.
- **Detect:** extract numbers and names from source and output and compare the sets;
  a number mismatch is a real failure, not an alert.

## 10. Replacement rule that matches nothing

- **Symptom:** the standardization (e.g. quotation marks) "ran" but the text did not
  change.
- **Cause:** the pattern does not match the text's real format.
- **Fix:** adjust the pattern and rerun.
- **Detect:** every search-and-replace rule must report the number of matches; zero
  is a warning, never silence.
