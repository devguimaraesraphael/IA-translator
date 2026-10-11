import argparse
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translation_gates as tg  # noqa: E402

# Targets are Portuguese fixtures: the gates compare an English source with a non-English target.
LONG_SRC = (
    "The weather turned bitter overnight and everyone gathered around the kitchen "
    "table waiting for morning to arrive."
)
LONG_TGT = (
    "O tempo azedou durante a noite e todos se reuniram em torno da mesa "
    "da cozinha esperando a manhã chegar."
)

GLOSSARY = """# Glossary

| Source term | Meaning or function | Target form | Policy |
| --- | --- | --- | --- |
| Alice Hart | Father | Alice Hart | Preserve |
| Alice | Given name | Alice | Preserve |
| the Minch | Sea channel | o Minch | Translate |
| smirr | Drizzle | smirr | Preserve regional texture |
| oxters | Armpits | TO DECIDE | Preserve |
| Ghost Term | Never appears | Ghost Term | Preserve |
| TO ADD | TO ADD | TO DECIDE | Preserve / Translate |
"""


class Workspace:
    def __init__(self, test: unittest.TestCase):
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.src = root / "src"
        self.tgt = root / "tgt"
        self.src.mkdir()
        self.tgt.mkdir()
        self.glossary = root / "glossary.md"

    def write(self, name, source=None, target=None):
        if source is not None:
            (self.src / name).write_text(source, encoding="utf-8")
        if target is not None:
            (self.tgt / name).write_text(target, encoding="utf-8")

    def run(self, **overrides):
        args = argparse.Namespace(
            source=str(self.src),
            target=str(self.tgt),
            glossary=str(self.glossary) if self.glossary.exists() else None,
            glob="*.md",
            strict=False,
            json=False,
            heading_tolerance=0,
            para_tolerance=0,
            allow_number=[],
            overlap=0.8,
            min_content_words=6,
            min_ratio=0.4,
            end_chars=tg.DEFAULT_END_CHARS,
            max_examples=10,
        )
        for k, v in overrides.items():
            setattr(args, k, v)
        results, _ = tg.run(args)
        return {r.gate: r for r in results}


class PairingTests(unittest.TestCase):
    def test_passes_when_names_match(self):
        w = Workspace(self)
        w.write("a.md", "# T\n\nHello.", "# T\n\nOlá.")
        self.assertEqual(w.run()["G1"].findings, [])

    def test_fails_on_missing_and_extra(self):
        w = Workspace(self)
        w.write("a.md", "# T\n\nHello.", None)
        w.write("b.md", None, "# T\n\nOlá.")
        g1 = w.run()["G1"]
        self.assertTrue(g1.failed)
        self.assertEqual(len(g1.findings), 2)


class StructureTests(unittest.TestCase):
    def test_passes_with_same_structure(self):
        w = Workspace(self)
        w.write("a.md", "# T\n\nOne.\n\nTwo.", "# U\n\nUm.\n\nDois.")
        self.assertEqual(w.run()["G2"].findings, [])

    def test_fails_on_skipped_paragraph_and_skips_g4(self):
        w = Workspace(self)
        w.write("a.md", f"# T\n\n{LONG_SRC}\n\nTwo.", f"# T\n\n{LONG_SRC}")
        res = w.run()
        self.assertTrue(res["G2"].failed)
        self.assertIn("paragraphs 2 -> 1", res["G2"].findings[0])
        self.assertEqual(res["G4"].findings, [])
        self.assertTrue(any("a.md" in n for n in res["G4"].notes))

    def test_tolerance_allows_difference(self):
        w = Workspace(self)
        w.write("a.md", "# T\n\nOne.\n\nTwo.", "# T\n\nUm.")
        self.assertEqual(w.run(para_tolerance=1)["G2"].findings, [])


