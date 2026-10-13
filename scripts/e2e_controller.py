#!/usr/bin/env python3
"""Deterministic controller for the end-to-end translation loop.

It keeps the state of each chapter, runs the mechanical gates, writes the judge
prompt files and decides the next action. All creative and judging work is done
by the caller. Every command prints JSON on stdout.

Locate the workspace with `--workspace <translation dir> --lang <tag>` or with
`--state <path to pipeline.json>`.
"""

import argparse
import glob as globmod
import hashlib
import json
import math
import random
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import mqm_score as mqm  # noqa: E402

TEMPLATE_DIR = SCRIPT_DIR.parent / "templates" / "project" / "translation"
SUPPORT_LIMIT = 12000
TARGET_SUBDIRS = ("manuscript", "decisions", "verification", "state", "attempts", "reports")

DEFAULT_CONFIG = {
    "max_retranslations": 10,
    "passage_min": 98.0,
    "chapter_min": 99.0,
    "window": 3,
    "noise_floor": 0.5,
    "batch": 10,
    "judge_misses_max": 3,
    "stagnation_escalate": [2, 4],
    "chapter_check_rounds_max": 2,
    "audit_fraction": 0.1,
    "max_judged_passages": None,
    "max_steps": 5000,
    "seed": 1,
}
FLOAT_KEYS = {"passage_min", "chapter_min", "noise_floor", "audit_fraction"}


class UsageError(Exception):
    pass


