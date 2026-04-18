"""
向量检索模块 —— 使用 sentence-transformers 将知识库嵌入向量空间，
实现语义相似度检索，替代原有纯关键词匹配作为补充层。

模型：paraphrase-multilingual-MiniLM-L12-v2
  - 支持中英文双语
  - 模型大小约 120MB，首次运行自动下载
  - CPU 推理，查询延迟 < 100ms
"""

from __future__ import annotations

import json
import os
import pickle
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
CACHE_PATH = BASE_DIR / "data" / "vector_index.pkl"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# 全局缓存，避免重复加载模型
_model = None
_index: dict[str, Any] | None = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(MODEL_NAME)
        except ImportError:
            return None
        except Exception:
            return None
    return _model


def _text_for_item(item: dict[str, Any]) -> str:
    """将知识库条目转为用于嵌入的文本"""
    parts = []
    for field in ["title", "question", "knowledge_point", "topic",
                  "definition", "summary", "core_question", "key_insight",
                  "shipping_scenario", "math_concept"]:
        val = item.get(field, "")
        if val and str(val).strip():
            parts.append(str(val).strip())
    # 加入关键词
    for field in ["keywords", "knowledge_points"]:
        val = item.get(field, [])
        if isinstance(val, list):
            parts.extend(str(v) for v in val if v)
        elif isinstance(val, str) and val:
            parts.extend(v.strip() for v in val.split("|") if v.strip())
    return " ".join(parts)


def build_index(knowledge_base: dict[str, Any],
                interdisciplinary_cases: list[dict[str, Any]]) -> bool:
    """
    构建向量索引并缓存到磁盘。
    只在知识库内容变化时需要重新构建。
    """
    model = _get_model()
    if model is None:
        return False

    all_items: list[dict[str, Any]] = []
    all_texts: list[str] = []

    # 问题库
    for item in knowledge_base.get("problems", []):
        text = _text_for_item(item)
        if text.strip():
            all_items.append({"type": "problem", "data": item})
            all_texts.append(text)

    # 知识点库
    for item in knowledge_base.get("knowledge_points", []):
        text = _text_for_item(item)
        if text.strip():
            all_items.append({"type": "knowledge_point", "data": item})
            all_texts.append(text)

    # 跨学科案例库
    for item in interdisciplinary_cases:
        text = _text_for_item(item)
        if text.strip():
            all_items.append({"type": "interdisciplinary", "data": item})
            all_texts.append(text)

    if not all_texts:
        return False

    embeddings = model.encode(all_texts, batch_size=64,
                              show_progress_bar=False, normalize_embeddings=True)

    index = {
        "items": all_items,
        "texts": all_texts,
        "embeddings": embeddings,
    }

    with CACHE_PATH.open("wb") as f:
        pickle.dump(index, f)

    global _index
    _index = index
    return True


def _load_index() -> dict[str, Any] | None:
    global _index
    if _index is not None:
        return _index
    if not CACHE_PATH.exists():
        return None
    try:
        with CACHE_PATH.open("rb") as f:
            _index = pickle.load(f)
        return _index
    except Exception:
        return None


def vector_search(query: str, top_k: int = 3,
                  type_filter: str | None = None) -> list[dict[str, Any]]:
    """
    向量检索主入口。
    返回最相关的 top_k 条结果，每条包含 score、type、data。

    type_filter: "problem" | "knowledge_point" | "interdisciplinary" | None (全部)
    """
    model = _get_model()
    if model is None:
        return []

    index = _load_index()
    if index is None:
        return []

    import numpy as np
    query_emb = model.encode([query], normalize_embeddings=True)[0]
    embeddings = index["embeddings"]
    scores = embeddings @ query_emb  # 余弦相似度（已归一化）

    # 按类型过滤
    items = index["items"]
    filtered = [
        (i, float(scores[i]), items[i])
        for i in range(len(items))
        if type_filter is None or items[i]["type"] == type_filter
    ]

    # 排序取 top_k
    filtered.sort(key=lambda x: x[1], reverse=True)
    results = []
    for _, score, item in filtered[:top_k]:
        results.append({
            "score": round(score, 4),
            "type": item["type"],
            "data": item["data"],
        })
    return results


def vector_search_problems(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    return vector_search(query, top_k=top_k, type_filter="problem")


def vector_search_knowledge_points(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    return vector_search(query, top_k=top_k, type_filter="knowledge_point")


def vector_search_cases(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    return vector_search(query, top_k=top_k, type_filter="interdisciplinary")


def is_index_ready() -> bool:
    return CACHE_PATH.exists()
