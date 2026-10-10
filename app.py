"""命令行问答。人数门槛也可以不调用模型，直接用 --classify 演算。"""

import argparse
import json

from chatbot.policy import classify, render


def main() -> None:
    parser = argparse.ArgumentParser(description="数据跨境问答机器人")
    parser.add_argument("-q", "--question", help="只问一个问题后退出")
    parser.add_argument("--reindex", action="store_true", help="重建向量索引")
    parser.add_argument("--classify", action="store_true", help="只用规则判断路径，不调用模型")
    parser.add_argument("--ciio", action="store_true", help="是关键信息基础设施运营者")
    parser.add_argument("--important", action="store_true", help="已被告知或公布为重要数据")
    parser.add_argument("--general", type=int, default=0, help="当年累计一般个人信息人数")
    parser.add_argument("--sensitive", type=int, default=0, help="当年累计敏感个人信息人数")
    parser.add_argument(
        "--exemption",
        default="none",
        choices=["none", "trade", "overseas_roundtrip", "contract", "hr", "emergency", "ftz_outside_list"],
    )
    args = parser.parse_args()

    if args.classify:
        result = classify(args.ciio, args.important, args.general, args.sensitive, args.exemption)
        print(render(result))
        print("\n" + json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.reindex:
        from chatbot.rag import get_index

        get_index(rebuild=True)
        print("索引已写入 storage/")
        if not args.question:
            return

    from chatbot.agent import answer

    if args.question:
        print(answer(args.question))
        return

    print("数据跨境问答。输入 exit 退出。人数门槛会调用规则工具，不会让模型心算。")
    history: list[dict] = []
    while True:
        try:
            question = input("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break
        reply = answer(question, history)
        history.extend(
            [
                {"role": "user", "content": question},
                {"role": "assistant", "content": reply},
            ]
        )
        print(f"\n{reply}")


if __name__ == "__main__":
    main()
