from __future__ import annotations
from pathlib import Path
import json
import math
import re
from collections import Counter
from normalize_text import normalize_text

ROOT = Path(__file__).resolve().parents[1]
FAQ_INDEX_PATH = ROOT / "data" / "faq_index" / "faq_index_seed.json"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for",
    "from", "how", "i", "in", "is", "it", "of", "on", "or", "that", "the", "their",
    "this", "to", "use", "used", "what", "when", "where", "who", "why", "with", "you",
    "me", "my", "your", "about", "tell", "get", "find", "file", "files"
}

FAQ_INTENT_TERMS = [
    "what is nhis", "about nhis", "who is included", "included in nhis", "population", "sample",
    "questionnaire", "documentation", "public use", "puf", "data files", "download data",
    "how are data used", "confidential", "confidentiality", "privacy", "data safe", "data secure",
    "restricted data", "rdc", "redesign", "state estimates", "preliminary", "early release",
    "dqt", "data query", "dashboard", "methods", "weights", "where can i find",
    "where do i find", "where do i get", "documentation page", "survey design",
    # Participant / respondent-facing source retrieval terms. These route to the FAQ/document source
    # retriever, not to a free-form persuasion module.
    "participate", "participation", "participant", "respondent", "interviewer", "field representative",
    "why should i participate", "why participate", "what is in it for me", "what's in it for me",
    "benefit from participating", "directly benefit", "real life benefits", "six real life benefits",
    "why was i selected", "selected for nhis", "survey legitimate", "is this legitimate",
    "what to expect", "what should i expect", "survey letter", "nhis letter", "trust",
    "data breach", "alias", "my information", "personal information", "refuse", "reluctant",
    "values language", "real life benefits", "real-life benefits", "how has nhis data helped",
    "how does nhis data help", "nhis impact", "impact summaries", "talking points",
    "how data helped", "how data help", "used to help", "data benefits"
]

PHRASE_BOOSTS = [
    "public use", "questionnaires", "documentation", "data query", "preliminary", "final data",
    "restricted data", "confidential", "confidentiality", "privacy", "data safe", "data secure",
    "civilian", "institutions", "children", "adults", "subgroups", "early release",
    "sample adult", "sample child", "weights", "survey design", "state estimates", "nhis teen",
    "health insurance", "redesign", "participants", "participant", "respondent", "interview",
    "why participate", "what to expect", "what should i expect", "selected", "real life benefits",
    "real-life benefits", "nhis impact", "cancer screening", "asthma", "diabetes", "insulin",
    "hearing aids", "values", "personal privacy", "selected", "benefit", "help real people",
    "how data helped", "survey legitimate"
]


def load_faq_index(path: Path = FAQ_INDEX_PATH) -> list[dict]:
    """Load the local approved-source FAQ index."""
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    docs = data.get("documents", [])
    # Normalize older seed indexes to the richer Phase 4 shape.
    for d in docs:
        d.setdefault("id", d.get("url", "source"))
        d.setdefault("title", "NHIS source")
        d.setdefault("url", "")
        d.setdefault("source_type", "cdc_nhis_webpage")
        d.setdefault("source_category", d.get("source_type", "cdc_nhis_webpage"))
        d.setdefault("text", "")
        d.setdefault("excerpt", d.get("text", "")[:450])
    return docs


def _tokens(text: str) -> list[str]:
    txt = normalize_text(text)
    toks = re.findall(r"[a-z0-9]+", txt)
    return [t for t in toks if t not in STOPWORDS and len(t) > 1]


def looks_like_faq_question(question: str) -> bool:
    q = normalize_text(question)
    return any(term in q for term in FAQ_INTENT_TERMS)