def sha1(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha1(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def rnd(value):
    return None if value is None else round(value, 2)


class Ctx:
    def __init__(self, pipeline_path):
        self.pipeline_path = Path(pipeline_path)
        self.pipeline = read_json(self.pipeline_path)
        self.lang = self.pipeline["lang"]
        self.workspace = Path(self.pipeline["workspace"])
        self.source = Path(self.pipeline["source"])
        self.cfg = self.pipeline["config"]
        self.target = self.workspace / "targets" / self.lang

    def manuscript(self, name):
        return self.target / "manuscript" / name

    def state_path(self, name):
        return self.target / "state" / f"{Path(name).stem}.json"

    def sample_path(self, name):
        return self.target / "state" / f"{Path(name).stem}.sample.json"

    def prompts_dir(self, name):
        return self.target / "state" / f"{Path(name).stem}.prompts"

    def attempt_path(self, name, index, n):
        return self.target / "attempts" / Path(name).stem / f"p{index}-a{n:02d}.md"

    def load_file(self, name):
        if name not in self.pipeline["files"]:
            raise UsageError(f"unknown file: {name}")
        path = self.state_path(name)
        return read_json(path) if path.is_file() else new_file_state(name)

    def save_file(self, fs):
        write_json(self.state_path(fs["file"]), fs)

    def save_pipeline(self):
        write_json(self.pipeline_path, self.pipeline)


def pipeline_path_from(args):
    if getattr(args, "state", None):
        return Path(args.state)
    if getattr(args, "workspace", None) and getattr(args, "lang", None):
        return Path(args.workspace) / "targets" / args.lang / "state" / "pipeline.json"
    raise UsageError("pass --state, or both --workspace and --lang")


def open_ctx(args):
    path = pipeline_path_from(args)
    if not path.is_file():
        raise UsageError(f"workspace not initialised: {path} not found (run init)")
    return Ctx(path)


def new_file_state(name):
    return {
        "file": name, "stem": Path(name).stem, "status": "pending", "revision": None,
        "exists": False, "parity_ok": None, "passages": {}, "gates": {"rev": None},
        "gate_rounds": 0, "chapter_check_rounds": 0, "chapter_checks_rev": None,
        "chapter_check_notes": [], "steps": 0, "finished": False, "final": None,
        "audit": {"done": False, "selected": [], "reopened": [], "judged": []},
    }


def new_passage(pid, index, chunk):
    return {
        "id": pid, "index": index, "size": len(chunk), "type": mqm.classify(chunk, None),
        "attempts": [], "current": None, "best": None, "stagnation": 0, "misses": 0,
        "status": "new", "rejected_notes": [],
    }


def new_attempt(n, text_hash, words):
    return {"n": n, "hash": text_hash, "words": words, "judged": False, "rejected": False}


def read_manuscript(path):
    raw = Path(path).read_bytes()
    lines = raw.decode("utf-8").splitlines(keepends=True)
    idx = [i for i, ln in enumerate(lines) if ln.strip() and not ln.lstrip().startswith("#")]
    return raw, lines, idx


def passage_text(lines, idx, start, size):
    return "\n\n".join(lines[i].strip() for i in idx[start:start + size])


def attempt_of(p, n):
    return None if n is None else p["attempts"][n]


def best_of(p):
    return attempt_of(p, p["best"])


def attempts_made(p):
    return sum(1 for a in p["attempts"] if a["judged"] and a["n"] >= 1)


def better(a, b):
    return (a["critical"], a["major"], a["penalty"]) < (b["critical"], b["major"], b["penalty"])


def judge_notes(attempt):
    return [f"{e['s']} {e['c']}: {e['n']}" for e in attempt.get("errors", [])]


def passage_notes(p):
    best = best_of(p)
    return (judge_notes(best) if best else []) + p["rejected_notes"][-5:]


def needs_judge(cfg, p):
    cur = attempt_of(p, p["current"])
    return cur is not None and not cur["judged"] and p["misses"] < cfg["judge_misses_max"]


def needs_restore(cfg, p):
    cur, best = attempt_of(p, p["current"]), best_of(p)
    if best is None or cur is None or cur["n"] == best["n"]:
        return False
    return cur["judged"] or p["misses"] >= cfg["judge_misses_max"]


def passage_status(cfg, p):
    cur, best = attempt_of(p, p["current"]), best_of(p)
    if best is None:
        unjudged = cur is not None and p["misses"] >= cfg["judge_misses_max"]
        return "unjudged" if unjudged else "new"
    if best["critical"] == 0 and best["major"] == 0 and best["score"] >= cfg["passage_min"]:
        return "pass"
    return "unresolved" if attempts_made(p) >= cfg["max_retranslations"] else "fail"


def refresh_statuses(ctx, fs):
    for p in fs["passages"].values():
        p["status"] = passage_status(ctx.cfg, p)


def is_resolved(p):
    return p["status"] in ("pass", "unresolved", "unjudged")


def chapter_stats(fs):
    penalty = words = judged = 0
    for p in fs["passages"].values():
        best = best_of(p)
        if best:
            penalty += best["penalty"]
            words += best["words"]
            judged += 1
    total = len(fs["passages"])
    return {"score": mqm.to_score(penalty, words), "penalty": penalty,
            "coverage": judged / total if total else 0.0}


def save_attempt_text(ctx, fs, p, n, text):
    path = ctx.attempt_path(fs["file"], p["index"], n)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_attempt_text(ctx, fs, p, n):
    path = ctx.attempt_path(fs["file"], p["index"], n)
    if not path.is_file():
        raise RuntimeError(f"attempt text missing: {path}")
    return path.read_text(encoding="utf-8")


def register_text(ctx, fs, p, text):
    text_hash = sha1(text)
    attempts = p["attempts"]
    cur = attempt_of(p, p["current"])
    if cur and cur["hash"] == text_hash:
        return
    p["misses"] = 0
    for a in attempts:
        if a["hash"] == text_hash:
            p["current"] = a["n"]
            best = best_of(p)
            if (a["judged"] and best is not None and a["n"] > best["n"]
                    and not better(a, best) and not better(best, a)
                    and a["score"] >= best["score"]):
                p["best"] = a["n"]
                a["retained_on_resume"] = True
            return
    words = len(text.split())
    if cur and not cur["judged"]:
        cur.update(hash=text_hash, words=words)
        n = cur["n"]
    else:
        n = len(attempts)
        attempts.append(new_attempt(n, text_hash, words))
        p["current"] = n
    save_attempt_text(ctx, fs, p, n, text)


def source_layout(ctx, name):
    paras = mqm.paragraphs(ctx.source / name)
    size = ctx.cfg["window"]
    return paras, [(start, paras[start:start + size]) for start in range(0, len(paras), size)]


def sync_file(ctx, fs):
    name = fs["file"]
    src_paras, windows = source_layout(ctx, name)
    path = ctx.manuscript(name)
    info = {"exists": path.is_file(), "source_paras": src_paras, "parity": False, "lines": None, "idx": None, "target_paragraphs": None}
    fs["exists"] = info["exists"]
    if not info["exists"]:
        fs["revision"] = None
        return info
    raw, lines, idx = read_manuscript(path)
    fs["revision"] = sha1(raw)
    info.update(lines=lines, idx=idx, target_paragraphs=len(idx))
    if len(idx) != len(src_paras):
        fs["parity_ok"] = False
        return info
    fs["parity_ok"] = True
    info["parity"] = True
    if fs["status"] == "pending":
        fs["status"] = "active"
    for start, chunk in windows:
        pid = f"{fs['stem']}:{start}"
        p = fs["passages"].get(pid)
        if p is None:
            p = fs["passages"][pid] = new_passage(pid, start, chunk)
        register_text(ctx, fs, p, passage_text(lines, idx, start, len(chunk)))
    refresh_statuses(ctx, fs)
    return info


def run_gates(ctx, fs):
    name = fs["file"]
    cmd = [sys.executable, str(SCRIPT_DIR / "translation_gates.py"), "--source", str(ctx.source),
           "--target", str(ctx.target / "manuscript"), "--glob", globmod.escape(name), "--json"]
    glossary = ctx.target / "glossary.md"
    if glossary.is_file():
        cmd += ["--glossary", str(glossary)]
    for entry in ctx.pipeline.get("allow_numbers", []):
        if entry.startswith(name + ":"):
            cmd += ["--allow-number", entry]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        raise RuntimeError(f"translation_gates failed: {proc.stderr.strip() or proc.stdout.strip()}")
    failed, warn_counts = {}, {}
    for gate, g in payload["gates"].items():
        if g["kind"] == "GATE" and g["status"] == "fail":
            failed[gate] = {"name": g["name"], "count": g["finding_count"], "findings": g["findings"][:20]}
        elif g["kind"] == "WARN" and g["status"] == "warn":
            warn_counts[gate] = g["finding_count"]
    fs["gates"] = {"rev": fs["revision"], "passed": not failed, "failed": failed, "warn_counts": warn_counts}


def ensure_gates(ctx, fs):
    if fs["parity_ok"] and fs["gates"].get("rev") != fs["revision"]:
        run_gates(ctx, fs)


def gates_ok(fs):
    return fs["gates"].get("rev") == fs["revision"] and fs["gates"].get("passed", False)


def restore_best(ctx, fs, ids):
    if not ids:
        return []
    path = ctx.manuscript(fs["file"])
    _, lines, idx = read_manuscript(path)
    restored = []
    for pid in ids:
        p = fs["passages"][pid]
        best = best_of(p)
        paras = load_attempt_text(ctx, fs, p, best["n"]).split("\n\n")
        positions = idx[p["index"]:p["index"] + p["size"]]
        if len(paras) != len(positions):
            continue
        for pos, para in zip(positions, paras):
            body = lines[pos].splitlines()[0]
            lead = body[:len(body) - len(body.lstrip())]
            lines[pos] = lead + para + lines[pos][len(body):]
        p["current"] = best["n"]
        p["misses"] = 0
        restored.append(pid)
    raw = "".join(lines).encode("utf-8")
    path.write_bytes(raw)
    fs["revision"] = sha1(raw)
    refresh_statuses(ctx, fs)
    return restored


def pending_restores(ctx, fs, everything=False):
    out = []
    for pid, p in sorted(fs["passages"].items(), key=lambda kv: kv[1]["index"]):
        best, cur = best_of(p), attempt_of(p, p["current"])
        if everything:
            if best is not None and cur is not None and cur["n"] != best["n"]:
                out.append(pid)
        elif needs_restore(ctx.cfg, p):
            out.append(pid)
    return out


def read_support(path):
    path = Path(path)
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:SUPPORT_LIMIT] + ("\n[truncated]" if len(text) > SUPPORT_LIMIT else "")


def support_section(ctx, name, audit):
    sources = [
        ("Glossary", ctx.target / "glossary.md"),
        ("Editorial conventions", ctx.target / "editorial-conventions.md"),
        (f"Translation decisions for {name}", ctx.target / "decisions" / name),
        ("Style guide", ctx.workspace / "context" / "style-guide.md"),
    ]
    parts = ["# SUPPORT TEXTS\n\nRead these before judging. Do not penalise a choice that the "
             "translation decisions below document."]
    if audit:
        parts.append("This is an independent second opinion: judge each passage from scratch.")
    found = False
    for title, path in sources:
        text = read_support(path)
        if text is not None:
            found = True
            parts.append(f"## {title}\n\n{text}")
    if not found:
        parts.append("(no support texts available)")
    return "\n\n".join(parts)


def sample_passage(fs, info, p):
    start, size = p["index"], p["size"]
    target = passage_text(info["lines"], info["idx"], start, size)
    return {"id": p["id"], "file": fs["file"], "index": start, "type": p["type"],
            "source": "\n\n".join(info["source_paras"][start:start + size]),
            "target": target, "words": len(target.split())}


def build_judge_files(ctx, fs, info, ids, audit):
    name = fs["file"]
    passages = [sample_passage(fs, info, fs["passages"][pid]) for pid in ids]
    sample = {"version": 1, "seed": ctx.cfg["seed"], "window": ctx.cfg["window"], "glob": name,
              "requested": len(passages), "skipped": [], "audit": audit, "passages": passages}
    write_json(ctx.sample_path(name), sample)
    outdir = ctx.prompts_dir(name)
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("batch-*.md"):
        old.unlink()
    support = support_section(ctx, name, audit)
    size = ctx.cfg["batch"]
    files = []
    for i, start in enumerate(range(0, len(passages), size), 1):
        path = outdir / f"batch-{i:02d}.md"
        body = mqm.judge_prompt(passages[start:start + size], ctx.lang)
        path.write_text(support + "\n\n---\n\n" + body, encoding="utf-8")
        files.append(str(path))
    return {"passages": ids, "sample": str(ctx.sample_path(name)), "prompts_dir": str(outdir),
            "batches": len(files), "prompt_files": files}


def strategy_for(cfg, p):
    low, high = cfg["stagnation_escalate"]
    if p["stagnation"] < low:
        return "targeted_notes"
    return "widen_context" if p["stagnation"] < high else "multi_candidate"


def build_retranslation(ctx, fs, info, p):
    strategy = strategy_for(ctx.cfg, p)
    k = 2 if strategy == "targeted_notes" else 6
    start, size = p["index"], p["size"]
    src, lines, idx = info["source_paras"], info["lines"], info["idx"]
    target = [lines[i].strip() for i in idx]
    lo, hi = max(0, start - k), start + size
    best = best_of(p)
    return {
        "id": p["id"], "index": start, "attempt": len(p["attempts"]), "strategy": strategy,
        "source": "\n\n".join(src[start:hi]),
        "current": passage_text(lines, idx, start, size),
        "notes": passage_notes(p), "best_score": rnd(best["score"]) if best else None,
        "paragraph_count": size,
        "context_before": {"source": src[lo:start], "target": target[lo:start]},
        "context_after": {"source": src[hi:hi + k], "target": target[hi:hi + k]},
        "line_numbers": [i + 1 for i in idx[start:hi]],
    }


def select_audit(ctx, fs):
    passed = sorted(pid for pid, p in fs["passages"].items() if p["status"] == "pass")
    if not passed:
        return []
    count = min(20, len(passed), max(1, math.ceil(ctx.cfg["audit_fraction"] * len(passed))))
    return sorted(random.Random(ctx.cfg["seed"]).sample(passed, count))


def decide_next(ctx, fs, info):
    cfg, name = ctx.cfg, fs["file"]
    base = {"file": name}
    budget = cfg["max_judged_passages"]
    if budget is not None and ctx.pipeline["budget"]["judged_passages"] >= budget:
        return {**base, "action": "stop", "reason": "budget"}
    if fs["steps"] > cfg["max_steps"]:
        return {**base, "action": "stop", "reason": "max_steps"}
    if not info["exists"]:
        return {**base, "action": "translate", "source_path": str(ctx.source / name),
                "target_path": str(ctx.manuscript(name))}
    if not info["parity"]:
        return {**base, "action": "repair_parity", "source_paragraphs": len(info["source_paras"]),
                "target_paragraphs": info["target_paragraphs"]}
    if not fs["gates"]["passed"] and fs["gate_rounds"] < cfg["max_retranslations"]:
        fs["gate_rounds"] += 1
        return {**base, "action": "repair_gates", "findings": fs["gates"]["failed"],
                "gate_rounds": fs["gate_rounds"]}
    passages = sorted(fs["passages"].values(), key=lambda p: p["index"])
    need = [p["id"] for p in passages if needs_judge(cfg, p)]
    if need:
        return {**base, "action": "judge", **build_judge_files(ctx, fs, info, need, False)}
    failing = [p for p in passages if p["status"] == "fail"]
    if failing:
        return {**base, "action": "retranslate", "reason": "fail",
                "passages": [build_retranslation(ctx, fs, info, p) for p in failing]}
    stats = chapter_stats(fs)
    if stats["score"] is not None and stats["score"] < cfg["chapter_min"]:
        polish = [p for p in passages if p["status"] == "pass" and best_of(p)["penalty"] > 0
                  and attempts_made(p) < cfg["max_retranslations"]]
        polish.sort(key=lambda p: (-best_of(p)["penalty"], p["index"]))
        if polish:
            return {**base, "action": "retranslate", "reason": "polish",
                    "passages": [build_retranslation(ctx, fs, info, p) for p in polish]}
    rounds = fs["chapter_check_rounds"]
    if rounds < cfg["chapter_check_rounds_max"] and fs["chapter_checks_rev"] != fs["revision"]:
        return {**base, "action": "chapter_checks", "round": rounds + 1,
                "max_rounds": cfg["chapter_check_rounds_max"]}
    if cfg["audit_fraction"] > 0 and not fs["audit"]["done"]:
        if not fs["audit"]["selected"]:
            fs["audit"]["selected"] = select_audit(ctx, fs)
        if fs["audit"]["selected"]:
            return {**base, "action": "audit", "audit": True,
                    **build_judge_files(ctx, fs, info, fs["audit"]["selected"], True)}
        fs["audit"]["done"] = True
    return {**base, "action": "finalize"}


def final_record(ctx, fs):
    stats = chapter_stats(fs)
    unresolved = []
    for p in sorted(fs["passages"].values(), key=lambda p: p["index"]):
        if p["status"] != "pass":
            best = best_of(p)
            unresolved.append({"id": p["id"], "status": p["status"],
                               "best_score": rnd(best["score"]) if best else None,
                               "notes": passage_notes(p)})
    ok = gates_ok(fs)
    verified = ok and not unresolved and bool(fs["passages"])
    return {
        "status": "finished", "manifest_status": "verified" if verified else "drafted",
        "score": rnd(stats["score"]), "passages": len(fs["passages"]), "unresolved": unresolved,
        "gates_ok": ok, "revision": fs["revision"],
        "chapter_min_unmet": stats["score"] is not None and stats["score"] < ctx.cfg["chapter_min"],
    }


def apply_judgments(ctx, fs, sample, results, audit):
    cfg = ctx.cfg
    judged, missing, stale, restore_ids, reopened = [], [], [], [], []
    for sp in sample["passages"]:
        pid = sp["id"]
        p = fs["passages"].get(pid)
        cur = attempt_of(p, p["current"]) if p else None
        if cur is None or sha1(sp["target"]) != cur["hash"] or (cur["judged"] and not audit):
            stale.append(pid)
            continue
        if pid not in results:
            missing.append(pid)
            if not audit:
                p["misses"] += 1
            continue
        judged.append(pid)
        errors = results[pid]
        if audit:
            if audit_passage(cfg, fs, p, errors):
                reopened.append(pid)
        else:
            judge_attempt(cfg, p, cur, errors)
            if cur["rejected"]:
                restore_ids.append(pid)
    if audit:
        fs["audit"]["done"] = True
        fs["audit"]["judged"] = sorted(set(fs["audit"]["judged"]) | set(judged))
        fs["audit"]["reopened"] = sorted(set(fs["audit"]["reopened"]) | set(reopened))
    ctx.pipeline["budget"]["judged_passages"] += len(judged)
    ctx.save_pipeline()
    refresh_statuses(ctx, fs)
    restored = restore_best(ctx, fs, [pid for pid in pending_restores(ctx, fs)]) if fs["parity_ok"] else []
    return judged, missing, stale, restored, reopened


def set_judgment(attempt, errors):
    attempt["errors"] = errors
    attempt["penalty"] = sum(mqm.SEVERITY_WEIGHTS[e["s"]] for e in errors)
    attempt["critical"] = sum(e["s"] == "critical" for e in errors)
    attempt["major"] = sum(e["s"] == "major" for e in errors)
    attempt["score"] = mqm.to_score(attempt["penalty"], attempt["words"])


def judge_attempt(cfg, p, attempt, errors):
    set_judgment(attempt, errors)
    attempt["judged"] = True
    best = best_of(p)
    if best is None:
        p["best"] = attempt["n"]
        p["stagnation"] = 0
    elif better(attempt, best):
        dropped = (attempt["critical"], attempt["major"]) < (best["critical"], best["major"])
        gain = attempt["score"] - best["score"]
        p["stagnation"] = 0 if (gain > cfg["noise_floor"] or dropped) else p["stagnation"] + 1
        p["best"] = attempt["n"]
    elif not better(best, attempt) and attempt["score"] >= best["score"]:
        p["best"] = attempt["n"]
        p["stagnation"] += 1
    else:
        attempt["rejected"] = True
        p["stagnation"] += 1
        short = "; ".join(judge_notes(attempt)[:3]) or "no errors listed"
        p["rejected_notes"].append(
            f"attempt {attempt['n']} rejected (score {attempt['score']:.1f} vs best "
            f"{best['score']:.1f}): {short}")


def audit_passage(cfg, fs, p, errors):
    best = best_of(p) or attempt_of(p, p["current"])
    penalty = sum(mqm.SEVERITY_WEIGHTS[e["s"]] for e in errors)
    score = mqm.to_score(penalty, best["words"])
    best["audit"] = {"penalty": penalty, "score": score, "errors": errors}
    if not (any(e["s"] in ("major", "critical") for e in errors) or score < cfg["passage_min"]):
        return False
    merged = best.get("errors", []) + [{**e, "n": "[audit] " + e["n"]} for e in errors]
    set_judgment(best, merged)
    return True


def render_report(ctx):
    pl = ctx.pipeline
    models = pl.get("models", {})
    rows, details, warnings = [], [], []
    for name in pl["files"]:
        path = ctx.state_path(name)
        fs = read_json(path) if path.is_file() else new_file_state(name)
        stats = chapter_stats(fs)
        counts = Counter(p["status"] for p in fs["passages"].values())
        retrans = sum(attempts_made(p) for p in fs["passages"].values())
        gate = fs["gates"]
        gate_state = ("ok" if gate.get("passed") else "FAILED") if gate.get("rev") else "not run"
        audit = fs["audit"]
        audit_state = (f"{len(audit['judged'])} judged, {len(audit['reopened'])} reopened"
                       if audit["done"] else "pending")
        score = "-" if stats["score"] is None else f"{stats['score']:.2f}"
        final = fs.get("final") or {}
        status = final.get("manifest_status", fs["status"]) if fs["finished"] else fs["status"]
        rows.append(f"| {name} | {status} | {score} | {counts['pass']}/{len(fs['passages'])} pass, "
                    f"{counts['unresolved']} unresolved, {counts['unjudged']} unjudged | "
                    f"{retrans} | {gate_state} | {audit_state} |")
        if gate.get("rev") and not gate.get("passed"):
            details.append(f"- `{name}`: gates failed ({', '.join(sorted(gate.get('failed', {})))})")
            if fs["gate_rounds"] >= ctx.cfg["max_retranslations"]:
                warnings.append(f"`{name}`: gates unresolved after {fs['gate_rounds']} repair rounds")
        if gate.get("warn_counts"):
            details.append(f"- `{name}`: gate warnings (counts only): "
                           + ", ".join(f"{g}={n}" for g, n in sorted(gate["warn_counts"].items())))
        if final.get("chapter_min_unmet"):
            warnings.append(f"`{name}`: chapter score below chapter_min ({ctx.cfg['chapter_min']})")
        if counts["unjudged"]:
            warnings.append(f"`{name}`: {counts['unjudged']} passage(s) never returned by the judge")
        for p in sorted(fs["passages"].values(), key=lambda p: p["index"]):
            if p["status"] in ("unresolved", "unjudged"):
                notes = "; ".join(passage_notes(p)[:5]) or "no notes"
                best = best_of(p)
                shown = "-" if best is None else f"{best['score']:.1f}"
                details.append(f"- `{p['id']}` ({p['status']}, best score {shown}): {notes}")
    judge, translator = models.get("judge"), models.get("translator")
    if not judge:
        warnings.append("judge model not recorded; use a different model than the translator")
    elif translator and judge.strip().lower() == translator.strip().lower():
        warnings.append("judge and translator are the same model; expect an inflated score")
    budget, limit = pl["budget"]["judged_passages"], ctx.cfg["max_judged_passages"]
    out = [
        f"# End-to-end translation report ({ctx.lang})", "",
        "This result is machine-verified only. It was not human reviewed.", "",
        f"- Translator model: {translator or 'not recorded'}",
        f"- Judge model: {judge or 'not recorded'}",
        f"- Judged passages used: {budget}" + (f" of {limit}" if limit is not None else ""), "",
        "## Files", "",
        "| File | Status | Score | Passages | Retranslations | Gates | Audit |",
        "| --- | --- | --- | --- | --- | --- | --- |", *rows, "",
        "## Unresolved passages and gate state", "", *(details or ["None."]), "",
        "## Warnings", "", *([f"- {w}" for w in warnings] or ["None."]), "",
    ]
    return "\n".join(out)


def file_summary(ctx, fs):
    stats = chapter_stats(fs)
    made = Counter(attempts_made(p) for p in fs["passages"].values())
    gate = fs["gates"]
    return {
        "file": fs["file"], "status": fs["status"], "finished": fs["finished"],
        "score": rnd(stats["score"]), "coverage": rnd(stats["coverage"]),
        "passages": dict(Counter(p["status"] for p in fs["passages"].values())),
        "attempts_histogram": {str(k): v for k, v in sorted(made.items())},
        "retranslations": sum(made[k] * k for k in made), "steps": fs["steps"],
        "gates": "not run" if not gate.get("rev") else ("ok" if gate["passed"] else "failed"),
        "gate_rounds": fs["gate_rounds"], "chapter_check_rounds": fs["chapter_check_rounds"],
        "audit": fs["audit"],
    }


def sync_and_prepare(ctx, fs):
    info = sync_file(ctx, fs)
    if info["parity"]:
        restored = restore_best(ctx, fs, pending_restores(ctx, fs))
        if restored:
            info = {**info, "lines": read_manuscript(ctx.manuscript(fs["file"]))[1]}
        ensure_gates(ctx, fs)
    else:
        restored = []
    return info, restored


def cmd_init(args):
    source = Path(args.source).resolve()
    if not source.is_dir():
        raise UsageError(f"source folder not found: {source}")
    ws = Path(args.workspace).resolve() if args.workspace else source / "translation"
    if not ws.exists() and TEMPLATE_DIR.is_dir():
        shutil.copytree(TEMPLATE_DIR, ws)
    target = ws / "targets" / args.lang
    for sub in TARGET_SUBDIRS:
        (target / sub).mkdir(parents=True, exist_ok=True)
    if args.files:
        names = list(args.files)
        for n in names:
            if not (source / n).is_file():
                raise UsageError(f"source file not found: {n}")
    else:
        pattern = args.glob or "*.md"
        names = sorted(p.name for p in source.glob(pattern) if p.is_file() and p.suffix.lower() == ".md")
    if not names:
        raise UsageError("no source files selected")
    given = {k: getattr(args, k) for k in DEFAULT_CONFIG if getattr(args, k) is not None}
    pipeline_file = target / "state" / "pipeline.json"
    if args.reset:
        for old in (target / "state").glob("*"):
            shutil.rmtree(old) if old.is_dir() else old.unlink()
        shutil.rmtree(target / "attempts", ignore_errors=True)
        (target / "attempts").mkdir()
    created = not pipeline_file.is_file()
    if created:
        pipeline = {"version": 1, "lang": args.lang, "source": str(source), "workspace": str(ws),
                    "glob": args.glob or "*.md", "files": [], "allow_numbers": [],
                    "config": dict(DEFAULT_CONFIG),
                    "models": {"translator": None, "judge": None}, "budget": {"judged_passages": 0}}
    else:
        pipeline = read_json(pipeline_file)
        if "window" in given and given["window"] != pipeline["config"]["window"] and pipeline["files"]:
            raise UsageError("window cannot change on an existing workspace; use --reset")
    pipeline["config"].update(given)
    if pipeline["config"]["window"] < 1 or pipeline["config"]["batch"] < 1:
        raise UsageError("window and batch must be at least 1")
    pipeline["source"], pipeline["workspace"] = str(source), str(ws)
    if args.translator_model:
        pipeline["models"]["translator"] = args.translator_model
    if args.judge_model:
        pipeline["models"]["judge"] = args.judge_model
    pipeline["files"] += [n for n in names if n not in pipeline["files"]]
    write_json(pipeline_file, pipeline)
    ctx = Ctx(pipeline_file)
    for n in pipeline["files"]:
        if not ctx.state_path(n).is_file():
            ctx.save_file(new_file_state(n))
    return {"created": created, "workspace": str(ws), "target_dir": str(target),
            "pipeline": str(pipeline_file), "files": pipeline["files"], "config": pipeline["config"]}


def cmd_next(args):
    ctx = open_ctx(args)
    fs = ctx.load_file(args.file)
    info, restored = sync_and_prepare(ctx, fs)
    if fs["finished"]:
        if fs["revision"] == (fs["final"] or {}).get("revision"):
            ctx.save_file(fs)
            f = fs["final"]
            return {"file": fs["file"], "action": "done", "manifest_status": f["manifest_status"],
                    "score": f["score"], "unresolved": f["unresolved"]}
        fs["finished"], fs["status"] = False, "active"
    fs["steps"] += 1
    action = decide_next(ctx, fs, info)
    if restored:
        action["restored"] = restored
    ctx.save_file(fs)
    return action


def cmd_record_judgments(args):
    ctx = open_ctx(args)
    fs = ctx.load_file(args.file)
    sync_file(ctx, fs)
    sample_path = ctx.sample_path(args.file)
    if not sample_path.is_file():
        raise UsageError("no sample for this file; run next until it returns judge or audit")
    sample = read_json(sample_path)
    if bool(sample.get("audit")) != bool(args.audit):
        raise UsageError("the current sample is " + ("an audit sample; pass --audit" if sample.get("audit")
                                                    else "not an audit sample; drop --audit"))
    texts = [Path(p).read_text(encoding="utf-8", errors="replace") for p in args.judgments]
    results, issues = mqm.load_judgments(sample, texts)
    judged, missing, stale, restored, reopened = apply_judgments(ctx, fs, sample, results, args.audit)
    stats = chapter_stats(fs)
    ctx.save_file(fs)
    by_status = {s: [pid for pid, p in fs["passages"].items() if p["status"] == s]
                 for s in ("pass", "fail", "unresolved")}
    return {"judged": len(judged), "pass": len(by_status["pass"]), "fail": by_status["fail"],
            "unresolved": by_status["unresolved"] + [pid for pid, p in fs["passages"].items()
                                                     if p["status"] == "unjudged"],
            "restored": restored, "missing": missing, "stale": stale,
            "chapter_score": rnd(stats["score"]), "coverage": rnd(stats["coverage"]),
            "audit_reopened": reopened, "parse_issues": dict(issues)}


def cmd_reconsider(args):
    ctx = open_ctx(args)
    fs = ctx.load_file(args.file)
    info = sync_file(ctx, fs)
    if not info["parity"] or fs["finished"]:
        raise UsageError("reconsider requires an active file with matching paragraph counts")
    reason = args.reason.strip()
    if not reason:
        raise UsageError("reconsider requires a concrete reason")
    selected = []
    for pid in dict.fromkeys(args.passages):
        passage = fs["passages"].get(pid)
        if passage is None or passage["status"] != "fail":
            raise UsageError("reconsider requires a failing passage: " + pid)
        current = attempt_of(passage, passage["current"])
        if not current["judged"] or passage.get("reconsidered"):
            raise UsageError("reconsider is allowed once per passage, after judging: " + pid)
        if attempts_made(passage) >= ctx.cfg["max_retranslations"]:
            raise UsageError("passage attempt limit reached: " + pid)
        selected.append(passage)
    for passage in selected:
        current = attempt_of(passage, passage["current"])
        number = len(passage["attempts"])
        attempt = new_attempt(number, current["hash"], current["words"])
        attempt["reconsideration"] = {"reason": reason, "previous_attempt": current["n"]}
        text = passage_text(info["lines"], info["idx"], passage["index"], passage["size"])
        save_attempt_text(ctx, fs, passage, number, text)
        passage["attempts"].append(attempt)
        passage["current"] = number
        passage["reconsidered"] = True
    ctx.save_file(fs)
    return {"file": args.file, "pending": [passage["id"] for passage in selected], "reason": reason}


def cmd_record_chapter_checks(args):
    ctx = open_ctx(args)
    fs = ctx.load_file(args.file)
    sync_file(ctx, fs)
    fs["chapter_check_rounds"] += 1
    if args.note:
        fs["chapter_check_notes"].append(args.note)
    if args.issues == 0:
        fs["chapter_checks_rev"] = fs["revision"]
    ctx.save_file(fs)
    return {"file": fs["file"], "rounds": fs["chapter_check_rounds"],
            "checks_done": fs["chapter_checks_rev"] == fs["revision"]}


def cmd_finalize(args):
    ctx = open_ctx(args)
    fs = ctx.load_file(args.file)
    sync_file(ctx, fs)
    restored = []
    if fs["parity_ok"]:
        restored = restore_best(ctx, fs, pending_restores(ctx, fs, everything=True))
        ensure_gates(ctx, fs)
    final = final_record(ctx, fs)
    fs["final"], fs["finished"], fs["status"] = final, True, "finished"
    ctx.save_file(fs)
    return {"file": fs["file"], **{k: v for k, v in final.items() if k != "revision"},
            "restored": restored}


def cmd_status(args):
    ctx = open_ctx(args)
    names = [args.file] if args.file else ctx.pipeline["files"]
    return {"lang": ctx.lang, "models": ctx.pipeline["models"], "budget": ctx.pipeline["budget"],
            "files": [file_summary(ctx, ctx.load_file(n)) for n in names]}


def cmd_report(args):
    ctx = open_ctx(args)
    out = Path(args.out) if args.out else ctx.target / "reports" / "e2e-report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report(ctx), encoding="utf-8")
    return {"path": str(out)}


def cmd_allow_number(args):
    ctx = open_ctx(args)
    fs = ctx.load_file(args.file)
    entry = f"{args.file}:{args.value}"
    if entry not in ctx.pipeline["allow_numbers"]:
        ctx.pipeline["allow_numbers"].append(entry)
        ctx.save_pipeline()
    sync_file(ctx, fs)
    fs["gates"] = {"rev": None}
    ensure_gates(ctx, fs)
    ctx.save_file(fs)
    return {"file": args.file, "allow_numbers": ctx.pipeline["allow_numbers"],
            "gates_passed": fs["gates"].get("passed"),
            "failed": sorted(fs["gates"].get("failed", {}))}


def cmd_set_models(args):
    ctx = open_ctx(args)
    if args.translator_model:
        ctx.pipeline["models"]["translator"] = args.translator_model
    if args.judge_model:
        ctx.pipeline["models"]["judge"] = args.judge_model
    ctx.save_pipeline()
    return {"models": ctx.pipeline["models"]}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--workspace", help="translation workspace folder")
    common.add_argument("--lang", help="target language tag")
    common.add_argument("--state", help="path to pipeline.json (alternative to --workspace/--lang)")

    def add(name, func, help_text, parents=True):
        p = sub.add_parser(name, help=help_text, parents=[common] if parents else [])
        p.set_defaults(func=func)
        return p

    p = add("init", cmd_init, "create or update the workspace and the state files", parents=False)
    p.add_argument("--source", required=True)
    p.add_argument("--workspace", help="default: <source>/translation")
    p.add_argument("--lang", required=True)
    group = p.add_mutually_exclusive_group()
    group.add_argument("--glob", help="default: *.md")
    group.add_argument("--files", nargs="+")
    p.add_argument("--translator-model")
    p.add_argument("--judge-model")
    p.add_argument("--reset", action="store_true", help="discard the state and the saved attempts")
    for key, default in DEFAULT_CONFIG.items():
        flag = "--" + key.replace("_", "-")
        if key == "stagnation_escalate":
            p.add_argument(flag, nargs=2, type=int, metavar=("LOW", "HIGH"))
        else:
            p.add_argument(flag, type=float if key in FLOAT_KEYS else int)

    p = add("next", cmd_next, "sync with the manuscript, run the gates, return the next action")
    p.add_argument("--file", required=True)

    p = add("record-judgments", cmd_record_judgments, "apply the judge answers to the current sample")
    p.add_argument("--file", required=True)
    p.add_argument("--judgments", nargs="+", required=True)
    p.add_argument("--audit", action="store_true")

    p = add("reconsider", cmd_reconsider, "request one bounded rejudgment without changing the manuscript")
    p.add_argument("--file", required=True)
    p.add_argument("--passages", nargs="+", required=True)
    p.add_argument("--reason", required=True)

    p = add("record-chapter-checks", cmd_record_chapter_checks, "record one chapter-check round")
    p.add_argument("--file", required=True)
    p.add_argument("--issues", type=int, required=True)
    p.add_argument("--note")

    p = add("finalize", cmd_finalize, "restore the best attempts and close the file")
    p.add_argument("--file", required=True)

    p = add("status", cmd_status, "show per-file status")
    p.add_argument("--file")

    p = add("report", cmd_report, "write the final Markdown report")
    p.add_argument("--out")

    p = add("allow-number", cmd_allow_number, "waive a number in the numeric gate and rerun the gates")
    p.add_argument("--file", required=True)
    p.add_argument("--value", required=True)

    p = add("set-models", cmd_set_models, "record the translator and judge models")
    p.add_argument("--translator-model")
    p.add_argument("--judge-model")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        result = args.func(args)
    except (UsageError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
