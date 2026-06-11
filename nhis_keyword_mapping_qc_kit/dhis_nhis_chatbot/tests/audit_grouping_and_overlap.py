from __future__ import annotations
import csv, sys
from pathlib import Path
sys.path.append('src')
from load_sources import load_data, load_keyword_mappings
from matchers import detect_group_intent, match_topic, extract_years
from normalize_text import normalize_text

OUTDIR = Path('tests/qc_reports')
OUTDIR.mkdir(parents=True, exist_ok=True)
km = load_keyword_mappings()
dfs = {'adult': load_data('adult'), 'child': load_data('child')}

LABEL_SYNONYMS = {
    'Age groups with 65+': 'age groups including 65 plus',
    'Age groups with 75+': 'age groups including 75 plus',
    'Age groups': 'age group',
    'Difficulty status': 'functioning difficulty status',
    'Difficulty Status': 'functioning difficulty status',
    'Disability status': 'disability status',
    'Disability Status': 'disability status',
    'Education': 'education level',
    'Parental Education': 'parents education level',
    'Employment status': 'employment status',
    'Working status': 'parent working status',
    'Family income': 'family income group',
    'Family structure': 'family structure',
    'Health insurance coverage: 65 and over': 'insurance coverage for people 65 and over',
    'Health insurance coverage: Under 65': 'insurance coverage under 65',
    'Health insurance coverage': 'insurance coverage',
    'Hispanic or Latino origin and race': 'race and ethnicity',
    'Marital status': 'marital status',
    'Metropolitan statistical area status': 'MSA status',
    'Place of residence': 'MSA residence',
    'Metro': 'urbanicity',
    'Urbanicity': 'urbanicity',
    'Nativity': 'nativity',
    'Poverty status': 'poverty level',
    'Race': 'racial group',
    'Region': 'census region',
    'Sex': 'gender',
    'Sexual orientation': 'sexual orientation',
    'Social vulnerability': 'SVI',
    'Social vulnerability index': 'SVI',
    'Veteran Status': 'veteran status',
    'Total': 'overall',
}
TOPIC_PHRASE = {
    'Receipt of influenza vaccination': 'got a flu shot',
    'Current asthma': 'had current asthma',
    'Diabetes diagnosis, self-reported': 'had diabetes',
    'Uninsured at time of interview': 'were uninsured',
    'Urgent care center visit': 'used urgent care',
    'Angina/angina pectoris': 'had angina',
}

def topic_for_label(pop, label):
    df = dfs[pop]
    flu = df[(df['Outcome (or Indicator)'].eq('Receipt of influenza vaccination')) & (df['col_label'].eq(label))]
    if not flu.empty:
        return 'Receipt of influenza vaccination'
    if pop == 'adult' and label == 'Family income':
        return 'Urgent care center visit'
    # Use first outcome with label as fallback.
    return str(sorted(df[df['col_label'].eq(label)]['Outcome (or Indicator)'].unique())[0])

def phrase_for_topic(topic):
    return TOPIC_PHRASE.get(topic, topic.lower())

def pop_word(pop): return 'adults' if pop == 'adult' else 'kids'

def row_count(pop, years, outcome, label):
    df=dfs[pop]
    s=df[(df['Year'].astype(int).isin(years)) & (df['Outcome (or Indicator)'].eq(outcome)) & (df['col_label'].eq(label))]
    return len(s)

