---
name: update-story-bible
description: |
  Extracts facts established in a freshly finished fiction chapter and incorporates them
  into the project's story bible (characters, world, timeline, narrative promises). Use
  PROACTIVELY right after a chapter is written and revised. Trigger when the user
  mentions "update the story bible", "record the chapter's facts", or "extract
  continuity". Slash form: `/update-story-bible`.
---

# Skill: Update Story Bible

Reads a finished chapter and proposes the updates needed in the project's story bible,
keeping track of where each fact came from.

## How to use

```
/update-story-bible chapter=<number>
```

**Example:**
- `/update-story-bible chapter=09` — extracts facts from chapter 9 and updates the bible

## Process

1. **Read the finished chapter** in the manuscript
2. **Extract canonical facts** in 5 categories:

### Characters
- New or confirmed physical descriptions
- Revealed personality traits
- Discovered motivations or secrets
- Relationships established or changed
- Knowledge acquired by the character

### World / Geography
- Places visited or described
- Distances and travel times mentioned
- Details of culture, customs, politics

### Magic / Technology System
- Newly revealed properties
- Demonstrated limitations
- Specific objects/artifacts identified

### Timeline
- When the chapter takes place (relative to the others)
- Notable events with date/time if mentioned

### Narrative Promises
- Foreshadowing planted
- Open questions that need a payoff

Record each one as a row in `bible/promises.md` (create it if missing, with the
header `| Promise | Planted in ch<NN> | Status | Payoff in ch<NN> |`). A
promise enters with `Status: open` until another chapter resolves it — when
resolved, update the same row (do not duplicate), filling in "Payoff in ch<NN>" and
changing the status to `resolved`. This keeps an always-current list of
pending threads without rereading the whole manuscript — consult this file, not
memory of the chapter, when deciding whether an old piece of foreshadowing has had its payoff.

## Output

Files to update, with the exact sections:

```
FILE: bible/characters/<name>.md
ADD UNDER: ## Canonical Facts
---
- [ch<NN>] <fact>
---

FILE: bible/timeline.md
ADD UNDER: ## Chapter <NN>
---
- <event>
---
```

Always indicate the source chapter number in brackets for traceability.

After updating the bible, also update `state/current/continuity.md` (see the project's
writing workflow, if one exists) to reflect the new "where we left off".

## Translation mode (target glossary)

When the project is a translation (`translation/targets/<locale>/` exists), the "bible" is the
target's `glossary.md`, and what is extracted from the translated chapter is terminology and
decisions, not plot.

1. Read the chapter in `manuscript/` and the matching `decisions/<same filename>.md`.
2. For each proper name, place, title, regional term or embedded-language phrase that
   recurs, make sure there is a row in `glossary.md` in the format
   `| Source term | Meaning or function | Target form | Policy |`, with `Policy` equal to
   `Preserve` or `Translate`.
3. Replace `TO DECIDE` when the chapter has already fixed the form. If the term appeared in
   different forms within the same chapter, do not choose on your own: list it as an open decision.
4. Update the existing row instead of duplicating it, and keep the origin in brackets
   (`[ch<NN>]`) in the meaning column.
5. Record decisions that apply to later chapters in `decisions/<file>.md`, and
   update `manifest.md` only if the chapter's status changed.

Then run the `translation-gates` skill passing the glossary, to confirm that the new
rules match in the text (a rule that matches zero occurrences is reported).

## References

- Order of calls within the full workflow: see the project's writing workflow, if one exists
