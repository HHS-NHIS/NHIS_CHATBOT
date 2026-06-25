from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ask_router import ask

failures=[]

def check(cond, label, detail=""):
    if not cond:
        failures.append((label, detail))
        print(f"FAIL: {label} {detail}")
    else:
        print(f"PASS: {label}")

def run_seq(label, queries):
    cid="qc_"+label
    out=[]
    for q in queries:
        r=ask(q, conversation_id=cid, debug=True, use_model=False)
        out.append(r)
    return out

# FAQ repeated should vary deterministically even without OpenAI.
r=run_seq("faq_repeat", ["Why should I participate in NHIS?", "Why should I participate in NHIS?"])
check(r[0].get('mode')=='faq' and r[0].get('status')=='ok', 'faq_repeat_turn1_ok')
check(r[1].get('mode')=='faq' and 'Building on that' in r[1].get('answer',''), 'faq_repeat_turn2_varied')

# Vague follow-up after resource stays resource.
r=run_seq("faq_more", ["Why should I participate in NHIS?", "tell me more"])
check(r[1].get('mode')=='faq' and r[1].get('status')=='ok', 'tell_me_more_after_faq_stays_faq')
check('SHS' not in r[1].get('answer','')[:250] or 'resource index' in r[1].get('answer',''), 'tell_me_more_not_shs_fallback')

# Lane switches.
r=run_seq("lane_switch_teen", ["Why should I participate in NHIS?", "What percent of teens had asthma last year?"])
check(r[1].get('mode')=='teen_redirect', 'faq_to_teen_estimate_switch')
r=run_seq("lane_switch_estimate", ["Why should I participate in NHIS?", "What percent of adults had diabetes last year?"])
check(r[1].get('mode')=='estimate' and r[1].get('status')=='ok', 'faq_to_adult_estimate_switch')
r=run_seq("lane_switch_faq", ["What percent of adults had diabetes last year?", "Why should I participate in NHIS?"])
check(r[1].get('mode')=='faq' and r[1].get('status')=='ok', 'estimate_to_faq_switch')

# Estimate follow-ups.
r=run_seq("estimate_follow", ["What percent of adults had diabetes last year?", "What about by SVI?", "Show last 2 years."])
check(r[0].get('mode')=='estimate' and r[0].get('status')=='ok', 'diabetes_estimate_ok')
check(r[1].get('mode')=='estimate' and r[1].get('status')=='ok' and 'Social vulnerability' in r[1].get('answer',''), 'diabetes_by_svi_followup_ok')
check(r[2].get('mode')=='estimate' and r[2].get('status')=='ok', 'show_last_2_years_followup_ok')

# Teen participation vs teen estimate.
r=run_seq("teen_part", ["Why should teens participate?", "tell me more"])
check(r[0].get('mode')=='faq' and r[0].get('status')=='ok', 'teen_participation_routes_faq')
check(r[1].get('mode')=='faq' and r[1].get('status')=='ok', 'teen_participation_tell_more_routes_faq')
r=run_seq("teen_est", ["What percent of teens had asthma last year?"])
check(r[0].get('mode')=='teen_redirect', 'teen_estimate_redirect')

# Insurance deconfliction.
r=run_seq("ins_adult", ["How many people had insurance by insurance status?"])
check(r[0].get('mode')=='estimate' and r[0].get('status')=='ok' and 'insurance coverage estimates' in r[0].get('answer','').lower(), 'insurance_topic_status_adult_special')
r=run_seq("ins_child", ["What percent of children had insurance by insurance status?"])
check(r[0].get('mode')=='estimate' and r[0].get('status')=='ok' and 'insurance coverage estimates' in r[0].get('answer','').lower(), 'insurance_topic_status_child_special')
r=run_seq("ins_cov", ["What percent of adults had asthma by insurance status?"])
check(r[0].get('mode')=='estimate' and r[0].get('status')=='ok' and 'Current asthma' in r[0].get('answer',''), 'insurance_covariate_still_works')

# Existing overlap examples.
r=run_seq("overlap", ["Uninsured kids got a flu shot last year", "Kids were uninsured last year"])
check(r[0].get('mode')=='estimate' and 'influenza' in r[0].get('answer','').lower(), 'uninsured_kids_flu_shot_topic_deconflict')
check(r[1].get('mode')=='estimate' and 'Uninsured at time of interview' in r[1].get('answer',''), 'kids_uninsured_topic_deconflict')

# No-context vague prompt should not produce an SHS false estimate.
r=run_seq("no_context", ["tell me more"])
check(r[0].get('status') in {'not_found','error'} or r[0].get('mode') != 'estimate', 'no_context_tell_me_more_safe')

TOTAL_CHECKS = 19
print(f"\nV2C conversational orchestrator QC: {TOTAL_CHECKS-len(failures)} / {TOTAL_CHECKS} passed")
if failures:
    raise SystemExit(1)
