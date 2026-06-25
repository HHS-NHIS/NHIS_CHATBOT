from __future__ import annotations
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ask_router import ask  # noqa: E402

CASES = []
def add(id, question, status="ok", outcome=None, label=None, group=None, answer_contains=None):
    CASES.append({
        "id": id,
        "question": question,
        "status": status,
        "outcome": outcome,
        "label": label,
        "group": group,
        "answer_contains": answer_contains,
    })

# Insurance topic/covariate collisions
add('ins_topic_all','How many people had insurance by insurance status?', outcome='Uninsured at time of interview')
add('ins_topic_under65','What percent of adults had insurance last year by insurance for people under 65?', outcome='Uninsured at time of interview', answer_contains='18-34')
add('ins_private_under65','What percent of adults under 65 had private insurance last year?', outcome='Private health insurance coverage at time of interview')
add('ins_public_over65','What percent of adults 65 and older had public coverage last year?', outcome='Public health plan coverage at time of interview')
add('ins_medicare','What percent of adults 65 and over had Medicare Advantage last year?', outcome='Public health plan coverage at time of interview')
add('ins_cov_asthma','What percent of adults had asthma by insurance status last year?', outcome='Current asthma', label='Health insurance coverage')
add('ins_cov_diabetes_private','What percent of adults with private insurance had diabetes last year?', outcome='Diagnosed diabetes', group='Private')
add('ins_cov_child_flu_uninsured','What percent of uninsured kids got a flu shot last year?', outcome='Receipt of influenza vaccination', group='Uninsured')
add('ins_child_uninsured_topic','What percent of kids were uninsured last year?', outcome='Uninsured at time of interview')

# Income/poverty/FPL equivalence
for term in ['income','household income','family income','poverty','poverty status','FPL','federal poverty level']:
    add(f'income_{term}','What percent of adults got a flu shot last year by '+term, outcome='Receipt of influenza vaccination', label='Family income')
add('income_sub_below','What percent of adults below poverty had diabetes last year?', outcome='Diagnosed diabetes', label='Family income', group='Less than 100% FPL')

# Asthma topic collisions
add('asthma_generic_adult','asthma last year', outcome='Current asthma')
add('asthma_attack_adult','asthma attack last year', outcome='Asthma episode/attack')
add('asthma_ever_child','What percent of children ever had asthma last year?', outcome='Ever having asthma')
add('asthma_current_child','What percent of kids currently have asthma last year?', outcome='Current asthma')

# Mental health and cost collisions
add('anx_feelings','What percent of adults had feelings of anxiety last year?', outcome='Regularly had feelings of worry, nervousness, or anxiety')
add('anx_med','What percent of adults took medication for anxiety last year?', outcome='Taking prescription medication for feelings of worry, nervousness, or anxiety')
add('dep_feelings','What percent of adults had feelings of depression last year?', outcome='Regularly had feelings of depression')
add('dep_med','What percent of adults took medication for depression last year?', outcome='Taking prescription medication for feelings of depression')
add('mh_cost','What percent of adults needed mental health care but did not get it due to cost last year?', outcome='Did not get needed mental health care due to cost')
add('mh_services_child','What percent of children received mental health services last year?', outcome='Receive services for mental health problems')
add('cost_delay','What percent of adults delayed medical care due to cost last year?', outcome='Delayed getting medical care due to cost')
add('cost_need','What percent of adults did not get needed medical care due to cost last year?', outcome='Did not get needed medical care due to cost')
add('cost_meds','What percent of adults skipped medication to save money last year?', outcome='Did not take medication as prescribed to save money')

# Difficulty/disability topic-vs-subgroup collisions
add('difficulty_child','What percent of children had difficulty last year?', outcome='Difficulty status (composite)')
add('disability_child','What percent of children had disability last year?', outcome='Disability status (composite)')
add('difficulty_adult_seeing','What percent of adults had difficulty seeing last year?', outcome='Difficulty seeing')
add('difficulty_adult_composite','What percent of adults had functioning difficulty last year?', outcome='Difficulty status (composite)')
add('disabled_flu','What percent of adults with disability got a flu shot last year?', outcome='Receipt of influenza vaccination', label='Disability status', group='With disability')
add('difficulty_asthma','What percent of children with functioning difficulty had asthma last year?', outcome='Current asthma', label='Difficulty Status', group='With functioning difficulty')

# Sex and sexual orientation collisions
add('women_asthma','What percent of women had current asthma last year?', outcome='Current asthma', label='Sex', group='Female')
add('gay_asthma','What percent of gay adults had current asthma last year?', outcome='Current asthma', label='Sexual orientation', group='Gay or Lesbian')
add('gay_men_asthma','What percent of gay men had current asthma last year?', outcome='Current asthma', label='Sexual orientation', group='Gay or Lesbian', answer_contains='crosstab')
add('by_so','What percent of men had current asthma by sexual orientation last year?', outcome='Current asthma', label='Sexual orientation', answer_contains='crosstab')

# Race/ethnicity collisions
add('race_asthma','What percent of adults had asthma by race last year?', outcome='Current asthma', label='Race')
add('hisp_asthma','What percent of Hispanic adults had asthma last year?', outcome='Current asthma', label='Hispanic or Latino origin and race', group='Hispanic')
add('mexican_asthma','What percent of Mexican American adults had asthma last year?', outcome='Current asthma', group='Mexican or Mexican American')

