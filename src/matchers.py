from __future__ import annotations
from difflib import SequenceMatcher
import re
from typing import Optional
import pandas as pd
from normalize_text import normalize_text, strip_population_suffix

POP_CHILD_WORDS = [
    "child", "children", "kid", "kids", "pediatric",
    "adolescent", "adolescents", "youth",
    "younger than 18", "under age 18"
]
POP_ADULT_WORDS = ["adult", "adults", "18 and over", "18+", "aged 18"]

# Topic fallbacks are intentionally NHIS-SHS-focused. The JSON mapping is primary.
MANUAL_TOPIC_SYNONYMS = {
    "adhd": ["Ever having attention-deficit/hyperactivity disorder"],
    "attention deficit": ["Ever having attention-deficit/hyperactivity disorder"],
    "attention-deficit": ["Ever having attention-deficit/hyperactivity disorder"],
    "medicare": ["Public health plan coverage at time of interview"],
    "medicaid": ["Public health plan coverage at time of interview"],
    "public health plan": ["Public health plan coverage at time of interview"],
    "public coverage": ["Public health plan coverage at time of interview"],
    "uninsured": ["Uninsured at time of interview"],
    "without insurance": ["Uninsured at time of interview"],
    "current asthma": ["Current asthma"],
    "asthma attack": ["Asthma episode/attack", "Current asthma", "Ever having asthma"],
    "ever asthma": ["Ever having asthma"],
    "high blood pressure": ["Diagnosed hypertension", "Hypertension diagnosis, self-reported"],
    "hypertension": ["Diagnosed hypertension", "Hypertension diagnosis, self-reported"],
    "diabetes": ["Diagnosed diabetes", "Diabetes diagnosis, self-reported"],
    "blood sugar": ["Diagnosed diabetes", "Diabetes diagnosis, self-reported"],
    "vaping": ["Current electronic cigarette use", "Current electronic cigarette or vaping product use"],
    "e-cigarette": ["Current electronic cigarette use", "Current electronic cigarette or vaping product use"],
    "ecigarette": ["Current electronic cigarette use", "Current electronic cigarette or vaping product use"],
    "smoking": ["Current cigarette smoking"],
    "tobacco": ["Current cigarette smoking"],
    "cigarette": ["Current cigarette smoking"],
    "obesity": ["Obesity"],
    "obese": ["Obesity"],
    "flu shot": ["Receipt of influenza vaccination"],
    "flu vaccine": ["Receipt of influenza vaccination"],
    "flu vaccination": ["Receipt of influenza vaccination"],
    "influenza vaccination": ["Receipt of influenza vaccination"],
    "pneumococcal": ["Ever received a pneumococcal vaccination"],
    "pneumonia vaccine": ["Ever received a pneumococcal vaccination"],
    "influenza vaccine": ["Receipt of influenza vaccination"],
    "regular source of care": ["Has a usual place of care"],
    "regular place of care": ["Has a usual place of care"],
    "usual place of care": ["Has a usual place of care"],
    "doctor visit": ["Doctor visit"],
    "fair or poor health": ["Fair or poor health status"],
    "urgent or retail": ["Urgent care center or retail health clinic visit"],
    "urgent care or retail": ["Urgent care center or retail health clinic visit"],
    "urgent care and retail": ["Urgent care center or retail health clinic visit"],
    "urgent care": ["Urgent care center visit"],
    "used urgent care": ["Urgent care center visit"],
    "retail clinic": ["Retail health clinic visit"],
    "could not afford care": ["Did not get needed medical care due to cost"],
    "couldn t afford care": ["Did not get needed medical care due to cost"],
    "could not afford medical care": ["Did not get needed medical care due to cost"],
    "skipped medicine to save money": ["Did not take medication as prescribed to save money"],
    "skipped medication to save money": ["Did not take medication as prescribed to save money"],
    "skipped meds to save money": ["Did not take medication as prescribed to save money"],
    "school absences": ["Missing 11 or more school days due to illness or injury"],
    "school absence": ["Missing 11 or more school days due to illness or injury"],
    "missed school": ["Missing 11 or more school days due to illness or injury"],
    "disabled": ["Disability status (composite)"],
    "with disability": ["Disability status (composite)"],
}

# Used only as a fallback if the JSON mapping is missing. Do not include generic population
# words like "adults" or "children" here, because those should route population only.
GROUP_SYNONYMS = {
    "sexual_orientation": ["sexual orientation", "gay", "lesbian", "bisexual", "straight", "lgb", "lgbt", "lgbtq", "same-sex"],
    "sex": ["sex", "gender", "male", "female", "men", "women", "boys", "girls", "by sex", "by gender"],
    "age": ["age", "age group", "ages", "older", "65+", "75+", "seniors", "elderly", "by age"],
    "race": ["race", "racial", "black", "white", "asian", "aian", "american indian", "alaska native", "nhpi", "two or more races"],
    "hispanic": ["hispanic", "latino", "mexican", "ethnicity", "race and ethnicity", "race and hispanic", "hispanic origin"],
    "region": ["region", "northeast", "midwest", "south", "west"],
    "metro": ["metro", "msa", "metropolitan", "urban", "rural", "place of residence", "urbanicity"],
    "poverty": ["poverty", "fpl", "federal poverty level", "income-to-poverty", "income to poverty", "below poverty", "family poverty", "family income", "household income", "income", "income group", "income level"],
    "social_vulnerability": ["svi", "social vulnerability", "social vulnerability index", "vulnerability", "socially vulnerable", "by svi", "by social vulnerability"],
    "insurance": ["insurance", "coverage", "insured", "uninsured", "private", "medicaid", "medicare"],
    "education": ["education", "educational", "school", "college", "parental education"],
    "difficulty": ["difficulty", "functioning", "functional limitation", "with difficulty", "trouble"],
    "disability": ["disability", "disabled", "with disability"],
    "employment": ["employment", "employed", "working", "work status", "job status"],
    "family": ["family", "family structure", "marital", "married", "single parent", "cohabiting"],
    "nativity": ["nativity", "foreign born", "us born", "u.s. born", "born in the us"],
    "veteran": ["veteran", "veterans", "military service"],
    "total": ["total", "overall", "all"],
}

