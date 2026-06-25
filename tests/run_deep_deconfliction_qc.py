from __future__ import annotations
import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ask_router import ask

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "tests" / "deep_deconfliction_qc_report.csv"
MATRIX = ROOT / "tests" / "deep_deconfliction_testing_matrix.csv"

CASES = [
    # lane switching / conversational controller
    {"id":"lane_faq_to_more", "query_seq":["Why should I participate in NHIS?", "tell me more"], "turn":1, "status":"ok", "mode":"faq", "answer_contains":"Source"},
    {"id":"lane_faq_to_teen_est", "query_seq":["Why should I participate in NHIS?", "What percent of teens had asthma last year?"], "turn":1, "mode":"teen_redirect", "answer_contains":"Teen Summary Health Statistics"},
    {"id":"lane_faq_to_adult_est", "query_seq":["Why should I participate in NHIS?", "What percent of adults had diabetes last year?"], "turn":1, "status":"ok", "mode":"estimate", "outcome":"Diagnosed diabetes"},
    {"id":"lane_est_to_faq", "query_seq":["What percent of adults had diabetes last year?", "Why should I participate in NHIS?"], "turn":1, "status":"ok", "mode":"faq"},
    {"id":"lane_est_followup_svi", "query_seq":["What percent of adults had diabetes last year?", "What about by SVI?"], "turn":1, "status":"ok", "mode":"estimate", "label_contains":"Social vulnerability"},
    {"id":"lane_no_context_vague", "query_seq":["tell me more"], "turn":0, "not_mode":"estimate"},

    # insurance topic vs insurance grouping
    {"id":"ins_topic_status_adult", "query":"How many people had insurance by insurance status?", "status":"ok", "mode":"estimate", "answer_contains":"insurance coverage estimates"},
    {"id":"ins_topic_status_under65", "query":"What percent of adults had insurance last year by insurance for people under 65?", "status":"ok", "mode":"estimate", "answer_contains":"insurance coverage estimates"},
    {"id":"ins_private_under65", "query":"What percent of adults under 65 had private insurance last year?", "status":"ok", "mode":"estimate", "answer_contains":"18-34 years"},
    {"id":"ins_private_over65", "query":"What percent of adults 65 and older had private insurance last year?", "status":"ok", "mode":"estimate", "answer_contains":"***"},
    {"id":"ins_uninsured_under65", "query":"What percent of adults under 65 were uninsured last year?", "status":"ok", "mode":"estimate", "answer_contains":"18-34 years"},
    {"id":"ins_public_over65", "query":"What percent of adults 65 and over had public coverage last year?", "status":"ok", "mode":"estimate", "answer_contains":"***"},
    {"id":"ins_child_status", "query":"What percent of children had insurance by insurance status last year?", "status":"ok", "mode":"estimate", "answer_contains":"Uninsured at time of interview"},
    {"id":"ins_child_uninsured", "query":"How many kids were uninsured last year?", "status":"ok", "mode":"estimate", "answer_contains":"Uninsured at time of interview"},
    {"id":"ins_covariate_adult_asthma", "query":"What percent of adults had asthma by insurance status last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma", "label_contains":"Health insurance coverage"},
    {"id":"ins_covariate_child_flu_uninsured", "query":"What percent of uninsured kids got a flu shot last year?", "status":"ok", "mode":"estimate", "outcome":"Receipt of influenza vaccination", "label_contains":"Health insurance coverage", "group":"Uninsured"},
    {"id":"ins_covariate_child_flu_private", "query":"What percent of children with private insurance got a flu shot last year?", "status":"ok", "mode":"estimate", "outcome":"Receipt of influenza vaccination", "label_contains":"Health insurance coverage", "group":"Private"},

    # income/poverty/FPL equivalence
    {"id":"income_by_income", "query":"What percent of adults had diabetes by income last year?", "status":"ok", "mode":"estimate", "outcome":"Diagnosed diabetes", "label":"Family income"},
    {"id":"income_by_household_income", "query":"What percent of adults had diabetes by household income last year?", "status":"ok", "mode":"estimate", "outcome":"Diagnosed diabetes", "label":"Family income"},
    {"id":"income_by_poverty", "query":"What percent of adults had diabetes by poverty status last year?", "status":"ok", "mode":"estimate", "outcome":"Diagnosed diabetes", "label":"Family income"},
    {"id":"income_by_fpl", "query":"What percent of adults had diabetes by FPL last year?", "status":"ok", "mode":"estimate", "outcome":"Diagnosed diabetes", "label":"Family income"},
    {"id":"income_below_poverty", "query":"What percent of adults below poverty had diabetes last year?", "status":"ok", "mode":"estimate", "outcome":"Diagnosed diabetes", "label":"Family income", "group":"Less than 100% FPL"},

    # topic deconfliction
    {"id":"asthma_generic_adult", "query":"What percent of adults had asthma last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma"},
    {"id":"asthma_current_adult", "query":"What percent of adults had current asthma last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma"},
    {"id":"asthma_attack_adult", "query":"What percent of adults had an asthma attack last year?", "status":"ok", "mode":"estimate", "outcome":"Asthma episode/attack"},
    {"id":"asthma_ever_child", "query":"What percent of children ever had asthma last year?", "status":"ok", "mode":"estimate", "outcome":"Ever having asthma"},
    {"id":"asthma_current_child", "query":"What percent of children had current asthma last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma"},
    {"id":"mh_cost", "query":"What percent of adults needed mental health care but did not get it due to cost last year?", "status":"ok", "mode":"estimate", "outcome":"Did not get needed mental health care due to cost"},
    {"id":"cost_medical", "query":"What percent of adults could not afford care last year?", "status":"ok", "mode":"estimate", "outcome":"Did not get needed medical care due to cost"},
    {"id":"cost_skipped_meds", "query":"What percent of adults skipped medication to save money last year?", "status":"ok", "mode":"estimate", "outcome":"Did not take medication as prescribed to save money"},
    {"id":"anxiety_feelings", "query":"What percent of adults had anxiety last year?", "status":"ok", "mode":"estimate", "outcome":"Regularly had feelings of worry, nervousness, or anxiety"},
    {"id":"anxiety_medication", "query":"What percent of adults took medication for anxiety last year?", "status":"ok", "mode":"estimate", "outcome":"Taking prescription medication for feelings of worry, nervousness, or anxiety"},
    {"id":"depression_feelings", "query":"What percent of adults had depression last year?", "status":"ok", "mode":"estimate", "outcome":"Regularly had feelings of depression"},
    {"id":"depression_medication", "query":"What percent of adults took medication for depression last year?", "status":"ok", "mode":"estimate", "outcome":"Taking prescription medication for feelings of depression"},

    # grouping/subgroup overlaps
    {"id":"sex_women", "query":"What percent of women had current asthma last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma", "label":"Sex", "group":"Female"},
    {"id":"race_ethnicity", "query":"What percent of adults had current asthma by race and ethnicity last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma", "label":"Hispanic or Latino origin and race"},
    {"id":"hispanic_subgroup", "query":"What percent of Hispanic adults had current asthma last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma", "label":"Hispanic or Latino origin and race", "group":"Hispanic"},
    {"id":"gay_men_current_asthma", "query":"What percent of gay men had current asthma last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma", "label":"Sexual orientation", "group":"Gay or Lesbian", "answer_contains":"multi-group crosstab"},
    {"id":"men_by_sexual_orientation_warning", "query":"What percent of men had current asthma by sexual orientation last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma", "label":"Sexual orientation", "answer_contains":"exact crosstab"},
    {"id":"svi_group", "query":"What percent of adults had current asthma by SVI last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma", "label_contains":"Social vulnerability"},
    {"id":"high_svi_subgroup", "query":"What percent of high SVI adults had current asthma last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma", "label_contains":"Social vulnerability", "group":"High social vulnerability"},

    # child topic vs grouping overlaps
    {"id":"child_learning_disability", "query":"What percent of children had a learning disability last year?", "status":"ok", "mode":"estimate", "outcome":"Ever having a learning disability"},
    {"id":"child_special_education", "query":"What percent of children got special education last year?", "status":"ok", "mode":"estimate", "outcome":"Receiving special education or early intervention services"},
    {"id":"child_missed_school", "query":"What percent of kids missed school last year?", "status":"ok", "mode":"estimate", "outcome":"Missing 11 or more school days due to illness or injury"},
    {"id":"child_adhd", "query":"What percent of kids had ADHD last year?", "status":"ok", "mode":"estimate", "outcome":"Ever having attention-deficit/hyperactivity disorder"},
    {"id":"child_disability", "query":"What percent of children had a disability last year?", "status":"ok", "mode":"estimate", "outcome":"Disability status (composite)"},
    {"id":"child_difficulty", "query":"What percent of children had difficulty last year?", "status":"ok", "mode":"estimate", "outcome":"Difficulty status (composite)"},
    {"id":"disabled_child_asthma", "query":"What percent of disabled children had asthma last year?", "status":"ok", "mode":"estimate", "outcome":"Current asthma", "label":"Disability Status", "group":"With disability"},

    # access/urgent/retail overlaps
    {"id":"adult_urgent_or_retail", "query":"What percent of adults had urgent care or retail clinic visit last year?", "status":"ok", "mode":"estimate", "outcome":"Urgent care center or retail health clinic visit"},
    {"id":"adult_urgent", "query":"What percent of adults went to urgent care last year?", "status":"ok", "mode":"estimate", "outcome":"Urgent care center visit"},
    {"id":"adult_retail", "query":"What percent of adults went to a retail clinic last year?", "status":"ok", "mode":"estimate", "outcome":"Retail health clinic visit"},
    {"id":"child_urgent_or_retail", "query":"What percent of children went to urgent care or retail clinic last year?", "status":"ok", "mode":"estimate", "outcome":"Two or more urgent care center or retail health clinic visits"},
    {"id":"child_urgent", "query":"What percent of children went to urgent care last year?", "status":"ok", "mode":"estimate", "outcome":"Two or more urgent care center visits"},
    {"id":"child_retail", "query":"What percent of children went to a retail clinic last year?", "status":"ok", "mode":"estimate", "outcome":"Two or more retail health clinic visits"},

    # FAQ/resource lane
    {"id":"faq_participate", "query":"Why should I participate in NHIS?", "status":"ok", "mode":"faq"},
    {"id":"faq_privacy", "query":"Is my information private?", "status":"ok", "mode":"faq"},
    {"id":"faq_impact_diabetes", "query":"How has NHIS helped with diabetes?", "status":"ok", "mode":"faq"},
    {"id":"faq_benefits", "query":"What are real life benefits of NHIS?", "status":"ok", "mode":"faq"},
    {"id":"teen_participate", "query":"Why should teens participate?", "status":"ok", "mode":"faq"},
    {"id":"teen_estimate_redirect", "query":"What percent of teens had asthma last year?", "mode":"teen_redirect"},
]


