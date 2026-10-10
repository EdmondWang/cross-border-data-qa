"""用固定问题做关键词回归。需要可用的百炼 API Key 和已建好的索引。"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chatbot.agent import answer  # noqa: E402


def main() -> None:
    path = Path(__file__).with_name("questions.jsonl")
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    failed = 0
    for case in cases:
        reply = answer(case["question"])
        ok = any(token in reply for token in case["expect_any"])
        mark = "通过" if ok else "未通过"
        print(f"[{mark}] {case['id']}")
        if not ok:
            failed += 1
            print(reply)
            print("---")
    print(f"\n{len(cases) - failed}/{len(cases)} 通过")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