GROUP_LABEL_HINTS = {
    "sexual_orientation": ["sexual orientation"],
    "sex": ["sex"],
    "age": ["age"],
    "race": ["race"],
    "hispanic": ["hispanic", "latino"],
    "region": ["region"],
    "metro": ["metro", "metropolitan", "urbanicity", "place of residence"],
    "poverty": ["family income", "poverty", "fpl", "income"],
    "social_vulnerability": ["social vulnerability", "social vulnerability index", "svi", "vulnerability"],
    "insurance": ["insurance", "coverage"],
    "education": ["education"],
    "difficulty": ["difficulty", "functioning", "functional limitation"],
    "disability": ["disability"],
    "employment": ["employment", "working"],
    "family": ["family", "marital"],
    "nativity": ["nativity"],
    "veteran": ["veteran"],
    "total": ["total"],
}

VALUE_SYNONYMS = {
    "gay adult males": "Gay or Lesbian",
    "gay adults": "Gay or Lesbian",
    "gay men": "Gay or Lesbian",
    "gay males": "Gay or Lesbian",
    "gay": "Gay or Lesbian",
    "lesbian": "Gay or Lesbian",
    "gay or lesbian": "Gay or Lesbian",
    "bisexual": "Bisexual",
    "bi adults": "Bisexual",
    "straight": "Straight",
    "heterosexual": "Straight",
    "women": "Female",
    "woman": "Female",
    "female": "Female",
    "girls": "Female",
    "girl": "Female",
    "men": "Male",
    "man": "Male",
    "male": "Male",
    "boys": "Male",
    "boy": "Male",
    "65+": "65 years and over",
    "65 and older": "65 years and over",
    "65 years and older": "65 years and over",
    "65 and over": "65 years and over",
    "75+": "75 years and over",
    "75 and older": "75 years and over",
    "75 and over": "75 years and over",
    "uninsured": "Uninsured",
    "insured": "Insured",
    "private insurance": "Private",
    "private coverage": "Private",
    "private": "Private",
    "medicaid": "Medicaid or other state programs",
    "medicare advantage": "Medicare Advantage",
    "high svi": "High social vulnerability",
    "high vulnerability": "High social vulnerability",
    "high social vulnerability": "High social vulnerability",
    "medium svi": "Medium social vulnerability",
    "medium vulnerability": "Medium social vulnerability",
    "medium social vulnerability": "Medium social vulnerability",
    "low svi": "Low social vulnerability",
    "low vulnerability": "Low social vulnerability",
    "low social vulnerability": "Low social vulnerability",
    "lowest svi": "Little to no social vulnerability",
    "little/no svi": "Little to no social vulnerability",
    "little to no svi": "Little to no social vulnerability",
    "little to no social vulnerability": "Little to no social vulnerability",
    "single parent": "Single parent",
    "single-parent": "Single parent",
    "single parent families": "Single parent",
    "single parent family": "Single parent",
    "married parents": "Married parents",
    "two parent families": "Married parents",
    "cohabiting parents": "Cohabiting parents",
    "cohabiting parent": "Cohabiting parents",
    "northeast": "Northeast",
    "midwest": "Midwest",
    "south": "South",
    "west": "West",
    "large msa": "Large MSA",
    "small msa": "Small MSA",
    "not in msa": "Not in MSA",
    "non-msa": "Nonmetropolitan",
    "nonmetropolitan": "Nonmetropolitan",
    "large central metro": "Large central metro",
    "large fringe metro": "Large fringe metro",
    "medium and small metro": "Medium and small metro",
    "white": "White only, non-Hispanic",
    "black": "Black only, non-Hispanic",
    "asian": "Asian only, non-Hispanic",
    "hispanic": "Hispanic",
    "latino": "Hispanic",
    "mexican": "Mexican or Mexican American",
}

GROUP_PRIORITY = [
    "Sexual orientation",
    "Sex",
    "Age groups with 65+",
    "Age groups with 75+",
    "Age groups",
    "Race",
    "Hispanic or Latino origin and race",
    "Region",
    "Metropolitan statistical area status",
    "Place of residence",
    "Metro",
    "Urbanicity",
    "Family income",
    "Poverty status",
    "Social vulnerability",
    "Social vulnerability index",
    "Health insurance coverage",
    "Health insurance coverage: Under 65",
    "Health insurance coverage: 65 and over",
    "Education",
    "Parental Education",
    "Disability status",
    "Disability Status",
    "Difficulty status",
    "Difficulty Status",
    "Employment status",
    "Working status",
    "Marital status",
    "Family structure",
    "Nativity",
    "Veteran Status",
    "Total",
]


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _contains_wordish(needle: str, haystack: str) -> bool:
    if not needle:
        return False
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])", haystack))


