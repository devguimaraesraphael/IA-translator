import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_controller as ec  # noqa: E402
import mqm_score  # noqa: E402

SRC_ONE = """# Chapter One

The weather turned bitter overnight and everyone gathered around the kitchen table.

"Is the kettle on?" asked Morag, without looking up from the cold hearth.

She counted 1847 stones along the old wall behind the house.

Nobody answered her for a long while after the question was asked.

The tide went out before dawn and left the shingle shining like tin.

A single gull stood on the roof and watched the empty road below.
"""

TGT_ONE = """# Capítulo Um

O tempo azedou durante a noite e todos se reuniram em torno da mesa da cozinha.

"A chaleira está no fogo?", perguntou Morag, sem tirar os olhos da lareira fria.

Ela contou 1847 pedras ao longo do velho muro atrás da casa.

Ninguém lhe respondeu por um bom tempo depois que a pergunta foi feita.

A maré baixou antes do amanhecer e deixou o cascalho brilhando como estanho.

Uma única gaivota pousou no telhado e observou a estrada vazia lá embaixo.
"""

SRC_TWO = """# Chapter Two

The boat left the harbour at first light with three men and a dog aboard.

Nobody spoke until the headland had disappeared behind the grey water.
"""

TGT_TWO = """# Capítulo Dois

O barco deixou o porto ao primeiro clarão com três homens e um cão a bordo.

Ninguém falou até o promontório desaparecer atrás da água cinzenta.
"""

ONE, TWO = "01-one.md", "02-two.md"
WORDS = ["alfa", "beta", "gama", "delta", "epsilon"]
MINOR = {"c": "fluency/grammar", "s": "minor", "n": "typo"}
MAJOR = {"c": "accuracy/mistranslation", "s": "major", "n": "wrong meaning"}


class Env:
    def __init__(self, test, *init_flags, translate=True):
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.src = self.root / "src"
        self.src.mkdir()
        (self.src / ONE).write_text(SRC_ONE, encoding="utf-8")
        (self.src / TWO).write_text(SRC_TWO, encoding="utf-8")
        self.ws = self.src / "translation"
        self.tdir = self.ws / "targets" / "pt-BR"
        self.test = test
        flags = ["--window", "2", "--max-retranslations", "2", "--audit-fraction", "0", *init_flags]
        self.cli("init", "--source", str(self.src), "--lang", "pt-BR", "--glob", "*.md", *flags, scoped=False)
        if translate:
            self.write(ONE, TGT_ONE)
            self.write(TWO, TGT_TWO)

    def cli(self, *argv, scoped=True):
        args = list(argv)
        if scoped:
            args += ["--workspace", str(self.ws), "--lang", "pt-BR"]
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = ec.main(args)
        return code, json.loads(buf.getvalue())

    def ok(self, *argv):
        code, data = self.cli(*argv)
        self.test.assertEqual(code, 0, data)
        return data

    def nxt(self, name):
        return self.ok("next", "--file", name)

    def path(self, name):
        return self.tdir / "manuscript" / name

    def write(self, name, text):
        self.path(name).write_text(text, encoding="utf-8")

    def state(self, name):
        return json.loads((self.tdir / "state" / f"{Path(name).stem}.json").read_text(encoding="utf-8"))

    def edit_passage(self, name, line_numbers, new_text):
        lines = self.path(name).read_text(encoding="utf-8").splitlines(keepends=True)
        paras = new_text.split("\n\n")
        self.test.assertEqual(len(paras), len(line_numbers))
        for n, para in zip(line_numbers, paras):
            lines[n - 1] = para + lines[n - 1][len(lines[n - 1].rstrip("\n")):]
        self.path(name).write_text("".join(lines), encoding="utf-8")

    def judge(self, name, answers=None, omit=(), audit=False):
        sample = json.loads((self.tdir / "state" / f"{Path(name).stem}.sample.json").read_text(encoding="utf-8"))
        answers = answers or {}
        payload = [{"id": p["id"], "errors": answers.get(p["id"], [])}
                   for p in sample["passages"] if p["id"] not in omit]
        out = self.root / f"answers-{len(list(self.root.glob('answers-*')))}.json"
        out.write_text(json.dumps(payload), encoding="utf-8")
        extra = ["--audit"] if audit else []
        return self.ok("record-judgments", "--file", name, "--judgments", str(out), *extra)

    def settle(self, name, answers=None):
        """Judge every pending passage once and return the next action."""
        action = self.nxt(name)
        self.test.assertEqual(action["action"], "judge", action)
        self.judge(name, answers)
        return self.nxt(name)


