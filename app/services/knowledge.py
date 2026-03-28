from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "knowledge_base.json"
IMPORT_DIR = BASE_DIR / "data" / "imports"

MIN_PROBLEM_SCORE = 7
MIN_KNOWLEDGE_SCORE = 6

SEMANTIC_REWRITE_RULES = [
    ("主要作用是什么", "作用"),
    ("有什么作用", "作用"),
    ("有何作用", "作用"),
    ("主要功能是什么", "功能"),
    ("有什么功能", "功能"),
    ("用途是什么", "用途"),
    ("怎么理解", "解释"),
    ("请解释", "解释"),
    ("解释一下", "解释"),
    ("是什么意思", "定义"),
    ("什么叫", "定义"),
    ("叫什么", "定义"),
    ("属于什么类型", "类型"),
    ("是什么类型", "类型"),
    ("怎么判断", "判断"),
    ("如何判断", "判断"),
]

SEMANTIC_ALIASES = {
    "国际贸易术语": ["贸易术语", "incoterms"],
    "远洋运输业务": ["远洋运输", "航运业务", "国际航运"],
    "船舶保安": ["船舶安全保安", "保安体系"],
    "双曲抛物面": ["鞍面", "马鞍面"],
    "抛物面": ["碗状曲面", "碗面"],
    "极限": ["limit", "趋近"],
    "导数": ["求导", "微分"],
    "积分": ["积分计算", "定积分", "不定积分"],
    "曲面": ["三维图形", "三维曲面"],
}

STOP_PHRASES = [
    "请问",
    "一下",
    "这个",
    "这个题",
    "这道题",
    "帮我",
    "给我",
    "一下子",
    "一下吧",
]


@dataclass
class MatchResult:
    score: int
    item: dict[str, Any]


def load_knowledge_base() -> dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        knowledge_base = json.load(file)

    imported = load_imported_records()
    if imported["problems"]:
        knowledge_base["problems"].extend(imported["problems"])
    if imported["knowledge_points"]:
        knowledge_base["knowledge_points"].extend(imported["knowledge_points"])

    knowledge_base["problems"] = [item for item in knowledge_base.get("problems", []) if not is_broken_record(item)]
    knowledge_base["knowledge_points"] = [
        item for item in knowledge_base.get("knowledge_points", []) if not is_broken_record(item)
    ]
    return knowledge_base


def load_imported_records() -> dict[str, list[dict[str, Any]]]:
    result = {"knowledge_points": [], "problems": []}
    knowledge_file = _find_import_file("knowledge_points")
    problem_file = _find_import_file("problems")

    if knowledge_file is not None:
        result["knowledge_points"] = _read_tabular_records(knowledge_file)
    if problem_file is not None:
        result["problems"] = _read_tabular_records(problem_file)
    return result


def get_import_status() -> dict[str, Any]:
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for stem in ["knowledge_points", "problems"]:
        path = _find_import_file(stem)
        files.append(
            {
                "name": path.name if path is not None else f"{stem}.csv",
                "exists": path is not None,
                "size": path.stat().st_size if path is not None else 0,
            }
        )

    imported = load_imported_records()
    return {
        "directory": str(IMPORT_DIR),
        "files": files,
        "counts": {
            "knowledge_points": len(imported["knowledge_points"]),
            "problems": len(imported["problems"]),
        },
    }


def save_import_csv(kind: str, content: bytes) -> dict[str, Any]:
    mapping = {
        "knowledge_points": "knowledge_points.csv",
        "problems": "problems.csv",
    }
    if kind not in mapping:
        raise ValueError("仅支持 knowledge_points 和 problems 两种导入类型。")

    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    target = IMPORT_DIR / mapping[kind]
    target.write_bytes(content)

    records = _read_csv_records(target)
    return {"kind": kind, "path": str(target), "count": len(records)}


