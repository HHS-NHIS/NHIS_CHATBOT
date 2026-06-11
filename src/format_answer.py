from __future__ import annotations
import math
import re
import pandas as pd

DQT_URL = "https://www.cdc.gov/nchs/nhis/products/data-query-systems.html"
NHIS_DOC_URL = "https://www.cdc.gov/nchs/nhis/documentation/2024-nhis.html"


def pct_code(value) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        iv = int(float(value))
        if float(value) == iv and str(iv) in {"444", "555", "777", "888", "999"}:
            return str(iv)
    except Exception:
        return None
    return None


def numeric_pct(value) -> float | None:
    if pct_code(value):
        return None
    try:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return None
        return float(value)
    except Exception:
        return None


def format_percentage(value, symbol_rules: dict) -> tuple[str, list[str]]:
    code = pct_code(value)
    if code:
        rule = symbol_rules[code]
        return rule["display"], [rule["footnote"]]
    try:
        return f"{float(value):.1f}%", []
    except Exception:
        return "Not available", []


def format_ci(ci: str) -> str:
    ci = "" if ci is None or (isinstance(ci, float) and math.isnan(ci)) else str(ci).strip()
    if not ci:
        return ""
    parts = [p.strip() for p in ci.replace(";", ",").split(",")]
    if len(parts) == 2:
        return f"95% CI: {parts[0]}%–{parts[1]}%"
    return f"95% CI: {ci}"


def find_se(row: pd.Series) -> str:
    for col in row.index:
        nc = re.sub(r"[^a-z0-9]", "", str(col).lower())
        if nc in {"se", "stderr", "standarderror", "standarderr"}:
            val = row.get(col)
            if val is not None and not (isinstance(val, float) and math.isnan(val)) and str(val).strip() != "":
                try:
                    return f"SE: {float(val):.3f}"
                except Exception:
                    return f"SE: {val}"
    return ""


def format_row(row: pd.Series, symbol_rules: dict, include_year: bool = False) -> tuple[str, list[str]]:
    pct, notes = format_percentage(row.get("Percentage"), symbol_rules)
    ci = format_ci(row.get("Confidence Interval", ""))
    se = find_se(row)
    label = str(row.get("Group", "")).strip() or "Total"
    year = str(int(row.get("Year"))) if include_year and pd.notna(row.get("Year")) else ""
    prefix = f"{year} — {label}: " if year else f"{label}: "
    details = [pct]
    if ci:
        details.append(ci)
    if se:
        details.append(se)
    return prefix + details[0] + " (" + "; ".join(details[1:]) + ")" if len(details) > 1 else prefix + details[0], notes


def excerpt_from_rows(rows: pd.DataFrame) -> str:
    if rows.empty:
        return ""
    desc = str(rows.iloc[0].get("Description", "") or "").strip()
    title = str(rows.iloc[0].get("Title", "") or "").strip()
    if desc:
        return f"Definition/excerpt from DHIS file: {desc}"
    if title:
        return f"Source title/excerpt from DHIS file: {title}"
    return ""


def source_line(source: dict, years: list[int] | int) -> str:
    if isinstance(years, int):
        year_text = str(years)
    else:
        year_text = f"{min(years)}–{max(years)}" if len(years) > 1 else str(years[0])
    return f"Source: {source['name']}, {year_text}. Socrata ID: {source['socrata_id']}. {source['socrata_about_url']}"


def dqt_line() -> str:
    return f"More information: NHIS Interactive Data Query Systems: {DQT_URL}"


def summarize_high_low(rows: pd.DataFrame) -> str:
    if rows.empty:
        return ""
    work = rows.copy()
    work["_numeric_pct"] = work["Percentage"].map(numeric_pct)
    work = work[work["_numeric_pct"].notna()]
    if work.empty or len(work) < 2:
        return ""
    hi = work.loc[work["_numeric_pct"].idxmax()]
    lo = work.loc[work["_numeric_pct"].idxmin()]
    def lbl(r):
        y = int(r["Year"])
        g = str(r.get("Group", "Total") or "Total")
        return f"{g} in {y}: {float(r['_numeric_pct']):.1f}%"
    return f"Highest among the returned rows: {lbl(hi)}. Lowest among the returned rows: {lbl(lo)}."
