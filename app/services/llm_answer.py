from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from app.services.web_search import build_web_context


DEFAULT_API_BASE = "https://api.moonshot.cn/v1"
DEFAULT_MODEL = "moonshot-v1-8k"


def _retrieve_context(text: str) -> str:
    """召回本地向量检索结果，拼成上下文字符串供 prompt 使用。"""
    try:
        from app.services.vector_search import is_index_ready, vector_search
        if not is_index_ready():
            return ""
        results = vector_search(text, top_k=3)
        if not results:
            return ""
        parts = []
        for r in results:
            d = r["data"]
            if r["type"] == "problem":
                chunk = f"[题目] {d.get('question', '')} 答案：{d.get('answer', '')} 解析：{d.get('analysis_steps', '')}"
            elif r["type"] == "knowledge_point":
                chunk = f"[知识点] {d.get('knowledge_point', '')}：{d.get('definition', '')} {d.get('summary', '')}"
            else:
                chunk = f"[跨学科案例] {d.get('title', '')}：{d.get('key_insight', '')}"
            parts.append(chunk.strip())
        return "\n".join(parts)
    except Exception:
        return ""


def answer_question_with_kimi(text: str, course: str, web_results: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    api_key = (
        os.getenv("KIMI_API_KEY", "").strip()
        or os.getenv("MOONSHOT_API_KEY", "").strip()
        or os.getenv("DEEPSEEK_API_KEY", "").strip()
    )
    if not api_key or not text.strip():
        return None

    api_base = os.getenv("KIMI_API_BASE", DEFAULT_API_BASE).rstrip("/")
    model = os.getenv("KIMI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    local_context = _retrieve_context(text)
    web_context = build_web_context(web_results or [])
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是课程学习辅助系统里的教学问答助手。"
                    "请优先基于提供的本地资料回答，再把联网补充信息作为扩展说明。"
                    "如果联网资料和本地教材有冲突，先说明本地教材口径，再单独提示联网信息。"
                    "直接输出严格 JSON，不要输出 JSON 之外的任何内容。"
                ),
            },
            {
                "role": "user",
                "content": build_answer_prompt(text, course, local_context, web_context),
            },
        ],
        "temperature": 0.3,
    }

    request = urllib.request.Request(
        f"{api_base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Kimi API 请求失败: HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Kimi API 网络错误: {exc}") from exc

    content = body["choices"][0]["message"]["content"].strip()
    parsed = _extract_json_object(content)
    if not parsed:
        raise RuntimeError("Kimi 问答返回内容无法解析为 JSON。")

    normalized = normalize_answer_payload(parsed, text, course)
    normalized["parser"] = "kimi"
    normalized["web_results_used"] = web_results or []
    return normalized


def build_answer_prompt(text: str, course: str, local_context: str = "", web_context: str = "") -> str:
    schema = {
        "title": "一句话标题，2到10个字",
        "course": course or "通用课程",
        "knowledge_points": ["知识点1", "知识点2"],
        "analysis_steps": [
            "先直接回答问题。",
            "再解释关键概念或判断依据。",
            "最后给出一个理解提示或应用场景。",
        ],
        "solution": "写成适合学生阅读的短正文，先给结论，再解释，再补一句提示。",
    }
    local_section = (
        f"\n本地资料（优先依据这部分回答）：\n{local_context}\n"
        if local_context else "\n本地资料：当前未命中直接材料。\n"
    )
    web_section = (
        f"\n联网补充资料（用于补充最新信息或现实案例）：\n{web_context}\n"
        if web_context else "\n联网补充资料：当前未检索到有效结果。\n"
    )
    return (
        f"课程：{course or '未指定'}\n"
        f"用户问题：{text}\n"
        f"{local_section}"
        f"{web_section}\n"
        f"请按这个 JSON 模板返回：{json.dumps(schema, ensure_ascii=False)}\n"
        "要求：\n"
        "1. solution 适合直接展示给学生，不要写成碎片化条目。\n"
        "2. analysis_steps 控制在 3 到 4 条，每条一句话。\n"
        "3. knowledge_points 只保留最相关的 2 到 4 个。\n"
        "4. 若使用了联网资料，请在 solution 中用一句简短的话说明这是补充信息，不要编造来源。\n"
        "5. 不要出现 markdown，不要出现 JSON 之外的任何内容。"
    )


def normalize_answer_payload(payload: dict[str, Any], text: str, course: str) -> dict[str, Any]:
    knowledge_points = _normalize_string_list(payload.get("knowledge_points"), fallback=["模型补充回答"])
    analysis_steps = _normalize_string_list(
        payload.get("analysis_steps"),
        fallback=[
            "先给出问题的直接结论。",
            "再解释核心概念或判断依据。",
            "最后补充一个理解提示。",
        ],
    )
    solution = _normalize_solution(payload.get("solution"))

    return {
        "title": _normalize_text(payload.get("title"), fallback="Kimi 补充回答"),
        "course": _normalize_text(payload.get("course"), fallback=course or "通用课程"),
        "knowledge_points": knowledge_points,
        "analysis_steps": analysis_steps,
        "solution": solution,
        "question": text,
        "answer": solution,
    }


def _normalize_solution(value: Any) -> str:
    text = _normalize_text(value, fallback="")
    if text:
        return text
    return "当前由模型补充回答，但未返回完整正文。"


def _normalize_string_list(value: Any, fallback: list[str]) -> list[str]:
    if isinstance(value, list):
        items = [_normalize_text(item) for item in value]
        items = [item for item in items if item]
        if items:
            return items
    if isinstance(value, str):
        text = value.strip()
        if text:
            parts = [part.strip(" ：:、.-") for part in text.replace("\r", "\n").split("\n")]
            parts = [part for part in parts if part]
            if parts:
                return parts
    return fallback


def _normalize_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
