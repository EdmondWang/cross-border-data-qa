"""加载百炼 API Key。优先环境变量，其次项目根目录 Key.json。"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY_FILE = ROOT / "Key.json"


def load_api_key() -> str:
    key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if key:
        return key
    if KEY_FILE.exists():
        data = json.loads(KEY_FILE.read_text(encoding="utf-8"))
        key = str(data.get("DASHSCOPE_API_KEY", "")).strip()
        if key:
            os.environ["DASHSCOPE_API_KEY"] = key
            return key
    raise RuntimeError(
        "未找到 DASHSCOPE_API_KEY。请导出环境变量，或在项目根目录创建 Key.json："
        '{"DASHSCOPE_API_KEY": "sk-..."}'
    )
