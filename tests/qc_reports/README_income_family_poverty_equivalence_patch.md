# Income / Poverty / FPL Equivalence Patch

This patch treats user wording for `income`, `household income`, `family income`, `poverty`, `poverty status`, and `FPL` as one user-facing grouping: **Family income**.

Implementation notes:

- The SHS source files contain FPL-style rows under both `Family income` and `Poverty status`, depending on population/topic/year.
- The matcher now routes all income/poverty/FPL wording to the user-facing label `Family income`.
- The retriever prefers rows where `col_label == Family income` when available, and falls back to `col_label == Poverty status` when those are the available current rows.
- The answer header displays `by Family income` for both cases.

Additional deconfliction checks were rerun for income/poverty, family structure, insurance 65+/under 65, race/ethnicity, metro/urbanicity/place, disability/difficulty, sex/sexual orientation, education/topic overlap, age, SVI, employment/working status, nativity, and veteran status.
