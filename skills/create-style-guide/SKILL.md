---
name: create-style-guide
description: |
  Analyzes prose samples already revised and approved by the author and automatically
  derives a structured style guide (9 dimensions: lexicon, syntax, openings, rhythm,
  show-vs-tell, dialogue, emotional appeal, narrator voice, distinctive elements).
  Use when the
  user asks to "create a style guide", "calibrate the voice", "derive writing
  patterns", or after revising a block of chapters. Slash form: `/create-style-guide`.
---

# Skill: Create Style Guide

Derives (or updates) a structured style guide from chapters that have already been revised,
to serve as a reference for future scenes written in the same voice.

## When to use

- At the start of the project, to calibrate the voice from the first revised chapters
- After revising a new block of chapters, to update the guide with validated prose
- When the voice is drifting in new chapters

## How to use

```
/create-style-guide chapters=<list of revised chapters>
```

**Examples:**
- `/create-style-guide chapters=1-7` — derive a guide from the first 7 chapters (already revised)
- `/create-style-guide chapters=1,5,8` — specific chapters as samples

## Process — 9 Dimensions of Analysis

For each chapter provided, extract patterns in:

### 1. Lexical Choices
- Preferred vs. avoided words
- Register level (formal, colloquial, poetic)
- Dominant semantic field — analyze the core emotion, recurring vocabulary and anchor
  symbols explicitly (or use the project's chapter-review skill, if one exists) instead of
  naming the semantic field loosely

### 2. Sentence Structure
- Average sentence length
- Variation pattern (short-long-short)
- Use of fragments

### 3. Opening Techniques
- How scenes/chapters begin
- In medias res vs. gradual contextualization
- First-sentence pattern

### 4. Flow and Rhythm
- How transitions work
- Use of short paragraphs for impact
- Narrative tempo (fast vs. contemplative)
- Use objective criteria (sentence-length variation, closing cadence, phonetic devices)
  instead of judging rhythm only impressionistically

### 5. Show vs. Tell
- Ratio of action to reflection
- How emotions are encoded physically
- Density of concrete detail

### 6. Dialogue
- Dialogue/narration ratio
- Use of action beats vs. dialogue tags
- Subtext and the unsaid

### 7. Emotional Appeal
- Dominant tone (epic, intimate, dark)
- How tension is built and released
- Which emotion the reader should feel

### 8. Narrator Tone and Voice
- Narrative distance (close vs. distant)
- Irony or neutrality
- How the narrator relates to the character

### 9. Distinctive Elements
- Patterns unique to this voice
- Constructions that do not appear in other authors
- What would make this text identifiable as this author's
- Before recording a repetition as a "distinctive element of the voice", apply the
  intentionality test from `review-writing-tics` (`references/tics-catalog.md`, section C) —
  a pattern that repeats out of writing reflex (a tic) must not enter the guide as if it
  were a deliberate trait; only record here what evolves, has a function, or is a confirmed
  rhetorical echo

## Output

Update the project's author-voice guide (e.g. `notes/author-voice.md`) with:

```markdown
## Automatically Derived Guide (ch <N>-<N>)

### Confirmed Patterns
- [dimension]: [pattern found] — example: "[quote from the text]"

### Newly Identified Patterns
- ...

### Patterns to Avoid (found but inconsistent with the voice)
- ...
```

Never overwrite the "Validated Prose Examples" section — only add to the derived-guide
section.

## Note on few-shot prompting

Passing **5+ diverse examples** produces better
style consistency than manual instructions. The more revised chapters are passed as
samples, the more precise the guide. Recommended minimum: 3 chapters
from different emotional phases of the story.

## References

- Consumed by the project's scene-writing and chapter-review skills, if any
- Order of calls in the full workflow: see the project's writing workflow, if one exists
