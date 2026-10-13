#!/usr/bin/env python3
"""Sampled, MQM-style quality scoring for literary translation (one Markdown file per chapter)."""

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SEVERITY_WEIGHTS = {"minor": 1, "major": 5, "critical": 10}

CATEGORIES = {
    "accuracy/mistranslation": "meaning differs from the source",
    "accuracy/omission": "source content missing from the translation",
    "accuracy/addition": "content in the translation that the source does not have",
    "accuracy/untranslated": "text left in the source language that should have been translated",
    "fluency/grammar": "spelling, grammar, agreement, punctuation errors",
    "fluency/calque": "literal rendering that reads as foreign or unnatural",
    "fluency/register": "formality, dialect or tone does not fit the speaker or scene",
    "terminology/glossary": "contradicts the project glossary or is inconsistent across passages",
    "style/voice": "narrator or character voice flattened, changed or made generic",
    "style/subtext": "implied meaning made explicit, or deliberate ambiguity resolved",
    "typography/convention": "quotation marks, dashes, italics or other conventions broken",
}

LANG_NAMES = {"pt-BR": "Brazilian Portuguese", "pt": "Portuguese", "es": "Spanish", "fr": "French"}

DIALOGUE_STARTS = "“\"«—–-‘"
COVERAGE_WARN = 0.8


def paragraphs(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]


def is_dialogue(paragraph):
    return paragraph[:1] in DIALOGUE_STARTS


def classify(source_paras, embedded_re):
    text = "\n".join(source_paras)
    if embedded_re and embedded_re.search(text):
        return "embedded"
    dialogue = sum(is_dialogue(p) for p in source_paras)
    if is_dialogue(source_paras[0]) or dialogue * 2 > len(source_paras):
        return "dialogue"
    return "narration"


def build_windows(source_dir, target_dir, glob, window, embedded_re):
    windows, skipped = [], []
    for src in sorted(Path(source_dir).glob(glob)):
        tgt = Path(target_dir) / src.name
        if not tgt.is_file():
            skipped.append({"file": src.name, "reason": "no target file"})
            continue
        sp, tp = paragraphs(src), paragraphs(tgt)
        if len(sp) != len(tp):
            skipped.append({"file": src.name, "reason": f"paragraph count {len(sp)} != {len(tp)}"})
            continue
        for start in range(0, len(sp), window):
            s_chunk, t_chunk = sp[start:start + window], tp[start:start + window]
            words = sum(len(p.split()) for p in t_chunk)
            if words == 0:
                continue
            windows.append({
                "id": f"{src.stem}:{start}",
                "file": src.name,
                "index": start,
                "type": classify(s_chunk, embedded_re),
                "source": "\n\n".join(s_chunk),
                "target": "\n\n".join(t_chunk),
                "words": words,
            })
    return windows, skipped


def allocate(quota, sizes):
    """Largest-remainder split of quota across strata, capped by stratum size."""
    total = sum(sizes.values())
    alloc = {k: 0 for k in sizes}
    if total == 0 or quota <= 0:
        return alloc
    quota = min(quota, total)
    exact = {k: quota * v / total for k, v in sizes.items()}
    for k in sizes:
        alloc[k] = min(int(exact[k]), sizes[k])
    for k in sorted(sizes, key=lambda k: (-(exact[k] - int(exact[k])), k)):
        if sum(alloc.values()) >= quota:
            break
        if alloc[k] < sizes[k]:
            alloc[k] += 1
    while sum(alloc.values()) < quota:
        room = [k for k in sorted(sizes) if alloc[k] < sizes[k]]
        if not room:
            break
        alloc[room[0]] += 1
    return alloc