class NumberTests(unittest.TestCase):
    def test_equivalent_separators_pass(self):
        w = Workspace(self)
        w.write("a.md", "Paid 1,000 in 1999 and 3.5 more.", "Pagou 1.000 em 1999 e 3,5 mais.")
        self.assertEqual(w.run()["G3"].findings, [])

    def test_changed_number_fails(self):
        w = Workspace(self)
        w.write("a.md", "In 1999 he paid 1,000.", "Em 1998 ele pagou 1.000.")
        g3 = w.run()["G3"]
        self.assertTrue(g3.failed)
        self.assertIn("1999", g3.findings[0])

    def test_clock_conversion_12h_to_24h_passes(self):
        # Portuguese target writes times in 24h style (20h, 19h05).
        w = Workspace(self)
        w.write("a.md", "At 8 p.m. and again at 7.05 p.m.", "Às 20h e de novo às 19h05.")
        self.assertEqual(w.run()["G3"].findings, [])

    def test_wrong_clock_time_fails(self):
        w = Workspace(self)
        w.write("a.md", "At 8 p.m. he left.", "Às 19h ele saiu.")
        self.assertTrue(w.run()["G3"].failed)

    def test_allow_number_waives_inspected_difference(self):
        w = Workspace(self)
        w.write("a.md", "He had 4 cats.", "Ele tinha quatro gatos.")
        self.assertTrue(w.run()["G3"].failed)
        g3 = w.run(allow_number=["a.md:4"])["G3"]
        self.assertEqual(g3.findings, [])
        self.assertTrue(g3.notes)

    def test_spelled_out_numbers_ignored(self):
        w = Workspace(self)
        w.write("a.md", "He had twenty sheep.", "Ele tinha vinte ovelhas.")
        self.assertEqual(w.run()["G3"].findings, [])


class UntranslatedTests(unittest.TestCase):
    def test_translated_paragraph_passes(self):
        w = Workspace(self)
        w.write("a.md", f"# T\n\n{LONG_SRC}", f"# T\n\n{LONG_TGT}")
        self.assertEqual(w.run()["G4"].findings, [])

    def test_identical_paragraph_warns_but_does_not_gate(self):
        w = Workspace(self)
        w.write("a.md", f"# T\n\n{LONG_SRC}", f"# T\n\n{LONG_SRC}")
        g4 = w.run()["G4"]
        self.assertEqual(len(g4.findings), 1)
        self.assertFalse(g4.failed)

    def test_strict_makes_it_gate(self):
        w = Workspace(self)
        w.write("a.md", f"# T\n\n{LONG_SRC}", f"# T\n\n{LONG_SRC}")
        self.assertTrue(w.run(strict=True)["G4"].failed)

    def test_short_paragraph_below_floor_not_accused(self):
        w = Workspace(self)
        w.write("a.md", "# T\n\nCiamar a tha thu.", "# T\n\nCiamar a tha thu.")
        self.assertEqual(w.run()["G4"].findings, [])

    def test_preserved_terms_do_not_count_toward_floor(self):
        w = Workspace(self)
        w.glossary.write_text(
            "| Source term | Meaning or function | Target form | Policy |\n"
            "| --- | --- | --- | --- |\n"
            "| Ciamar a tha thu an-diugh | Greeting | Ciamar a tha thu an-diugh | Preserve |\n",
            encoding="utf-8",
        )
        text = "Ciamar a tha thu an-diugh Ciamar a tha thu an-diugh"
        w.write("a.md", f"# T\n\n{text}", f"# T\n\n{text}")
        self.assertEqual(w.run()["G4"].findings, [])


class TruncationTests(unittest.TestCase):
    def test_complete_target_passes(self):
        w = Workspace(self)
        w.write("a.md", f"# T\n\n{LONG_SRC}", f"# T\n\n{LONG_TGT}")
        self.assertEqual(w.run()["G5"].findings, [])

    def test_missing_final_punctuation_warns(self):
        w = Workspace(self)
        w.write("a.md", f"# T\n\n{LONG_SRC}", f"# T\n\n{LONG_TGT.rstrip('.')}")
        g5 = w.run()["G5"]
        self.assertEqual(len(g5.findings), 1)
        self.assertFalse(g5.failed)

    def test_short_target_warns(self):
        w = Workspace(self)
        w.write("a.md", f"# T\n\n{LONG_SRC}", "# T\n\nO tempo azedou.")
        self.assertIn("words", w.run()["G5"].findings[0])


