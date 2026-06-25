from __future__ import annotations

"""Special-case handling for insurance-as-topic + insurance-as-grouping questions.

The SHS files use insurance both as an outcome/topic and as a grouping variable.
Generic questions like "how many people had insurance by insurance status" often
fail normal topic matching because "insurance" is too ambiguous. This module
provides a controlled direct response using available insurance-related SHS
outcomes rather than falling into not_found.
"""
from pathlib import Path
from typing import Any, Dict, List
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


def _has_any(q: str, phrases: list[str]) -> bool:
    return any(p in q for p in phrases)


def looks_like_insurance_topic_status_question(question: str) -> bool:
    q = normalize_text(question)
    if not _has_any(q, ["insurance", "insured", "uninsured", "coverage", "health plan"]):
        return False
    # Special case only when insurance is being asked about as the substantive topic,
    # not when another topic is clearly requested by insurance status.
    other_topics = [
        "asthma", "diabetes", "flu", "influenza", "hypertension", "blood pressure", "obesity",
        "smoking", "vaping", "adhd", "depression", "anxiety", "doctor", "urgent", "school",
        "health status", "cholesterol", "cancer", "medication", "care due to cost"
    ]
    if any(t in q for t in other_topics):
        return False
    return _has_any(q, [
        "by insurance status", "by health insurance", "by coverage", "insurance status",
        "health insurance status", "how many people had insurance", "how many had insurance",
        "percent of people had insurance", "percent had insurance", "insurance coverage by insurance",
        "insurance by insurance", "had insurance by", "insured by insurance", "coverage by insurance status"
    ])


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
    if any(p in q for p in ["last year", "latest", "most recent"]):
        return [years[-1]]
    if any(p in q for p in ["last 2 years", "last two years", "past 2 years", "past two years"]):
        return years[-2:]
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


def insurance_topic_status_response(question: str) -> Dict[str, Any]:
    population = _detect_population(question)
    path = CHILD_PATH if population == "child" else ADULT_PATH
    source = CHILD_SOURCE if population == "child" else ADULT_SOURCE
    df = pd.read_csv(path)
    years = _detect_years(df, question)
    available = set(df["Outcome (or Indicator)"].dropna().unique())
    outcomes = [o for o in INSURANCE_OUTCOMES_PRIORITY if o in available]
    if not outcomes:
        return {
            "status": "not_found",
            "mode": "insurance_special_not_found",
            "answer": "I found an insurance-status request, but this SHS file does not include a directly available insurance outcome for the requested population.",
            "citations": [source],
            "source_cards": [{"title": f"DHIS NHIS {'Child' if population == 'child' else 'Adult'} Summary Health Statistics", "url": source, "excerpt": "Insurance special-case lookup."}],
            "why": ["The question was recognized as an insurance-as-topic and insurance-as-grouping request, but no supported insurance outcome was found."],
            "debug": {"reason": "insurance_special_no_outcomes", "population": population, "years": years},
        }

    pop_label = "Children" if population == "child" else "Adults"
    lines: List[str] = []
    lines.append(f"{min(years)}" + (f"–{max(years)}" if len(years) > 1 else "") + f" NHIS insurance coverage estimates — {pop_label}")
    lines.append("")
    lines.append("I treated this as an insurance coverage question where insurance is both the topic and the requested status/breakout. In the current adult/child SHS files, the cleanest available answer is the set of insurance-related coverage outcomes available for the requested population.")
    lines.append("")
    for outcome in outcomes:
        sub = df[(df["Outcome (or Indicator)"] == outcome) & (df["Year"].isin(years))]
        # Prefer total rows because asking insurance-by-insurance status can be tautological.
        total = sub[(sub.get("row_label", "") == "Total") | (sub.get("col_label", "") == "Total") | (sub.get("Group", "") == "Total")]
        if total.empty:
            total = sub[sub.get("Group", "").astype(str).str.lower().eq("total")]
        if total.empty:
            # fall back to rows with no group labels, then all rows
            total = sub.head(len(years))
        lines.append(outcome)
        for _, row in total.sort_values("Year").iterrows():
            lines.append(f"- {_row_line(row)}")
        lines.append("")
    if population == "adult":
        lines.append("Note: Adult SHS also uses health insurance coverage as a grouping variable for many non-insurance outcomes, for example asthma or diabetes by insurance status. When the outcome itself is insurance, a status-by-status table can be tautological, so I returned the available insurance coverage outcomes instead.")
    else:
        lines.append("Note: Child SHS currently provides an uninsured-at-time-of-interview insurance outcome and also uses health insurance coverage as a grouping variable for many child outcomes. When the outcome itself is insurance, I returned the available child insurance outcome instead of treating it as a separate health condition by insurance group.")
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
            "This was handled by the insurance deconfliction rule because insurance was both the topic and the requested status/breakout.",
            "The response uses available insurance-related SHS outcomes instead of falling through to the generic not-found message.",
        ],
        "debug": {
            "reason": "insurance_topic_status_special_case",
            "population": population,
            "years": years,
            "outcomes": outcomes,
            "source": source,
        },
    }
