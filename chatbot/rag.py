"""按 Markdown 标题分块，并用百炼向量模型检索。"""

from __future__ import annotations

from pathlib import Path

from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.schema import TextNode
from llama_index.embeddings.dashscope import (
    DashScopeEmbedding,
    DashScopeTextEmbeddingModels,
)

from config.settings import ROOT, load_api_key

KNOWLEDGE_DIR = ROOT / "knowledge"
PERSIST_DIR = ROOT / "storage"


def build_nodes() -> list[TextNode]:
    nodes: list[TextNode] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        for index, (title, body) in enumerate(split_markdown(path.read_text(encoding="utf-8"))):
            nodes.append(
                TextNode(
                    text=body,
                    metadata={"source": path.name, "title": title},
                    id_=f"{path.stem}-{index}",
                )
            )
    if not nodes:
        raise RuntimeError(f"知识库为空：{KNOWLEDGE_DIR}")
    return nodes


def split_markdown(text: str) -> list[tuple[str, str]]:
    """每个二级标题单独成块，块内保留来源，避免检索时法条和结论拆散。"""
    sections: list[tuple[str, str]] = []
    title = "概述"
    buffer: list[str] = []
    for line in text.splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            continue
        if line.startswith("## "):
            _flush(sections, title, buffer)
            title = line[3:].strip()
            buffer = []
        else:
            buffer.append(line)
    _flush(sections, title, buffer)
    return sections


def get_index(rebuild: bool = False) -> VectorStoreIndex:
    load_api_key()
    embed_model = DashScopeEmbedding(model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V2)
    if not rebuild and _has_index():
        storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
        return load_index_from_storage(storage_context, embed_model=embed_model)
    index = VectorStoreIndex(build_nodes(), embed_model=embed_model)
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    index.storage_context.persist(persist_dir=str(PERSIST_DIR))
    return index


def retrieve_context(question: str, top_k: int = 4) -> str:
    try:
        index = get_index()
    except Exception as exc:
        return f"（知识库索引还不可用：{exc}。可先运行 python app.py --reindex。人数门槛仍可调用 classify_export。）"
    nodes = index.as_retriever(similarity_top_k=top_k).retrieve(question)
    if not nodes:
        return "（没有检索到相关摘录）"
    blocks = []
    for node in nodes:
        source = node.metadata.get("source", "知识库")
        title = node.metadata.get("title", "摘录")
        blocks.append(f"[{source}｜{title}]\n{node.text.strip()}")
    return "\n\n".join(blocks)


def _has_index() -> bool:
    return (PERSIST_DIR / "docstore.json").exists()


def _flush(sections: list[tuple[str, str]], title: str, buffer: list[str]) -> None:
    body = "\n".join(buffer).strip()
    if body:
        sections.append((title, body))
