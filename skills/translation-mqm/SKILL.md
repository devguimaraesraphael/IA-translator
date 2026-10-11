---
name: translation-mqm
description: Evaluates the quality of a literary translation by sampling, with an MQM-style score (severity penalty ÷ words evaluated), a judge in a separate session and noise measurement. Use when the user asks to "evaluate translation quality", "MQM score", "compare translations" (versions, languages or prompts), "sampled translation QA" or "/translation-mqm".
---

# Evaluate a translation by sampling (MQM)

The score is for **comparing** (version A vs B, prompt A vs B, language A vs B), not for approving a book on its own.

## Where the script is

`scripts/mqm_score.py` at the root of the IA-translator repository (stdlib only, Python 3). With the skill installed as a symlink:

```bash
REPO="$(dirname "$(dirname "$(readlink -f ~/.claude/skills/translation-mqm)")")"
python3 "$REPO/scripts/mqm_score.py" --help
```

## Steps

1. **Mechanical gates first.** Run the `translation-gates` skill on the target. If any gate fails (missing chapter, misaligned paragraphs, leftover marker), fix it before judging: the judge wastes time on defects a script finds.
2. **Draw the sample** (reproducible, stratified by dialogue/narration and spread across chapters):
   `python3 $REPO/scripts/mqm_score.py sample --source <source-dir> --target <target-dir> --glob '0*.md' -n 40 --seed 1 --out sample.json`
   To flag passages with embedded foreign-language text, use `--embedded '<regex>'` (applied to the source text). Files whose paragraphs do not match between source and target are skipped and listed in the warning.
3. **Generate the judge prompts:**
   `python3 $REPO/scripts/mqm_score.py prompt --sample sample.json --lang pt-BR --batch 10 --outdir prompts/`
4. **Run the judge in a separate session, preferably a different model** than the translator. Paste each `batch-NN.md` into a fresh conversation (without the translation context) and save the answer as `batch-NN.json`. If the glossary or documented decisions matter, attach them to the prompt.
5. **Score:**
   `python3 $REPO/scripts/mqm_score.py score --sample sample.json --judgments prompts/batch-*.json --model-translator <X> --model-judge <Y>`
   Accepts an answer wrapped in a code fence or with text before the JSON. Exits with code 1 if nothing was evaluated.
6. **Read the most penalized passages** (the report lists id and notes; the text is in `sample.json`) and confirm the judge's reading before changing the translation. Judges make mistakes, and the rubric tells them not to punish documented choices.
7. **Measure the noise:** run the judge again on the same sample and compare:
   `python3 $REPO/scripts/mqm_score.py compare --sample sample.json --run1 a/*.json --run2 b/*.json`
   Score differences smaller than the difference between the two runs are not signal.

## Rules

- Never read decimal places: the `compare` difference is the noise floor.
- An excluded passage (unreadable or missing answer, or invalid category/severity) is **not** a clean passage. Evaluated fraction < 80% invalidates the score reading.
- Judge different from translator; record both models. A model grading itself is generous.
- To compare versions, use the same sample (same seed, same files) and the same judge.
- Never paste the whole manuscript into any prompt; only the sample.

## References

| File | When to read | What it contains |
|---|---|---|
| `references/mqm-rubric.md` | When revising the judge prompt or contesting a score | Categories, severities with fiction examples, guidance against judge bias |