def _read_csv_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _read_xlsx_records(path: Path) -> list[dict[str, Any]]:
    frame = pd.read_excel(path).fillna("")
    return [
        {str(key): _clean_cell_value(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def _read_tabular_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".xlsx":
        return _read_xlsx_records(path)
    return _read_csv_records(path)


def _find_import_file(stem: str) -> Path | None:
    for suffix in [".csv", ".xlsx"]:
        candidate = IMPORT_DIR / f"{stem}{suffix}"
        if candidate.exists():
            return candidate
    return None


def _clean_cell_value(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def normalize_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def semantic_normalize_text(text: Any) -> str:
    normalized = normalize_text(text).lower()
    for source, target in SEMANTIC_REWRITE_RULES:
        normalized = normalized.replace(source, target)
    for phrase in STOP_PHRASES:
        normalized = normalized.replace(phrase, "")
    return normalized.strip()


def simplify_match_text(text: Any) -> str:
    simplified = semantic_normalize_text(text)
    simplified = re.sub(r"[（）()\[\]【】《》“”‘’：:，。！？、；;·\-\s]", "", simplified)
    simplified = re.sub(
        r"(什么是|是什么|是否|多少|哪些|有何|怎么|如何|为什么|呢|吗)$",
        "",
        simplified,
    )
    return simplified


def expand_semantic_forms(text: Any) -> set[str]:
    base = semantic_normalize_text(text)
    forms = {normalize_text(text).lower(), base, simplify_match_text(text)}
    seeds = list(forms)
    for canonical, aliases in SEMANTIC_ALIASES.items():
        hit = False
        for seed in seeds:
            if canonical in seed or any(alias in seed for alias in aliases):
                hit = True
                break
        if not hit:
            continue

        forms.add(canonical)
        forms.add(simplify_match_text(canonical))
        for alias in aliases:
            forms.add(alias)
            forms.add(simplify_match_text(alias))
    return {form for form in forms if form}


def split_pipe_text(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split("|") if part.strip()]
    return []


def is_broken_text(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    if text.count("?") >= 3:
        return True
    if "\ufffd" in text:
        return True
    return False


def is_broken_record(item: dict[str, Any]) -> bool:
    fields = [
        item.get("question"),
        item.get("title"),
        item.get("knowledge_point"),
        item.get("definition"),
    ]
    return any(is_broken_text(field) for field in fields)


def _text_overlap_score(query: str, candidate: str) -> int:
    if not query or not candidate:
        return 0
    if query == candidate:
        return 14
    if candidate in query:
        return 9 if len(candidate) >= 4 else 5
    if query in candidate:
        return 7 if len(query) >= 5 else 3
    return 0


def _token_overlap_score(query: str, candidate: str) -> int:
    if not query or not candidate:
        return 0
    query_tokens = set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]{2,}", query))
    candidate_tokens = set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]{2,}", candidate))
    if not query_tokens or not candidate_tokens:
        return 0
    common = query_tokens & candidate_tokens
    if not common:
        return 0
    return min(len(common) * 2, 8)


def _semantic_similarity_score(query: str, candidate: str) -> int:
    if not query or not candidate:
        return 0
    ratio = SequenceMatcher(None, query, candidate).ratio()
    if ratio >= 0.9:
        return 6
    if ratio >= 0.8:
        return 4
    if ratio >= 0.68:
        return 2
    return 0


def _field_score(query_forms: set[str], candidate_text: Any) -> int:
    candidate_forms = expand_semantic_forms(candidate_text)
    best = 0
    for query_form in query_forms:
        for candidate_form in candidate_forms:
            score = 0
            score += _text_overlap_score(query_form, candidate_form)
            score += _token_overlap_score(query_form, candidate_form)
            score += _semantic_similarity_score(query_form, candidate_form)
            if score > best:
                best = score
    return best


def _score_match(text: str, item: dict[str, Any], extra_fields: list[str] | None = None) -> int:
    query_forms = expand_semantic_forms(text)
    score = 0

    primary_fields = ["title", "question", "knowledge_point", "topic", "section"]
    if extra_fields:
        primary_fields.extend(extra_fields)

    for field in primary_fields:
        field_score = _field_score(query_forms, item.get(field, ""))
        if field in {"title", "question", "knowledge_point"}:
            field_score += 1 if field_score else 0
        score += field_score

    for keyword in split_pipe_text(item.get("keywords", [])):
        score += _field_score(query_forms, keyword)

    for point in split_pipe_text(item.get("knowledge_points", [])):
        score += _field_score(query_forms, point)

    return score


def _best_match(
    items: list[dict[str, Any]],
    text: str,
    min_score: int,
    extra_fields: list[str] | None = None,
) -> dict[str, Any] | None:
    matches: list[MatchResult] = []
    for item in items:
        score = _score_match(text, item, extra_fields=extra_fields)
        if score >= min_score:
            matches.append(MatchResult(score=score, item=item))

    if not matches:
        return None

    matches.sort(key=lambda result: result.score, reverse=True)
    return matches[0].item


def score_problem_match(text: str, item: dict[str, Any] | None) -> int:
    if item is None:
        return 0
    return _score_match(normalize_text(text).lower(), item)


def score_knowledge_point_match(text: str, item: dict[str, Any] | None) -> int:
    if item is None:
        return 0
    return _score_match(normalize_text(text).lower(), item, extra_fields=["definition", "summary"])


def match_problem(text: str, knowledge_base: dict[str, Any]) -> dict[str, Any] | None:
    normalized = normalize_text(text).lower()
    return _best_match(knowledge_base.get("problems", []), normalized, min_score=MIN_PROBLEM_SCORE)


def match_knowledge_point(text: str, knowledge_base: dict[str, Any]) -> dict[str, Any] | None:
    normalized = normalize_text(text).lower()
    return _best_match(
        knowledge_base.get("knowledge_points", []),
        normalized,
        min_score=MIN_KNOWLEDGE_SCORE,
        extra_fields=["definition", "summary"],
    )


def find_formula_record(formula: str, knowledge_base: dict[str, Any]) -> dict[str, Any] | None:
    normalized = normalize_text(formula).replace(" ", "").lower()
    for item in knowledge_base.get("formulas", []):
        aliases = [alias.replace(" ", "").lower() for alias in item.get("aliases", [])]
        if normalized in aliases:
            return item
    return None


def detect_course(text: str) -> str:
    normalized = normalize_text(text).lower()
    maritime_keywords = [
        "船舶保安",
        "isps",
        "solas",
        "stcw",
        "远洋运输",
        "远洋运输业务",
        "国际贸易术语",
        "国际贸易惯例",
        "incoterms",
        "提单",
        "班轮",
        "租船",
        "港口设施保安",
        "海盗",
        "保安等级",
    ]
    if any(keyword in normalized for keyword in maritime_keywords):
        return "远洋运输业务"
    return "高等数学"
