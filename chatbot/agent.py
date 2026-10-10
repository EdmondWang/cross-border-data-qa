"""多轮问答：检索知识库，并用工具判断出境路径。"""

from __future__ import annotations

import json

from chatbot.llm import MODEL, get_client
from chatbot.policy import classify
from chatbot.prompts import DISCLAIMER, build_system_prompt
from chatbot.rag import retrieve_context

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "classify_export",
            "description": (
                "根据《促进和规范数据跨境流动规定》判断数据出境路径。"
                "人数门槛必须调用本工具。未知人数时不要调用，先向用户追问。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "is_ciio": {
                        "type": "boolean",
                        "description": "数据处理者是否为关键信息基础设施运营者",
                    },
                    "is_important_data": {
                        "type": "boolean",
                        "description": "是否已被有关部门、地区告知或公开发布为重要数据",
                    },
                    "general_pi_count": {
                        "type": "integer",
                        "description": "当年1月1日起累计出境的人数，只计一般个人信息，不含敏感个人信息",
                    },
                    "sensitive_pi_count": {
                        "type": "integer",
                        "description": "当年1月1日起累计出境的敏感个人信息人数",
                    },
                    "exemption": {
                        "type": "string",
                        "enum": [
                            "none",
                            "trade",
                            "overseas_roundtrip",
                            "contract",
                            "hr",
                            "emergency",
                            "ftz_outside_list",
                        ],
                        "description": (
                            "none；trade 第三条且不含个人信息或重要数据；"
                            "overseas_roundtrip 第四条；contract 第五条第一项；"
                            "hr 第五条第二项；emergency 第五条第三项；"
                            "ftz_outside_list 第六条且已确认在负面清单外"
                        ),
                    },
                },
                "required": [
                    "is_ciio",
                    "is_important_data",
                    "general_pi_count",
                    "sensitive_pi_count",
                    "exemption",
                ],
            },
        },
    }
]


def answer(question: str, history: list[dict] | None = None) -> str:
    history = history or []
    messages: list[dict] = [
        {"role": "system", "content": build_system_prompt(retrieve_context(question))}
    ]
    for item in history[-6:]:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})

    client = get_client()
    for _ in range(4):
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0.1,
        )
        message = completion.choices[0].message
        tool_calls = message.tool_calls or []
        if not tool_calls:
            return _with_disclaimer((message.content or "").strip())
        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ],
            }
        )
        for call in tool_calls:
            payload = run_tool(call.function.name, call.function.arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(payload, ensure_ascii=False),
                }
            )
    return _with_disclaimer("本轮工具调用次数已用完。请把事实拆开，分成更短的问题再问一次。")


def run_tool(name: str, arguments: str | dict) -> dict:
    if name != "classify_export":
        return {"path": "invalid", "message": f"未知工具 {name}"}
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments or "{}")
        except json.JSONDecodeError:
            return {"path": "invalid", "message": "工具参数不是合法 JSON"}
    try:
        return classify(**arguments)
    except (TypeError, ValueError) as exc:
        return {"path": "invalid", "message": str(exc)}


def _with_disclaimer(text: str) -> str:
    if DISCLAIMER in text:
        return text
    return f"{text.rstrip()}\n\n{DISCLAIMER}"