class InitTests(unittest.TestCase):
    def test_layout_and_idempotency(self):
        env = Env(self, translate=False)
        for sub in ec.TARGET_SUBDIRS:
            self.assertTrue((env.tdir / sub).is_dir(), sub)
        self.assertTrue((env.ws / "manifest.md").is_file())
        pipeline = json.loads((env.tdir / "state" / "pipeline.json").read_text(encoding="utf-8"))
        self.assertEqual(pipeline["files"], [ONE, TWO])
        self.assertEqual(pipeline["config"]["window"], 2)
        self.assertEqual(pipeline["config"]["passage_min"], 98.0)
        self.assertTrue((env.tdir / "state" / "01-one.json").is_file())

        st = env.state(ONE)
        st["steps"] = 7
        ec.write_json(env.tdir / "state" / "01-one.json", st)
        data = env.cli("init", "--source", str(env.src), "--lang", "pt-BR", "--max-steps", "9", scoped=False)[1]
        self.assertFalse(data["created"])
        self.assertEqual(data["config"]["max_steps"], 9)
        self.assertEqual(data["files"], [ONE, TWO])
        self.assertEqual(env.state(ONE)["steps"], 7)

        data = env.cli("init", "--source", str(env.src), "--lang", "pt-BR", "--reset", scoped=False)[1]
        self.assertEqual(env.state(ONE)["steps"], 0)

    def test_state_option_and_usage_errors(self):
        env = Env(self, translate=False)
        pipeline = env.tdir / "state" / "pipeline.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(ec.main(["status", "--state", str(pipeline)]), 0)
        self.assertEqual(len(json.loads(buf.getvalue())["files"]), 2)
        code, data = env.cli("next", "--file", "nope.md")
        self.assertEqual(code, 2)
        self.assertIn("unknown file", data["error"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(ec.main(["status"]), 2)

    def test_files_option_and_translation_folder_excluded(self):
        env = Env(self, translate=False)
        data = env.cli("init", "--source", str(env.src), "--lang", "pt-BR", "--files", ONE, scoped=False)[1]
        self.assertEqual(data["files"], [ONE, TWO])
        self.assertNotIn("manifest.md", data["files"])


class ActionTests(unittest.TestCase):
    def test_reconsider_preserves_text_and_judgment_history(self):
        env = Env(self)
        pid = env.nxt(ONE)["passages"][0]
        env.judge(ONE, {pid: [MAJOR]})
        before = env.path(ONE).read_bytes()
        env.ok("reconsider", "--file", ONE, "--passages", pid,
               "--reason", "The glossary explicitly preserves this name")
        self.assertEqual(env.path(ONE).read_bytes(), before)
        self.assertEqual(env.nxt(ONE)["passages"], [pid])
        state = env.state(ONE)["passages"][pid]
        self.assertEqual(state["attempts"][0]["errors"], [MAJOR])
        self.assertEqual(state["attempts"][1]["reconsideration"]["previous_attempt"], 0)
        env.judge(ONE)
        self.assertEqual(env.state(ONE)["passages"][pid]["status"], "pass")
        self.assertEqual(env.path(ONE).read_bytes(), before)
        self.assertEqual(ec.attempts_made(env.state(ONE)["passages"][pid]), 1)

    def test_reconsider_is_once_only_and_never_auto_approves(self):
        env = Env(self)
        pid = env.nxt(ONE)["passages"][0]
        env.judge(ONE, {pid: [MAJOR]})
        env.ok("reconsider", "--file", ONE, "--passages", pid, "--reason", "Check context")
        self.assertEqual(env.nxt(ONE)["action"], "judge")
        env.judge(ONE, {pid: [MAJOR]})
        self.assertEqual(env.state(ONE)["passages"][pid]["status"], "fail")
        code, result = env.cli("reconsider", "--file", ONE, "--passages", pid,
                               "--reason", "Try again")
        self.assertEqual(code, 2)
        self.assertIn("once", result["error"])

    def test_translate_when_manuscript_missing(self):
        env = Env(self, translate=False)
        action = env.nxt(ONE)
        self.assertEqual(action["action"], "translate")
        self.assertTrue(action["source_path"].endswith(ONE))
        self.assertTrue(action["target_path"].endswith("manuscript/" + ONE))

    def test_repair_parity(self):
        env = Env(self)
        lines = TGT_ONE.splitlines(keepends=True)
        env.write(ONE, "".join(lines[:-2]))
        action = env.nxt(ONE)
        self.assertEqual(action["action"], "repair_parity")
        self.assertEqual((action["source_paragraphs"], action["target_paragraphs"]), (6, 5))

    def test_repair_gates_on_changed_number_and_round_limit(self):
        env = Env(self)
        env.write(ONE, TGT_ONE.replace("1847", "1848"))
        first = env.nxt(ONE)
        self.assertEqual(first["action"], "repair_gates")
        self.assertIn("G3", first["findings"])
        self.assertTrue(any("1847" in f for f in first["findings"]["G3"]["findings"]))
        self.assertEqual(first["gate_rounds"], 1)
        self.assertEqual(env.nxt(ONE)["gate_rounds"], 2)
        self.assertEqual(env.nxt(ONE)["action"], "judge")

    def test_allow_number_reruns_gates(self):
        env = Env(self)
        env.write(ONE, TGT_ONE.replace("1847", "muitas"))
        self.assertEqual(env.nxt(ONE)["action"], "repair_gates")
        data = env.ok("allow-number", "--file", ONE, "--value", "1847")
        self.assertTrue(data["gates_passed"])
        self.assertEqual(env.nxt(ONE)["action"], "judge")
        self.assertTrue(env.state(ONE)["gates"]["passed"])

    def test_gates_rerun_only_when_manuscript_changes(self):
        env = Env(self)
        env.nxt(ONE)
        marker = env.state(ONE)["gates"]
        marker["warn_counts"] = {"G9": 1}
        st = env.state(ONE)
        st["gates"] = marker
        ec.write_json(env.tdir / "state" / "01-one.json", st)
        env.nxt(ONE)
        self.assertEqual(env.state(ONE)["gates"]["warn_counts"], {"G9": 1})

    def test_judge_prompt_files_and_mqm_compatibility(self):
        env = Env(self)
        (env.tdir / "glossary.md").write_text("# Glossary\n\nGLOSSARY-MARK Morag stays Morag.\n", encoding="utf-8")
        (env.tdir / "editorial-conventions.md").write_text("EDITORIAL-MARK use curly quotes", encoding="utf-8")
        (env.tdir / "decisions").mkdir(exist_ok=True)
        (env.tdir / "decisions" / ONE).write_text("DECISION-MARK kept 1847 as is", encoding="utf-8")
        (env.ws / "context" / "style-guide.md").write_text("STYLE-MARK" + "x" * 13000 + "END-MARK", encoding="utf-8")
        action = env.nxt(ONE)
        self.assertEqual(action["action"], "judge")
        self.assertEqual(action["passages"], ["01-one:0", "01-one:2", "01-one:4"])
        self.assertEqual(action["batches"], 1)
        text = Path(action["prompt_files"][0]).read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# SUPPORT TEXTS"))
        for mark in ("GLOSSARY-MARK", "EDITORIAL-MARK", "DECISION-MARK", "STYLE-MARK"):
            self.assertIn(mark, text)
        self.assertNotIn("END-MARK", text)
        self.assertIn("=== PASSAGE id=01-one:0", text)
        self.assertLess(text.index("DECISION-MARK"), text.index("=== PASSAGE"))

        sample = action["sample"]
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(mqm_score.main(["prompt", "--sample", sample, "--outdir", str(env.root / "p")]), 0)
        answers = env.root / "a.json"
        answers.write_text(json.dumps([{"id": pid, "errors": []} for pid in action["passages"]]), encoding="utf-8")
        with redirect_stdout(buf):
            self.assertEqual(mqm_score.main(["score", "--sample", sample, "--judgments", str(answers)]), 0)
        self.assertIn("score: 100.0", buf.getvalue())

    def test_judge_batches(self):
        env = Env(self, "--batch", "2")
        action = env.nxt(ONE)
        self.assertEqual((action["batches"], len(action["prompt_files"])), (2, 2))

    def test_next_is_idempotent(self):
        env = Env(self)
        a, b = env.nxt(ONE), env.nxt(ONE)
        self.assertEqual(a, b)
        self.assertEqual(env.state(ONE)["steps"], 2)


class JudgmentTests(unittest.TestCase):
    def test_record_updates_scores_and_status(self):
        env = Env(self)
        env.nxt(ONE)
        data = env.judge(ONE, {"01-one:0": [MAJOR], "01-one:2": [MINOR]})
        self.assertEqual(data["judged"], 3)
        self.assertEqual(data["pass"], 1)
        self.assertEqual(sorted(data["fail"]), ["01-one:0", "01-one:2"])
        self.assertLess(data["chapter_score"], 100)
        self.assertEqual(data["coverage"], 1.0)
        st = env.state(ONE)
        att = st["passages"]["01-one:0"]["attempts"][0]
        self.assertEqual((att["major"], att["penalty"], att["judged"]), (1, 5, True))
        self.assertEqual(st["passages"]["01-one:4"]["status"], "pass")
        self.assertEqual(env.ok("status", "--file", ONE)["files"][0]["passages"], {"fail": 2, "pass": 1})
        self.assertEqual(env.ok("status")["budget"]["judged_passages"], 3)

    def test_unjudged_after_repeated_misses(self):
        env = Env(self, "--judge-misses-max", "2")
        env.nxt(ONE)
        env.judge(ONE, omit={"01-one:0"})
        again = env.nxt(ONE)
        self.assertEqual((again["action"], again["passages"]), ("judge", ["01-one:0"]))
        data = env.judge(ONE, omit={"01-one:0"})
        self.assertEqual(data["missing"], ["01-one:0"])
        self.assertIn("01-one:0", data["unresolved"])
        self.assertEqual(env.state(ONE)["passages"]["01-one:0"]["status"], "unjudged")
        self.assertEqual(env.nxt(ONE)["action"], "chapter_checks")
        self.assertIsNone(env.state(ONE)["passages"]["01-one:0"]["best"])

    def test_stale_answers_are_ignored(self):
        env = Env(self)
        env.nxt(ONE)
        env.edit_passage(ONE, [3, 5], "Nova frase um para a primeira linha.\n\nNova frase dois para a segunda linha.")
        data = env.judge(ONE)
        self.assertEqual(data["stale"], ["01-one:0"])
        self.assertEqual(data["judged"], 2)

    def test_judgment_for_wrong_mode_is_rejected(self):
        env = Env(self)
        env.nxt(ONE)
        out = env.root / "x.json"
        out.write_text("[]", encoding="utf-8")
        code, data = env.cli("record-judgments", "--file", ONE, "--judgments", str(out), "--audit")
        self.assertEqual(code, 2)
        self.assertIn("audit", data["error"])


class ConvergenceTests(unittest.TestCase):
    def test_full_flow_to_done(self):
        env = Env(self, "--audit-fraction", "0.5")
        env.nxt(ONE)
        env.judge(ONE, {"01-one:0": [MAJOR]})
        retr = env.nxt(ONE)
        self.assertEqual((retr["action"], retr["reason"]), ("retranslate", "fail"))
        item = retr["passages"][0]
        self.assertEqual((item["id"], item["attempt"], item["strategy"]), ("01-one:0", 1, "targeted_notes"))
        self.assertEqual(item["line_numbers"], [3, 5])
        self.assertTrue(any("wrong meaning" in n for n in item["notes"]))
        self.assertEqual(item["paragraph_count"], 2)
        self.assertEqual(item["context_before"]["source"], [])
        self.assertEqual(len(item["context_after"]["target"]), 2)

        env.edit_passage(ONE, item["line_numbers"],
                         "O tempo virou amargo durante a noite e todos se juntaram à mesa da cozinha.\n\n"
                         '"A chaleira está ao fogo?", disse Morag, sem erguer os olhos da lareira fria.')
        again = env.nxt(ONE)
        self.assertEqual((again["action"], again["passages"]), ("judge", ["01-one:0"]))
        data = env.judge(ONE)
        self.assertEqual((data["pass"], data["fail"], data["restored"]), (3, [], []))
        self.assertEqual(env.state(ONE)["passages"]["01-one:0"]["best"], 1)

        cc = env.nxt(ONE)
        self.assertEqual((cc["action"], cc["round"]), ("chapter_checks", 1))
        env.ok("record-chapter-checks", "--file", ONE, "--issues", "0")
        audit = env.nxt(ONE)
        self.assertEqual(audit["action"], "audit")
        self.assertTrue(audit["audit"])
        self.assertEqual(len(audit["passages"]), 2)
        env.judge(ONE, audit=True)
        self.assertEqual(env.nxt(ONE)["action"], "finalize")
        fin = env.ok("finalize", "--file", ONE)
        self.assertEqual(fin["manifest_status"], "verified")
        self.assertEqual(fin["score"], 100.0)
        self.assertEqual(fin["unresolved"], [])
        done = env.nxt(ONE)
        self.assertEqual((done["action"], done["manifest_status"]), ("done", "verified"))

    def test_equal_clean_attempt_keeps_latest_correction(self):
        env = Env(self)
        env.nxt(ONE)
        env.judge(ONE)
        corrected = TGT_ONE.replace("Morag", "Morag revisada")
        env.write(ONE, corrected)
        self.assertEqual(env.nxt(ONE)["action"], "judge")
        result = env.judge(ONE)
        self.assertEqual(result["restored"], [])
        self.assertEqual(env.path(ONE).read_text(encoding="utf-8"), corrected)
        passage = env.state(ONE)["passages"]["01-one:0"]
        self.assertEqual((passage["best"], passage["current"]), (1, 1))
        self.assertEqual(passage["stagnation"], 1)
        self.assertEqual(len(passage["attempts"]), 2)

    def test_resume_retains_later_clean_attempt_rejected_by_old_tie_policy(self):
        env = Env(self)
        env.nxt(ONE)
        env.judge(ONE)
        corrected = TGT_ONE.replace("Morag", "Morag revisada")
        env.write(ONE, corrected)
        env.nxt(ONE)
        env.judge(ONE)
        state = env.state(ONE)
        passage = state["passages"]["01-one:0"]
        passage["best"] = passage["current"] = 0
        passage["attempts"][1]["rejected"] = True
        state_path = env.tdir / "state" / "01-one.json"
        state_path.write_text(json.dumps(state), encoding="utf-8")
        result = env.nxt(ONE)
        self.assertNotIn("restored", result)
        self.assertEqual(env.path(ONE).read_text(encoding="utf-8"), corrected)
        resumed = env.state(ONE)["passages"]["01-one:0"]
        self.assertEqual((resumed["best"], resumed["current"]), (1, 1))
        self.assertTrue(resumed["attempts"][1]["rejected"])
        self.assertEqual(len(resumed["attempts"]), 2)

    def test_worse_attempt_is_rejected_and_best_restored(self):
        env = Env(self)
        env.nxt(ONE)
        env.judge(ONE, {"01-one:0": [MINOR], "01-one:2": [MINOR]})
        retr = env.nxt(ONE)
        by_id = {p["id"]: p for p in retr["passages"]}
        good = ("O tempo virou amargo durante a noite e todos se juntaram à mesa da cozinha.\n\n"
                '"A chaleira está ao fogo?", disse Morag, sem erguer os olhos da lareira fria.')
        env.edit_passage(ONE, by_id["01-one:0"]["line_numbers"], good)
        env.edit_passage(ONE, by_id["01-one:2"]["line_numbers"],
                         "Ela contou 1847 seixos no muro.\n\nNinguém respondeu.")
        original = env.path(ONE).read_text(encoding="utf-8")
        env.nxt(ONE)
        data = env.judge(ONE, {"01-one:2": [MAJOR]})
        self.assertEqual(data["restored"], ["01-one:2"])
        text = env.path(ONE).read_text(encoding="utf-8")
        expected = TGT_ONE.replace(TGT_ONE.split("\n\n")[1] + "\n\n" + TGT_ONE.split("\n\n")[2], good)
        self.assertEqual(text, expected)
        self.assertNotEqual(text, original)
        self.assertIn("# Capítulo Um", text)
        self.assertTrue(text.endswith("\n"))
        st = env.state(ONE)["passages"]["01-one:2"]
        self.assertTrue(st["attempts"][1]["rejected"])
        self.assertEqual((st["best"], st["current"], st["stagnation"]), (0, 0, 1))
        nxt = env.nxt(ONE)
        self.assertEqual(nxt["action"], "retranslate")
        self.assertEqual([p["id"] for p in nxt["passages"]], ["01-one:2"])
        self.assertEqual(nxt["passages"][0]["attempt"], 2)
        self.assertTrue(any("rejected" in n for n in nxt["passages"][0]["notes"]))

    def test_restore_keeps_file_bytes_without_trailing_newline(self):
        env = Env(self)
        text = TGT_ONE.rstrip("\n")
        env.write(ONE, text)
        env.nxt(ONE)
        env.judge(ONE, {"01-one:4": [MINOR]})
        retr = env.nxt(ONE)
        env.edit_passage(ONE, retr["passages"][0]["line_numbers"], "Uma gaivota.\n\nUma estrada.")
        env.nxt(ONE)
        data = env.judge(ONE, {"01-one:4": [MAJOR]})
        self.assertEqual(data["restored"], ["01-one:4"])
        self.assertEqual(env.path(ONE).read_text(encoding="utf-8"), text)

    def test_agent_revert_to_best_text_needs_no_rejudging(self):
        env = Env(self)
        env.nxt(ONE)
        env.judge(ONE, {"01-one:0": [MINOR]})
        retr = env.nxt(ONE)
        lines = retr["passages"][0]["line_numbers"]
        env.edit_passage(ONE, lines, "Texto novo um.\n\nTexto novo dois.")
        env.nxt(ONE)
        env.edit_passage(ONE, lines, "\n\n".join(TGT_ONE.splitlines()[2::2][:2]))
        action = env.nxt(ONE)
        self.assertEqual(action["action"], "retranslate")
        self.assertEqual(env.state(ONE)["passages"]["01-one:0"]["current"], 0)

    def test_stagnation_escalates_strategy(self):
        env = Env(self, "--max-retranslations", "6")
        env.nxt(ONE)
        env.judge(ONE, {"01-one:0": [MINOR]})
        seen = []
        for i in range(5):
            retr = env.nxt(ONE)
            self.assertEqual(retr["action"], "retranslate", retr)
            seen.append(retr["passages"][0]["strategy"])
            env.edit_passage(ONE, retr["passages"][0]["line_numbers"], f"Versão {WORDS[i]} linha um.\n\nVersão {WORDS[i]} linha dois.")
            env.nxt(ONE)
            env.judge(ONE, {"01-one:0": [MINOR]})
        self.assertEqual(seen, ["targeted_notes", "targeted_notes", "widen_context", "widen_context", "multi_candidate"])
        wide = env.nxt(ONE)["passages"][0]
        self.assertEqual(wide["strategy"], "multi_candidate")
        self.assertEqual(len(wide["context_after"]["source"]), 4)

    def test_passage_becomes_unresolved_after_max_retranslations(self):
        env = Env(self)
        env.nxt(ONE)
        env.judge(ONE, {"01-one:0": [MAJOR]})
        for i in range(2):
            retr = env.nxt(ONE)
            self.assertEqual(retr["action"], "retranslate")
            env.edit_passage(ONE, retr["passages"][0]["line_numbers"], f"Tentativa {WORDS[i]} um.\n\nTentativa {WORDS[i]} dois.")
            env.nxt(ONE)
            data = env.judge(ONE, {"01-one:0": [MAJOR]})
        self.assertEqual(data["unresolved"], ["01-one:0"])
        self.assertEqual(env.nxt(ONE)["action"], "chapter_checks")
        env.ok("record-chapter-checks", "--file", ONE, "--issues", "0")
        self.assertEqual(env.nxt(ONE)["action"], "finalize")
        fin = env.ok("finalize", "--file", ONE)
        self.assertEqual(fin["manifest_status"], "drafted")
        self.assertEqual([u["id"] for u in fin["unresolved"]], ["01-one:0"])
        self.assertTrue(any("wrong meaning" in n for n in fin["unresolved"][0]["notes"]))

    def test_polish_loop_when_chapter_below_minimum(self):
        env = Env(self, "--passage-min", "90", "--chapter-min", "99")
        env.nxt(ONE)
        env.judge(ONE, {"01-one:0": [MINOR]})
        polish = env.nxt(ONE)
        self.assertEqual((polish["action"], polish["reason"]), ("retranslate", "polish"))
        self.assertEqual([p["id"] for p in polish["passages"]], ["01-one:0"])
        env.edit_passage(ONE, polish["passages"][0]["line_numbers"], "Melhor um.\n\nMelhor dois.")
        env.nxt(ONE)
        env.judge(ONE)
        self.assertEqual(env.nxt(ONE)["action"], "chapter_checks")

    def test_polish_exhausted_records_chapter_min_unmet(self):
        env = Env(self, "--passage-min", "90", "--chapter-min", "99")
        env.nxt(ONE)
        env.judge(ONE, {"01-one:0": [MINOR]})
        for i in range(2):
            polish = env.nxt(ONE)
            self.assertEqual(polish["reason"], "polish")
            env.edit_passage(ONE, polish["passages"][0]["line_numbers"], f"Pior {WORDS[i]} um.\n\nPior {WORDS[i]} dois.")
            env.nxt(ONE)
            env.judge(ONE, {"01-one:0": [MINOR]})
        self.assertEqual(env.nxt(ONE)["action"], "chapter_checks")
        env.ok("record-chapter-checks", "--file", ONE, "--issues", "0")
        fin = env.ok("finalize", "--file", ONE)
        self.assertTrue(fin["chapter_min_unmet"])

    def test_chapter_checks_rounds_are_bounded(self):
        env = Env(self)
        env.nxt(ONE)
        env.judge(ONE)
        self.assertEqual(env.nxt(ONE)["round"], 1)
        env.ok("record-chapter-checks", "--file", ONE, "--issues", "2", "--note", "tics")
        self.assertEqual(env.nxt(ONE)["round"], 2)
        env.ok("record-chapter-checks", "--file", ONE, "--issues", "1")
        self.assertEqual(env.nxt(ONE)["action"], "finalize")
        self.assertEqual(env.state(ONE)["chapter_check_notes"], ["tics"])

    def test_chapter_check_fix_flows_through_judging_again(self):
        env = Env(self)
        env.nxt(ONE)
        env.judge(ONE)
        env.nxt(ONE)
        env.edit_passage(ONE, [3, 5], "Ajuste um.\n\nAjuste dois.")
        env.ok("record-chapter-checks", "--file", ONE, "--issues", "1")
        nxt = env.nxt(ONE)
        self.assertEqual((nxt["action"], nxt["passages"]), ("judge", ["01-one:0"]))

    def test_audit_reopens_a_passage(self):
        env = Env(self, "--audit-fraction", "1")
        env.nxt(ONE)
        env.judge(ONE)
        env.nxt(ONE)
        env.ok("record-chapter-checks", "--file", ONE, "--issues", "0")
        audit = env.nxt(ONE)
        self.assertEqual((audit["action"], len(audit["passages"])), ("audit", 3))
        data = env.judge(ONE, {"01-one:2": [MAJOR]}, audit=True)
        self.assertEqual(data["audit_reopened"], ["01-one:2"])
        self.assertEqual(data["fail"], ["01-one:2"])
        retr = env.nxt(ONE)
        self.assertEqual(retr["action"], "retranslate")
        self.assertTrue(any("[audit]" in n for n in retr["passages"][0]["notes"]))
        env.edit_passage(ONE, retr["passages"][0]["line_numbers"], "Corrigido, ela contou 1847 pedras.\n\nCorrigido dois.")
        env.nxt(ONE)
        self.assertEqual(env.judge(ONE)["fail"], [])
        self.assertEqual(env.nxt(ONE)["action"], "chapter_checks")
        env.ok("record-chapter-checks", "--file", ONE, "--issues", "0")
        self.assertEqual(env.nxt(ONE)["action"], "finalize")
        self.assertEqual(env.state(ONE)["audit"]["reopened"], ["01-one:2"])

    def test_finalize_restores_best_everywhere(self):
        env = Env(self)
        env.nxt(ONE)
        env.judge(ONE, {"01-one:0": [MINOR]})
        retr = env.nxt(ONE)
        env.edit_passage(ONE, retr["passages"][0]["line_numbers"], "Mudou um.\n\nMudou dois.")
        env.nxt(ONE)
        self.assertEqual(env.nxt(ONE)["action"], "judge")
        fin = env.ok("finalize", "--file", ONE)
        self.assertEqual(fin["restored"], ["01-one:0"])
        self.assertEqual(env.path(ONE).read_text(encoding="utf-8"), TGT_ONE)


class BudgetAndReportTests(unittest.TestCase):
    def test_budget_stop(self):
        env = Env(self, "--max-judged-passages", "2")
        env.nxt(ONE)
        env.judge(ONE)
        stop = env.nxt(ONE)
        self.assertEqual((stop["action"], stop["reason"]), ("stop", "budget"))

    def test_max_steps_stop(self):
        env = Env(self, "--max-steps", "3", translate=False)
        for _ in range(3):
            self.assertEqual(env.nxt(ONE)["action"], "translate")
        stop = env.nxt(ONE)
        self.assertEqual((stop["action"], stop["reason"]), ("stop", "max_steps"))

    def test_report_content_and_model_warnings(self):
        env = Env(self)
        env.nxt(ONE)
        env.judge(ONE, {"01-one:0": [MAJOR]})
        for i in range(2):
            retr = env.nxt(ONE)
            env.edit_passage(ONE, retr["passages"][0]["line_numbers"], f"R{WORDS[i]} um.\n\nR{WORDS[i]} dois.")
            env.nxt(ONE)
            env.judge(ONE, {"01-one:0": [MAJOR]})
        env.nxt(ONE)
        env.ok("record-chapter-checks", "--file", ONE, "--issues", "0")
        env.nxt(ONE)
        env.ok("finalize", "--file", ONE)

        out = env.ok("report")["path"]
        text = Path(out).read_text(encoding="utf-8")
        self.assertTrue(out.endswith("reports/e2e-report.md"))
        self.assertIn("not human reviewed", text)
        self.assertIn(f"| {ONE} | drafted |", text)
        self.assertIn(f"| {TWO} | pending |", text)
        self.assertIn("01-one:0", text)
        self.assertIn("wrong meaning", text)
        self.assertIn("judge model not recorded", text)

        env.ok("set-models", "--translator-model", "Model-X", "--judge-model", "model-x")
        text = Path(env.ok("report", "--out", str(env.root / "r.md"))["path"]).read_text(encoding="utf-8")
        self.assertIn("same model", text)
        self.assertNotIn("not recorded; use", text)

        env.ok("set-models", "--judge-model", "Model-Y")
        text = Path(env.ok("report", "--out", str(env.root / "r.md"))["path"]).read_text(encoding="utf-8")
        self.assertNotIn("same model", text)
        self.assertIn("Judge model: Model-Y", text)

    def test_two_files_are_independent(self):
        env = Env(self)
        self.assertEqual(env.nxt(TWO)["passages"], ["02-two:0"])
        self.assertEqual(env.nxt(ONE)["passages"], ["01-one:0", "01-one:2", "01-one:4"])


if __name__ == "__main__":
    unittest.main()
