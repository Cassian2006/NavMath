from app.services.knowledge import (
    detect_course,
    load_knowledge_base,
    match_problem,
    score_problem_match,
)


def test_weak_semantic_match_for_ocean_question() -> None:
    knowledge_base = load_knowledge_base()
    query = "国际贸易术语主要有什么用"
    match = match_problem(query, knowledge_base)

    assert match is not None
    assert "国际贸易术语" in str(match.get("question", "")) or "国际贸易术语" in str(match.get("title", ""))
    assert score_problem_match(query, match) >= 7


def test_course_detection_for_ocean_transport() -> None:
    assert detect_course("请解释一下国际贸易术语的主要作用") == "远洋运输业务"


def test_irrelevant_query_does_not_local_hit() -> None:
    knowledge_base = load_knowledge_base()
    query = "解释一下超弦理论与量子涨落的关系"

    assert match_problem(query, knowledge_base) is None