def _phrase_in_question(phrase: str, q: str) -> bool:
    np = normalize_text(phrase)
    if not np:
        return False
    if len(np) <= 3:
        return _contains_wordish(np, q)
    return _contains_wordish(np, q) or np in q


def detect_population(question: str, topic_guess: str = "") -> Optional[str]:
    q = normalize_text(question)
    if any(_phrase_in_question(w, q) for w in POP_CHILD_WORDS):
        return "child"
    if any(_phrase_in_question(w, q) for w in POP_ADULT_WORDS):
        return "adult"
    tg = normalize_text(topic_guess)
    if "child" in tg or "children" in tg:
        return "child"
    if "adult" in tg or "adults" in tg:
        return "adult"
    return None


def extract_years(question: str, df: pd.DataFrame) -> tuple[list[int], dict]:
    years = sorted(int(y) for y in df["Year"].dropna().unique())
    q = normalize_text(question)
    explicit = [int(y) for y in re.findall(r"\b(20\d{2})\b", question)]
    if explicit:
        return [explicit[-1]], {"mode": "explicit", "explanation": None, "available_years": years}
    m = re.search(r"\b(?:last|past|most recent|latest)\s+(\d+)\s+years?\b", q)
    if m:
        n = max(1, int(m.group(1)))
        selected = years[-n:]
        return selected, {"mode": "last_n_years", "n": n, "explanation": f"You asked for the last {n} years, so I used the latest {len(selected)} years available in the current DHIS file: {selected[0]}–{selected[-1]}.", "available_years": years}
    if "last year" in q or "latest year" in q or "most recent year" in q or ("latest" in q and "year" in q) or ("most recent" in q and "year" in q):
        return [years[-1]], {"mode": "latest", "explanation": f"You asked for the latest/last year, so I used the latest year available in the current DHIS file: {years[-1]}.", "available_years": years}
    return years, {"mode": "all_available", "explanation": f"No year was specified, so I returned all years available in the current DHIS file ({years[0]}–{years[-1]}).", "available_years": years}


def extract_year(question: str, df: pd.DataFrame) -> int:
    return extract_years(question, df)[0][-1]


def topic_candidates_from_mapping(keyword_mappings: dict) -> list[tuple[str, str, float]]:
    out = []
    for _key, obj in keyword_mappings.get("topic_mappings", {}).items():
        conf = float(obj.get("confidence", 0.75))
        cdc_topics = obj.get("cdc_topics", []) or []
        user_keywords = obj.get("user_keywords", []) or []
        for kw in user_keywords:
            for topic in cdc_topics or [kw]:
                out.append((kw, topic, conf))
    return out


def _resolve_mapped_topic(mapped_topic: str, outcomes: list[str]) -> Optional[str]:
    norm_to_out = {normalize_text(o): o for o in outcomes}
    stripped_to_out = {strip_population_suffix(o): o for o in outcomes}
    mt_norm = normalize_text(mapped_topic)
    mt_strip = strip_population_suffix(mapped_topic)
    if mt_norm in norm_to_out:
        return norm_to_out[mt_norm]
    if mt_strip in stripped_to_out:
        return stripped_to_out[mt_strip]
    best_o, best_or = None, 0.0
    for so, real in stripped_to_out.items():
        r = max(_ratio(mt_strip, so), 1.0 if mt_strip and (mt_strip in so or so in mt_strip) else 0.0)
        if r > best_or:
            best_o, best_or = real, r
    return best_o if best_or >= 0.74 else None


