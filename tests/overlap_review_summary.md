# NHIS SHS potential topic/subgroup overlap review list

Generated from the uploaded adult and child DHIS/NHIS SHS files. This is intentionally broad/over-inclusive so you can stress-test the parser.

## Counts

- Adult topics: 56

- Child topics: 22

- Adult grouping labels: 22

- Child grouping labels: 17

- Potential topic-topic overlap rows: 137

- Potential subgroup-subgroup overlap rows: 138

- Potential topic-subgroup overlap rows: 148

- Combined rows: 423


## Highest-risk curated topic overlaps

- **asthma** → adult Current asthma; adult Asthma episode/attack; child Current asthma; child Ever having asthma
  - Risk: Generic asthma may mean current vs ever vs attack; adult/child phrasing matters.
  - Test: "asthma last year"; "currently have asthma"; "ever had asthma"; "asthma attack"; "kids asthma"
  - Expected: current asthma should be default for generic asthma unless ever/attack is explicit; child terms route child.

- **cancer** → Any type of cancer; Any skin cancer; Breast cancer; Cervical cancer; Prostate cancer
  - Risk: Generic cancer can incorrectly select a specific cancer.
  - Test: "adults with cancer last year"; "skin cancer"; "breast cancer"
  - Expected: generic cancer -> Any type of cancer; exact cancer terms -> specific cancer.

- **heart disease/heart attack/chest pain** → Coronary heart disease; Heart attack/myocardial infarction; Angina/angina pectoris
  - Risk: Heart disease language overlaps with MI/angina.
  - Test: "heart disease"; "heart attack"; "angina"; "chest pain"
  - Expected: Exact phrase wins; generic heart disease -> coronary heart disease only if mapped explicitly.

- **blood pressure/high blood pressure/hypertension** → Diagnosed hypertension; Blood pressure check
  - Risk: High blood pressure can be diagnosis, check, medication, or measured BP in other systems.
  - Test: "high blood pressure"; "blood pressure check"; "had bp checked"
  - Expected: diagnosis words -> Diagnosed hypertension; check/screening words -> Blood pressure check.

- **cholesterol/high cholesterol/cholesterol check** → High cholesterol
  - Risk: Current file has high cholesterol topic; user may ask cholesterol levels/check ambiguously.
  - Test: "high cholesterol"; "cholesterol"; "cholesterol levels"
  - Expected: High cholesterol only unless separate cholesterol-check topic exists.

- **diabetes/blood sugar** → Diagnosed diabetes
  - Risk: Blood sugar wording should not drift to unrelated blood pressure/cholesterol.
  - Test: "diabetes"; "blood sugar"
  - Expected: diabetes/blood sugar -> Diagnosed diabetes.

- **flu shot/vaccine/vaccination** → Receipt of influenza vaccination adult; Receipt of influenza vaccination child; Ever received pneumococcal vaccination adult
  - Risk: Vaccine language can select flu vs pneumococcal.
  - Test: "flu shot"; "vaccine"; "pneumonia vaccine"; "pneumococcal"
  - Expected: flu/influenza -> influenza; pneumococcal/pneumonia vaccine -> pneumococcal; generic vaccine should ask clarification or use flu only if context says flu.

- **smoking/vaping/e-cig/tobacco** → Current cigarette smoking; Current electronic cigarette use
  - Risk: Current/e-cig/tobacco overlap.
  - Test: "smoking"; "vaping"; "e-cigarettes"; "tobacco"
  - Expected: vape/e-cig -> e-cig topic; cigarette/smoking -> cigarette topic; tobacco generic may need clarification.

- **depression/anxiety/worry/mental health** → Adult Regularly had feelings of depression; Adult Regularly had feelings of worry, nervousness, or anxiety; Adult Taking prescription medication for depression; Adult Taking prescription medication for anxiety; Adult Counseled by mental health professional; Adult Did not get needed mental health care due to cost; Child Daily feelings of worry/nervousness/anxiety; Child Receive services for mental health problems
  - Risk: Mental health terms overlap by symptom, medication, counseling, care access, and child services.
  - Test: "anxiety"; "depression"; "mental health care"; "therapy"; "anxiety medicine"; "mental health services for kids"
  - Expected: symptom terms -> feelings topic; medication terms -> medication topic; counseling/therapy -> counseled; cost/needed care -> access topic; child services -> services topic.

- **disability/difficulty/functioning** → Adult/child Disability status (composite); adult/child Difficulty status (composite); adult individual difficulty topics hearing/seeing/etc.
  - Risk: Disability and functioning difficulty are not interchangeable.
  - Test: "disabled adults"; "difficulty walking"; "functioning difficulty"; "hearing difficulty"
  - Expected: specific difficulty -> individual difficulty where adult; composite difficulty -> Difficulty status; disability -> Disability status.