def stratified_sample(windows, n, seed):
    rng = random.Random(seed)
    if n >= len(windows):
        return list(windows)
    by_file = defaultdict(list)
    for w in windows:
        by_file[w["file"]].append(w)
    chosen = {}
    if n >= len(by_file):
        for name in sorted(by_file):
            pick = rng.choice(by_file[name])
            chosen[pick["id"]] = pick
    pool = defaultdict(list)
    for w in windows:
        if w["id"] not in chosen:
            pool[w["type"]].append(w)
    alloc = allocate(n - len(chosen), {k: len(v) for k, v in pool.items()})
    for kind in sorted(pool):
        for w in rng.sample(pool[kind], alloc[kind]):
            chosen[w["id"]] = w
    return sorted(chosen.values(), key=lambda w: (w["file"], w["index"]))


def cmd_sample(args):
    embedded_re = re.compile(args.embedded) if args.embedded else None
    windows, skipped = build_windows(args.source, args.target, args.glob, args.window, embedded_re)
    if not windows:
        print("no comparable passages found", file=sys.stderr)
        return 1
    passages = stratified_sample(windows, args.n, args.seed)
    data = {
        "version": 1,
        "seed": args.seed,
        "window": args.window,
        "glob": args.glob,
        "requested": args.n,
        "skipped": skipped,
        "passages": passages,
    }
    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    kinds = Counter(p["type"] for p in passages)
    files = len({p["file"] for p in passages})
    print(f"{len(passages)} passages from {files} files: " + ", ".join(f"{k}={v}" for k, v in sorted(kinds.items())))
    for s in skipped:
        print(f"skipped {s['file']}: {s['reason']}", file=sys.stderr)
    return 0


def judge_prompt(passages, lang):
    language = LANG_NAMES.get(lang, lang)
    cats = "\n".join(f"- {k}: {v}" for k, v in CATEGORIES.items())
    body = "\n\n".join(
        f"=== PASSAGE id={p['id']} type={p['type']} ===\n--- SOURCE ---\n{p['source']}\n--- TRANSLATION ({lang}) ---\n{p['target']}"
        for p in passages
    )
    return f"""You are a bilingual editor auditing a translation into {language} for its actual genre and audience.
For each passage below, compare the translation with the source and list every real error. Verify; do not rewrite as a coauthor.

Rules:
- Judge meaning, voice and conventions against the source. A smooth sentence that changes the meaning is an error.
- Do not penalise deliberate choices (kept foreign words, adapted idioms) unless they break meaning or contradict the glossary you were given.
- Report an error only when you can point to a concrete problem. A clean passage has an empty error list.
- Keep correct, natural variants unchanged. A preferred synonym, closer literal wording or repetition alone is not a defect.
- Include source/target evidence and concrete impact in each short note: changed information, incorrect language, genuinely unnatural phrasing or a broken applicable convention.
- Apply glossary rules to their defined sense, not ordinary uses of technical words. Allow grammatical inflection and idiomatic reformulation that preserves meaning.
- Objective spelling, agreement and punctuation errors remain reportable. Group duplicate findings without inflating severity.
- Examine subtext, wordplay and literary effects where the source uses them; do not invent them in plain exposition. Preserve nuances that matter to the argument, instruction, facts or voice.
- Do not demand a minimum number of findings or justify clean lexical choices. A merely possible ambiguity is not an error without a plausible contextual misunderstanding.
- Count one problem once; do not stack several categories on the same problem.

Categories (use exactly these labels):
{cats}

Severities:
- minor: a demonstrable local language or fidelity defect while the passage remains usable; not an acceptable alternative or preference.
- major: substantially changes meaning, breaks an important voice/effect or seriously impedes comprehension. Routine spelling, capitalization or a familiar untranslated place name is not automatically major.
- critical: reverses or destroys a key meaning, drops a crucial fact, or leaves a passage unusable.

Answer with ONLY a JSON array, one object per passage, covering every id below:
[{{"id": "<passage id>", "errors": [{{"c": "<category>", "s": "<minor|major|critical>", "n": "<short note>"}}]}}]

{body}
"""