def match_topic(question: str, df: pd.DataFrame, keyword_mappings: dict) -> tuple[Optional[str], dict]:
    q = normalize_text(question)
    # Treat text before an explicit "by ..." as the topic portion.
    # Grouping/subgroup terms after "by" should not override a clear topic such as "flu shot".
    topic_part = q.split(" by ", 1)[0] if " by " in q else q
    outcomes = sorted(df["Outcome (or Indicator)"].dropna().unique())
    best = {"score": 0.0, "keyword": None, "mapped_topic": None, "method": None, "outcome": None}

    # Strong deconfliction phrases that should win before generic topic or subgroup words.
    if "asthma" in q and any(p in q for p in ["ever", "ever had", "ever having"]):
        outcome = _resolve_mapped_topic("Ever having asthma", outcomes)
        if outcome:
            best = {"score": 1.32, "keyword": "ever asthma", "mapped_topic": "Ever having asthma", "method": "strong_deconfliction_phrase", "outcome": outcome}
        else:
            # The adult SHS file currently has current asthma and asthma episode/attack, but not
            # an ever-asthma outcome. Do not silently convert an explicit ever-asthma request to
            # current asthma.
            return None, {"score": 0.0, "keyword": "ever asthma", "mapped_topic": "Ever having asthma", "method": "explicit_topic_not_available", "outcome": None}

    if "learning disability" in q:
        outcome = _resolve_mapped_topic("Ever having a learning disability", outcomes)
        if outcome and 1.31 > best["score"]:
            best = {"score": 1.31, "keyword": "learning disability", "mapped_topic": "Ever having a learning disability", "method": "strong_deconfliction_phrase", "outcome": outcome}
    if any(p in q for p in ["special education", "early intervention"]):
        outcome = _resolve_mapped_topic("Receiving special education or early intervention services", outcomes)
        if outcome and 1.30 > best["score"]:
            best = {"score": 1.30, "keyword": "special education", "mapped_topic": "Receiving special education or early intervention services", "method": "strong_deconfliction_phrase", "outcome": outcome}
    if any(p in q for p in ["mental health services"]):
        outcome = _resolve_mapped_topic("Receive services for mental health problems", outcomes)
        if outcome and 1.29 > best["score"]:
            best = {"score": 1.29, "keyword": "mental health services", "mapped_topic": "Receive services for mental health problems", "method": "strong_deconfliction_phrase", "outcome": outcome}
    if any(p in q for p in ["anxiety medicine", "anxiety medication", "anxiety meds", "medication for anxiety", "medicine for anxiety"]):
        outcome = _resolve_mapped_topic("Taking prescription medication for feelings of worry, nervousness, or anxiety", outcomes)
        if outcome:
            best = {"score": 1.30, "keyword": "anxiety medication", "mapped_topic": "Taking prescription medication for feelings of worry, nervousness, or anxiety", "method": "strong_deconfliction_phrase", "outcome": outcome}
    if any(p in q for p in ["depression medicine", "depression medication", "depression meds", "medication for depression", "medicine for depression"]):
        outcome = _resolve_mapped_topic("Taking prescription medication for feelings of depression", outcomes)
        if outcome and 1.30 > best["score"]:
            best = {"score": 1.30, "keyword": "depression medication", "mapped_topic": "Taking prescription medication for feelings of depression", "method": "strong_deconfliction_phrase", "outcome": outcome}
    if any(p in q for p in ["skipped medicine", "skipped medication", "skipped meds", "medicine to save money", "medication to save money", "meds to save money"]):
        outcome = _resolve_mapped_topic("Did not take medication as prescribed to save money", outcomes)
        if outcome and 1.28 > best["score"]:
            best = {"score": 1.28, "keyword": "skipped medicine", "mapped_topic": "Did not take medication as prescribed to save money", "method": "strong_deconfliction_phrase", "outcome": outcome}
    if any(p in q for p in ["could not afford care", "couldnt afford care", "could not afford medical care", "couldnt afford medical care", "did not get care due to cost"]):
        outcome = _resolve_mapped_topic("Did not get needed medical care due to cost", outcomes)
        if outcome and 1.26 > best["score"]:
            best = {"score": 1.26, "keyword": "could not afford care", "mapped_topic": "Did not get needed medical care due to cost", "method": "strong_deconfliction_phrase", "outcome": outcome}
    if any(p in q for p in ["urgent or retail", "urgent care or retail", "urgent care and retail"]):
        outcome = _resolve_mapped_topic("Urgent care center or retail health clinic visit", outcomes)
        if outcome and 1.24 > best["score"]:
            best = {"score": 1.24, "keyword": "urgent or retail", "mapped_topic": "Urgent care center or retail health clinic visit", "method": "strong_deconfliction_phrase", "outcome": outcome}
    if any(p in q for p in ["school absences", "school absence", "missed school"]):
        outcome = _resolve_mapped_topic("Missing 11 or more school days due to illness or injury", outcomes)
        if outcome and 1.22 > best["score"]:
            best = {"score": 1.22, "keyword": "school absences", "mapped_topic": "Missing 11 or more school days due to illness or injury", "method": "strong_deconfliction_phrase", "outcome": outcome}

    # Strong action phrases: these are common user phrasings where another word in the
    # same question may be a subgroup (for example, "uninsured kids got a flu shot").
    if any(p in q for p in ["got a flu shot", "flu shot", "flu vaccine", "flu vaccination", "influenza vaccine", "influenza vaccination"]):
        outcome = _resolve_mapped_topic("Receipt of influenza vaccination", outcomes)
        if outcome:
            best = {"score": 1.20, "keyword": "flu shot", "mapped_topic": "Receipt of influenza vaccination", "method": "strong_action_phrase", "outcome": outcome}

    for keyword, mapped_topics in MANUAL_TOPIC_SYNONYMS.items():
        nkw = normalize_text(keyword)
        hit_topic = _contains_wordish(nkw, topic_part) or (len(nkw) >= 5 and nkw in topic_part)
        hit_full = _contains_wordish(nkw, q) or (len(nkw) >= 5 and nkw in q)
        if hit_topic or hit_full:
            for mapped_topic in mapped_topics:
                outcome = _resolve_mapped_topic(mapped_topic, outcomes)
                if outcome:
                    base = 1.05 if normalize_text(outcome) in topic_part or strip_population_suffix(outcome) in topic_part else 0.94
                    score = base if hit_topic else base - 0.20
                    if score > best["score"]:
                        best = {"score": score, "keyword": keyword, "mapped_topic": mapped_topic, "method": "manual_synonym", "outcome": outcome}

    for kw, mapped_topic, conf in topic_candidates_from_mapping(keyword_mappings):
        nkw = normalize_text(kw)
        if not nkw:
            continue
        hit_topic = _contains_wordish(nkw, topic_part) or (len(nkw) >= 5 and nkw in topic_part)
        hit_full = _contains_wordish(nkw, q) or (len(nkw) >= 5 and nkw in q)
        if hit_topic or hit_full:
            outcome = _resolve_mapped_topic(mapped_topic, outcomes)
            if outcome:
                score = conf + (0.03 if normalize_text(mapped_topic) in topic_part else 0)
                if not hit_topic:
                    score -= 0.20
                if score > best["score"]:
                    best = {"score": score, "keyword": kw, "mapped_topic": mapped_topic, "method": "keyword_mapping", "outcome": outcome}

    # Conservative fuzzy fallback against actual outcome labels only.
    for outcome in outcomes:
        no = normalize_text(outcome)
        so = strip_population_suffix(outcome)
        score = max(_ratio(q, no), _ratio(q, so), 0.90 if so and so in q else 0.0)
        if score > best["score"] and score >= 0.78:
            best = {"score": score, "keyword": outcome, "mapped_topic": outcome, "method": "outcome_fuzzy", "outcome": outcome}

    return best["outcome"], best



