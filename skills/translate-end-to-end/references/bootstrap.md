# Bootstrap (no questions)

Goal: a complete workspace before the first `init`, built only from the source.
Every choice a human would normally approve is made by you, recorded as
`auto-decided` with a one-line reason, and counted in the final residual risk.
Never block on rights, review or approval questions.

## 1. Workspace

If `$WS` does not exist, copy the template and create the target directories:

```bash
cp -r "$REPO/templates/project/translation" "$WS"
mkdir -p "$WS/targets/$LANG_TAG"/{manuscript,decisions,verification}
cp -n "$WS/context/glossary.md" "$WS/context/editorial-conventions.md" "$WS/targets/$LANG_TAG/"
```

If it exists, keep everything already filled in and only complete what is still
`TO ADD` or `TO DECIDE`. Fill the target metadata in `targets/README.md`
(language tag, name, spelling standard).

## 2. Source profile

Read the first, middle and last parts of several source files and fill
`context/source-profile.md`: language and variety, embedded languages, genre,
narrative person and tense, register, setting, period signals, dialogue
conventions of the source, recurring forms (songs, scripture, letters, verse).

## 3. Glossary

Scan every source file (not only samples) for recurring proper nouns, places,
institutions, titles, nicknames, regional or period terms, units, and
embedded-language phrases. Follow the `update-story-bible` translation-mode rules
for row format and `Preserve` / `Translate`:

- `Preserve`: personal names, place names, and embedded-language phrases.
- `Translate`: common terms, titles of office, units with an established
  equivalent.
- One row per term, with the origin in brackets (`[ch<NN>]`) in the meaning column.
- The embedded-languages table gets all four fields filled; the treatment is
  usually "kept as in the source" plus the literal sense in a decision record,
  never inside the text.

Every `TO DECIDE` is resolved now: choose the most defensible option for the
target language and register, and record it in
`targets/$LANG_TAG/decisions/_bootstrap.md`:

| Item | Choice | Marker | Reason |
| --- | --- | --- | --- |
| `<term or convention>` | `<form>` | `auto-decided` | `<one line>` |

## 4. Editorial conventions

Fill `targets/$LANG_TAG/editorial-conventions.md` with the standard conventions
of the target language and spelling standard: dialogue punctuation (dashes or
quotation marks), quotation marks and nesting, ellipsis, numbers and dates,
italics, capitalisation of titles, treatment of embedded languages. For
scripture, songs and quoted verse: use an established published translation only
if one exists for that passage and language; otherwise translate it freshly and
record it as `auto-decided`. Copyright or permission questions are recorded as
`auto-decided` with the risk noted, never raised.

## 5. Style guide

From several representative source passages (narration, dialogue, the most
distinctive voice moments), fill `context/style-guide.md` with voice anchors:
sentence length and rhythm, diction, how dialect or non-standard speech is
marked, how subtext is carried, what must not be explained. Use 3 to 4 real
passages with a one-line annotation each. There are no approved target pairs yet:
the controller loop adds them after the first file verifies (SKILL.md step 6).

## 6. Manifest

List the source files in order in `translation/manifest.md` with status
`not started`. Tick no global gate that needs a human (glossary approval,
native-speaker review); leave those unchecked.

## Done when

No `TO ADD` or `TO DECIDE` remains in the glossary, conventions and source
profile, and `decisions/_bootstrap.md` lists every automatic choice.
