# Translation workspace

Prepares a manuscript for literary translation without changing the source files at the
repository root. Fill `context/source-profile.md` first: it records source language,
embedded languages, register and period signals.

## Before translating

1. Choose a target language and BCP 47 tag, such as `pt-BR` or `fr-FR`.
2. Copy `targets/README.md` to `targets/<language-tag>/README.md` and create the
   directories described there.
3. Resolve every `TO DECIDE` entry in `context/glossary.md` for that target.
4. Add two to four approved source-to-target pairs to `context/style-guide.md`.
5. Record target-language dialogue and typography choices in
   `context/editorial-conventions.md`.

## Translation cycle

Translate one file at a time, in the order defined by `manifest.md`. Keep persona, style
guide, glossary and rules for non-equivalent language fixed as the prompt prefix; only the
source text varies.

For every translated file:

1. Save the clean translated text under the target's `manuscript/` directory.
2. Record non-trivial choices using `templates/translation-decisions.md`.
3. Complete all four checks in `templates/verification-log.md`.
4. Compare characterization and tone with every earlier translated chapter.
5. Update the file's status in `manifest.md`.

The translated manuscript contains only literary text. Decisions and QA logs stay separate
from publication-ready files.