def _has_any_phrase(q: str, phrases: list[str]) -> bool:
    # Strict word/phrase boundaries are needed here so "elderly" does not match "nonelderly"
    # and age-qualified insurance routing does not flip to the 65+ grouping incorrectly.
    return any(_contains_wordish(normalize_text(t), q) for t in phrases)


def _has_insurance_cue(q: str) -> bool:
    return _has_any_phrase(q, [
        "insurance", "insured", "uninsured", "coverage", "private coverage",
        "private insurance", "medicaid", "medicare", "health plan"
    ])


def _has_under65_insurance_cue(q: str) -> bool:
    return _has_any_phrase(q, [
        "under 65", "under age 65", "younger than 65", "younger than age 65",
        "less than 65", "below 65", "65 and under", "65 or under",
        "nonelderly", "non elderly", "non-elderly", "18-64", "18 to 64",
        "18 through 64", "aged 18-64", "ages 18-64"
    ])


def _has_over65_insurance_cue(q: str) -> bool:
    return _has_any_phrase(q, [
        "65+", "65 and over", "65 years and over", "65 or over",
        "65 and older", "65 years and older", "65 or older",
        "older than 65", "age 65 and over", "aged 65 and over",
        "seniors", "senior", "elderly", "older adults", "medicare advantage",
        "medicare and medicaid", "medicare only", "medicare"
    ])



def _has_income_poverty_cue(q: str) -> bool:
    return _has_any_phrase(q, [
        "family income", "household income", "income", "income group", "income level",
        "poverty", "poverty status", "fpl", "federal poverty level",
        "income to poverty", "income-to-poverty", "below poverty", "family poverty"
    ])

def _force_age_specific_insurance_label(labels: list[str], q: str, actual: list[str]) -> list[str]:
    """Resolve adult age-qualified insurance labels before generic age logic.

    The adult file has two separate insurance groupings: Under 65 and 65 and over.
    Generic phrasing such as "65+ by insurance" was previously selecting Under 65
    because the fallback insurance resolver found the first insurance-like label.
    This function makes age-qualified insurance wording explicit and removes competing
    age-group labels when the user is clearly asking for an insurance breakdown.
    """
    if not _has_insurance_cue(q):
        return labels
    desired = None
    if _has_over65_insurance_cue(q) and "Health insurance coverage: 65 and over" in actual:
        desired = "Health insurance coverage: 65 and over"
    elif _has_under65_insurance_cue(q) and "Health insurance coverage: Under 65" in actual:
        desired = "Health insurance coverage: Under 65"
    if not desired:
        return labels
    out = [l for l in labels if not l.startswith("Health insurance coverage") and not l.startswith("Age groups")]
    out.insert(0, desired)
    return list(dict.fromkeys(out))

def _population_from_df(df: pd.DataFrame) -> Optional[str]:
    outcomes = " ".join(sorted(set(map(str, df["Outcome (or Indicator)"].dropna().head(100)))))
    n = normalize_text(outcomes)
    if "children" in n or "child" in n:
        return "child"
    if "adult" in n or "adults" in n:
        return "adult"
    # Fallback: child file has no Sexual orientation/Veteran Status and has Parental Education.
    labels = set(map(str, df.get("col_label", pd.Series(dtype=str)).dropna().unique()))
    if "Parental Education" in labels or "Family structure" in labels:
        return "child"
    if "Sexual orientation" in labels or "Veteran Status" in labels:
        return "adult"
    return None


def _json_group_entries(keyword_mappings: dict | None, df: pd.DataFrame) -> list[dict]:
    if not keyword_mappings:
        return []
    pop = _population_from_df(df)
    entries = []
    if pop:
        pop_map = keyword_mappings.get("population_demographic_mappings", {}).get(pop, {})
        entries.extend(pop_map.values())
    # Backward-compatible enhanced structure: demographic_mappings -> concept -> population-specific entries.
    for concept_obj in keyword_mappings.get("demographic_mappings", {}).values():
        if isinstance(concept_obj, dict):
            for obj in concept_obj.values():
                if isinstance(obj, dict) and (not pop or obj.get("population") == pop):
                    entries.append(obj)
    seen = set()
    out = []
    for obj in entries:
        labels = tuple(obj.get("cdc_groups", []) or [])
        key = (obj.get("population"), labels)
        if labels and key not in seen:
            seen.add(key)
            out.append(obj)
    return out