def cmd_prompt(args):
    sample = json.loads(Path(args.sample).read_text(encoding="utf-8"))
    passages = sample["passages"]
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    batches = [passages[i:i + args.batch] for i in range(0, len(passages), args.batch)]
    for i, batch in enumerate(batches, 1):
        (outdir / f"batch-{i:02d}.md").write_text(judge_prompt(batch, args.lang), encoding="utf-8")
    print(f"{len(batches)} batch files in {outdir}")
    print("Run each one in a separate session, ideally with a different model than the translator,")
    print("and save each answer as batch-NN.json.")
    return 0


def extract_array(text):
    decoder = json.JSONDecoder()
    pos = text.find("[")
    while pos != -1:
        try:
            value, _ = decoder.raw_decode(text, pos)
        except ValueError:
            value = None
        if isinstance(value, list) and all(isinstance(v, dict) for v in value):
            return value
        pos = text.find("[", pos + 1)
    return None


def validate_errors(raw):
    if not isinstance(raw, list):
        return None
    errors = []
    for item in raw:
        if not isinstance(item, dict):
            return None
        cat = item.get("c", item.get("category"))
        sev = str(item.get("s", item.get("severity", ""))).lower()
        if cat not in CATEGORIES or sev not in SEVERITY_WEIGHTS:
            return None
        errors.append({"c": cat, "s": sev, "n": str(item.get("n", item.get("note", "")))})
    return errors


def load_judgments(sample, texts):
    known = {p["id"] for p in sample["passages"]}
    results = {}
    stats = Counter()
    for text in texts:
        entries = extract_array(text)
        if entries is None:
            stats["unreadable_files"] += 1
            continue
        for entry in entries:
            pid = str(entry.get("id"))
            if pid not in known:
                stats["unknown_ids"] += 1
                continue
            errors = validate_errors(entry.get("errors"))
            if errors is None:
                stats["invalid_entries"] += 1
                continue
            if pid in results:
                stats["duplicates"] += 1
            results[pid] = errors
    return results, stats


def to_score(penalty, words):
    return max(0.0, 100 - penalty / words * 100) if words else None


def evaluate(sample, texts):
    results, stats = load_judgments(sample, texts)
    passages = sample["passages"]
    evaluated = [p for p in passages if p["id"] in results]
    per_file = defaultdict(lambda: {"penalty": 0, "words": 0, "passages": 0})
    severities, categories = Counter(), Counter()
    penalized = []
    for p in evaluated:
        pen = sum(SEVERITY_WEIGHTS[e["s"]] for e in results[p["id"]])
        f = per_file[p["file"]]
        f["penalty"] += pen
        f["words"] += p["words"]
        f["passages"] += 1
        for e in results[p["id"]]:
            severities[e["s"]] += 1
            categories[e["c"]] += 1
        if pen:
            penalized.append({"id": p["id"], "file": p["file"], "penalty": pen,
                              "notes": [f"{e['s']} {e['c']}: {e['n']}" for e in results[p["id"]]]})
    words = sum(p["words"] for p in evaluated)
    penalty = sum(f["penalty"] for f in per_file.values())
    penalized.sort(key=lambda x: (-x["penalty"], x["id"]))
    return {
        "score": to_score(penalty, words),
        "penalty": penalty,
        "words_evaluated": words,
        "passages_total": len(passages),
        "passages_evaluated": len(evaluated),
        "coverage": len(evaluated) / len(passages) if passages else 0.0,
        "excluded_ids": [p["id"] for p in passages if p["id"] not in results],
        "stats": dict(stats),
        "severities": dict(severities),
        "categories": dict(categories.most_common()),
        "per_file": {k: {**v, "score": to_score(v["penalty"], v["words"])} for k, v in sorted(per_file.items())},
        "worst": penalized[:10],
    }


def read_texts(paths):
    return [Path(p).read_text(encoding="utf-8", errors="replace") for p in paths]


