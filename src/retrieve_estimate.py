from __future__ import annotations
from pathlib import Path
import sys
import re
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))

from load_sources import load_data, load_sources, load_symbol_rules, load_keyword_mappings, load_fallback_language
from matchers import detect_population, extract_years, match_topic, detect_group_intent
from normalize_text import normalize_text
from format_answer import format_row, source_line, dqt_line, summarize_high_low, excerpt_from_rows, NHIS_DOC_URL, DQT_URL


def _match_population(question: str, keyword_mappings: dict, adult_df: pd.DataFrame, child_df: pd.DataFrame):
    explicit = detect_population(question)
    if explicit:
        return explicit, None

    adult_topic, adult_meta = match_topic(question, adult_df, keyword_mappings)
    child_topic, child_meta = match_topic(question, child_df, keyword_mappings)

    # Product rule: default to adults unless children/kids/pediatric language is present.
    # Exception: child-only SHS topics should still route to child when the adult match is just
    # a generic overlap (for example, "learning disability" should not become adult disability).
    child_only_topics = {
        "Ever having attention-deficit/hyperactivity disorder",
        "Ever having a learning disability",
        "Receiving special education or early intervention services",
        "Receive services for mental health problems",
        "Missing 11 or more school days due to illness or injury",
        "Well child check-up",
    }
    qn = normalize_text(question)
    child_only_cues = [
        "adhd", "attention deficit", "learning disability", "special education",
        "early intervention", "well child", "missed school", "school absence",
        "school absences", "mental health services"
    ]
    if child_topic in child_only_topics and any(c in qn for c in child_only_cues):
        return "child", None
    if adult_topic:
        return "adult", None
    if child_topic:
        return "child", None
    return "adult", None


def _fallback_answer(fallback: str, reason: str = "") -> str:
    lines = [fallback]
    lines.append("")
    lines.append(f"Relevant CDC/NHIS links: {NHIS_DOC_URL}; {DQT_URL}")
    if reason:
        lines.append(f"Why: {reason}")
    return "\n".join(lines)


def _filter_label(subset: pd.DataFrame, label: str | None) -> pd.DataFrame:
    if not label:
        return subset
    nl = normalize_text(label)

    # Family income / Poverty status equivalence:
    # In the NHIS SHS files these are the same FPL-style subgroup concept, but
    # different topics/years/populations may store the available rows under one
    # label or the other. User-facing routing should treat income, household
    # income, FPL, and poverty as Family income, while retrieval should still
    # find the available rows in the current file.
    if nl in {"family income", "poverty status"}:
        preferred = ["family income", "poverty status"]
        for candidate in preferred:
            s2 = subset[subset["col_label"].map(normalize_text).eq(candidate)]
            if not s2.empty:
                return s2
        return subset.iloc[0:0]

    s2 = subset[subset["col_label"].map(normalize_text).eq(nl)]
    if s2.empty:
        s2 = subset[subset["col_label"].map(lambda x: nl in normalize_text(x) or normalize_text(x) in nl)]
    return s2


def _filter_group_exact_or_contains(subset: pd.DataFrame, group_value: str | None) -> pd.DataFrame:
    if not group_value:
        return subset
    gv = normalize_text(group_value)
    s2 = subset[subset["Group"].map(normalize_text).eq(gv)]
    if s2.empty:
        s2 = subset[subset["Group"].map(lambda x: gv in normalize_text(x) or normalize_text(x) in gv)]
    return s2


def _sort_rows(subset: pd.DataFrame, requested_group: str | None = None) -> pd.DataFrame:
    work = subset.copy()
    rg = normalize_text(requested_group or "")
    def sort_key(row):
        g = normalize_text(row.get("Group", ""))
        year = int(row.get("Year", 0))
        if rg and (g == rg or g.startswith(rg + " ") or g.startswith(rg + ":")):
            pri = 0
        elif g == "total":
            pri = 1
        else:
            pri = 2
        return (year, pri, str(row.get("Group", "")))
    work["_sort_tuple"] = work.apply(sort_key, axis=1)
    return work.sort_values("_sort_tuple").drop(columns=["_sort_tuple"], errors="ignore")


def _wants_se(question: str) -> bool:
    q = normalize_text(question)
    return bool(re.search(r"\bse\b", q)) or "standard error" in q