rows=[]
for pop,df in dfs.items():
    for label in sorted(df['col_label'].dropna().unique()):
        topic=topic_for_label(pop,label)
        syn = LABEL_SYNONYMS.get(label,label)
        avail = sorted(df[(df['Outcome (or Indicator)'].eq(topic)) & (df['col_label'].eq(label))]['Year'].dropna().astype(int).unique())
        audit_year = int(avail[-1]) if avail else 2024
        if label == 'Total':
            q=f'How many {pop_word(pop)} {phrase_for_topic(topic)} in {audit_year} overall?'
        else:
            q=f'How many {pop_word(pop)} {phrase_for_topic(topic)} in {audit_year} by {syn}?'
        years,ym=extract_years(q,df)
        outcome,tm=match_topic(q,df,km)
        got_label,got_value,gm=detect_group_intent(q,df,km)
        n=row_count(pop,years,outcome,label) if outcome else 0
        ok = (outcome==topic and got_label==label and n>0)
        rows.append({'audit_type':'grouping_category','population':pop,'query':q,'expected_outcome':topic,'matched_outcome':outcome,'expected_label':label,'matched_label':got_label,'matched_group_value':got_value,'rows_available':n,'pass':ok,'note':'' if ok else str({'topic_meta':tm,'group_meta':gm})[:500]})

overlap_tests = [
    ('adult','What percent of adults were uninsured last year?','Uninsured at time of interview','Total','topic_not_insurance_subgroup'),
    ('child','What percent of kids were uninsured last year?','Uninsured at time of interview','Total','topic_not_insurance_subgroup'),
    ('adult','What percent of adults had diabetes last year by SVI?','Diagnosed diabetes','Social vulnerability','svi_grouping_expands'),
    ('adult','What percent of gay men had current asthma last year?','Current asthma','Sexual orientation','sexual_orientation_priority_over_sex'),
    ('adult','What percent of male adults had current asthma last year?','Current asthma','Sex','sex_subgroup'),
    ('child','How many uninsured kids got a flu shot last year?','Receipt of influenza vaccination','Health insurance coverage','insurance_subgroup_when_topic_is_flu'),
    ('adult','How many private insurance adults got a flu shot last year?','Receipt of influenza vaccination','Health insurance coverage: Under 65','insurance_subgroup_private'),
    ('child','How many Hispanic kids got a flu shot last year?','Receipt of influenza vaccination','Hispanic or Latino origin and race','hispanic_subgroup'),
    ('adult','How many Black adults got a flu shot last year?','Receipt of influenza vaccination','Race','race_subgroup'),
    ('adult','How many adults got a flu shot last year by family income?','Receipt of influenza vaccination','Family income','expected_not_available_for_flu'),
]
for pop,q,exp_out,exp_label,case in overlap_tests:
    df=dfs[pop]
    years,ym=extract_years(q,df)
    out,tm=match_topic(q,df,km)
    lab,val,gm=detect_group_intent(q,df,km)
    # Simulate retrieve_estimate.py deconfliction: if the subgroup value is actually part
    # of the matched topic itself (e.g., uninsured), it should not also force a grouping.
    if val and out and normalize_text(str(val)) in normalize_text(str(out)):
        lab, val = 'Total', None
    n=row_count(pop,years,out,lab) if out and lab else 0
    if case == 'expected_not_available_for_flu':
        ok = (out==exp_out and lab==exp_label and n==0)
    else:
        ok = (out==exp_out and lab==exp_label and n>0)
    rows.append({'audit_type':'topic_subgroup_overlap','population':pop,'query':q,'expected_outcome':exp_out,'matched_outcome':out,'expected_label':exp_label,'matched_label':lab,'matched_group_value':val,'rows_available':n,'pass':ok,'note':case if ok else str({'topic_meta':tm,'group_meta':gm})[:500]})

with open(OUTDIR/'grouping_and_overlap_qc_report.csv','w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader(); writer.writerows(rows)
summary=[]
for typ in sorted(set(r['audit_type'] for r in rows)):
    sub=[r for r in rows if r['audit_type']==typ]
    summary.append({'audit_type':typ,'passed':sum(bool(r['pass']) for r in sub),'total':len(sub),'failed':sum(not bool(r['pass']) for r in sub)})
with open(OUTDIR/'grouping_and_overlap_qc_summary.csv','w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f, fieldnames=['audit_type','passed','total','failed'])
    writer.writeheader(); writer.writerows(summary)
print(summary)
failed=[r for r in rows if not r['pass']]
if failed:
    print('FAILED ROWS')
    for r in failed: print(r)
    raise SystemExit(1)
