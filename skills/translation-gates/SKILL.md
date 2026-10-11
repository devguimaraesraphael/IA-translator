---
name: translation-gates
description: |
  Mechanically verifies a literary translation in Markdown (one file per chapter) against the
  source: file pairing, heading and paragraph parity, altered numbers, paragraphs left in the
  source language, truncation and glossary terminology. Reports only; never fixes or
  retranslates on its own. Use after translating one or more chapters, before closing a batch or
  exporting. Trigger when the user asks to "verify translation", "check paragraph parity",
  "translation gates", "did the translation skip a paragraph", "check glossary", "did any number
  change", "is any paragraph untranslated?" or "/translation-gates".
---

# translation-gates

Runs `scripts/translation_gates.py` and turns the report into confirmed fixes. The script flags
suspicions; you decide whether each is a defect by reading the passage.

## Non-negotiable rules

- **Coverage is not completeness.** One target file per chapter does not prove the chapter was
  translated in full; the gates compare target against source.
- **Inspect before acting.** Read the report samples (source and target side by side) before
  touching any file. A finding you have not read does not become a fix.
- **Never purge or retranslate automatically.** Fix only the passage confirmed as a defect.
- **Numbers fail; terms warn.** An altered number is a GATE. Glossary and "left in the source
  language" are WARN (inflection and proper names cause false positives); they gate only with
  `--strict`.
- **A rule that matches zero is reported**, never silent: see the "matched 0 times" note of G6.

## Steps

1. **Find the folders and locate the script.** In a translation project: sources at the root (or
   wherever `translation/context/source-profile.md` points), translations in
   `translation/targets/<locale>/manuscript/`, glossary in `translation/targets/<locale>/glossary.md`.
   Confirm the `<locale>` with the user if there is more than one. The script lives in the
   IA-translator repository, not in the project. With the skill installed as a symlink, go up two
   levels from it:
   ```bash
   REPO=$(dirname "$(dirname "$(readlink -f ~/.claude/skills/translation-gates)")")
   SCRIPT="$REPO/scripts/translation_gates.py"
   ```
   If the skill was copied (not a symlink) and the path does not exist, locate it with
   `find ~ -name translation_gates.py -path '*/scripts/*' 2>/dev/null`.
2. **Run.** Restrict `--glob` to the chapters (e.g. `'0*.md'`) to keep READMEs and the like out:
   ```bash
   python3 "$SCRIPT" --source <sources> --target <manuscript> \
     --glossary <glossary.md> --glob '0*.md'
   ```
   Use `--json` for the full report (text mode shows up to 10 examples per gate). Exit code 1 =
   some GATE failed.
3. **Read the samples before any fix.** For each finding, open the source and target files at the
   indicated position and classify it as a real defect or a known false positive
   (`references/gates.md`). If G2 failed on a file, G4 was skipped on it: fix parity first.
4. **Fix only what is confirmed.** Edit the exact passage in the manuscript; if the cause is an
   editorial decision (term, convention), adjust the glossary or record it in `decisions/` instead
   of repeating the fix across chapters. For an already inspected number false positive, use
   `--allow-number file.md:value` (repeatable); never silence one without reading it.
5. **Run again** until the GATES pass and every remaining WARN is classified as a false positive
   or fixed. Report to the user: what failed, what was a defect, what was a false positive and why.

## Reference files

| File | When to read | What it contains |
|---|---|---|
| `references/gates.md` | In step 3, when classifying a finding | Table of gates G1–G6: what each checks, GATE or WARN, known false positives, what to do |
