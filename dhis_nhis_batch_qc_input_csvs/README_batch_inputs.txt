DHIS/NHIS chatbot batch QC input files
Generated from current uploaded adult/child DHIS SHS CSVs.

Files:
1. batch_01_all_topics_total_last_year.csv
   - 78 rows
   - one total-population / latest-available-year query for each adult and child topic
   - uses common wording rather than exact DHIS labels where possible

2. batch_02_flu_shot_all_demographic_subgroups_last_year.csv
   - 139 rows
   - one flu-shot / latest-available-year query for every demographic subgroup available in the adult and child flu-shot records
   - uses common demographic wording/synonyms where possible

3. batch_input_qc_report.csv
   - structural QC checks for row counts, blank questions, duplicate questions, source coverage, and last-year wording

Run with existing batch CLI:
python batch_cli.py batch_01_all_topics_total_last_year.csv --output batch_01_debug_output.csv
python batch_cli.py batch_02_flu_shot_all_demographic_subgroups_last_year.csv --output batch_02_debug_output.csv

Send back the debug output CSVs when the parser/retriever fails or gives unexpected results.
