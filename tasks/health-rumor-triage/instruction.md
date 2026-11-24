# Health claim triage

A health-information site has received user-submitted claims (in Chinese) and needs each one
checked against its evidence library before it is published.

- `/app/claims.csv` has 20 claims (`claim_id,claim`).
- `/app/evidence/` has 100 evidence cards in English, one per file (`EV-###.txt`).
- `/app/RULES.md` defines the three verdicts. Follow it exactly.

For every claim, find the one evidence card it is about and decide its verdict.

Write `/app/verdicts.csv` with this header and one row per claim (20 rows):

```
claim_id,evidence_id,verdict
```

`evidence_id` is the card's id (for example `EV-123`) and `verdict` is one of
`SUPPORTED`, `CONTRADICTED`, `OVERSTATED`.
