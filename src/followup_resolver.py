from __future__ import annotations

"""Phase 7 follow-up resolver.

The resolver is conservative:
- It only reuses prior context when the new question looks like a follow-up.
- It never returns estimates itself; it only builds a safer resolved question for
  the deterministic estimate/FAQ tools to answer.
- OpenAI structured routing is optional and validated/fallback-only.
"""

from typing import Any, Dict, Optional, Tuple
import re
from normalize_text import normalize_text
from model_orchestrator import resolve_followup_with_model

GROUP_PHRASES = {
    "svi": "SVI",
    "social vulnerability": "SVI",
    "sex": "sex",
    "gender": "sex",
    "age": "age",
    "race and ethnicity": "race and ethnicity",
    "race and hispanic": "race and ethnicity",
    "race": "race",
    "ethnicity": "race and ethnicity",
    "insurance": "insurance",
    "coverage": "insurance",
    "income": "family income",
    "family income": "family income",
    "household income": "family income",
    "poverty": "family income",
    "fpl": "family income",
    "region": "region",
    "metro": "metro",
    "msa": "metro",
    "urbanicity": "metro",
    "place of residence": "place of residence",
    "disability": "disability",
    "difficulty": "difficulty",
    "sexual orientation": "sexual orientation",
}

CHILD_WORDS = ["child", "children", "kid", "kids", "youth", "adolescent", "adolescents", "pediatric"]
ADULT_WORDS = ["adult", "adults", "18+", "18 and over"]


def _contains_phrase(q: str, phrase: str) -> bool:
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(normalize_text(phrase)) + r"(?![a-z0-9])", q))


def _has_topic_like_content(q: str) -> bool:
    # Follow-up questions are usually short and modifier-only. If these common
    # topic words appear, let the normal router handle it as a fresh question.
    topics = [
        "asthma", "diabetes", "flu", "influenza", "hypertension", "blood pressure",
        "uninsured", "insurance", "obesity", "smoking", "vaping", "adhd",
        "depression", "anxiety", "cholesterol", "doctor", "urgent", "care",
        "vaccination", "health status", "disability", "difficulty",
    ]
    # Note: insurance/disability/difficulty can be both topics and groups, so a phrase
    # like "by insurance" still counts as follow-up because it has explicit by-modifier.
    if q.startswith("by ") or " by " in f" {q} ":
        return False
    return any(t in q for t in topics)


def looks_like_followup(question: str, context: Optional[Dict[str, Any]]) -> bool:
    if not context or not context.get("outcome"):
        return False
    q = normalize_text(question)
    if not q:
        return False
    starters = ["what about", "how about", "show", "and", "now", "instead", "compare", "what if"]
    if any(q.startswith(s) for s in starters):
        return True
    if q.startswith("by ") or " by " in f" {q} ":
        return True
    if any(p in q for p in ["last 2 years", "last two years", "all years", "latest year", "last year", "2024", "2023", "2022", "2021", "2020", "2019"]):
        return not _has_topic_like_content(q)
    if any(_contains_phrase(q, w) for w in CHILD_WORDS + ADULT_WORDS):
        return not _has_topic_like_content(q)
    if any(_contains_phrase(q, p) for p in GROUP_PHRASES):
        return not _has_topic_like_content(q)
    if any(p in q for p in ["confidence interval", "what is ci", "explain ci", "explain confidence", "standard error", "what does this mean", "where do i get", "where are the files", "data file", "puf"]):
        return True
    return False


def _year_phrase(q: str, context: Dict[str, Any]) -> str:
    if "last 2 years" in q or "last two years" in q or "past 2 years" in q or "past two years" in q:
        return "last 2 years"
    if "all years" in q or "every year" in q or "trend" in q:
        return "all years"
    if "last year" in q or "latest year" in q or "most recent" in q:
        return "last year"
    explicit = re.findall(r"\b(20\d{2})\b", q)
    if explicit:
        return explicit[-1]
    years = context.get("years") or []
    if isinstance(years, list) and len(years) == 1:
        return str(years[0])
    if isinstance(years, list) and len(years) > 1:
        return "all years"
    return "last year"


def _population_phrase(q: str, context: Dict[str, Any]) -> str:
    if any(_contains_phrase(q, w) for w in CHILD_WORDS):
        return "children"
    if any(_contains_phrase(q, w) for w in ADULT_WORDS):
        return "adults"
    return "adults" if context.get("population") == "adult" else "children"


def _group_phrase(q: str) -> Optional[str]:
    # Prefer longer phrases first.
    for phrase, canonical in sorted(GROUP_PHRASES.items(), key=lambda kv: len(kv[0]), reverse=True):
        if _contains_phrase(q, phrase):
            return canonical
    return None


def _subgroup_phrase(q: str) -> Optional[str]:
    # Keep simple; the existing matcher resolves actual subgroup labels.
    candidates = [
        "female", "women", "male", "men", "gay", "lesbian", "bisexual", "straight",
        "uninsured", "private insurance", "private", "medicaid", "medicare",
        "seniors", "65+", "under 65", "younger than 65",
        "black", "white", "asian", "hispanic", "latino", "mexican",
        "high svi", "medium svi", "low svi", "little to no svi",
    ]
    for c in sorted(candidates, key=len, reverse=True):
        if _contains_phrase(q, c):
            return c
    return None