def retrieve(question: str, debug: bool = False) -> dict:
    sources = load_sources()
    symbol_rules = load_symbol_rules()
    keyword_mappings = load_keyword_mappings()
    fallback = load_fallback_language()["default"]

    q_norm = normalize_text(question)
    if any(term in q_norm for term in ["public use", "puf", "documentation", "questionnaire", "questionnaires", "dataset", "datasets", "data file", "data files"]):
        year_match = re.findall(r"\b(20\d{2})\b", question)
        doc_url = f"https://www.cdc.gov/nchs/nhis/documentation/{year_match[-1]}-nhis.html" if year_match else NHIS_DOC_URL
        ans = ("For NHIS public use files, questionnaires, datasets, and documentation, use the official NHIS Questionnaires, Datasets, and Documentation page: "
               f"{doc_url}. This prototype only returns precomputed adult/child Summary Health Statistics estimates from the current DHIS files; if an estimate is not available there, use the relevant year's NHIS public use files and documentation.")
        return {"status": "not_found", "answer": ans, "debug": {"reason": "documentation_or_puf_request", "question": question, "documentation_url": doc_url}}

    adult_df = load_data("adult")
    child_df = load_data("child")
    population, pop_msg = _match_population(question, keyword_mappings, adult_df, child_df)
    if pop_msg:
        return {"status": "clarify", "answer": pop_msg, "debug": {"question": question}}
    if not population:
        return {"status": "not_found", "answer": _fallback_answer(fallback, "I could not determine whether the question was asking about adults or children."), "debug": {"reason": "population_not_detected", "question": question}}

    df = adult_df if population == "adult" else child_df
    source = sources[population]
    years, year_meta = extract_years(question, df)
    available_years = set(int(y) for y in df["Year"].dropna().unique())
    if any(y not in available_years for y in years):
        return {"status": "not_found", "answer": _fallback_answer(fallback, f"The requested year is not available in the current {source['name']} file."), "debug": {"reason": "year_not_available", "population": population, "years": years}}

    outcome, topic_meta = match_topic(question, df, keyword_mappings)
    if not outcome:
        return {"status": "not_found", "answer": _fallback_answer(fallback, "I could not match the requested topic to an outcome in the current adult/child DHIS files."), "debug": {"reason": "topic_not_matched", "population": population, "years": years, "topic_meta": topic_meta}}

    label, group_value, group_meta = detect_group_intent(question, df, keyword_mappings=keyword_mappings)
    # If a subgroup value or inferred label is part of the matched topic itself, do not also
    # force it as a demographic row. This prevents topic words like "special education" and
    # "missed school" from becoming Parental Education rows when no breakdown was requested.
    if group_value and normalize_text(str(group_value)) in normalize_text(outcome):
        label, group_value = "Total", None
        group_meta = {**group_meta, "wants_breakdown": False, "group_value_absorbed_into_topic": True}
    if label and not group_meta.get("wants_breakdown") and normalize_text(str(label)).replace("parental ", "") in normalize_text(outcome):
        label, group_value = "Total", None
        group_meta = {**group_meta, "wants_breakdown": False, "label_absorbed_into_topic": True}

    subset = df[(df["Year"].astype(int).isin(years)) & (df["Outcome (or Indicator)"] == outcome)]
    subset = _filter_label(subset, label)
    if subset.empty:
        return {"status": "not_found", "answer": _fallback_answer(fallback, "The topic was found, but the requested grouping was not available in the current DHIS file."), "debug": {"reason": "grouping_not_found", "population": population, "years": years, "outcome": outcome, "label": label, "group_meta": group_meta}}

    # If a true composite/crosstab grouping exists and the user named multiple subgroups,
    # return the row(s) that contain all requested subgroup values.
    if group_meta.get("is_composite") and len(group_meta.get("requested_values", [])) > 1:
        vals = [normalize_text(v) for v in group_meta.get("requested_values", [])]
        comp = subset[subset["Group"].map(lambda g: all(v in normalize_text(g) for v in vals))]
        if not comp.empty:
            subset = comp
            group_value = ": ".join(group_meta.get("requested_values", []))
            group_meta = {**group_meta, "wants_breakdown": False, "subgroup_first": False}

    # If a specific subgroup is requested, keep the full grouping but prioritize that row.
    filtered_to_group = False
    if group_value and not group_meta.get("subgroup_first"):
        subset2 = _filter_group_exact_or_contains(subset, group_value)
        if not subset2.empty:
            subset = subset2
            filtered_to_group = True
    elif group_value and group_meta.get("subgroup_first"):
        # Keep all rows in that grouping. If the requested subgroup does not exist, fallback to exact filtering attempt.
        if _filter_group_exact_or_contains(subset, group_value).empty:
            subset2 = _filter_group_exact_or_contains(subset, group_value)
            if not subset2.empty:
                subset = subset2
                filtered_to_group = True

    if subset.empty:
        return {"status": "not_found", "answer": _fallback_answer(fallback, "The topic and grouping were found, but the requested subgroup row was not available."), "debug": {"reason": "row_not_found", "population": population, "years": years, "outcome": outcome, "label": label, "group": group_value, "topic_meta": topic_meta, "group_meta": group_meta}}

    # If no group/breakdown was requested, use total population/overall rows only.
    if not group_meta.get("wants_breakdown") and not group_value:
        total = subset[subset["Group"].map(normalize_text).eq("total")]
        if not total.empty:
            subset = total
        else:
            subset = subset.head(1)

    subset = _sort_rows(subset, group_value)

    lines = []
    title_pop = source["population_label"]
    year_text = f"{min(years)}–{max(years)}" if len(years) > 1 else str(years[0])
    if group_meta.get("wants_breakdown") and label and normalize_text(label) != "total":
        lines.append(f"{year_text} NHIS estimate — {title_pop}")
        lines.append(f"{outcome} by {label}")
    else:
        lines.append(f"{year_text} NHIS estimate — {title_pop}")
        lines.append(outcome)
    lines.append("")

    if year_meta.get("explanation"):
        lines.append(year_meta["explanation"])
        lines.append("")
    if group_meta.get("explanation"):
        lines.append(group_meta["explanation"])
        lines.append("")
    if group_value and group_meta.get("subgroup_first") and not filtered_to_group:
        lines.append(f"You asked about {group_value}; I list that subgroup first and then show the rest of the {label} grouping for context.")
        lines.append("")

    notes = []
    include_year = len(years) > 1
    max_rows = 80
    shown = subset.head(max_rows)
    for _, row in shown.iterrows():
        row_text, row_notes = format_row(row, symbol_rules, include_year=include_year)
        lines.append(row_text)
        for n in row_notes:
            if n not in notes:
                notes.append(n)
    if len(subset) > max_rows:
        lines.append(f"... {len(subset) - max_rows} additional rows not shown in this brief response.")

    high_low = summarize_high_low(subset)
    if high_low:
        lines.append("")
        lines.append(high_low)

    excerpt = excerpt_from_rows(subset)
    if excerpt:
        lines.append("")
        lines.append(excerpt)

    if notes:
        lines.append("")
        lines.extend(notes)

    if _wants_se(question) and not any(c.lower().replace(" ", "") in {"se", "standarderror"} for c in subset.columns):
        lines.append("")
        lines.append("Note: Standard errors are not included as a separate field in the current DHIS summary file used by this prototype. Confidence intervals are shown where available.")

    lines.append("")
    lines.append(source_line(source, years))
    lines.append(dqt_line())

    if debug:
        lines.append("")
        lines.append("Matched source details:")
        lines.append(f"- Population: {population}")
        lines.append(f"- Outcome: {outcome}")
        lines.append(f"- Grouping label: {label}")
        lines.append(f"- Requested group value: {group_value or '[none]'}")
        lines.append(f"- Year mode: {year_meta.get('mode')}")
        lines.append(f"- Years returned: {', '.join(map(str, years))}")
        lines.append(f"- Topic match method: {topic_meta.get('method')}")
        lines.append(f"- Topic match score: {topic_meta.get('score'):.3f}")
        lines.append(f"- Rows returned: {len(subset)}")
        lines.append(f"- Reliability fields present: {', '.join([c for c in ['CR_P_RELIABLE','CR_Q_RELIABLE','P_CLERICAL','ZERO','KG_FLAG'] if c in subset.columns])}")

    citations = [
        {"title": source["name"], "url": source.get("socrata_about_url", ""), "score": 1.0},
        {"title": "NHIS Interactive Data Query Systems", "url": DQT_URL, "score": 1.0},
    ]
    source_cards = [
        {
            "title": source["name"],
            "url": source.get("socrata_about_url", ""),
            "excerpt": f"Matched {source['name']} row(s): outcome={outcome}; grouping={label}; years={', '.join(map(str, years))}.",
            "source_category": "dhis_nhis_summary_health_statistics",
            "score": 1.0,
        },
        {
            "title": "NHIS Interactive Data Query Systems",
            "url": DQT_URL,
            "excerpt": "Use the NHIS DQT page for additional dashboard views and NHIS data query systems.",
            "source_category": "cdc_nhis_webpage",
            "score": 1.0,
        },
    ]
    why = []
    if year_meta.get("explanation"):
        why.append(year_meta["explanation"])
    if group_meta.get("explanation"):
        why.append(group_meta["explanation"])
    if group_value and group_meta.get("subgroup_first") and not filtered_to_group:
        why.append(f"The requested subgroup ({group_value}) was shown first, then the rest of the {label} grouping was shown for context.")
    why.append("Estimates and confidence intervals were read from the current local DHIS NHIS Adult/Child Summary Health Statistics files.")

    return {
        "status": "ok",
        "answer": "\n".join(lines),
        "citations": citations,
        "source_cards": source_cards,
        "why": why,
        "debug": {"population": population, "years": years, "year_meta": year_meta, "outcome": outcome, "label": label, "group": group_value, "rows_returned": len(subset), "topic_meta": topic_meta, "group_meta": group_meta}
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Retrieve a sourced DHIS NHIS adult/child SHS estimate.")
    parser.add_argument("question", nargs="+", help="Question to answer")
    parser.add_argument("--debug", action="store_true", help="Show matched metadata")
    args = parser.parse_args()
    result = retrieve(" ".join(args.question), debug=args.debug)
    print(result["answer"])
