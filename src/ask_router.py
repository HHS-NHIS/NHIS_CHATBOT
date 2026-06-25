from __future__ import annotations
from normalize_text import normalize_text
from retrieve_estimate import retrieve
from faq_retriever import answer_faq, looks_like_faq_question
from model_orchestrator import polish_answer, compose_resource_answer
from conversation_state import new_conversation_id, get_context, clear_context, update_from_result, summarize_context
from followup_resolver import looks_like_followup, build_resolved_question, suggested_followups
from insurance_special import looks_like_insurance_topic_status_question, insurance_topic_status_response

ESTIMATE_TERMS = [
    "percent", "percentage", "estimate", "how many", "how much", "rate", "prevalence", "ci",
    "confidence interval", "standard error", "se", "by ", "last year", "latest", "last 2 years"
]

COMMON_ESTIMATE_TOPICS = [
    "asthma", "diabetes", "hypertension", "flu shot", "flu vaccine", "influenza", "uninsured",
    "obesity", "smoking", "vaping", "adhd", "depression", "anxiety", "cholesterol", "insurance"
]

TEEN_REDIRECT_URL = "https://wwwn.cdc.gov/NHISDataQueryTool/NHIS_teen/index.html"
TEEN_TERMS = ["teen", "teens", "teenager", "teenagers", "nhis teen", "nhis-teen", "teen shs", "teen summary"]


def looks_like_teen_question(question: str) -> bool:
    q = normalize_text(question)
    return any(term in q for term in TEEN_TERMS)


def teen_redirect_response(question: str) -> dict:
    answer = (
        "Teen estimates are not included in this adult/child NHIS Summary Health Statistics prototype yet. "
        "For teen-specific estimates, use the NHIS Teen Summary Health Statistics tool: "
        f"{TEEN_REDIRECT_URL}"
    )
    return {
        "status": "not_found",
        "mode": "teen_redirect",
        "question": question,
        "answer": answer,
        "citations": [TEEN_REDIRECT_URL],
        "source_cards": [{
            "title": "NHIS Teen Summary Health Statistics tool",
            "url": TEEN_REDIRECT_URL,
            "source_type": "teen_shs_redirect",
            "excerpt": "Use this teen-specific NHIS Data Query Tool for teen Summary Health Statistics estimates."
        }],
        "why": [
            "This question explicitly mentioned teens/teenagers or the NHIS Teen tool. Teen estimates are intentionally routed to the NHIS Teen Summary Health Statistics tool instead of the adult/child SHS prototype."
        ],
        "debug": {"reason": "teen_exception_redirect", "teen_terms": TEEN_TERMS, "redirect_url": TEEN_REDIRECT_URL}
    }

PARTICIPATION_OR_IMPACT_FAQ_TERMS = [
    "why should i participate", "why participate", "what is in it for me", "what's in it for me",
    "benefit from participating", "directly benefit", "selected for nhis", "why was i selected",
    "what should i expect", "what to expect", "survey legitimate", "is this legitimate",
    "is my information private", "is my information secure", "privacy", "confidentiality",
    "how does nhis data help", "how has nhis data helped", "real life benefits", "real-life benefits",
    "nhis impact", "talking points", "how data helped", "helped with diabetes", "helped with asthma",
    "helped with cancer", "helped with insulin", "helped with hearing aids"
]


def looks_like_participation_or_impact_faq(question: str) -> bool:
    q = normalize_text(question)
    if any(term in q for term in PARTICIPATION_OR_IMPACT_FAQ_TERMS):
        return True
    participant_words = [
        "participate", "participating", "participation", "selected", "respondent",
        "interview", "legitimate", "privacy", "private", "confidential", "secure",
        "what to expect", "expect", "benefit", "benefits", "help real people",
        "why should", "why do", "why would", "what is in it", "what's in it"
    ]
    resource_words = ["impact", "real life benefit", "real-life benefit", "talking point", "helped with", "data helped", "value", "values", "belief", "benefit"]
    has_participation_intent = any(w in q for w in participant_words)
    has_resource_intent = any(w in q for w in resource_words)
    if has_participation_intent or has_resource_intent:
        if not any(t in q for t in ["percent", "percentage", "prevalence", "estimate", "rate", "how many"]):
            return True
        if any(t in q for t in ["particip", "selected", "privacy", "confidential", "legitimate", "what to expect", "benefit", "impact", "talking point"]):
            return True
    return False


