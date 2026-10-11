# 数据跨境问答机器人

把阿里云大模型 ACP 课程里的问答链路，用到中国数据出境合规这个场景。

机器人回答的问题是：一批数据要不要办理出境手续，办理的是安全评估、标准合同，还是个人信息保护认证。人数门槛由代码计算，模型负责追问事实、检索知识库并解释依据。

回答用于学习制度路径，不构成法律意见。申报材料以《数据出境安全评估申报指南（第三版）》和现行标准合同文本为准。

## 课程能力对应到哪里

| 课程内容 | 在本项目中的位置 |
| --- | --- |
| 百炼兼容接口、多轮对话 | `chatbot/llm.py`、`chatbot/agent.py` |
| RAG 知识库 | `knowledge/`、`chatbot/rag.py` |
| 系统提示词和固定回答结构 | `chatbot/prompts.py` |
| 分块时把依据留在同一块 | `chatbot/rag.py` 按二级标题切分 |
| 自动化回归 | `eval/run_eval.py` |
| 工具调用，避免模型心算 | `chatbot/policy.py` 的 `classify_export` |
| 知识库没有依据时明确说未覆盖 | 系统提示词中的拒答句 |

制度依据是《促进和规范数据跨境流动规定》（国家互联网信息办公室令第16号，2024年3月22日起施行），以及国家网信办 2026年3月23日的配套进展通报。

## 环境

Python 3.10 及以上。在[阿里云百炼](https://bailian.console.aliyun.com/)创建 API Key。

```bash
cd /Users/edmond/developer/cross-border-data-qa
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

在 `.env` 中填入 `DASHSCOPE_API_KEY`。程序启动时会自动读取，终端里已经导出的同名变量优先。

## 使用

规则判断不调用模型，适合先核对门槛：

```bash
python app.py --classify --general 200000
python app.py --classify --sensitive 10000
python app.py --classify --general 500000 --exemption hr
```

建索引并开始问答：

```bash
python app.py --reindex
python app.py
python app.py -q "非关键信息基础设施运营者，今年出境20万一般个人信息、没有敏感个人信息，走哪条路径？"
python web.py
```

回归评测：

```bash
python -m unittest discover -s tests
python eval/run_eval.py
```

`unittest` 只检查路径规则和知识库文件，不访问百炼。`eval/run_eval.py` 会真实调用模型和向量检索。

## 目录

```text
app.py                 命令行
web.py                 浏览器问答
chatbot/policy.py      出境路径规则
chatbot/rag.py         建索引与检索
chatbot/agent.py       检索 + 工具调用 + 多轮对话
knowledge/             按条文整理的知识库
eval/questions.jsonl   回归问题
```