# Geography grouping collisions
add('region_flu','What percent of adults got a flu shot by region last year?', outcome='Receipt of influenza vaccination', label='Region')
add('urbanicity_flu','What percent of adults got a flu shot by urbanicity last year?', outcome='Receipt of influenza vaccination', label='Urbanicity')
add('msa_flu','What percent of adults got a flu shot by MSA last year?', outcome='Receipt of influenza vaccination', label='Metropolitan statistical area status')

# Nativity/veteran/employment/work collisions
add('foreign_diabetes','What percent of foreign-born adults had diabetes last year?', outcome='Diagnosed diabetes', label='Nativity', group='Foreign-born')
add('veteran_diabetes','What percent of veterans had diabetes last year?', outcome='Diagnosed diabetes', label='Veteran Status', group='Veteran')
add('employed_flu','What percent of employed adults got a flu shot last year?', outcome='Receipt of influenza vaccination', label='Employment status', group='Employed')
add('missed_work','What percent of adults missed six or more workdays last year?', outcome='Six or more workdays missed due to illness, injury, or disability')

# Education/family/marital collisions
add('edu_adult_flu','What percent of adults got a flu shot by education last year?', outcome='Receipt of influenza vaccination', label='Education')
add('parent_edu_child_flu','What percent of kids got a flu shot by parental education last year?', outcome='Receipt of influenza vaccination', label='Parental Education')
add('special_ed_child','What percent of children received special education last year?', outcome='Receiving special education or early intervention services')
add('family_struct_flu','What percent of kids got a flu shot by family structure last year?', outcome='Receipt of influenza vaccination', label='Family structure')
add('single_parent_flu','What percent of kids in single parent families got a flu shot last year?', outcome='Receipt of influenza vaccination', label='Family structure')
add('married_adult_flu','What percent of married adults got a flu shot last year?', outcome='Receipt of influenza vaccination', label='Marital status', group='Married')

# Care setting/place wording collisions
add('usual_care','What percent of adults had a usual place of care last year?', outcome='Has a usual place of care')
add('doctor_visit','What percent of adults had a doctor visit last year?', outcome='Doctor visit')
add('urgent_or_retail','What percent of adults used urgent care or retail clinic last year?', outcome='Urgent care center or retail health clinic visit')
add('urgent_only','What percent of adults used urgent care last year?', outcome='Urgent care center visit')
add('retail_only','What percent of adults used retail clinic last year?', outcome='Retail health clinic visit')

# Topic-topic collisions
add('skin_cancer','What percent of adults had skin cancer last year?', outcome='Any skin cancer')
add('any_cancer','What percent of adults had any cancer last year?', outcome='Any type of cancer')
add('breast_cancer','What percent of adults had breast cancer last year?', outcome='Breast cancer')
add('cervical_cancer','What percent of adults had cervical cancer last year?', outcome='Cervical cancer')
add('smoking','What percent of adults smoked cigarettes last year?', outcome='Current cigarette smoking')
add('vaping','What percent of adults used e-cigarettes last year?', outcome='Current electronic cigarette use')
add('pneumococcal','What percent of adults received pneumococcal vaccination last year?', outcome='Ever received a pneumococcal vaccination')


def check_case(c):
    result = ask(c['question'], debug=True, use_model=False, conversation_id='expanded_'+c['id'], reset_context=True)
    debug = result.get('debug') or {}
    answer = str(result.get('answer',''))
    ok = True
    notes = []
    if result.get('status') != c['status']:
        ok = False; notes.append(f"status {result.get('status')} != {c['status']}")
    if c.get('outcome') and c['outcome'] != debug.get('outcome') and c['outcome'] not in answer:
        ok = False; notes.append(f"outcome got {debug.get('outcome')}")
    if c.get('label'):
        label = debug.get('label') or ''
        if c['label'] not in label and c['label'] not in answer:
            ok = False; notes.append(f"label got {label}")
    if c.get('group'):
        group = debug.get('group') or ''
        if c['group'] not in group and c['group'] not in answer:
            ok = False; notes.append(f"group got {group}")
    if c.get('answer_contains') and c['answer_contains'].lower() not in answer.lower():
        ok = False; notes.append(f"answer lacks {c['answer_contains']}")
    return {
        **c,
        'pass': ok,
        'actual_status': result.get('status'),
        'actual_mode': result.get('mode'),
        'actual_outcome': debug.get('outcome'),
        'actual_label': debug.get('label'),
        'actual_group': debug.get('group'),
        'notes': ' | '.join(notes),
    }

rows = [check_case(c) for c in CASES]
report_path = ROOT / 'tests' / 'expanded_deconfliction_qc_report.csv'
with report_path.open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader(); writer.writerows(rows)

passed = sum(1 for r in rows if r['pass'])
for r in rows:
    print(('PASS' if r['pass'] else 'FAIL') + ': ' + r['id'] + ' — ' + r['question'])
    if not r['pass']:
        print('  ' + r['notes'])
print(f"\nExpanded deconfliction QC: {passed} / {len(rows)} passed")
print(f"Report: {report_path}")
if passed != len(rows):
    sys.exit(1)