def _actual_labels(df: pd.DataFrame) -> list[str]:
    return sorted([str(x) for x in df["col_label"].dropna().unique()])


def _entry_for_label(keyword_mappings: dict | None, df: pd.DataFrame, label: str) -> Optional[dict]:
    nl = normalize_text(label)
    for obj in _json_group_entries(keyword_mappings, df):
        for g in obj.get("cdc_groups", []) or []:
            if normalize_text(g) == nl:
                return obj
    return None


def _label_for_entry(obj: dict, df: pd.DataFrame) -> Optional[str]:
    labels = _actual_labels(df)
    norm_to_real = {normalize_text(l): l for l in labels}
    for g in obj.get("cdc_groups", []) or []:
        if normalize_text(g) in norm_to_real:
            return norm_to_real[normalize_text(g)]
    return None


def _by_segment(q: str) -> str:
    # Restrict explicit breakdown matching to the phrase after "by" when available.
    m = re.search(r"\bby\s+(.+)$", q)
    if m:
        return m.group(1)
    m = re.search(r"\bbreakdown\s+(?:by|of)?\s*(.+)$", q)
    if m:
        return m.group(1)
    return ""


def _label_matches_question(label: str, obj: dict | None, q: str, by_part: str) -> bool:
    fields = [label]
    if obj:
        fields.extend(obj.get("user_keywords", []) or [])
    targets = [by_part] if by_part else [q]
    # Require stronger evidence for generic labels such as Race/Sex/Age unless they are explicit in a by-clause.
    for target in targets:
        for kw in fields:
            nkw = normalize_text(kw)
            if not nkw:
                continue
            if _contains_wordish(nkw, target) or (len(nkw) >= 5 and nkw in target):
                return True
    return False


def _requested_labels(question: str, df: pd.DataFrame, keyword_mappings: dict | None = None) -> list[str]:
    q = normalize_text(question)
    by_part = _by_segment(q)
    labels = []
    actual = _actual_labels(df)

    # 1) JSON-specific grouping keywords, exact to available col_label values.
    for obj in _json_group_entries(keyword_mappings, df):
        label = _label_for_entry(obj, df)
        if not label:
            continue
        if _label_matches_question(label, obj, q, by_part) and label not in labels:
            labels.append(label)

    # 2) Fallback hard-coded concepts only if JSON missed it.
    for key, words in GROUP_SYNONYMS.items():
        if key == "total":
            continue
        target = by_part or q
        if any(_phrase_in_question(w, target) for w in words):
            lab = label_for_key(df, key)
            if lab and lab not in labels:
                labels.append(lab)

    # 3) Exact label names in by-clause.
    target = by_part or q
    for lab in actual:
        if _phrase_in_question(lab, target) and lab not in labels:
            labels.append(lab)

    labels = _force_age_specific_insurance_label(labels, q, actual)

    # Income/poverty/FPL wording should always route to the user-facing Family income
    # concept. Remove competing family/marital labels that are only triggered by the
    # word "family" in "family income". The retriever can still use Poverty status
    # rows behind the scenes when those are where the FPL rows are stored.
    if _has_income_poverty_cue(q):
        labels = [l for l in labels if l not in {"Family structure", "Marital status"}]
        labels = [l for l in labels if l not in {"Family income", "Poverty status"}]
        labels.insert(0, "Family income")

    labels.sort(key=lambda l: GROUP_PRIORITY.index(l) if l in GROUP_PRIORITY else 999)

    # Deconflict grouping families where the files have multiple related labels.
    # This prevents generic words like "age" or "insurance" from selecting every
    # adult age/insurance label when the query contains a more specific cue.
    def keep_one(options, preferred):
        nonlocal labels
        present = [x for x in options if x in labels]
        if len(present) <= 1:
            return
        chosen = preferred(present)
        labels = [x for x in labels if x not in present or x == chosen]

    keep_one(["Age groups with 65+", "Age groups with 75+"],
             lambda present: "Age groups with 75+" if any(t in q for t in ["75", "oldest"]) else "Age groups with 65+")
    keep_one(["Health insurance coverage: 65 and over", "Health insurance coverage: Under 65"],
             lambda present: "Health insurance coverage: 65 and over" if _has_over65_insurance_cue(q) and not _has_under65_insurance_cue(q) else "Health insurance coverage: Under 65")
    keep_one(["Metropolitan statistical area status", "Urbanicity"],
             lambda present: "Urbanicity" if any(t in q for t in ["urbanicity", "urban rural", "nonmetropolitan", "central metro", "fringe metro"]) else "Metropolitan statistical area status")
    keep_one(["Place of residence", "Metro"],
             lambda present: "Metro" if any(t in q for t in ["urbanicity", "central metro", "fringe metro", "nonmetropolitan"]) else "Place of residence")
    # Family income and Poverty status use the same FPL-style subgroup rows in the
    # current SHS files. Treat all user wording (income, household income, FPL,
    # poverty, below poverty) as the same user-facing concept: Family income.
    # The retriever will prefer the actual Family income label when present and
    # safely fall back to Poverty status rows when those are where the current
    # year/topic data live.
    keep_one(["Family income", "Poverty status"], lambda present: "Family income")
    keep_one(["Family income", "Family structure"],
             lambda present: "Family income" if any(t in q for t in ["family income", "household income", "income group"]) else "Family structure")
    keep_one(["Race", "Hispanic or Latino origin and race"],
             lambda present: "Hispanic or Latino origin and race" if any(t in q for t in ["ethnicity", "hispanic", "latino", "mexican", "race and ethnicity", "hispanic origin"]) else "Race")
    keep_one(["Disability status", "Difficulty status"],
             lambda present: "Difficulty status" if any(t in q for t in ["difficulty", "functioning", "functional limitation"]) else "Disability status")
    keep_one(["Disability Status", "Difficulty Status"],
             lambda present: "Difficulty Status" if any(t in q for t in ["difficulty", "functioning", "functional limitation"]) else "Disability Status")
    # If an insurance grouping is explicitly requested, do not also treat age 65 wording in the
    # insurance label as an age breakdown request.
    if any(l.startswith("Health insurance coverage") for l in labels):
        labels = [l for l in labels if not l.startswith("Age groups") or not any(x.startswith("Health insurance coverage") for x in labels)]

    return labels