def _score(query: str, doc: dict) -> float:
    q_tokens = _tokens(query)
    if not q_tokens:
        return 0.0
    d_text = f"{doc.get('title','')} {doc.get('text','')} {doc.get('excerpt','')}"
    d_tokens = _tokens(d_text)
    if not d_tokens:
        return 0.0
    q_counts = Counter(q_tokens)
    d_counts = Counter(d_tokens)
    overlap = sum(min(q_counts[t], d_counts[t]) for t in q_counts)
    # Title matches should matter because the index is intentionally curated.
    title_tokens = set(_tokens(doc.get("title", "")))
    title_overlap = sum(1 for t in set(q_tokens) if t in title_tokens)
    qn = normalize_text(query)
    dn = normalize_text(d_text)
    phrase_boost = sum(1.0 for phrase in PHRASE_BOOSTS if phrase in qn and phrase in dn)
    url_boost = 0.5 if "documentation" in qn and "documentation" in normalize_text(doc.get("url", "")) else 0.0
    category = normalize_text(doc.get("source_category", "") + " " + doc.get("source_type", ""))
    title = normalize_text(doc.get("title", ""))
    intent_boost = 0.0
    impact_query = any(p in qn for p in ["help real people", "real life benefit", "real-life benefit", "benefit people", "nhis impact", "talking point", "how has nhis data helped", "how does nhis data help", "data helped", "data help", "helped with", "used to help"])
    participant_query = any(p in qn for p in ["participate", "participation", "participant", "respondent", "selected", "survey legitimate", "what should i expect", "what to expect", "privacy", "confidential", "what is in it for me", "what's in it for me"])
    privacy_query = any(p in qn for p in ["privacy", "private", "secure", "confidential", "data safe", "data breach", "personal information"] )
    expect_query = any(p in qn for p in ["what should i expect", "what to expect", "selected", "interview process", "survey letter"] )
    if impact_query and ("impact" in category or "job aid" in category or "impact" in title or "real-life benefits" in title or "real life benefits" in title):
        intent_boost += 4.0
    if participant_query and ("participant" in category or "participant" in title):
        intent_boost += 2.0
    if privacy_query and ("privacy" in title or "confidential" in title):
        intent_boost += 4.0
    if expect_query and "what to expect" in title:
        intent_boost += 5.0
    if "why participate" in qn and "why participate" in title:
        intent_boost += 5.0
    return (overlap / max(1.0, math.sqrt(len(set(d_tokens))))) + (title_overlap * 0.75) + phrase_boost + url_boost + intent_boost


def search_faq(question: str, max_results: int = 4) -> list[dict]:
    docs = load_faq_index()
    scored = []
    for doc in docs:
        s = _score(question, doc)
        if s > 0:
            scored.append((s, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    seen_urls = set()
    for score, doc in scored:
        # Avoid returning many chunks from the same page unless that page is the only hit.
        key = (doc.get("url") or doc.get("id") or "").strip()
        if key in seen_urls and len(out) >= 2:
            continue
        seen_urls.add(key)
        item = dict(doc)
        item["score"] = round(score, 4)
        item["excerpt"] = _best_excerpt(question, doc.get("text", "") or doc.get("excerpt", ""))
        out.append(item)
        if len(out) >= max_results:
            break
    return out


def _best_excerpt(question: str, text: str, max_chars: int = 520) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= max_chars:
        return text
    q_tokens = set(_tokens(question))
    # Split conservatively into sentence-ish chunks.
    parts = re.split(r"(?<=[.!?])\s+", text)
    best = ""
    best_score = -1
    for i, part in enumerate(parts):
        window = " ".join(parts[i:i+2]).strip()
        score = sum(1 for t in _tokens(window) if t in q_tokens)
        if score > best_score:
            best_score = score
            best = window
    if not best:
        best = text[:max_chars]
    if len(best) > max_chars:
        best = best[:max_chars].rsplit(" ", 1)[0] + "…"
    return best


def answer_faq(question: str, debug: bool = False) -> dict:
    results = search_faq(question)
    if not results or results[0]["score"] < 0.25:
        answer = (
            "I do not have enough information from the approved NHIS FAQ source index to answer that. "
            "Try the official NHIS pages: https://www.cdc.gov/nchs/nhis/index.html and "
            "https://www.cdc.gov/nchs/nhis/documentation/index.html."
        )
        return {
            "status": "not_found", "mode": "faq", "answer": answer,
            "citations": [], "source_cards": [],
            "why": ["No approved NHIS FAQ source in the local index scored high enough for this question."],
            "debug": {"reason": "faq_no_source_match", "results": results}
        }

    top = results[0]
    lines = []
    lines.append(top["excerpt"] or top.get("text", ""))
    lines.append("")
    if top.get('url') and str(top.get('url')).startswith(('http://', 'https://')):
        lines.append(f"Source: {top['title']}. {top['url']}")
    else:
        lines.append(f"Source: {top['title']}.")
    if len(results) > 1:
        lines.append("")
        lines.append("Additional relevant NHIS sources:")
        for r in results[1:3]:
            if r.get('url') and str(r.get('url')).startswith(('http://', 'https://')):
                lines.append(f"- {r['title']}: {r['url']}")
            else:
                lines.append(f"- {r['title']}")
    if debug:
        lines.append("")
        lines.append("FAQ retrieval details:")
        for r in results:
            lines.append(f"- {r['id']} score={r['score']} url={r['url']}")

    citations = [{"title": r["title"], "url": r["url"], "score": r["score"]} for r in results]
    source_cards = [
        {
            "title": r["title"],
            "url": r["url"],
            "excerpt": r.get("excerpt", ""),
            "source_category": r.get("source_category", r.get("source_type", "cdc_nhis_webpage")),
            "score": r["score"],
        }
        for r in results
    ]
    why = [
        "This was routed to the NHIS FAQ/documentation retriever rather than the estimate engine.",
        "The answer was limited to the local approved CDC/NCHS NHIS source index.",
    ]
    return {
        "status": "ok", "mode": "faq", "answer": "\n".join(lines),
        "citations": citations, "source_cards": source_cards, "why": why,
        "debug": {"results": results}
    }
