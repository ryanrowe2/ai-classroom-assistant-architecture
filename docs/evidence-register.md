# Material claims and evidence register

**Purpose:** Preserve the evidentiary boundary around the original AI Classroom Assistant project. This is a human-reviewed *claim policy*, not an original project deliverable or a machine proof of truth. Source documents remain nonpublic and are not republished.

| ID | Material claim category | Evidence level | Permitted wording | Not supported by available evidence |
| --- | --- | --- | --- | --- |
| EV01 | V1 feature scope | Original five-page V1/full-outcome PRD, pp. 1–5, including student/professor diagrams | “The V1 specification described authentication, class codes, professor resources, Q&A and concept tutoring.” | Exact implemented APIs, code-level tests, deployed database or prompt internals |
| EV02 | Planned delivery structure | Original six-week Anvillent timeline, Weeks 1–6 | “The plan scheduled these workstreams and integration/QA objectives.” | Completion dates, actual person-hours, executed regression results or actual sprint velocity |
| EV03 | Individual responsibilities | Project lead’s first-hand account | “I led product definition, architecture direction, coordination and delivery oversight; four engineers implemented the code.” | Independent attribution from the PRD or team records, personal authorship of implementation code |
| EV04 | MVP outcome | Project lead’s first-hand report | “The engineering team completed a functional MVP, as confirmed by the project lead.” | Production deployment, school adoption, active student count, grade improvements, uptime, revenue or benchmarks |
| EV05 | Reported technology | Project lead’s first-hand account | “The reported stack included React, Flask/Python, GPT-4, AWS S3 and EC2.” | Verified deployment topology, authentication package, retrieval algorithm, model configuration or database vendor |
| EV06 | Reconstructed architecture and tests | Newly authored conceptual analysis based on original PRD and roadmap | “Proposed security boundaries, quality criteria and prospective acceptance oracles.” | Historically executed tests, independently validated implementation behavior, deployed security controls |
| EV07 | Publication rights | Employer-project context; authorization presumed granted on owner instruction (2026-11-12) | “Employer disclosure/IP authorization is treated as granted at the owner’s direction; this repository does not include the authorization paperwork.” | Independently verified legal opinion, employer endorsement, or permission inferred solely from scans |

## Claim-review rules

1. Before adding or changing a historical claim in `README.md`, `docs/delivery.md`, `docs/provenance.md`, `ATTRIBUTION.md`, or other protected narratives, identify the supporting evidence ID and original evidence, and record who reviewed the changed wording. Do not include private reviewer contact information in the repository.
2. If a claim would imply verified deployment, 10,000 students, increased grades, live customer adoption, independent authorship or measured performance, **reject it** without new primary supporting evidence and disclosure clearance.
3. Review proposed requirements/test assertions against the original private PRD/timeline when possible; classify extrapolations as prospective recommendations, never delivered V1 features by default.
4. Only after source verification, confidentiality review and authorized editorial sign-off should a reviewer update the single reviewed source manifest and independent release digest. Fingerprints detect change; they cannot establish truth or publication rights.

**External release status: OWNER-ASSUMED AUTHORIZATION.** This register does not override `docs/publication-safety.md`.