- **doctor/clinic/urgent care/retail/ER/hospital** → Doctor visit; Hospital emergency department visit; Urgent care center visit; Retail health clinic visit; Urgent care center or retail health clinic visit; child two-or-more variants
  - Risk: Care setting visit terms overlap heavily.
  - Test: "doctor visit"; "ER visit"; "urgent care"; "retail clinic"; "urgent or retail"
  - Expected: setting-specific words should win; combined phrase should use combined topic only.

- **usual place of care vs doctor visit** → Has a usual place of care; Doctor visit
  - Risk: Care access vs utilization may both contain care/doctor.
  - Test: "usual place of care"; "regular source of care"; "doctor visit"
  - Expected: usual/regular source/place -> usual place; visit -> doctor visit.

- **cost-related care** → Delayed getting medical care due to cost; Did not get needed medical care due to cost; Did not get needed mental health care due to cost; Did not take medication as prescribed to save money
  - Risk: Cost/affordability terms can map to delayed care, unmet need, mental health care, or meds.
  - Test: "delayed care due to cost"; "could not afford care"; "skipped medicine to save money"
  - Expected: delayed vs did not get vs medication vs mental health must be separated.

- **health insurance/uninsured/private/public/exchange/Medicaid/Medicare** → Uninsured at time of interview; Uninsured part past year; Uninsured > one year; Private coverage; Public coverage; Exchange-based coverage; health insurance subgroup labels
  - Risk: Insurance terms can be topic or subgroup; age-qualified insurance group conflicts.
  - Test: "uninsured adults"; "flu shot among uninsured adults"; "private insurance"; "Medicare adults 65+"; "nonelderly Medicaid"
  - Expected: If insurance term is main topic -> insurance topic; if another health topic is present -> insurance subgroup; 65+/under65 terms choose age-qualified grouping.

- **health status/wellness/well child** → Fair or poor health status; Wellness visit; Well child check-up
  - Risk: Wellness/well child/health status may overlap.
  - Test: "fair or poor health"; "wellness visit"; "well child check"
  - Expected: exact phrase wins.

- **ADHD/learning disability/special education/mental health services** → Ever having ADHD; Ever having learning disability; Receiving special education or early intervention; Receive services for mental health problems
  - Risk: Child developmental/education/service terms overlap.
  - Test: "ADHD"; "learning disability"; "special education"; "early intervention"; "mental health services"
  - Expected: condition vs service terms should be separated.

- **school absence/injury/illness** → Missing 11+ school days due to illness/injury; fair/poor health; urgent/ER visits
  - Risk: Illness/injury terms can drift to utilization.
  - Test: "missed school"; "school absences"; "injury"
  - Expected: school absence words -> missing school days topic.


## Highest-risk curated subgroup overlaps

- **insurance, health coverage, insured, uninsured, private, Medicaid, Medicare, nonelderly, senior** → Health insurance coverage: Under 65; Health insurance coverage: 65 and over; Uninsured/Private/Public/Exchange topics
  - Risk: Age-qualified insurance groupings conflict with generic insurance topics/subgroups.
  - Test: "flu shot among seniors with Medicare"; "flu shot by insurance for under 65"; "uninsured nonelderly adults"
  - Expected: 65+/Medicare/senior -> 65+ insurance grouping; under65/nonelderly/18-64 -> Under 65 insurance grouping; if insurance is topic and no other topic exists, use insurance topic.

- **race, ethnicity, Hispanic, Latino, Mexican, non-Hispanic, White, Black, Asian, AIAN** → Race; Hispanic or Latino origin and race
  - Risk: Race alone differs from race/ethnicity categories.
  - Test: "flu shot by race"; "flu shot among Hispanic adults"; "flu shot among Black non-Hispanic kids"; "flu shot among AIAN adults"
  - Expected: Hispanic/non-Hispanic/Mexican -> Hispanic or Latino origin and race; race-only terms -> Race when no ethnicity term.

- **income, poverty, FPL, poor, low income** → Family income; Poverty status
  - Risk: Income and poverty have overlapping FPL subgroup labels.
  - Test: "low income"; "below poverty"; "family income"; "FPL"
  - Expected: poverty/FPL/below poverty -> Poverty status unless exact family income term requested; family income -> Family income.

- **metro, MSA, urban, rural, nonmetro, place of residence** → Adult Metropolitan statistical area status; Adult Urbanicity; Child Place of residence; Child Metro
  - Risk: MSA/place/metro/urbanicity use similar words but are separate groupings.
  - Test: "by metro"; "large MSA"; "urbanicity"; "rural kids"; "nonmetro adults"
  - Expected: MSA/place of residence -> MSA/place; central/fringe/nonmetropolitan/urban/rural -> urbanicity/metro as available.

