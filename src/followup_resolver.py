from __future__ import annotations

"""NHIS Assistant V2 follow-up resolver.

The resolver is conservative but now supports both estimate follow-ups and
resource/FAQ follow-ups. Vague prompts like "tell me more" inherit the prior
answer lane instead of defaulting to the estimate engine.
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

VAGUE_FOLLOWUP_PHRASES = [
    "tell me more", "more", "more detail", "more information", "explain more",
    "can you expand", "expand", "what else", "why", "how so", "go on",
    "continue", "keep going", "give me more detail", "say more", "additional information"
]


def _contains_phrase(q: str, phrase: str) -> bool:
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(normalize_text(phrase)) + r"(?![a-z0-9])", q))


def _is_vague_followup(q: str) -> bool:
    qn = normalize_text(q).strip(" ?!.")
    return qn in VAGUE_FOLLOWUP_PHRASES or any(qn.startswith(p + " ") for p in VAGUE_FOLLOWUP_PHRASES)


def _has_topic_like_content(q: str) -> bool:
    topics = [
        "asthma", "diabetes", "flu", "influenza", "hypertension", "blood pressure",
        "uninsured", "insurance", "obesity", "smoking", "vaping", "adhd",
        "depression", "anxiety", "cholesterol", "doctor", "urgent", "care",
        "vaccination", "health status", "disability", "difficulty",
    ]
    if q.startswith("by ") or " by " in f" {q} ":
        return False
    return any(t in q for t in topics)


def looks_like_followup(question: str, context: Optional[Dict[str, Any]]) -> bool:
    if not context:
        return False
    q = normalize_text(question)
    if not q:
        return False

    # Vague follow-ups apply to any previous answer lane: FAQ/resource, estimate,
    # teen redirect, documentation, etc.
    if _is_vague_followup(q):
        return True

    starters = ["what about", "how about", "show", "and", "now", "instead", "compare", "what if"]
    if any(q.startswith(s) for s in starters):
        return True

    # The remaining patterns are estimate-style modifiers and require an estimate context.
    if not context.get("outcome"):
        if any(p in q for p in ["confidence interval", "what is ci", "explain ci", "explain confidence", "where do i get", "where are the files", "data file", "puf"]):
            return True
        return False

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
    for phrase, canonical in sorted(GROUP_PHRASES.items(), key=lambda kv: len(kv[0]), reverse=True):
        if _contains_phrase(q, phrase):
            return canonical
    return None


def _subgroup_phrase(q: str) -> Optional[str]:
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
        return question, {"used_followup_context": True, "method": "direct_followup_response", "previous_answer_type": context.get("answer_type")}, direct

    answer_type = context.get("answer_type") or context.get("last_mode") or "unknown"

    # Resource/FAQ/teen vague follow-up: keep the user in the prior answer lane.
    if _is_vague_followup(q) and not context.get("outcome"):
        prior = context.get("last_resolved_question") or context.get("last_question") or "NHIS"
        resolved = f"{prior} {question}"
        return resolved, {
            "used_followup_context": True,
            "method": "vague_followup_inherits_previous_resource_context",
            "previous_answer_type": answer_type,
            "previous_question": prior,
            "resolved_question": resolved,
        }, None

    if _is_vague_followup(q) and context.get("outcome"):
        # For estimate contexts, vague follow-ups should ask for interpretation rather than a fake new estimate.
        direct = {
            "status": "ok",
            "mode": "estimate_explanation_followup",
            "answer": (
                "This was a follow-up to the previous estimate answer. The prior result came from the DHIS NHIS Summary Health Statistics files. "
                "You can ask for a different breakout, such as 'show by sex', 'show by age', 'show by SVI', 'show last 2 years', or 'explain the confidence interval.'"
            ),
            "citations": [],
            "source_cards": context.get("source_cards") or [],
            "why": ["You asked a vague follow-up after an estimate answer, so the assistant stayed in the estimate context instead of starting a new topic."],
            "debug": {"reason": "vague_estimate_followup", "previous_context": context},
        }
        return question, {"used_followup_context": True, "method": "vague_estimate_followup_direct_response", "previous_answer_type": answer_type}, direct

    model_plan, model_meta = resolve_followup_with_model(question, context, use_model=use_model)

    population = _population_phrase(q, context)
    outcome = context.get("outcome") or ""
    year = _year_phrase(q, context)
    group = _group_phrase(q)
    subgroup = _subgroup_phrase(q)

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
        parts.append(f"for {subgroup}")
    resolved = " ".join(parts).strip() + "?"
    meta = {
        "used_followup_context": True,
        "method": "deterministic_plus_optional_model_plan",
        "original_question": question,
        "resolved_question": resolved,
        "previous_context": context,
        "previous_answer_type": answer_type,
        "detected_population_phrase": population,
        "detected_year_phrase": year,
        "detected_group_phrase": group,
        "detected_subgroup_phrase": subgroup,
        "model_followup": model_meta,
    }
    return resolved, meta, None


def suggested_followups(context: Optional[Dict[str, Any]], result: Optional[Dict[str, Any]] = None) -> list[str]:
    answer_type = (context or {}).get("answer_type") or (result or {}).get("mode")
    if answer_type in {"participation_resource", "general_nhis_faq", "faq"}:
        return ["Tell me more", "Is my information private?", "What should I expect?", "How does NHIS help real people?", "How has NHIS data helped with diabetes?"]
    if answer_type == "teen_redirect":
        return ["Why should teens participate?", "Where is the teen SHS tool?", "What about children?", "Start over"]
    if not context or not context.get("outcome"):
        return [
            "What percent of adults had current asthma last year?",
            "Show diabetes by SVI",
            "Why should I participate in NHIS?",
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
    out = []
    for s in suggestions:
        if s not in out:
            out.append(s)
    return out[:6]
