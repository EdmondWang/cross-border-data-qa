import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class KnowledgeTests(unittest.TestCase):
    def test_sections_carry_sources(self):
        files = sorted((ROOT / "knowledge").glob("*.md"))
        self.assertGreaterEqual(len(files), 6)
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertIn("来源", text)
            self.assertGreater(len(text), 200)


if __name__ == "__main__":
    unittest.main()
