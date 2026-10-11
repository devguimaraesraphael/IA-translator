import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mqm_score as m  # noqa: E402


def make_corpus(root, files=4, paras=12):
    src, tgt = Path(root) / "src", Path(root) / "tgt"
    src.mkdir()
    tgt.mkdir()
    for f in range(files):
        s, t = ["# title"], ["# title"]
        for i in range(paras):
            if i % 6 < 2:
                s.append(f"“Line {f}-{i} said the man.”")
                t.append(f"— Target line {f}-{i} said the man.")
            else:
                s.append(f"He walked along the road {f}-{i}.")
                t.append(f"Target: he walked along the road {f}-{i}.")
        (src / f"{f:03d}.md").write_text("\n\n".join(s), encoding="utf-8")
        (tgt / f"{f:03d}.md").write_text("\n\n".join(t), encoding="utf-8")
    return src, tgt


def sample_of(root, n=8, seed=1):
    src, tgt = make_corpus(root)
    windows, _ = m.build_windows(src, tgt, "*.md", 3, None)
    return {"seed": seed, "passages": m.stratified_sample(windows, n, seed)}


def judgment(sample, errors_by_id):
    return json.dumps([{"id": p["id"], "errors": errors_by_id.get(p["id"], [])} for p in sample["passages"]])


class SamplingTests(unittest.TestCase):
    def test_same_seed_same_sample(self):
        with tempfile.TemporaryDirectory() as d:
            a = sample_of(d, seed=7)["passages"]
        with tempfile.TemporaryDirectory() as d:
            b = sample_of(d, seed=7)["passages"]
        self.assertEqual([p["id"] for p in a], [p["id"] for p in b])

    def test_different_seed_changes_sample(self):
        with tempfile.TemporaryDirectory() as d:
            src, tgt = make_corpus(d, files=6, paras=30)
            windows, _ = m.build_windows(src, tgt, "*.md", 3, None)
            ids = {s: [p["id"] for p in m.stratified_sample(windows, 10, s)] for s in (1, 2)}
        self.assertNotEqual(ids[1], ids[2])

    def test_every_file_covered_and_types_mixed(self):
        with tempfile.TemporaryDirectory() as d:
            passages = sample_of(d, n=8)["passages"]
        self.assertEqual(len({p["file"] for p in passages}), 4)
        self.assertEqual(len(passages), 8)
        self.assertEqual({p["type"] for p in passages}, {"dialogue", "narration"})

    def test_mismatched_paragraph_counts_are_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            src, tgt = make_corpus(d, files=2)
            (tgt / "001.md").write_text("only one paragraph", encoding="utf-8")
            windows, skipped = m.build_windows(src, tgt, "*.md", 3, None)
        self.assertEqual([s["file"] for s in skipped], ["001.md"])
        self.assertTrue(all(w["file"] == "000.md" for w in windows))

    def test_embedded_pattern_marks_type(self):
        with tempfile.TemporaryDirectory() as d:
            src, tgt = make_corpus(d, files=1)
            import re
            windows, _ = m.build_windows(src, tgt, "*.md", 3, re.compile("road 0-2"))
        self.assertEqual(windows[0]["type"], "embedded")


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.sample = sample_of(self.tmp.name)
        self.ids = [p["id"] for p in self.sample["passages"]]

    def test_weights_and_formula(self):
        errors = {self.ids[0]: [{"c": "accuracy/omission", "s": "major", "n": "x"},
                                {"c": "fluency/grammar", "s": "minor", "n": "y"}],
                  self.ids[1]: [{"c": "accuracy/mistranslation", "s": "critical", "n": "z"}]}
        report = m.evaluate(self.sample, [judgment(self.sample, errors)])
        self.assertEqual(report["penalty"], 16)
        expected = 100 - 16 / report["words_evaluated"] * 100
        self.assertAlmostEqual(report["score"], expected)

    def test_clean_judgment_scores_100(self):
        report = m.evaluate(self.sample, [judgment(self.sample, {})])
        self.assertEqual(report["score"], 100)
        self.assertEqual(report["coverage"], 1)

    def test_unreadable_judgment_is_excluded_not_clean(self):
        good = json.dumps([{"id": self.ids[0], "errors": [{"c": "style/voice", "s": "major", "n": ""}]}])
        report = m.evaluate(self.sample, [good, "sorry, I cannot do that"])
        self.assertEqual(report["passages_evaluated"], 1)
        self.assertEqual(report["stats"]["unreadable_files"], 1)
        self.assertEqual(len(report["excluded_ids"]), len(self.ids) - 1)
        self.assertLess(report["score"], 100)

    def test_invalid_category_excludes_passage(self):
        bad = json.dumps([{"id": self.ids[0], "errors": [{"c": "made/up", "s": "minor", "n": ""}]}])
        report = m.evaluate(self.sample, [bad])
        self.assertEqual(report["passages_evaluated"], 0)
        self.assertEqual(report["stats"]["invalid_entries"], 1)

    def test_nothing_evaluated_fails_without_score(self):
        sample_path = Path(self.tmp.name) / "sample.json"
        sample_path.write_text(json.dumps(self.sample), encoding="utf-8")
        bad = Path(self.tmp.name) / "bad.json"
        bad.write_text("not json at all", encoding="utf-8")
        self.assertEqual(m.main(["score", "--sample", str(sample_path), "--judgments", str(bad)]), 1)

    def test_code_fence_and_leading_text(self):
        body = judgment(self.sample, {})
        text = f"Here is my evaluation [see below]:\n```json\n{body}\n```\nDone."
        self.assertEqual(len(m.extract_array(text)), len(self.ids))

    def test_partial_coverage_warns(self):
        sample_path = Path(self.tmp.name) / "sample.json"
        sample_path.write_text(json.dumps(self.sample), encoding="utf-8")
        part = Path(self.tmp.name) / "part.json"
        part.write_text(json.dumps([{"id": self.ids[0], "errors": []}]), encoding="utf-8")
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = m.main(["score", "--sample", str(sample_path), "--judgments", str(part),
                           "--model-translator", "a", "--model-judge", "A"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("same model", out)
        self.assertIn("evaluated", out)
        self.assertIn("< 80%", out)

    def test_compare_reports_absolute_difference(self):
        sample_path = Path(self.tmp.name) / "sample.json"
        sample_path.write_text(json.dumps(self.sample), encoding="utf-8")
        a = Path(self.tmp.name) / "a.json"
        b = Path(self.tmp.name) / "b.json"
        a.write_text(judgment(self.sample, {}), encoding="utf-8")
        b.write_text(judgment(self.sample, {self.ids[0]: [{"c": "style/voice", "s": "major", "n": ""}]}),
                     encoding="utf-8")
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = m.main(["compare", "--sample", str(sample_path), "--run1", str(a), "--run2", str(b)])
        self.assertEqual(code, 0)
        run1, run2 = m.evaluate(self.sample, [a.read_text()]), m.evaluate(self.sample, [b.read_text()])
        self.assertIn(f"difference: {abs(run1['score'] - run2['score']):.1f}", buf.getvalue())


class PromptTests(unittest.TestCase):
    def test_batches_written(self):
        with tempfile.TemporaryDirectory() as d:
            sample = sample_of(d)
            path = Path(d) / "sample.json"
            path.write_text(json.dumps(sample), encoding="utf-8")
            out = Path(d) / "out"
            self.assertEqual(m.main(["prompt", "--sample", str(path), "--batch", "3", "--outdir", str(out)]), 0)
            files = sorted(out.glob("batch-*.md"))
            self.assertEqual(len(files), 3)
            self.assertIn(sample["passages"][0]["id"], files[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