def run_case(case: dict) -> tuple[bool, dict]:
    cid = "deep_" + case["id"]
    seq = case.get("query_seq") or [case["query"]]
    results = []
    for idx, q in enumerate(seq):
        results.append(ask(q, conversation_id=cid, debug=True, use_model=False, reset_context=(idx == 0)))
    r = results[case.get("turn", len(results)-1)]
    dbg = r.get("debug") or {}
    ans = r.get("answer") or ""
    ok = True
    checks = []
    def check(label, cond, actual=""):
        nonlocal ok
        checks.append(f"{label}={actual}")
        if not cond:
            ok = False
    if "status" in case:
        check("status", r.get("status") == case["status"], r.get("status"))
    if "mode" in case:
        check("mode", r.get("mode") == case["mode"], r.get("mode"))
    if "not_mode" in case:
        check("not_mode", r.get("mode") != case["not_mode"], r.get("mode"))
    if "outcome" in case:
        check("outcome", dbg.get("outcome") == case["outcome"], dbg.get("outcome"))
    if "label" in case:
        check("label", dbg.get("label") == case["label"], dbg.get("label"))
    if "label_contains" in case:
        check("label_contains", case["label_contains"].lower() in str(dbg.get("label", "")).lower(), dbg.get("label"))
    if "group" in case:
        check("group", dbg.get("group") == case["group"], dbg.get("group"))
    if "answer_contains" in case:
        check("answer_contains", case["answer_contains"].lower() in ans.lower(), ans[:120].replace("\n", " | "))
    return ok, {
        "id": case["id"],
        "query": " || ".join(seq),
        "passed": ok,
        "status": r.get("status"),
        "mode": r.get("mode"),
        "outcome": dbg.get("outcome"),
        "label": dbg.get("label"),
        "group": dbg.get("group"),
        "reason": dbg.get("reason"),
        "checks": "; ".join(checks),
        "answer_preview": ans[:250].replace("\n", " | "),
    }


def main() -> None:
    rows=[]
    failures=[]
    for case in CASES:
        ok,row = run_case(case)
        rows.append(row)
        print(("PASS" if ok else "FAIL") + ": " + case["id"])
        if not ok:
            failures.append(row)
    REPORT.parent.mkdir(exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8") as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    with MATRIX.open("w", newline="", encoding="utf-8") as f:
        fieldnames=["id","query_or_sequence","expected_status","expected_mode","expected_outcome","expected_label","expected_group","answer_contains"]
        writer=csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in CASES:
            writer.writerow({
                "id": c["id"],
                "query_or_sequence": " || ".join(c.get("query_seq") or [c.get("query","")]),
                "expected_status": c.get("status",""),
                "expected_mode": c.get("mode",""),
                "expected_outcome": c.get("outcome",""),
                "expected_label": c.get("label") or c.get("label_contains", ""),
                "expected_group": c.get("group", ""),
                "answer_contains": c.get("answer_contains", ""),
            })
    total=len(CASES); passed=total-len(failures)
    print(f"\nDeep deconfliction QC: {passed} / {total} passed")
    print(f"Report: {REPORT}")
    print(f"Testing matrix: {MATRIX}")
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
