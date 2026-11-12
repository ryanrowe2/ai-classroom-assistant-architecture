# Assertion-level coverage map

**Generated prospective coverage, not executed results.** Each positive assertion identifies an observable expected outcome; negative assertions test denial/isolation, and failure assertions test degradation/recovery. Merely listing assertions does not prove they are implemented or that their oracles are valid: a reviewer must execute and inspect them.

Source of truth: [`data/requirements.json`](../data/requirements.json) and [`data/acceptance-cases.json`](../data/acceptance-cases.json). Detailed setups, actions and evidence appear in [the synthetic scenarios](../examples/synthetic-acceptance-scenarios.md).

| Requirement | Positive assertion IDs | Negative assertion IDs | Failure assertion IDs |
| --- | --- | --- | --- |
| R01 | A-S03-01, A-S17-00 | A-S15-01 | None |
| R02 | A-S01-01, A-S15-03, A-S17-00, A-S18-01 | A-S15-02, A-S15-04, A-S16-01, A-S18-02 | None |
| R03 | A-S02-01, A-S17-01 | A-S02-02 | A-S02-04, A-S02-05 |
| R04 | A-S03-02 | A-S03-04 | None |
| R05 | A-S03-03, A-S17-01 | A-S03-04, A-S05-01 | None |
| R06 | A-S01-03, A-S18-01 | A-S16-01 | A-S11-01 |
| R07 | A-S01-04, A-S18-01 | A-S16-01 | None |
| R08 | A-S10-01 | A-S16-01 | None |
| R09 | A-S10-02 | A-S16-01 | None |
| R10 | A-S04-01 | None | None |
| R11 | A-S10-03 | A-S10-04, A-S16-01 | None |
| R12 | A-S04-03, A-S06-01, A-S07-01, A-S17-02 | None | None |
| R13 | A-S06-02, A-S07-02, A-S17-02, A-S17-03 | None | None |
| R14 | A-S06-03, A-S17-02 | A-S05-02, A-S05-03, A-S06-05 | A-S04-04, A-S12-01 |
| R15 | A-S06-04, A-S17-02 | A-S06-05 | A-S04-04, A-S12-02, A-S13-01 |
| R16 | A-S07-03, A-S07-04, A-S17-03 | None | None |
| R17 | A-S08-01, A-S08-02, A-S09-01, A-S17-03 | None | A-S14-01 |
| R18 | A-S01-02, A-S04-02, A-S17-01, A-S18-01 | A-S18-02 | None |

**Specification inventory:** 18 requirements, 18 scenarios, 51 atomic proposed assertions. These are test design counts, not executed test counts.

## Review gate

Before treating coverage as meaningful, check each assertion’s initial state, independent action, expected result, prohibited side effect, evidence channel and eligibility for PASS. Validate source fidelity (including the three-problem learning flow), allow manual mathematical and AI-rubric review, and report BLOCKED/INCONCLUSIVE when observation is impossible.
