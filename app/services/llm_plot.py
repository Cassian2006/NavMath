from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


DEFAULT_API_BASE = "https://api.moonshot.cn/v1"
DEFAULT_MODEL = "moonshot-v1-8k"


def parse_natural_language_plot(text: str) -> dict[str, Any] | None:
    api_key = (
        os.getenv("KIMI_API_KEY", "").strip()
        or os.getenv("MOONSHOT_API_KEY", "").strip()
        or os.getenv("DEEPSEEK_API_KEY", "").strip()
    )
    if not api_key:
        return None

    api_base = os.getenv("KIMI_API_BASE", DEFAULT_API_BASE).rstrip("/")
    model = os.getenv("KIMI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是数学与工程绘图助手。"
                    "请把用户的自然语言绘图需求转换成严格 JSON。"
                    "如果能归纳成公式，请填写 formula；如果更像常见几何体，请填写 shape_kind。"
                    "shape_kind 只能是 sphere、cylinder、cone、torus、helix、saddle、wave 之一。"
                    "尽量返回可直接运行的 MATLAB 代码。"
                    "不要输出 JSON 之外的任何内容。"
                ),
            },
            {"role": "user", "content": build_prompt(text)},
        ],
        "temperature": 0.1,
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

    content = body["choices"][0]["message"]["content"]
    parsed = extract_json_object(content)
    if not parsed:
        raise RuntimeError("Kimi 绘图返回内容无法解析为 JSON。")

    parsed["parser"] = "kimi"
    return parsed


def build_prompt(text: str) -> str:
    schema = {
        "recognized": True,
        "formula": "可选，例如 z = x^2 - y^2 或 y = exp(-x^2)",
        "shape_kind": "可选，只能是 sphere/cylinder/cone/torus/helix/saddle/wave",
        "plot_label": "例如 三维曲面 / 二维函数 / MATLAB绘图",
        "summary": "一句中文摘要",
        "teaching_tip": "一句中文教学提示",
        "matlab_code": "可直接运行的 MATLAB 代码字符串",
    }
    return (
        "用户需求如下，请输出 JSON：\n"
        f"{text}\n"
        f"JSON 模板：{json.dumps(schema, ensure_ascii=False)}\n"
        "要求：\n"
        "1. 能转成公式就填 formula。\n"
        "2. 能转成常见图形就填 shape_kind。\n"
        "3. 尽量返回可以运行的 matlab_code。\n"
        "4. 只输出 JSON。"
    )


def extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