class GlossaryMatchTests(unittest.TestCase):
    def test_word_boundaries(self):
        v = [tg.compile_variant("cal", True)]
        counts, _ = tg.scan("Cal's calm cal. cal", v)
        self.assertEqual(counts["cal"], 2)

    def test_unicode_boundaries(self):
        v = [tg.compile_variant("são", False)]
        counts, _ = tg.scan("são sãos São", v)
        self.assertEqual(counts["são"], 2)

    def test_longest_term_first(self):
        variants = [tg.compile_variant("Alice", True), tg.compile_variant("Alice Hart", True)]
        counts, _ = tg.scan("Alice Hart met Alice", variants)
        self.assertEqual(counts["Alice Hart"], 1)
        self.assertEqual(counts["Alice"], 1)

    def test_case_sensitivity_only_for_capitalised_terms(self):
        w = Workspace(self)
        w.glossary.write_text(GLOSSARY, encoding="utf-8")
        g = tg.parse_glossary(w.glossary)
        by_label = {r.label: r for r in g.rows}
        self.assertTrue(by_label["Alice Hart"].source_variants[0].case_sensitive)
        self.assertFalse(by_label["smirr"].source_variants[0].case_sensitive)

    def test_parser_ignores_placeholders_and_undecided(self):
        w = Workspace(self)
        w.glossary.write_text(GLOSSARY, encoding="utf-8")
        g = tg.parse_glossary(w.glossary)
        self.assertEqual(g.total_rows, 7)
        self.assertEqual(g.ignored["TO DECIDE/TO ADD"], 2)

    def test_preserve_missing_warns(self):
        w = Workspace(self)
        w.glossary.write_text(GLOSSARY, encoding="utf-8")
        w.write("a.md", "Alice Hart waited.", "O pai esperou.")
        g6 = w.run()["G6"]
        self.assertTrue(any("Alice Hart" in f for f in g6.findings))
        self.assertFalse(g6.failed)
        self.assertTrue(w.run(strict=True)["G6"].failed)

    def test_longer_preserve_term_does_not_trigger_shorter(self):
        w = Workspace(self)
        w.glossary.write_text(GLOSSARY, encoding="utf-8")
        w.write("a.md", "Alice Hart waited.", "Alice Hart esperou.")
        self.assertEqual(w.run()["G6"].findings, [])

    def test_translate_target_form_missing_warns(self):
        w = Workspace(self)
        w.glossary.write_text(GLOSSARY, encoding="utf-8")
        w.write("a.md", "Across the Minch it rained.", "Do outro lado do canal choveu.")
        self.assertTrue(any("Translate" in f for f in w.run()["G6"].findings))

    def test_translate_target_form_present_passes(self):
        w = Workspace(self)
        w.glossary.write_text(GLOSSARY, encoding="utf-8")
        w.write("a.md", "Across the Minch it rained.", "Além, o Minch choveu.")
        self.assertEqual(w.run()["G6"].findings, [])

    def test_zero_match_rule_is_reported(self):
        w = Workspace(self)
        w.glossary.write_text(GLOSSARY, encoding="utf-8")
        w.write("a.md", "Alice Hart waited.", "Alice Hart esperou.")
        g6 = w.run()["G6"]
        self.assertIn("Ghost Term", g6.stats["zero_match_terms"])
        self.assertTrue(any("matched 0 times" in n for n in g6.notes))

    def test_without_glossary_g6_is_skipped(self):
        w = Workspace(self)
        w.write("a.md", "Hello.", "Olá.")
        self.assertIsNotNone(w.run()["G6"].skipped)


class CliTests(unittest.TestCase):
    def test_exit_codes(self):
        w = Workspace(self)
        w.write("a.md", "In 1999 it ended.", "Em 1999 acabou.")
        base = ["--source", str(w.src), "--target", str(w.tgt)]
        with redirect_stdout(io.StringIO()):
            self.assertEqual(tg.main(base), 0)
            w.write("a.md", None, "Em 1998 acabou.")
            self.assertEqual(tg.main(base), 1)

    def test_json_output_is_valid(self):
        w = Workspace(self)
        w.write("a.md", "Hello.", "Olá.")
        buf = io.StringIO()
        with redirect_stdout(buf):
            tg.main(["--source", str(w.src), "--target", str(w.tgt), "--json"])
        self.assertTrue(json.loads(buf.getvalue())["passed"])


if __name__ == "__main__":
    unittest.main()
