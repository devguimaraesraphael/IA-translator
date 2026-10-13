import tempfile
import unittest
from pathlib import Path

from publish_candidate import digest, publish


class PublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source.md"
        self.target = self.root / "target.md"
        self.candidate = self.root / "candidate.md"
        self.context = self.root / "glossary.md"
        self.source.write_text("First block.\n\nSecond block.\n", encoding="utf-8")
        self.target.write_text("Primeiro bloco.\n\nSegundo bloco.\n", encoding="utf-8")
        self.candidate.write_text("Primeiro trecho.\n\nSegundo bloco.\n", encoding="utf-8")
        self.context.write_text("Shared glossary\n", encoding="utf-8")
        self.spec = {name: {"path": str(path), "sha256": digest(path)}
                     for name, path in [("source", self.source), ("target", self.target),
                                        ("candidate", self.candidate)]}
        self.spec["context"] = [{"path": str(self.context), "sha256": digest(self.context)}]
        self.spec["allowed_blocks"] = [0]

    def test_publishes_exact_candidate_and_retains_inputs(self):
        result = publish(self.spec)
        self.assertEqual(self.target.read_bytes(), self.candidate.read_bytes())
        self.assertEqual(result["published_sha256"], self.spec["candidate"]["sha256"])
        self.assertEqual(digest(self.source), self.spec["source"]["sha256"])
        self.assertEqual(result["blocks"], 2)

    def test_stale_target_cannot_overwrite_newer_decision(self):
        self.target.write_text("Newer decision\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Version conflict"):
            publish(self.spec)
        self.assertEqual(self.target.read_text(encoding="utf-8"), "Newer decision\n")

    def test_source_candidate_and_context_changes_block_publication(self):
        for path in [self.source, self.candidate, self.context]:
            with self.subTest(path=path):
                original = path.read_bytes()
                baseline = self.target.read_bytes()
                path.write_bytes(original + b"changed")
                with self.assertRaisesRegex(ValueError, "Version conflict"):
                    publish(self.spec)
                self.assertEqual(self.target.read_bytes(), baseline)
                path.write_bytes(original)

    def test_rejects_out_of_scope_changes(self):
        self.spec["allowed_blocks"] = [1]
        with self.assertRaisesRegex(ValueError, "outside the approved scope"):
            publish(self.spec)
        self.assertEqual(digest(self.target), self.spec["target"]["sha256"])

    def test_rejects_missing_block_without_touching_target(self):
        self.candidate.write_text("Only one block\n", encoding="utf-8")
        self.spec["candidate"]["sha256"] = digest(self.candidate)
        with self.assertRaisesRegex(ValueError, "block count"):
            publish(self.spec)
        self.assertEqual(digest(self.target), self.spec["target"]["sha256"])

    def test_first_publication_requires_target_still_absent(self):
        self.target.unlink()
        self.spec["target"]["sha256"] = None
        publish(self.spec)
        with self.assertRaisesRegex(ValueError, "Version conflict"):
            publish(self.spec)


if __name__ == "__main__":
    unittest.main()