def _direct_explanation(question: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    q = normalize_text(question)
    if any(p in q for p in ["explain ci", "what is ci", "confidence interval", "explain confidence interval"]):
        return {
            "status": "ok",
            "mode": "explanation",
            "answer": (
                "A confidence interval gives a range around the estimate that reflects sampling uncertainty. "
                "In this prototype, estimates and confidence intervals are read directly from the current DHIS NHIS Summary Health Statistics files. "
                "A narrower interval generally means less sampling uncertainty, while a wider interval generally means more sampling uncertainty."
            ),
            "citations": [],
            "source_cards": [],
            "why": ["You asked for an explanation of confidence intervals rather than a new estimate."],
            "debug": {"reason": "ci_explanation_followup", "previous_context": context},
        }
    if any(p in q for p in ["where do i get", "where are the files", "data file", "puf", "public use"]):
        return {
            "status": "not_found",
            "mode": "documentation_followup",
            "answer": (
                "For NHIS public use files, questionnaires, datasets, and documentation, use the official NHIS Questionnaires, Datasets, and Documentation page: "
                "https://www.cdc.gov/nchs/nhis/documentation/2024-nhis.html. For additional NHIS DQT views, use the NHIS Interactive Data Query Systems page: "
                "https://www.cdc.gov/nchs/nhis/products/data-query-systems.html."
            ),
            "citations": [
                {"title": "NHIS 2024 Questionnaires, Datasets, and Documentation", "url": "https://www.cdc.gov/nchs/nhis/documentation/2024-nhis.html", "score": 1.0},
                {"title": "NHIS Interactive Data Query Systems", "url": "https://www.cdc.gov/nchs/nhis/products/data-query-systems.html", "score": 1.0},
            ],
            "source_cards": [
                {"title": "NHIS 2024 Questionnaires, Datasets, and Documentation", "url": "https://www.cdc.gov/nchs/nhis/documentation/2024-nhis.html", "excerpt": "Use this page for NHIS public use files and documentation.", "score": 1.0},
                {"title": "NHIS Interactive Data Query Systems", "url": "https://www.cdc.gov/nchs/nhis/products/data-query-systems.html", "excerpt": "Use this page for additional NHIS DQT dashboard views.", "score": 1.0},
            ],
            "why": ["You asked where to get files or additional data after an estimate answer."],
            "debug": {"reason": "documentation_followup", "previous_context": context},
        }
    return None


def build_resolved_question(question: str, context: Dict[str, Any], use_model: bool = False) -> Tuple[str, Dict[str, Any], Optional[Dict[str, Any]]]:
    """Return (resolved_question, metadata, direct_response)."""
    q = normalize_text(question)
    direct = _direct_explanation(question, context)
    if direct:
        return question, {"used_followup_context": True, "method": "direct_followup_response"}, direct

    model_plan, model_meta = resolve_followup_with_model(question, context, use_model=use_model)

    population = _population_phrase(q, context)
    outcome = context.get("outcome") or ""
    year = _year_phrase(q, context)
    group = _group_phrase(q)
    subgroup = _subgroup_phrase(q)

    # If the optional model returns a safe plan, allow it to override only supported fields.
    if model_plan:
        population = model_plan.get("population") if model_plan.get("population") in {"adults", "children"} else population
        year = model_plan.get("year_phrase") or year
        group = model_plan.get("grouping") or group
        subgroup = model_plan.get("subgroup") or subgroup

    parts = [f"What percent of {population} had {outcome} {year}".strip()]
    if group:
        parts.append(f"by {group}")
    elif subgroup:
        parts.append(f"among {subgroup}")
    if subgroup and group:
        # Keep subgroup wording too so the existing matcher can list that subgroup first.
        parts.append(f"for {subgroup}")
    resolved = " ".join(parts).strip() + "?"
    meta = {
        "used_followup_context": True,
        "method": "deterministic_plus_optional_model_plan",
        "original_question": question,
        "resolved_question": resolved,
        "previous_context": context,
        "detected_population_phrase": population,
        "detected_year_phrase": year,
        "detected_group_phrase": group,
        "detected_subgroup_phrase": subgroup,
        "model_followup": model_meta,
    }
    return resolved, meta, None


def suggested_followups(context: Optional[Dict[str, Any]], result: Optional[Dict[str, Any]] = None) -> list[str]:
    if not context or not context.get("outcome"):
        return [
            "What percent of adults had current asthma last year?",
            "Show diabetes by SVI",
            "Where can I find the 2024 NHIS public use files?",
        ]
    suggestions = []
    label = normalize_text(context.get("label") or "")
    if label != "sex":
        suggestions.append("Show by sex")
    if "age" not in label:
        suggestions.append("Show by age")
    if "race" not in label:
        suggestions.append("Show by race and ethnicity")
    if "social vulnerability" not in label:
        suggestions.append("Show by SVI")
    suggestions.extend(["Show last 2 years", "Where do I get the data?", "Explain the confidence interval"])
    # de-duplicate preserving order
    out = []
    for s in suggestions:
        if s not in out:
            out.append(s)
    return out[:6]
