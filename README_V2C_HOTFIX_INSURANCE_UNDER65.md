# V2C Hotfix: Insurance Under-65 Routing

This hotfix fixes a routing/matching issue for questions like:

```text
What percent of adults had insurance last year by insurance for people under 65?
```

Before the fix, that query could fall through to the generic SHS not-found response even though the adult SHS file contains insurance coverage outcomes for adults aged 18-64.

The updated behavior treats this as an insurance-as-topic/status request and returns the available insurance coverage outcomes for the requested year instead of returning not_found.

Updated files:

```text
src/insurance_special.py
tests/run_v2c_qc.py
tests/v2c_testing_matrix.csv
```

Run QC:

```bash
python tests/run_v2c_qc.py
```

Expected result:

```text
V2C conversational orchestrator QC: 20 / 20 passed
```
