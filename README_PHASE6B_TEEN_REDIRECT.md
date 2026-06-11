# Phase 6B — Teen redirect exception

This patch adds a small routing exception for teen/adolescent/youth requests.

## Why

The current prototype intentionally supports only the adult and child NHIS Summary Health Statistics files. Teen SHS has its own DQT/tool and is not yet integrated into this adult/child parser because it would add another population layer and more deconfliction rules.

## Behavior

Questions mentioning teen/teens/teenager/adolescent/youth are routed to a teen redirect response before adult/child estimate matching.

Example:

```text
What percent of teens had current asthma last year?
```

Response behavior:

```text
Teen estimates are not included in this adult/child NHIS Summary Health Statistics prototype yet. For teen-specific estimates, use the NHIS Teen Summary Health Statistics tool: https://wwwn.cdc.gov/NHISDataQueryTool/NHIS_teen/index.html
```

The response includes:

- `mode = teen_redirect`
- source card for the NHIS Teen SHS tool
- debug reason `teen_exception_redirect`
- no attempt to route to adult/child SHS estimates

## Terms currently routed to teen redirect

```text
teen, teens, teenager, teenagers, adolescent, adolescents, youth, nhis teen, nhis-teen, teen shs, teen summary
```

## QC

Run:

```bash
python tests/run_phase6b_qc.py
```

This confirms teen redirects work and adult/child estimate routing and FAQ routing are unaffected.