def requested_group_keys(question: str, df: pd.DataFrame | None = None, keyword_mappings: dict | None = None) -> list[str]:
    # Backward-compatible public helper: returns grouping labels, not generic keys.
    if df is None:
        q = normalize_text(question)
        keys = []
        for key, words in GROUP_SYNONYMS.items():
            if key != "total" and any(_phrase_in_question(w, q) for w in words):
                keys.append(key)
        return keys
    return _requested_labels(question, df, keyword_mappings)


def requested_group_values(question: str, df: pd.DataFrame, keyword_mappings: dict | None = None) -> list[str]:
    q = normalize_text(question)
    values = []

    for phrase, canonical in VALUE_SYNONYMS.items():
        if _phrase_in_question(phrase, q) and canonical not in values:
            values.append(canonical)

    # Use subgroup keywords from the NHIS-specific JSON mapping, preserving available group labels.
    actual_groups = {normalize_text(g): str(g) for g in df["Group"].dropna().unique()}
    for obj in _json_group_entries(keyword_mappings, df):
        for canonical, kws in (obj.get("subgroup_keywords", {}) or {}).items():
            canon_real = actual_groups.get(normalize_text(canonical), canonical)
            if any(_phrase_in_question(kw, q) for kw in kws) and canon_real not in values:
                values.append(canon_real)

    # Exact group value contained in question, with longer values checked first.
    groups = sorted(df["Group"].dropna().unique(), key=lambda x: len(str(x)), reverse=True)
    for g in groups:
        ng = normalize_text(g)
        if ng and len(ng) >= 3 and _phrase_in_question(ng, q) and str(g) not in values:
            values.append(str(g))
    return values


def _label_score_for_key(label: str, key: str) -> float:
    nl = normalize_text(label)
    hints = GROUP_LABEL_HINTS.get(key, [])
    return max([(1.0 if _contains_wordish(normalize_text(h), nl) else _ratio(normalize_text(h), nl)) for h in hints] or [0])


def label_for_key(df: pd.DataFrame, key: str) -> Optional[str]:
    # If caller already passed an exact label, return it.
    norm_to_label = {normalize_text(lab): lab for lab in _actual_labels(df)}
    if normalize_text(key) in norm_to_label:
        return norm_to_label[normalize_text(key)]
    labels = sorted(df["col_label"].dropna().unique())
    scored = sorted([(_label_score_for_key(str(lab), key), str(lab)) for lab in labels], reverse=True)
    return scored[0][1] if scored and scored[0][0] >= 0.55 else None


def infer_label_for_value(df: pd.DataFrame, value: str, preferred_labels: list[str] | None = None) -> Optional[str]:
    rv = normalize_text(value)
    possible = df[df["Group"].map(normalize_text).eq(rv)]
    if possible.empty:
        possible = df[df["Group"].map(lambda x: rv in normalize_text(x) or normalize_text(x) in rv)]
    if possible.empty:
        return None
    if preferred_labels:
        pref = {normalize_text(x) for x in preferred_labels}
        possible_pref = possible[possible["col_label"].map(normalize_text).isin(pref)]
        if not possible_pref.empty:
            possible = possible_pref
    # Prefer the actual grouping labels in the same priority order to avoid sex/race/value overlaps.
    vc = possible["col_label"].value_counts()
    ordered = sorted(vc.index, key=lambda l: GROUP_PRIORITY.index(l) if l in GROUP_PRIORITY else 999)
    return str(ordered[0]) if ordered else str(vc.index[0])