def looks_like_estimate_question(question: str) -> bool:
    q = normalize_text(question)
    if any(t in q for t in ESTIMATE_TERMS):
        return True
    if any(t in q for t in COMMON_ESTIMATE_TOPICS):
        return True
    return False


def _is_vague_only(question: str) -> bool:
    q = normalize_text(question).strip(" ?!.:")
    exact_vague = {
        "tell me more", "more", "more information", "more info", "more detail",
        "explain more", "expand", "can you expand", "what else", "say more",
        "go on", "continue", "why", "how so"
    }
    prefix_vague = ["tell me more", "more detail", "more information", "explain more", "can you expand", "say more"]
    return q in exact_vague or any(q.startswith(v + " ") for v in prefix_vague)


def _looks_like_contextual_modifier(question: str) -> bool:
    q = normalize_text(question).strip()
    starters = ["what about", "how about", "and", "now", "instead"]
    if any(q.startswith(s) for s in starters):
        return True
    if q.startswith("by ") or q.startswith("show by ") or q.startswith("show me by "):
        return True
    # "Show last 2 years" and similar are follow-up modifiers unless a new topic is named.
    if q.startswith("show") and any(p in q for p in ["last 2 years", "last two years", "all years", "latest", "last year", "by "]):
        if not any(t in q for t in COMMON_ESTIMATE_TOPICS):
            return True
    return False


def _strong_new_lane(question: str) -> str | None:
    """Return a lane when a new question should override prior context.

    Vague prompts and pure modifiers inherit context. Explicit new estimate/FAQ/teen
    signals switch lanes even if they occur after a different prior answer type.
    """
    if _is_vague_only(question) or _looks_like_contextual_modifier(question):
        return None
    q = normalize_text(question)
    # Teen participation/resource questions should go to FAQ/resource, not teen estimate redirect.
    if looks_like_participation_or_impact_faq(question):
        return "faq"
    if looks_like_teen_question(question):
        return "teen"
    if looks_like_insurance_topic_status_question(question):
        return "estimate"
    if looks_like_estimate_question(question):
        return "estimate"
    if looks_like_faq_question(question) or "nhis" in q:
        return "faq"
    return None


def _merge_common_payload(result: dict, question: str, mode: str) -> dict:
    result.setdefault("question", question)
    result.setdefault("mode", mode)
    result.setdefault("citations", [])
    result.setdefault("source_cards", [])
    result.setdefault("why", [])
    return result


def _attach_interactive_payload(result: dict, conversation_id: str, original_question: str, resolved_question: str, context_meta: dict, context: dict | None) -> dict:
    result["conversation_id"] = conversation_id
    result["original_question"] = original_question
    result["resolved_question"] = resolved_question
    result["context_resolution"] = context_meta or {"used_followup_context": False}
    result["conversation_context"] = summarize_context(context)
    result["suggested_followups"] = suggested_followups(context, result)
    return result


def _store_and_attach(cid: str, original: str, resolved: str, result: dict, context_meta: dict) -> dict:
    new_context = update_from_result(cid, original, resolved, result)
    return _attach_interactive_payload(result, cid, original, resolved, context_meta, new_context)


def _faq_answer(q: str, q_original: str, cid: str, context_meta: dict, debug: bool, use_model: bool, mode: str = "faq", prior_context: dict | None = None) -> dict:
    faq = answer_faq(q, debug=debug, conversation_context=prior_context or {})
    if faq.get("status") == "ok":
        # FAQ/resource answers are allowed to be conversationally composed from approved retrieved evidence.
        # Estimates still use the stricter polish_answer path below.
        polished, model_meta = compose_resource_answer(q, faq["answer"], evidence=faq, conversation_context=prior_context or {}, use_model=use_model)
        faq["answer"] = polished
        faq["model"] = model_meta
    faq = _merge_common_payload(faq, q_original, mode)
    return _store_and_attach(cid, q_original, q, faq, context_meta)