def cmd_score(args):
    sample = json.loads(Path(args.sample).read_text(encoding="utf-8"))
    report = evaluate(sample, read_texts(args.judgments))
    warnings = []
    if report["passages_evaluated"] == 0:
        print("no passage was evaluated; refusing to print a score", file=sys.stderr)
        return 1
    if report["coverage"] < COVERAGE_WARN:
        warnings.append(f"only {report['coverage']:.0%} of passages were evaluated (< {COVERAGE_WARN:.0%}); the score may not represent the book")
    if args.model_translator and args.model_judge:
        if args.model_translator.strip().lower() == args.model_judge.strip().lower():
            warnings.append("judge and translator are the same model; expect an inflated score")
    elif not args.model_judge:
        warnings.append("judge model not recorded; use a different model than the translator")
    report["warnings"] = warnings
    report["meta"] = {"model_translator": args.model_translator, "model_judge": args.model_judge,
                      "seed": sample.get("seed")}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return 0
    print(f"score: {report['score']:.1f} / 100  ({report['words_evaluated']} words, penalty {report['penalty']})")
    print(f"evaluated: {report['passages_evaluated']}/{report['passages_total']} passages ({report['coverage']:.0%})")
    if report["excluded_ids"]:
        print(f"excluded (not judged, not counted as clean): {len(report['excluded_ids'])}")
    if report["stats"]:
        print("judgment issues: " + ", ".join(f"{k}={v}" for k, v in sorted(report["stats"].items())))
    print("severities: " + (", ".join(f"{k}={v}" for k, v in sorted(report["severities"].items())) or "none"))
    for cat, count in report["categories"].items():
        print(f"  {cat}: {count}")
    print("per file:")
    for name, f in report["per_file"].items():
        print(f"  {name}: {f['score']:.1f} ({f['passages']} passages)")
    print("most penalized:")
    for w in report["worst"][:5]:
        print(f"  {w['id']} (penalty {w['penalty']}): " + "; ".join(w["notes"]))
    for w in warnings:
        print(f"WARNING: {w}")
    return 0


def cmd_compare(args):
    sample = json.loads(Path(args.sample).read_text(encoding="utf-8"))
    runs = [evaluate(sample, read_texts(group)) for group in (args.run1, args.run2)]
    for i, r in enumerate(runs, 1):
        if r["passages_evaluated"] == 0:
            print(f"run{i}: no passage was evaluated", file=sys.stderr)
            return 1
        print(f"run{i}: {r['score']:.1f} ({r['passages_evaluated']}/{r['passages_total']} passages)")
    diff = abs(runs[0]["score"] - runs[1]["score"])
    print(f"difference: {diff:.1f}")
    print("Score changes smaller than this difference are measurement noise on this sample.")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("sample", help="draw a reproducible stratified sample of passages")
    s.add_argument("--source", required=True)
    s.add_argument("--target", required=True)
    s.add_argument("--glob", default="*.md")
    s.add_argument("-n", type=int, default=40)
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--window", type=int, default=3)
    s.add_argument("--embedded", help="regex on the source text that marks embedded-language passages")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_sample)

    p = sub.add_parser("prompt", help="write judge prompt files, one per batch")
    p.add_argument("--sample", required=True)
    p.add_argument("--lang", default="pt-BR")
    p.add_argument("--batch", type=int, default=10)
    p.add_argument("--outdir", required=True)
    p.set_defaults(func=cmd_prompt)

    c = sub.add_parser("score", help="score the judge answers")
    c.add_argument("--sample", required=True)
    c.add_argument("--judgments", nargs="+", required=True)
    c.add_argument("--model-translator")
    c.add_argument("--model-judge")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_score)

    k = sub.add_parser("compare", help="compare two judging runs of the same sample")
    k.add_argument("--sample", required=True)
    k.add_argument("--run1", nargs="+", required=True)
    k.add_argument("--run2", nargs="+", required=True)
    k.set_defaults(func=cmd_compare)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
