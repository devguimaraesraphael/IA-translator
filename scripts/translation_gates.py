#!/usr/bin/env python3
"""Check a Markdown translation (one file per chapter) against its source.

Report only: never edits, deletes or retranslates files. Exit code 1 if any GATE fails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

HEADING_RE = re.compile(r"^\s{0,3}#{1,6}(\s|$)")
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")
# 12-hour source times (6 p.m., 7.05 pm) and 24-hour target times (18h, 19h05, Portuguese style) map to one token.
TIME_12H_RE = re.compile(r"(?<![\d.,])(\d{1,2})(?:[.:](\d{2}))?\s*([ap])\.?\s?m\b\.?", re.IGNORECASE)
TIME_24H_RE = re.compile(r"(?<![\d.,])(\d{1,2})h(?:(\d{2}))?(?:min)?(?!\w)")
WORD_RE = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*", re.UNICODE)
PLACEHOLDER_RE = re.compile(r"TO\s+(DECIDE|ADD)", re.IGNORECASE)
DEFAULT_END_CHARS = ".!?…\"”’»')]—–"
MIN_WORD_LEN = 4

GATE_NAMES = {
    "G1": "file pairing",
    "G2": "structural parity",
    "G3": "numeric integrity",
    "G4": "untranslated source text",
    "G5": "truncation",
    "G6": "glossary",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return (
        text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def split_blocks(text: str) -> tuple[list[str], list[str]]:
    """Return (headings, paragraphs) from the non-empty lines."""
    headings: list[str] = []
    paragraphs: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        (headings if HEADING_RE.match(line) else paragraphs).append(line.strip())
    return headings, paragraphs


def canonical_number(raw: str) -> str:
    parts = re.split(r"[.,]", raw)
    if len(parts) == 1:
        return parts[0]
    if len(parts[-1]) == 3 and all(len(p) == 3 for p in parts[1:]):
        return "".join(parts)
    return "".join(parts[:-1]) + "." + parts[-1]


def numbers_in(text: str) -> Counter:
    tokens: Counter = Counter()

    def take_12h(m: re.Match) -> str:
        hour = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "p" else 0)
        tokens[f"T{hour:02d}:{m.group(2) or '00'}"] += 1
        return " "

    def take_24h(m: re.Match) -> str:
        tokens[f"T{int(m.group(1)):02d}:{m.group(2) or '00'}"] += 1
        return " "

    text = TIME_12H_RE.sub(take_12h, text)
    text = TIME_24H_RE.sub(take_24h, text)
    tokens.update(canonical_number(m) for m in NUMBER_RE.findall(text))
    return tokens


def content_words(text: str) -> list[str]:
    return [w for w in (m.casefold() for m in WORD_RE.findall(text)) if len(w) >= MIN_WORD_LEN]


@dataclass
class Variant:
    text: str
    case_sensitive: bool
    regex: re.Pattern


def compile_variant(term: str, case_sensitive: bool, left_only: bool = False) -> Variant:
    norm = normalize(term)
    tail = "" if left_only else r"(?!\w)"
    flags = 0 if case_sensitive else re.IGNORECASE
    return Variant(norm, case_sensitive, re.compile(r"(?<!\w)" + re.escape(norm) + tail, flags))


def scan(text: str, variants: list[Variant]) -> tuple[Counter, list[tuple[int, int]]]:
    """Count matches longest term first; already matched spans are not reused."""
    taken = bytearray(len(text))
    counts: Counter = Counter()
    spans: list[tuple[int, int]] = []
    for v in sorted(variants, key=lambda x: len(x.text), reverse=True):
        for m in v.regex.finditer(text):
            if any(taken[m.start():m.end()]):
                continue
            taken[m.start():m.end()] = b"\x01" * (m.end() - m.start())
            counts[v.text] += 1
            spans.append((m.start(), m.end()))
    return counts, spans


def blank_spans(text: str, spans: list[tuple[int, int]]) -> str:
    chars = list(text)
    for a, b in spans:
        for i in range(a, b):
            chars[i] = " "
    return "".join(chars)


@dataclass
class GlossaryRow:
    source_variants: list[Variant]
    target_forms: list[str]
    policy: str
    label: str


@dataclass
class Glossary:
    rows: list[GlossaryRow] = field(default_factory=list)
    ignored: Counter = field(default_factory=Counter)
    total_rows: int = 0

    @property
    def preserve_variants(self) -> list[Variant]:
        return [v for r in self.rows if r.policy == "preserve" for v in r.source_variants]


def split_cells(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in re.split(r"(?<!\\)\|", inner)]


def split_alternatives(cell: str) -> list[str]:
    return [p.strip() for p in cell.split(" / ") if p.strip()]


def is_capitalized_term(term: str) -> bool:
    return any(ch.isupper() for ch in term)


def parse_glossary(path: Path) -> Glossary:
    glossary = Glossary()
    in_table = False
    for line in read_text(path).splitlines():
        if not line.strip().startswith("|"):
            in_table = False
            continue
        cells = split_cells(line)
        lowered = [c.lower() for c in cells]
        if not in_table:
            in_table = "source term" in lowered and "policy" in lowered
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        if len(cells) < 4:
            continue
        src, _meaning, target, policy = cells[0], cells[1], cells[2], cells[3]
        glossary.total_rows += 1
        if (
            PLACEHOLDER_RE.search(src)
            or PLACEHOLDER_RE.search(policy)
            or PLACEHOLDER_RE.search(target)
        ):
            glossary.ignored["TO DECIDE/TO ADD"] += 1
            continue
        kind = policy.lower()
        if kind.startswith("preserve"):
            kind = "preserve"
        elif kind.startswith("translate"):
            kind = "translate"
        else:
            glossary.ignored["non-binary policy"] += 1
            continue
        if kind == "translate" and not target:
            glossary.ignored["TO DECIDE/TO ADD"] += 1
            continue
        force_case = "case-sensitive" in policy.lower()
        variants = [
            compile_variant(t, force_case or is_capitalized_term(t))
            for t in split_alternatives(src)
        ]
        if not variants:
            continue
        glossary.rows.append(
            GlossaryRow(variants, split_alternatives(target), kind, src)
        )
    return glossary


@dataclass
class Pair:
    name: str
    source: str
    target: str


@dataclass
class GateResult:
    gate: str
    kind: str
    findings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    skipped: str | None = None
    stats: dict = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        return self.kind == "GATE" and bool(self.findings)


def gate_pairing(src_names: set[str], tgt_names: set[str]) -> GateResult:
    r = GateResult("G1", "GATE")
    for n in sorted(src_names - tgt_names):
        r.findings.append(f"{n}: no matching target file")
    for n in sorted(tgt_names - src_names):
        r.findings.append(f"{n}: target file without a matching source")
    r.stats = {"source_files": len(src_names), "target_files": len(tgt_names)}
    return r


def gate_structure(pairs: list[Pair], head_tol: int, para_tol: int) -> tuple[GateResult, set[str]]:
    r = GateResult("G2", "GATE")
    bad: set[str] = set()
    for p in pairs:
        sh, sp = split_blocks(p.source)
        th, tp = split_blocks(p.target)
        issues = []
        if abs(len(sh) - len(th)) > head_tol:
            issues.append(f"headings {len(sh)} -> {len(th)}")
        if abs(len(sp) - len(tp)) > para_tol:
            issues.append(f"paragraphs {len(sp)} -> {len(tp)}")
        if issues:
            bad.add(p.name)
            r.findings.append(f"{p.name}: " + "; ".join(issues))
    return r, bad


def gate_numbers(pairs: list[Pair], allowed: dict[str, set[str]]) -> GateResult:
    r = GateResult("G3", "GATE")
    for p in pairs:
        s, t = numbers_in(p.source), numbers_in(p.target)
        waived = allowed.get(p.name, set())
        missing = Counter({k: v for k, v in (s - t).items() if k not in waived})
        extra = Counter({k: v for k, v in (t - s).items() if k not in waived})
        if waived and (s - t or t - s):
            r.notes.append(f"{p.name}: numbers waived via --allow-number: {', '.join(sorted(waived))}")
        if missing or extra:
            parts = []
            if missing:
                parts.append("missing from target: " + ", ".join(sorted(missing.elements())[:8]))
            if extra:
                parts.append("extra in target: " + ", ".join(sorted(extra.elements())[:8]))
            r.findings.append(f"{p.name}: " + "; ".join(parts))
    return r


def gate_untranslated(
    pairs: list[Pair],
    skip: set[str],
    preserve: list[Variant],
    kind: str,
    threshold: float,
    min_words: int,
) -> GateResult:
    r = GateResult("G4", kind)
    if skip:
        r.notes.append(
            f"skipped in {len(skip)} file(s) due to parity failure (G2): "
            + ", ".join(sorted(skip)[:10])
        )
    for p in pairs:
        if p.name in skip:
            continue
        sp = split_blocks(p.source)[1]
        tp = split_blocks(p.target)[1]
        for i, (s_par, t_par) in enumerate(zip(sp, tp), start=1):
            s_clean = _strip_preserved(normalize(s_par), preserve)
            t_clean = _strip_preserved(normalize(t_par), preserve)
            t_words = content_words(t_clean)
            if len(t_words) < min_words:
                continue
            s_set = set(content_words(s_clean))
            overlap = sum(1 for w in t_words if w in s_set) / len(t_words)
            if overlap >= threshold:
                snippet = t_par[:50] + ("…" if len(t_par) > 50 else "")
                r.findings.append(
                    f"{p.name} §{i}: overlap {overlap:.2f} with source "
                    f"({len(t_words)} words) \"{snippet}\""
                )
    return r


def _strip_preserved(text: str, preserve: list[Variant]) -> str:
    if not preserve:
        return text
    _, spans = scan(text, preserve)
    return blank_spans(text, spans)


def last_body_line(text: str) -> str:
    paragraphs = split_blocks(text)[1]
    return paragraphs[-1] if paragraphs else ""


def gate_truncation(pairs: list[Pair], min_ratio: float, end_chars: str) -> GateResult:
    r = GateResult("G5", "WARN")
    for p in pairs:
        issues = []
        s_end = last_body_line(p.source).rstrip().rstrip("*_~ ")
        t_end = last_body_line(p.target).rstrip().rstrip("*_~ ")
        if s_end and s_end[-1] in end_chars and (not t_end or t_end[-1] not in end_chars):
            issues.append(f"ends without final punctuation ('…{t_end[-20:]}')")
        s_words = len(re.findall(r"\w+", p.source))
        t_words = len(re.findall(r"\w+", p.target))
        if s_words and t_words / s_words < min_ratio:
            issues.append(f"{t_words}/{s_words} words ({t_words / s_words:.0%} of source)")
        if issues:
            r.findings.append(f"{p.name}: " + "; ".join(issues))
    return r


def gate_glossary(pairs: list[Pair], glossary: Glossary, kind: str) -> GateResult:
    r = GateResult("G6", kind)
    preserve_rows = [row for row in glossary.rows if row.policy == "preserve"]
    translate_rows = [row for row in glossary.rows if row.policy == "translate"]
    all_variants = [v for row in glossary.rows for v in row.source_variants]
    preserve_variants = [v for row in preserve_rows for v in row.source_variants]
    total_hits: Counter = Counter()
    forms_cache: dict[int, list[Variant]] = {}

    for p in pairs:
        s_text, t_text = normalize(p.source), normalize(p.target)
        s_counts, _ = scan(s_text, all_variants)
        total_hits.update(s_counts)
        t_counts, _ = scan(t_text, preserve_variants)
        for row in preserve_rows:
            for v in row.source_variants:
                if s_counts[v.text] and not t_counts[v.text]:
                    r.findings.append(
                        f"{p.name}: Preserve term missing '{v.text}' (source {s_counts[v.text]}x, target 0x)"
                    )
        for row in translate_rows:
            if not any(s_counts[v.text] for v in row.source_variants):
                continue
            forms = forms_cache.setdefault(
                id(row),
                [compile_variant(f, is_capitalized_term(f), left_only=True) for f in row.target_forms],
            )
            if not any(f.regex.search(t_text) for f in forms):
                r.findings.append(
                    f"{p.name}: Translate '{row.label}' lacks the target form "
                    f"({' / '.join(row.target_forms)})"
                )

    zero = [
        row.label
        for row in glossary.rows
        if not any(total_hits[v.text] for v in row.source_variants)
    ]
    ignored = sum(glossary.ignored.values())
    r.stats = {
        "rows_total": glossary.total_rows,
        "rows_used": len(glossary.rows),
        "rows_ignored": ignored,
        "ignored_reasons": dict(glossary.ignored),
        "zero_match_terms": zero,
    }
    r.notes.append(
        f"{len(glossary.rows)} rule(s) used, {ignored} ignored "
        f"({', '.join(f'{k}: {v}' for k, v in glossary.ignored.items()) or 'none'})"
    )
    r.notes.append(f"{len(zero)} used rule(s) matched 0 times in the source")
    if zero:
        r.notes.append("no occurrence in source: " + "; ".join(zero[:10]))
    return r


def parse_allowed(entries: list[str]) -> dict[str, set[str]]:
    allowed: dict[str, set[str]] = {}
    for entry in entries:
        name, _, value = entry.partition(":")
        if not name or not value:
            raise SystemExit(f"invalid --allow-number (use file.md:value): {entry}")
        allowed.setdefault(name, set()).add(canonical_number(value))
    return allowed


def run(args: argparse.Namespace) -> tuple[list[GateResult], dict]:
    src_dir, tgt_dir = Path(args.source), Path(args.target)
    src_files = {p.name: p for p in sorted(src_dir.glob(args.glob)) if p.is_file()}
    tgt_files = {p.name: p for p in sorted(tgt_dir.glob(args.glob)) if p.is_file()}
    if not src_files:
        raise SystemExit(f"No source file matched '{args.glob}' in {src_dir}")

    pairs = [
        Pair(n, read_text(src_files[n]), read_text(tgt_files[n]))
        for n in src_files
        if n in tgt_files
    ]
    soft_kind = "GATE" if args.strict else "WARN"
    results = [gate_pairing(set(src_files), set(tgt_files))]
    g2, bad = gate_structure(pairs, args.heading_tolerance, args.para_tolerance)
    results.append(g2)
    results.append(gate_numbers(pairs, parse_allowed(args.allow_number)))

    glossary = parse_glossary(Path(args.glossary)) if args.glossary else None
    preserve = glossary.preserve_variants if glossary else []
    results.append(
        gate_untranslated(pairs, bad, preserve, soft_kind, args.overlap, args.min_content_words)
    )
    results.append(gate_truncation(pairs, args.min_ratio, args.end_chars))
    if glossary:
        results.append(gate_glossary(pairs, glossary, soft_kind))
    else:
        g6 = GateResult("G6", soft_kind, skipped="no --glossary")
        results.append(g6)
    meta = {
        "source": str(src_dir),
        "target": str(tgt_dir),
        "glossary": args.glossary,
        "source_files": len(src_files),
        "paired_files": len(pairs),
        "strict": args.strict,
    }
    return results, meta


def render_text(results: list[GateResult], meta: dict, max_examples: int) -> str:
    out = [
        f"Source: {meta['source']} ({meta['source_files']} files) | "
        f"Target: {meta['target']} | paired: {meta['paired_files']} | "
        f"Glossary: {meta['glossary'] or '-'}"
    ]
    for r in results:
        if r.skipped:
            status = f"SKIPPED ({r.skipped})"
        elif r.findings:
            status = f"{'FAIL' if r.kind == 'GATE' else 'WARN'} ({len(r.findings)} findings)"
        else:
            status = "OK"
        out.append(f"[{r.kind:<5}] {r.gate} {GATE_NAMES[r.gate]}: {status}")
        for note in r.notes:
            out.append(f"    * {note}")
        for f in r.findings[:max_examples]:
            out.append(f"    - {f}")
        if len(r.findings) > max_examples:
            out.append(f"    ... +{len(r.findings) - max_examples} findings (use --json)")
    failed = [r.gate for r in results if r.failed]
    out.append("Result: " + (f"FAILED ({', '.join(failed)})" if failed else "PASSED (warnings do not gate)"))
    return "\n".join(out)


def render_json(results: list[GateResult], meta: dict) -> str:
    gates = {
        r.gate: {
            "name": GATE_NAMES[r.gate],
            "kind": r.kind,
            "status": "skipped" if r.skipped else ("fail" if r.failed else ("warn" if r.findings else "ok")),
            "skipped_reason": r.skipped,
            "finding_count": len(r.findings),
            "findings": r.findings,
            "notes": r.notes,
            "stats": r.stats,
        }
        for r in results
    }
    payload = {"meta": meta, "passed": not any(r.failed for r in results), "gates": gates}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True, type=_dir, help="folder with the source chapters")
    p.add_argument("--target", required=True, type=_dir, help="folder with the translated chapters")
    p.add_argument("--glossary", type=_file, help="glossary in Markdown")
    p.add_argument("--glob", default="*.md", help="file pattern (default: *.md)")
    p.add_argument("--strict", action="store_true", help="G4 and G6 become gating")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--heading-tolerance", type=int, default=0)
    p.add_argument("--para-tolerance", type=int, default=0)
    p.add_argument(
        "--allow-number", action="append", default=[], metavar="FILE:VALUE",
        help="waive a number already inspected and justified in a file (repeatable)",
    )
    p.add_argument("--overlap", type=float, default=0.8, help="G4 threshold")
    p.add_argument("--min-content-words", type=int, default=6, help="G4 minimum content words")
    p.add_argument("--min-ratio", type=float, default=0.4, help="G5 minimum word ratio")
    p.add_argument("--end-chars", default=DEFAULT_END_CHARS, help="G5 accepted ending characters")
    p.add_argument("--max-examples", type=int, default=10)
    return p


def _dir(value: str) -> str:
    if not Path(value).is_dir():
        raise argparse.ArgumentTypeError(f"folder does not exist: {value}")
    return value


def _file(value: str) -> str:
    if not Path(value).is_file():
        raise argparse.ArgumentTypeError(f"file does not exist: {value}")
    return value


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results, meta = run(args)
    print(render_json(results, meta) if args.json else render_text(results, meta, args.max_examples))
    return 1 if any(r.failed for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
