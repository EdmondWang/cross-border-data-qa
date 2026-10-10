"""浏览器里的多轮问答。"""

import gradio as gr

from chatbot.agent import answer


def respond(message: str, history: list[dict]) -> str:
    prior = []
    for item in history or []:
        if isinstance(item, dict) and item.get("role") in {"user", "assistant"}:
            prior.append({"role": item["role"], "content": item.get("content", "")})
    return answer(message, prior)


demo = gr.ChatInterface(
    fn=respond,
    title="数据跨境问答",
    description="按《促进和规范数据跨境流动规定》回答出境路径。人数门槛由规则计算。回答用于学习，不构成法律意见。",
    type="messages",
)


if __name__ == "__main__":
    demo.launch()