- **disability, difficulty, functioning difficulty** → Disability status; Difficulty status; individual adult difficulty topics
  - Risk: Disability status and difficulty status are separate groupings; also topics exist.
  - Test: "flu shot by disability"; "flu shot by functioning difficulty"; "difficulty hearing"
  - Expected: disability words -> Disability status; difficulty/functioning -> Difficulty status; specific difficulty + no other topic -> topic.

- **sex, gender, male, female, gay, lesbian, bisexual, straight, men, women** → Sex; Sexual orientation
  - Risk: Sex and sexual orientation co-occur in phrases like gay men.
  - Test: "gay men asthma"; "straight women flu shot"; "by sexual orientation"; "by sex"
  - Expected: Sexual orientation should win for gay/lesbian/bisexual/straight; explain sex x sexual-orientation cross-tab unavailable if both asked.

- **age, older, elderly, senior, 65+, 75+** → Age groups with 65+; Age groups with 75+
  - Risk: Age group variants conflict.
  - Test: "age 65 and older"; "75 and older"; "seniors"
  - Expected: 75+ explicit -> Age groups with 75+; 65+/senior -> Age groups with 65+ unless insurance 65+ specified.

- **education, college, high school, parental education** → Adult Education; Child Parental Education; child special education topic
  - Risk: Education subgroup can conflict with child special education topic.
  - Test: "flu shot by education"; "kids by parental education"; "special education services"
  - Expected: adult education -> Education; child education grouping -> Parental Education; special education service phrase -> child topic.

- **work, employed, unemployed, working parents, missed workdays** → Adult Employment status; Child Working status; adult six+ workdays missed topic
  - Risk: Work terms can be employment grouping, child parent working status, or missed-work topic.
  - Test: "flu shot by work status"; "working parents"; "missed workdays"
  - Expected: employment/work status -> grouping; missed workdays -> topic.

- **single parent, married parents, working parents, family structure** → Family structure; Working status
  - Risk: Single-parent wording appears in both family structure and working status.
  - Test: "flu shot among single parent kids"; "working single parent"
  - Expected: working/no working/two parents working -> Working status; married/cohabiting/single parent family terms -> Family structure.

- **married, partner, divorced, separated, widowed, single** → Marital status; Sexual orientation? family structure not adult
  - Risk: Partner wording may be relationship or orientation context.
  - Test: "flu shot among married adults"; "living with partner"; "gay partner"
  - Expected: marital/legal relationship terms -> Marital status; gay/straight/bisexual -> Sexual orientation.

- **born, foreign, US-born, nativity, veteran** → Nativity; Veteran Status
  - Risk: born terms could be person status not topic.
  - Test: "foreign born"; "US-born"; "veterans"
  - Expected: foreign/us-born -> Nativity; veteran -> Veteran Status.

- **SVI, social vulnerability, vulnerable** → Adult Social vulnerability; Child Social vulnerability index
  - Risk: SVI wording differs by file label.
  - Test: "by SVI"; "high social vulnerability"; "low vulnerability"
  - Expected: SVI/social vulnerability -> the population-specific social vulnerability grouping and all statuses.


## Highest-risk curated topic/subgroup collisions

- **uninsured/private/public/Medicaid/Medicare/insurance** → Insurance topics vs Health insurance coverage subgroup values
  - Risk: Same user wording may be interpreted as either topic or subgroup.
  - Test: "uninsured adults" might be the uninsured topic; "flu shot among uninsured adults" should be subgroup.
  - Expected: Main-topic insurance query -> insurance topic; other-topic + insurance term -> subgroup.

- **disability/difficulty** → Disability/difficulty topics vs Disability/Difficulty status subgroups
  - Risk: Same user wording may be interpreted as either topic or subgroup.
  - Test: "adults with disability" can be a subgroup; "disability status" can be a topic.
  - Expected: If topic requested is flu/asthma/etc., disability is subgroup; if no other topic, use disability/difficulty topic.

- **special education / parental education / education** → Child special education topic vs Parental Education subgroup
  - Risk: Same user wording may be interpreted as either topic or subgroup.
  - Test: "special education" topic vs "by education" subgroup.
  - Expected: special education/early intervention -> topic; parent education/college/high school -> subgroup.

- **workdays / employment / working** → Six+ workdays missed topic vs Employment status subgroup
  - Risk: Same user wording may be interpreted as either topic or subgroup.
  - Test: "missed work" topic vs "working full time" subgroup.
  - Expected: missed workdays -> topic; employment/working status -> subgroup.

- **doctor/urgent/retail/ER visit vs place/metro/region?** → Care setting topics vs place of residence/metro/urbanicity subgroup
  - Risk: Same user wording may be interpreted as either topic or subgroup.
  - Test: Generic place words should not be confused with care setting.
  - Expected: clinic/ER/doctor/urgent/retail -> topic; metro/MSA/urban/rural/region -> subgroup.