def find_composite_label(df: pd.DataFrame, labels: list[str], values: list[str]) -> Optional[str]:
    # Labels are now actual col_label values. A true composite exists only when one label contains
    # every requested label/concept (rare in current adult/child SHS files).
    all_labels = sorted(df["col_label"].dropna().unique())
    requested = [normalize_text(x) for x in labels]
    candidates = []
    for lab in all_labels:
        nl = normalize_text(lab)
        hits = sum(1 for r in requested if r and ((_contains_wordish(r, nl) or _contains_wordish(nl, r)) if len(r) <= 3 or len(nl) <= 3 else (r in nl or nl in r)))
        # Also allow concept-like matches (Race + Hispanic, Age + Sex, etc.).
        concept_hits = 0
        for r in requested:
            if ("race" in r and "race" in nl) or ("hispanic" in r and "hispanic" in nl) or ("age" in r and "age" in nl) or ("sex" == r and _contains_wordish("sex", nl)) or ("poverty" in r and "poverty" in nl) or ("income" in r and "income" in nl):
                concept_hits += 1
        candidates.append((max(hits, concept_hits), lab))
    candidates.sort(reverse=True)
    if candidates and candidates[0][0] >= max(2, len(labels)):
        return str(candidates[0][1])
    return None


def _labels_for_values(df: pd.DataFrame, values: list[str], preferred: list[str] | None = None) -> list[str]:
    out = []
    for v in values:
        lab = infer_label_for_value(df, v, preferred_labels=preferred)
        if lab and lab not in out:
            out.append(lab)
    return out


def _value_belongs_to_label(df: pd.DataFrame, value: str, label: str) -> bool:
    rv = normalize_text(value)
    lab_norm = normalize_text(label)
    s = df[(df["col_label"].map(normalize_text).eq(lab_norm)) & (df["Group"].map(lambda g: rv == normalize_text(g) or rv in normalize_text(g) or normalize_text(g) in rv))]
    return not s.empty


def detect_group_intent(question: str, df: pd.DataFrame, keyword_mappings: dict | None = None) -> tuple[Optional[str], Optional[str], dict]:
    q = normalize_text(question)
    labels = _requested_labels(question, df, keyword_mappings)
    values = requested_group_values(question, df, keyword_mappings=keyword_mappings)
    wants_breakdown = " by " in f" {q} " or q.startswith("show ") or "breakdown" in q
    wants_total = any(_phrase_in_question(t, q) for t in ["total", "overall", "all adults", "all children", "all kids"])

    # If an age-qualified insurance grouping is selected, age words such as "65+"
    # are part of the grouping label, not a subgroup row.
    if labels and labels[0].startswith("Health insurance coverage"):
        values = [v for v in values if _value_belongs_to_label(df, v, labels[0])]

    # If a label was only inferred from a topic word (for example "special education" or
    # "missed school") and the user did not ask for a breakdown or name a subgroup value,
    # do not filter to that demographic label.
    if labels and not wants_breakdown and not values and not wants_total:
        keep_contextual_label = (" among " in f" {q} " or " with " in f" {q} ") and any(
            l.startswith("Health insurance coverage") or "Social vulnerability" in l or l in {"Sexual orientation", "Disability status", "Difficulty status"}
            for l in labels
        )
        if not keep_contextual_label:
            labels = []

    # If values are named but no grouping label was named, infer labels from the value(s).
    if values and not labels:
        labels = _labels_for_values(df, values)

    # If both an explicit label and subgroup values exist, keep only values that can belong to the chosen label first.
    if labels and values:
        primary = labels[0]
        label_values = [v for v in values if _value_belongs_to_label(df, v, primary)]
        if label_values:
            values = label_values + [v for v in values if v not in label_values]

    # Try a true composite/crosstab grouping if the user requested multiple dimensions.
    if len(labels) > 1:
        composite = find_composite_label(df, labels, values)
        if composite:
            return composite, None if wants_breakdown else (values[0] if len(values) == 1 else None), {
                "wants_breakdown": wants_breakdown or not values,
                "requested_keys": labels,
                "requested_values": values,
                "is_composite": True,
                "explanation": None,
            }
        # Prefer the first concrete non-sex grouping when multiple subgroup concepts are named.
        primary = labels[0]
        if "Sexual orientation" in labels:
            primary = "Sexual orientation"
        chosen_value = None
        for v in values:
            if _value_belongs_to_label(df, v, primary):
                chosen_value = v
                break
        return primary or "Total", chosen_value, {
            "wants_breakdown": True,
            "requested_keys": labels,
            "requested_values": values,
            "is_composite": False,
            "explanation": "You requested more than one grouping/subgroup. A multi-group crosstab was not available for that exact combination in the current DHIS file, so I returned the closest available single grouping and list the requested subgroup first when available.",
            "subgroup_first": bool(chosen_value),
        }

    label = labels[0] if labels else None
    if wants_total and not label:
        label = "Total"

    if label or values:
        group_value = None
        if values:
            if label:
                for v in values:
                    if _value_belongs_to_label(df, v, label):
                        group_value = v
                        break
            else:
                group_value = values[0]
        return label or infer_label_for_value(df, group_value or "") or "Total", group_value, {
            "wants_breakdown": wants_breakdown or bool(group_value),
            "requested_keys": labels,
            "requested_values": values,
            "is_composite": False,
            "explanation": None,
            "subgroup_first": bool(group_value),
        }

    return "Total", None, {"wants_breakdown": False, "requested_keys": [], "requested_values": [], "is_composite": False, "explanation": None}
