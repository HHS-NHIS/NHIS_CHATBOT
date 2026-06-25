from __future__ import annotations

"""Special-case handling for insurance topic/covariate conflicts.

Insurance appears in the SHS files both as an outcome/topic (for example,
"Uninsured at time of interview") and as a grouping/covariate (for example,
"Current asthma by Health insurance coverage"). Generic routing can confuse
those roles. This module handles questions where insurance itself is the topic,
including insurance-by-insurance-status and age-scoped insurance questions, while
leaving non-insurance topics by insurance status to the standard SHS retriever.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional
import re
import pandas as pd
from normalize_text import normalize_text

ROOT = Path(__file__).resolve().parents[1]
ADULT_PATH = ROOT / "data" / "NHIS_adult_SHS.csv"
CHILD_PATH = ROOT / "data" / "NHIS_child_SHS.csv"

ADULT_SOURCE = "https://data.cdc.gov/National-Center-for-Health-Statistics/NHIS-Adult-Summary-Health-Statistics/25m4-6qqq/about_data"
CHILD_SOURCE = "https://data.cdc.gov/National-Center-for-Health-Statistics/NHIS-Child-Summary-Health-Statistics/wxz7-ekz9/about_data"

INSURANCE_OUTCOMES_PRIORITY = [
    "Uninsured at time of interview",
    "Private health insurance coverage at time of interview",
    "Public health plan coverage at time of interview",
    "Exchange-based coverage coverage at time of interview",
    "Uninsured for at least part of the past year",
    "Uninsured for more than one year",
]

OTHER_HEALTH_TOPICS = [
    "asthma", "diabetes", "flu", "influenza", "hypertension", "blood pressure", "obesity",
    "smoking", "vaping", "adhd", "depression", "anxiety", "doctor", "urgent", "school",
    "health status", "cholesterol", "cancer", "medication", "medicine", "care due to cost",
    "hearing", "seeing", "walking", "difficulty", "disability", "pain", "arthritis", "copd",
    "heart", "angina", "wellness", "dental", "pneumococcal"
]


def _has_any(q: str, phrases: list[str]) -> bool:
    return any(p in q for p in phrases)


def _contains_wordish(needle: str, haystack: str) -> bool:
    if not needle:
        return False
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])", haystack))


def _has_any_wordish(q: str, phrases: list[str]) -> bool:
    return any(_contains_wordish(normalize_text(p), q) for p in phrases)


def _has_insurance_cue(q: str) -> bool:
    return _has_any_wordish(q, [
        "insurance", "insured", "uninsured", "coverage", "private coverage", "private insurance",
        "public coverage", "public health plan", "health plan", "medicaid", "medicare", "exchange coverage"
    ])


def _has_under65_cue(q: str) -> bool:
    return _has_any_wordish(q, [
        "under 65", "under age 65", "younger than 65", "younger than age 65", "less than 65",
        "below 65", "65 and under", "65 or under", "nonelderly", "non elderly", "non-elderly",
        "18-64", "18 to 64", "aged 18-64", "ages 18-64", "people under 65", "adults under 65"
    ])


def _has_over65_cue(q: str) -> bool:
    # Check "nonelderly" first by word-boundary caller; elderly will not match nonelderly.
    return _has_any_wordish(q, [
        "65+", "65 and over", "65 years and over", "65 or over", "65 and older",
        "65 years and older", "65 or older", "older than 65", "age 65 and over", "aged 65 and over",
        "seniors", "senior", "elderly", "older adults", "medicare advantage", "medicare only", "medicare"
    ]) and not _has_under65_cue(q)


def _age_scope(q: str) -> Optional[str]:
    if _has_under65_cue(q):
        return "under65"
    if _has_over65_cue(q):
        return "over65"
    return None


def _specific_insurance_outcomes(q: str, available: set[str]) -> list[str]:
    wanted: list[str] = []
    def add(outcome: str):
        if outcome in available and outcome not in wanted:
            wanted.append(outcome)

    if _has_any(q, ["at least part of the past year", "part of the past year", "some of the past year", "past year uninsured"]):
        add("Uninsured for at least part of the past year")
    if _has_any(q, ["more than one year", "over one year", "longer than one year"]):
        add("Uninsured for more than one year")
    if _has_any_wordish(q, ["uninsured", "without insurance", "no insurance"]):
        add("Uninsured at time of interview")
    if _has_any(q, ["private insurance", "private health insurance", "private coverage"]) or _contains_wordish("private", q):
        add("Private health insurance coverage at time of interview")
    if _has_any(q, ["public coverage", "public health plan", "public insurance", "government coverage", "medicaid", "medicare", "health plan coverage"]):
        add("Public health plan coverage at time of interview")
    if _has_any(q, ["exchange", "marketplace", "aca marketplace"]):
        add("Exchange-based coverage coverage at time of interview")
    return wanted


def looks_like_insurance_topic_status_question(question: str) -> bool:
    q = normalize_text(question)
    if not _has_insurance_cue(q):
        return False
    # Special case only when insurance is the substantive topic. If another clear health topic
    # appears, the standard retriever should answer that topic by the insurance grouping.
    if any(t in q for t in OTHER_HEALTH_TOPICS):
        # Keep true insurance-outcome questions such as "mental health insurance" out of scope.
        return False

    status_phrases = [
        "by insurance status", "by health insurance", "by coverage", "by insurance",
        "insurance status", "health insurance status", "insurance coverage by insurance",
        "insurance by insurance", "insured by insurance", "coverage by insurance status"
    ]
    insurance_topic_phrases = [
        "how many people had insurance", "how many had insurance", "how many people were insured",
        "how many were insured", "percent of people had insurance", "percent had insurance",
        "what percent of adults had insurance", "what percent of people had insurance",
        "had insurance last year", "had insurance", "were insured", "were uninsured",
        "had private insurance", "had public coverage", "had medicare", "had medicaid",
        "had health insurance", "health insurance coverage", "private insurance coverage",
        "public health plan coverage", "exchange based coverage", "exchange coverage"
    ]
    if _has_any(q, status_phrases) or _has_any(q, insurance_topic_phrases):
        return True
    # Age-scoped insurance outcome questions are especially easy to mishandle in the generic
    # retriever, so route them here even without explicit "by insurance status" wording.
    if _age_scope(q) and _specific_insurance_outcomes(q, set(INSURANCE_OUTCOMES_PRIORITY)):
        return True
    return False


def _detect_population(question: str) -> str:
    q = normalize_text(question)
    if any(w in q for w in ["child", "children", "kid", "kids", "youth", "adolescent"]):
        return "child"
    return "adult"


def _detect_years(df: pd.DataFrame, question: str) -> list[int]:
    q = normalize_text(question)
    years = sorted(int(y) for y in df["Year"].dropna().unique())
    explicit = re.findall(r"\b(20\d{2})\b", q)
    if explicit:
        return [int(explicit[-1])] if int(explicit[-1]) in years else [years[-1]]
    m = re.search(r"\b(?:last|past|most recent|latest)\s+(\d+)\s+years?\b", q)
    if m:
        n = max(1, int(m.group(1)))
        return years[-n:]
    if any(p in q for p in ["last year", "latest", "most recent"]):
        return [years[-1]]
    return years


def _fmt_pct(v: Any) -> str:
    try:
        f = float(v)
    except Exception:
        return str(v)
    special = {999: "*", 444: "**", 555: "***", 777: "NA", 888: "-"}
    if int(f) in special and abs(f - int(f)) < 1e-9:
        return special[int(f)]
    return f"{f:.1f}%"


def _row_line(row: pd.Series) -> str:
    ci = str(row.get("Confidence Interval", "") or "").strip()
    pct = _fmt_pct(row.get("Percentage"))
    if ci and ci.lower() != "nan":
        return f"{int(row['Year'])}: {pct} (95% CI: {ci})"
    return f"{int(row['Year'])}: {pct}"


def _rows_for_outcome(df: pd.DataFrame, outcome: str, years: list[int], scope: Optional[str]) -> pd.DataFrame:
    sub = df[(df["Outcome (or Indicator)"] == outcome) & (df["Year"].isin(years))]
    if sub.empty:
        return sub
    if scope == "under65" and "Age groups with 65+" in set(sub["col_label"]):
        age = sub[sub["col_label"].eq("Age groups with 65+")]
        # There is usually not a single 18-64 combined row, so return the under-65 age rows.
        age = age[age["Group"].astype(str).str.contains(r"18-34|35-49|50-64|18-44|45-64", regex=True, na=False)]
        if not age.empty:
            return age
    if scope == "over65" and "Age groups with 65+" in set(sub["col_label"]):
        age = sub[(sub["col_label"].eq("Age groups with 65+")) & (sub["Group"].astype(str).str.contains("65", na=False))]
        if not age.empty:
            return age
    total = sub[sub["Group"].map(normalize_text).eq("total")]
    return total if not total.empty else sub.head(len(years))


def insurance_topic_status_response(question: str) -> Dict[str, Any]:
    q = normalize_text(question)
    population = _detect_population(question)
    path = CHILD_PATH if population == "child" else ADULT_PATH
    source = CHILD_SOURCE if population == "child" else ADULT_SOURCE
    df = pd.read_csv(path)
    years = _detect_years(df, question)
    scope = _age_scope(q) if population == "adult" else None
    available = set(df["Outcome (or Indicator)"].dropna().unique())

    specific = _specific_insurance_outcomes(q, available)
    outcomes = specific or [o for o in INSURANCE_OUTCOMES_PRIORITY if o in available]
    if not outcomes:
        return {
            "status": "not_found",
            "mode": "insurance_special_not_found",
            "answer": "I found an insurance-status request, but this SHS file does not include a directly available insurance outcome for the requested population.",
            "citations": [source],
            "source_cards": [{"title": f"DHIS NHIS {'Child' if population == 'child' else 'Adult'} Summary Health Statistics", "url": source, "excerpt": "Insurance special-case lookup."}],
            "why": ["The question was recognized as an insurance-as-topic request, but no supported insurance outcome was found."],
            "debug": {"reason": "insurance_special_no_outcomes", "population": population, "years": years, "scope": scope},
        }

    pop_label = "Children" if population == "child" else "Adults"
    year_text = f"{min(years)}" + (f"–{max(years)}" if len(years) > 1 else "")
    lines: List[str] = []
    lines.append(f"{year_text} NHIS insurance coverage estimates — {pop_label}")
    lines.append("")
    if specific:
        lines.append("I treated this as an insurance coverage outcome question. Because insurance can also be a grouping variable in the SHS files, I used the insurance-outcome special-case path to avoid mixing up topic and covariate roles.")
    else:
        lines.append("I treated this as an insurance coverage question where insurance is both the topic and the requested status/breakout. In the current adult/child SHS files, the cleanest available answer is the set of insurance-related coverage outcomes available for the requested population.")
    if scope == "under65":
        lines.append("You asked about adults under 65. When a single combined under-65 row is not available, I show the available under-65 age rows from the SHS file.")
    elif scope == "over65":
        lines.append("You asked about adults aged 65 and over. Some adult insurance measures in this SHS file are limited to adults aged 18–64; when that applies, the result displays as ***.")
    lines.append("")

    for outcome in outcomes:
        rows = _rows_for_outcome(df, outcome, years, scope)
        lines.append(outcome)
        if rows.empty:
            lines.append("- Not available for the requested population/year scope in the current SHS file.")
        else:
            for _, row in rows.sort_values(["Year", "Group"]).iterrows():
                group = str(row.get("Group", "")).strip()
                prefix = f"{group}: " if group and group.lower() != "total" else ""
                lines.append(f"- {prefix}{_row_line(row)}")
        lines.append("")

    if population == "adult":
        lines.append("Note: Adult SHS uses insurance both as an outcome and as a grouping variable. For non-insurance outcomes such as asthma or diabetes by insurance status, I use the standard estimate path. For insurance-as-topic questions, I use this special path to avoid tautological insurance-by-insurance rows.")
    else:
        lines.append("Note: Child SHS currently provides an uninsured-at-time-of-interview insurance outcome and also uses health insurance coverage as a grouping variable for many child outcomes. For insurance-as-topic questions, I return the available child insurance outcome.")
    lines.append(f"Source: {source}")

    return {
        "status": "ok",
        "mode": "estimate",
        "answer": "\n".join(lines),
        "citations": [source],
        "source_cards": [{
            "title": f"DHIS NHIS {'Child' if population == 'child' else 'Adult'} Summary Health Statistics",
            "url": source,
            "source_type": "dhis_shs_source",
            "excerpt": "Insurance coverage estimates from the local SHS file.",
            "score": 1.0,
        }],
        "why": [
            "This was handled by the insurance deconfliction rule because insurance was the topic and could otherwise be confused with insurance as a grouping variable.",
            "The response uses available insurance-related SHS outcomes instead of falling through to the generic not-found message or returning tautological insurance-by-insurance rows.",
        ],
        "debug": {
            "reason": "insurance_topic_status_special_case",
            "population": population,
            "years": years,
            "scope": scope,
            "outcomes": outcomes,
            "source": source,
        },
    }
