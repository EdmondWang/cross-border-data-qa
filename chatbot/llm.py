"""百炼 OpenAI 兼容接口。"""

from openai import OpenAI

from config.settings import load_api_key

MODEL = "qwen-plus"
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def get_client() -> OpenAI:
    return OpenAI(api_key=load_api_key(), base_url=BASE_URL)
