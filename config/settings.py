"""加载百炼 API Key。优先已有环境变量，其次项目根目录 .env。"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOTENV_FILE = ROOT / ".env"


def load_dotenv(path: Path = DOTENV_FILE) -> None:
    """读取 .env。已经存在的环境变量保持不变。"""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip("'").strip('"')
        if name and name not in os.environ:
            os.environ[name] = value


def load_api_key() -> str:
    load_dotenv()
    key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if key:
        return key
    raise RuntimeError(
        "未找到 DASHSCOPE_API_KEY。请在项目根目录 .env 中写入 DASHSCOPE_API_KEY=sk-..."
    )
