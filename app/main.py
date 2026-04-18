from __future__ import annotations

import json
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.services.imports import handle_csv_import, load_import_dashboard
from app.services.knowledge import (
    detect_course,
    find_formula_record,
    load_interdisciplinary_cases,
    load_knowledge_base,
    match_interdisciplinary_case,
    match_knowledge_point,
    match_problem,
    normalize_text,
    score_knowledge_point_match,
    score_problem_match,
    split_pipe_text,
)
from app.services.llm_answer import answer_question_with_kimi
from app.services.llm_plot import parse_natural_language_plot
from app.services.math_plot import build_plot_bundle, extract_formula_text, extract_formula_texts, suggest_formula
from app.services.ocr import extract_text_from_image
from app.services.vector_search import (
    build_index,
    is_index_ready,
    vector_search,
)
from app.services.visualization import build_shape_bundle, build_shape_bundle_from_kind


load_dotenv()

app = FastAPI(title="NavMath Vision API", version="0.6.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def error_response(message: str, status_code: int = 502) -> JSONResponse:
    return JSONResponse({"detail": message}, status_code=status_code)


def looks_like_plot_request(text: str) -> bool:
    normalized = normalize_text(text).lower()
    plot_keywords = [
        "画",
        "绘",
        "图像",
        "绘图",
        "曲线",
        "曲面",
        "三维",
        "二维",
        "matlab",
        "3d",
        "surface",
        "plot",
        "mesh",
        "=",
    ]
    return any(keyword in normalized for keyword in plot_keywords)


def build_fallback_problem(course: str) -> dict[str, Any]:
    return {
        "title": "未命中预置题库",
        "course": course,
        "knowledge_points": ["待补充知识点"],
        "analysis_steps": [
            "系统未在当前题库中找到直接匹配项。",
            "当前输入已保留，后续可补充到知识点表或题目表中。",
            "如果输入里包含公式或图形意图，系统仍会继续尝试给出绘图结果。",
        ],
        "solution": "当前问题未命中本地题库，可在后续补充到结构化数据中，或在模型可用时由大模型补答。",
    }


def normalize_matched_problem(problem: dict[str, Any] | None) -> dict[str, Any] | None:
    if problem is None:
        return None

    normalized = dict(problem)
    normalized["knowledge_points"] = split_pipe_text(normalized.get("knowledge_points", []))
    normalized["analysis_steps"] = split_pipe_text(normalized.get("analysis_steps", []))
    normalized["options"] = split_pipe_text(normalized.get("options", []))
    return normalized


def normalize_knowledge_point_item(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if item is None:
        return None

    normalized = dict(item)
    normalized["keywords"] = split_pipe_text(normalized.get("keywords", []))
    return normalized


def build_source_detail(
    parser: str,
    matched_problem: dict[str, Any] | None,
    matched_knowledge_point: dict[str, Any] | None,
    plot: dict[str, Any] | None,
) -> str:
    if parser == "kimi":
        if plot:
            return "Kimi 已将自然语言转成绘图意图，并生成可展示的图形结果。"
        return "本地知识库未命中，已切换到 Kimi 二级中转回答。"

    if plot:
        return "本地公式解析或预设绘图规则已命中。"
    if matched_problem and matched_problem.get("title") != "未命中预置题库":
        return "本地题库已命中。"
    if matched_knowledge_point:
        return "本地知识点库已命中。"
    return "当前结果来自本地默认回退。"


def classify_confidence(score: int, parser: str, plot: dict[str, Any] | None) -> str:
    if parser == "kimi":
        return "模型兜底"
    if plot is not None and score <= 0:
        return "规则命中"
    if score >= 18:
        return "高"
    if score >= 10:
        return "中"
    if score > 0:
        return "低"
    return "未命中"


def build_match_meta(
    cleaned_text: str,
    matched_problem: dict[str, Any] | None,
    matched_knowledge_point: dict[str, Any] | None,
    formula_record: dict[str, Any] | None,
    parser: str,
    plot: dict[str, Any] | None,
) -> dict[str, Any]:
    problem_score = score_problem_match(cleaned_text, matched_problem)
    knowledge_score = score_knowledge_point_match(cleaned_text, matched_knowledge_point)

    if parser == "kimi":
        match_type = "llm_fallback"
        score = 0
    elif plot is not None and formula_record is not None:
        match_type = "formula_record"
        score = 10
    elif plot is not None and not matched_problem and not matched_knowledge_point:
        match_type = "plot_rule"
        score = 8
    elif problem_score >= knowledge_score and matched_problem is not None:
        match_type = "problem"
        score = problem_score
    elif matched_knowledge_point is not None:
        match_type = "knowledge_point"
        score = knowledge_score
    else:
        match_type = "fallback"
        score = 0

    return {
        "type": match_type,
        "score": score,
        "confidence": classify_confidence(score, parser, plot),
    }


def resolve_view_mode(
    matched_problem: dict[str, Any] | None,
    matched_knowledge_point: dict[str, Any] | None,
    plot: dict[str, Any] | None,
) -> str:
    if plot:
        return "visualization"
    if matched_knowledge_point and (
        matched_problem is None
        or matched_problem.get("title") == "未命中预置题库"
        or matched_problem.get("course") == "船舶保安"
    ):
        return "knowledge"
    if matched_problem and matched_problem.get("title") != "未命中预置题库":
        return "problem"
    return "problem"


def build_llm_plot(cleaned_text: str) -> tuple[dict[str, Any] | None, str | None, str]:
    llm_result = parse_natural_language_plot(cleaned_text)
    if not llm_result:
        return None, None, "local"

    parser = llm_result.get("parser", "kimi")
    llm_formula = str(llm_result.get("formula", "")).strip() or None
    llm_shape_kind = str(llm_result.get("shape_kind", "")).strip().lower() or None
    plot = None

    if llm_formula:
        try:
            plot = build_plot_bundle(llm_formula)
        except Exception:
            plot = None

    if plot is None and llm_shape_kind:
        plot = build_shape_bundle_from_kind(llm_shape_kind)

    if plot is None and llm_result.get("matlab_code"):
        plot = {
            "plot_type": "matlab_only",
            "plot_label": llm_result.get("plot_label", "MATLAB 绘图"),
            "data": [],
            "layout": {},
            "summary": llm_result.get("summary", "已根据自然语言生成 MATLAB 绘图代码。"),
            "matlab_code": llm_result.get("matlab_code", ""),
            "teaching_tip": llm_result.get("teaching_tip", ""),
        }

    if plot is not None:
        plot["parser"] = parser
        if llm_result.get("summary"):
            plot["summary"] = llm_result["summary"]
        if llm_result.get("teaching_tip"):
            plot["teaching_tip"] = llm_result["teaching_tip"]
        if llm_result.get("plot_label"):
            plot["plot_label"] = llm_result["plot_label"]

    return plot, llm_formula, parser


def compose_analysis(
    text: str,
    formula: str | None = None,
    previous_plot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    knowledge_base = load_knowledge_base()
    cleaned_text = normalize_text(text)
    detected_course = detect_course(cleaned_text)
    matched_problem = match_problem(cleaned_text, knowledge_base)
    matched_knowledge_point = match_knowledge_point(cleaned_text, knowledge_base)

    # ── 跨学科案例检索（关键词层） ──
    matched_case = match_interdisciplinary_case(cleaned_text)

    # ── 向量检索补充层（仅在关键词层未命中时启用，避免延迟影响已命中结果） ──
    vector_results: list[dict] = []
    if is_index_ready() and not matched_problem and not matched_knowledge_point and not matched_case:
        try:
            vector_results = vector_search(cleaned_text, top_k=3)
            # 若向量检索命中跨学科案例，补充到 matched_case
            for vr in vector_results:
                if vr["type"] == "interdisciplinary" and vr["score"] >= 0.55:
                    matched_case = vr["data"]
                    break
                if vr["type"] == "problem" and vr["score"] >= 0.65 and not matched_problem:
                    matched_problem = vr["data"]
                    break
                if vr["type"] == "knowledge_point" and vr["score"] >= 0.60 and not matched_knowledge_point:
                    matched_knowledge_point = vr["data"]
                    break
        except Exception:
            vector_results = []
    raw_formula = formula or ""
    detected_formula = suggest_formula(raw_formula) or suggest_formula(cleaned_text)
    detected_formulas = extract_formula_texts(raw_formula) or extract_formula_texts(cleaned_text)
    formula_record = find_formula_record(detected_formula, knowledge_base) if detected_formula else None
    plot = None
    parser = "local"
    plot_requested = bool(detected_formula) or looks_like_plot_request(cleaned_text)

    if detected_formula:
        try:
            plot = build_plot_bundle(raw_formula or cleaned_text, previous_plot=previous_plot)
            plot["parser"] = "local"
        except Exception as exc:
            plot = {
                "plot_type": "unsupported",
                "plot_label": "绘图失败",
                "data": [],
                "layout": {},
                "summary": f"公式已识别，但当前 MVP 暂不支持该表达式绘图：{exc}",
                "matlab_code": "",
                "teaching_tip": "",
                "parser": "local",
                "error_detail": str(exc),
            }
    elif cleaned_text:
        if previous_plot:
            try:
                plot = build_plot_bundle(cleaned_text, previous_plot=previous_plot)
                plot["parser"] = "local"
            except Exception as exc:
                plot = {
                    "plot_type": "unsupported",
                    "plot_label": "绘图失败",
                    "data": [],
                    "layout": {},
                    "summary": f"图像修改失败：{exc}",
                    "matlab_code": "",
                    "teaching_tip": "",
                    "parser": "local",
                    "error_detail": str(exc),
                }
        elif plot_requested:
            try:
                plot = build_plot_bundle(cleaned_text)
                plot["parser"] = "local"
            except Exception:
                plot = None
        if plot is None:
            plot = build_shape_bundle(cleaned_text)
            if plot:
                plot["parser"] = "local"

    result_formula = extract_formula_text(detected_formula) if detected_formula else None

    if plot is None and plot_requested and cleaned_text:
        llm_plot, llm_formula, parser = build_llm_plot(cleaned_text)
        if llm_plot is not None:
            plot = llm_plot
            if not result_formula and llm_formula:
                result_formula = llm_formula

    if plot is None and formula_record and formula_record.get("formula"):
        try:
            plot = build_plot_bundle(formula_record["formula"])
            plot["parser"] = "local"
        except Exception as exc:
            plot = {
                "plot_type": "unsupported",
                "plot_label": "绘图失败",
                "data": [],
                "layout": {},
                "summary": f"预置公式存在，但当前绘图失败：{exc}",
                "matlab_code": "",
                "teaching_tip": "",
                "parser": "local",
                "error_detail": str(exc),
            }

    if not result_formula and formula_record:
        result_formula = formula_record.get("formula")

    local_hit = matched_problem is not None or matched_knowledge_point is not None or formula_record is not None
    if not local_hit and cleaned_text:
        kimi_answer = answer_question_with_kimi(cleaned_text, detected_course)
        if kimi_answer is not None:
            matched_problem = kimi_answer

    if matched_problem is None:
        matched_problem = build_fallback_problem(detected_course)

    matched_problem = normalize_matched_problem(matched_problem)
    matched_knowledge_point = normalize_knowledge_point_item(matched_knowledge_point)

    resolved_parser = plot.get("parser", parser) if plot else matched_problem.get("parser", parser)
    match_meta = build_match_meta(
        cleaned_text,
        matched_problem,
        matched_knowledge_point,
        formula_record,
        resolved_parser,
        plot,
    )
    view_mode = resolve_view_mode(matched_problem, matched_knowledge_point, plot)

    return {
        "input_text": cleaned_text,
        "detected_course": detected_course,
        "view_mode": view_mode,
        "matched_problem": matched_problem,
        "matched_knowledge_point": matched_knowledge_point,
        "matched_case": matched_case,
        "vector_results": [
            {"score": r["score"], "type": r["type"],
             "title": r["data"].get("title", r["data"].get("question", "")[:40])}
            for r in vector_results
        ],
        "formula": result_formula,
        "formulas": plot.get("formulas", detected_formulas) if plot else detected_formulas,
        "formula_record": formula_record,
        "plot": plot,
        "parser": resolved_parser,
        "match_meta": match_meta,
        "source_detail": build_source_detail(
            resolved_parser,
            matched_problem,
            matched_knowledge_point,
            plot,
        ),
    }


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "name": "NavMath Vision API",
        "frontend": "Use the Vue + Vite app in /frontend",
        "docs": "/docs",
    }


@app.post("/api/analyze-text")
async def analyze_text(
    question_text: str = Form(""),
    formula: str = Form(""),
    previous_plot: str = Form(""),
) -> JSONResponse:
    merged_text = "\n".join(filter(None, [question_text, formula]))
    try:
        plot_payload = json.loads(previous_plot) if previous_plot.strip() else None
        return JSONResponse(compose_analysis(merged_text, formula or None, plot_payload))
    except RuntimeError as exc:
        return error_response(str(exc))
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        return error_response(f"后端处理失败: {exc}", status_code=500)


@app.post("/api/analyze-image")
async def analyze_image(file: UploadFile = File(...), formula: str = Form("")) -> JSONResponse:
    try:
        file_bytes = await file.read()
        ocr_result = extract_text_from_image(file_bytes)
        result = compose_analysis(ocr_result["text"], formula or None)
        result["ocr"] = ocr_result
        result["filename"] = file.filename
        return JSONResponse(result)
    except RuntimeError as exc:
        return error_response(str(exc))
    except Exception as exc:
        return error_response(f"后端处理失败: {exc}", status_code=500)


@app.get("/api/import-status")
async def import_status() -> JSONResponse:
    return JSONResponse(load_import_dashboard())


@app.post("/api/import-csv")
async def import_csv(kind: str = Form(...), file: UploadFile = File(...)) -> JSONResponse:
    content = await file.read()
    return JSONResponse(handle_csv_import(kind, content))


@app.post("/api/build-index")
async def build_vector_index() -> JSONResponse:
    """构建/重建向量索引。知识库有大幅更新时调用一次即可。"""
    try:
        kb = load_knowledge_base()
        cases = load_interdisciplinary_cases()
        ok = build_index(kb, cases)
        if ok:
            return JSONResponse({
                "status": "ok",
                "message": f"向量索引构建成功：{len(kb.get('problems', []))}题 + "
                           f"{len(kb.get('knowledge_points', []))}知识点 + "
                           f"{len(cases)}跨学科案例"
            })
        return JSONResponse({"status": "skip", "message": "sentence-transformers 未安装或知识库为空"})
    except Exception as exc:
        return error_response(f"索引构建失败: {exc}", status_code=500)


@app.get("/api/index-status")
async def index_status() -> JSONResponse:
    return JSONResponse({
        "ready": is_index_ready(),
        "message": "向量索引已就绪" if is_index_ready() else "向量索引未构建，请调用 POST /api/build-index"
    })


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
