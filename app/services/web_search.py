from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
from typing import Any


DUCKDUCKGO_HTML = "https://html.duckduckgo.com/html/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

FRESHNESS_KEYWORDS = (
    "最新",
    "近期",
    "最近",
    "当前",
    "今天",
    "本周",
    "本月",
    "今年",
    "news",
    "latest",
    "recent",
    "today",
    "current",
)


def looks_like_web_query(text: str, local_hit: bool = False) -> bool:
    normalized = str(text or "").strip().lower()
    if not normalized:
        return False
    if any(keyword in normalized for keyword in FRESHNESS_KEYWORDS):
        return True
    return not local_hit


def _strip_tags(value: str) -> str:
    value = re.sub(r"<.*?>", "", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _extract_results(page: str, max_results: int) -> list[dict[str, Any]]:
    pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
        r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
        flags=re.S,
    )
    results: list[dict[str, Any]] = []
    for match in pattern.finditer(page):
        href = html.unescape(match.group("href"))
        title = _strip_tags(match.group("title"))
        snippet = _strip_tags(match.group("snippet"))
        if not title or not href:
            continue
        if href.startswith("//"):
            href = "https:" + href
        domain = ""
        try:
            domain = urllib.parse.urlparse(href).netloc
        except Exception:
            domain = ""
        results.append({"title": title, "url": href, "snippet": snippet, "domain": domain})
        if len(results) >= max_results:
            break
    return results


def search_web(query: str, max_results: int = 3) -> list[dict[str, Any]]:
    text = str(query or "").strip()
    if not text:
        return []

    data = urllib.parse.urlencode({"q": text}).encode("utf-8")
    request = urllib.request.Request(
        DUCKDUCKGO_HTML,
        data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            page = response.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    return _extract_results(page, max_results=max_results)


def build_web_context(results: list[dict[str, Any]]) -> str:
    if not results:
        return ""
    parts = []
    for item in results:
        title = item.get("title", "").strip()
        snippet = item.get("snippet", "").strip()
        url = item.get("url", "").strip()
        line = f"[联网资料] {title}"
        if snippet:
            line += f"：{snippet}"
        if url:
            line += f" 来源：{url}"
        parts.append(line)
    return "\n".join(parts)
