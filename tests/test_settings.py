import os
import tempfile
import unittest
from pathlib import Path

from config.settings import load_dotenv


class DotenvTests(unittest.TestCase):
    def test_loads_assignment_without_overriding_existing_env(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "\n".join(
                    [
                        "# comment",
                        "CROSS_BORDER_TEST_KEY=from-file",
                        "CROSS_BORDER_TEST_EXISTING=from-file",
                        "QUOTED='quoted-value'",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            os.environ["CROSS_BORDER_TEST_EXISTING"] = "already-set"
            try:
                load_dotenv(path)
                self.assertEqual(os.environ["CROSS_BORDER_TEST_KEY"], "from-file")
                self.assertEqual(os.environ["CROSS_BORDER_TEST_EXISTING"], "already-set")
                self.assertEqual(os.environ["QUOTED"], "quoted-value")
            finally:
                os.environ.pop("CROSS_BORDER_TEST_KEY", None)
                os.environ.pop("CROSS_BORDER_TEST_EXISTING", None)
                os.environ.pop("QUOTED", None)


if __name__ == "__main__":
    unittest.main()