def ask(
    question: str,
    debug: bool = False,
    use_model: bool = False,
    conversation_id: str | None = None,
    reset_context: bool = False,
) -> dict:
    q_original = question.strip()
    if not q_original:
        cid = conversation_id or new_conversation_id()
        return {"status": "error", "mode": "none", "answer": "Please enter a question.", "question": question, "conversation_id": cid}

    cid = conversation_id or new_conversation_id()
    if reset_context:
        clear_context(cid)

    prior_context = get_context(cid)
    resolved_question = q_original
    context_meta = {"used_followup_context": False}

    # V2C conversation controller: explicit new lane signals override prior context;
    # vague prompts inherit the previous lane.
    strong_lane = _strong_new_lane(q_original)
    if strong_lane is None and looks_like_followup(q_original, prior_context):
        resolved_question, context_meta, direct_response = build_resolved_question(q_original, prior_context or {}, use_model=use_model)
        if direct_response is not None:
            direct_response = _merge_common_payload(direct_response, q_original, direct_response.get("mode", "followup"))
            return _store_and_attach(cid, q_original, resolved_question, direct_response, context_meta)

    q = resolved_question

    # Participant/impact questions use approved FAQ/resource index before estimate engine.
    if looks_like_participation_or_impact_faq(q):
        return _faq_answer(q, q_original, cid, context_meta, debug, use_model, mode="faq", prior_context=prior_context)

    # Insurance as both topic and status/breakout gets an explicit deconfliction path.
    if looks_like_insurance_topic_status_question(q):
        result = insurance_topic_status_response(q)
        if result.get("status") == "ok":
            polished, model_meta = polish_answer(q, result["answer"], evidence=result, use_model=use_model)
            result["answer"] = polished
            result["model"] = model_meta
        result = _merge_common_payload(result, q_original, result.get("mode", "estimate"))
        return _store_and_attach(cid, q_original, q, result, context_meta)

    # Teen estimates intentionally remain outside adult/child SHS prototype for now.
    if looks_like_teen_question(q):
        result = teen_redirect_response(q)
        if use_model:
            polished, model_meta = polish_answer(q, result["answer"], evidence=result, use_model=use_model)
            result["answer"] = polished
            result["model"] = model_meta
        result = _merge_common_payload(result, q_original, "teen_redirect")
        return _store_and_attach(cid, q_original, q, result, context_meta)

    # Estimate-like questions go to deterministic DHIS engine first.
    if looks_like_estimate_question(q):
        est = retrieve(q, debug=debug)
        if est.get("status") == "ok":
            est["mode"] = "estimate"
            est.setdefault("why", [])
            if context_meta.get("used_followup_context"):
                est["why"].insert(0, "This was interpreted as a follow-up and resolved using the previous successful context.")
            est["why"].insert(0, "This was routed to the deterministic DHIS NHIS Adult/Child Summary Health Statistics estimate engine.")
            polished, model_meta = polish_answer(q, est["answer"], evidence=est, use_model=use_model)
            est["answer"] = polished
            est["model"] = model_meta
            est = _merge_common_payload(est, q_original, "estimate")
            return _store_and_attach(cid, q_original, q, est, context_meta)

        # If clearly documentation/FAQ, try FAQ after estimate miss.
        if looks_like_faq_question(q):
            return _faq_answer(q, q_original, cid, context_meta, debug, use_model, mode="faq", prior_context=prior_context)
        est["mode"] = "estimate_not_found"
        est.setdefault("why", [])
        est["why"].insert(0, "This looked like an estimate request, but no matching row was found in the current DHIS adult/child SHS files.")
        est = _merge_common_payload(est, q_original, "estimate_not_found")
        return _attach_interactive_payload(est, cid, q_original, q, context_meta, get_context(cid))

    # Route general NHIS questions to FAQ retrieval.
    if looks_like_faq_question(q) or "nhis" in normalize_text(q):
        return _faq_answer(q, q_original, cid, context_meta, debug, use_model, mode="faq", prior_context=prior_context)

    # Safe default: FAQ first. Avoid treating very vague text as SHS estimate unless there is a stronger signal.
    faq = answer_faq(q, debug=debug)
    if faq.get("status") == "ok":
        polished, model_meta = compose_resource_answer(q, faq["answer"], evidence=faq, conversation_context=prior_context or {}, use_model=use_model)
        faq["answer"] = polished
        faq["model"] = model_meta
        faq = _merge_common_payload(faq, q_original, "faq")
        return _store_and_attach(cid, q_original, q, faq, context_meta)

    est = retrieve(q, debug=debug)
    est["mode"] = "estimate_fallback_attempt"
    est.setdefault("why", []).insert(0, "No strong FAQ match was found, so the estimate engine was tried as a fallback.")
    est = _merge_common_payload(est, q_original, "estimate_fallback_attempt")
    if est.get("status") == "ok":
        return _store_and_attach(cid, q_original, q, est, context_meta)
    return _attach_interactive_payload(est, cid, q_original, q, context_meta, get_context(cid))
