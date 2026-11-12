# Evidence, provenance and limitations

This case study is a newly authored public-facing account based on two **nonpublic historical planning documents** plus the project lead's first-hand account. Its purpose is to show defensible requirements engineering, architectural reasoning, release prioritization and coordination without claiming access to the original source code.

## Evidence taxonomy

| Category | Supported statement | Appropriate formulation |
| --- | --- | --- |
| **E1 — original documented requirement** | PRD V1 scopes professor setup, student joining, resources and two AI modes | “The V1 specification required…” |
| **E2 — original planned work** | Timeline lays out weeks, milestones, integration, QA and deployment preparation | “The six-week plan scheduled…” |
| **E3 — lead-confirmed outcome** | Project lead reports a functional integrated MVP delivered by the team | “I confirmed that our team completed a functional MVP.” |
| **E4 — reported technology** | React, Python/Flask, GPT-4, S3 and EC2 in project lead's account | “The reported technology stack included…” |
| **E5 — retrospective reconstruction** | Components, information flows, diagrams and reconstructed decisions in this repo | “A conceptual decomposition is…” |
| **E6 — proposed validation/controls** | Acceptance criteria, access policy and risk mitigations authored for this portfolio | “Recommended / proposed; not verified in the historical system” |

## Original materials examined (not included in repository)

1. **AI-Powered Classroom Assistant PRD, V1 and Full Outcome**, five pages, including a student-side and professor-side flowchart on p. 5. Original file label: `PRD including V1(1).pdf`. Other three named copies were checked and are byte-for-byte identical.
2. **Anvillent AI Classroom Assistant Timeline**, complete six-week plan and attached user stories. Original file label: `Anvillent AI Classroom Assistant Timeline.txt`. Its alternate copy was checked and is byte-for-byte identical.
3. Earlier project brief and portfolio blueprint were consulted as **secondary context**, not used to override the original PRD or plan.

The PRD retains placeholder author/date fields; a PDF metadata author string also cannot establish actual authorship. Neither the PRD nor the timeline independently verifies Ryan's personal assignment of responsibilities, execution records or milestone acceptance. Those role claims come from his first-hand account, not the source documents. The delivery timeline is a plan, not a commit history. Both originals came from a former employer environment and **are deliberately omitted from the shareable repository**.

## Exact source gaps that constrain claims

- No original application code, migrations, executable demo, deployment logs, release confirmation, QA execution results or user statistics were provided.
- No verified implementation endpoints, database engine, prompts, model configuration, retrieval library, class-code algorithm, encryption scheme or identity system.
- No independently confirmed live production rollout, institutional adoption, learner outcomes or business impact.
- No historical measurement of effort; the PRD line items, stated V1 total and weekly allocations disagree. The mismatch makes actual-hours claims unsound.
- The professor diagram contains an LMS upload path despite the PRD's explicit deferral of direct LMS uploads; the written V1/future scope is used to resolve the portfolio representation.
- The PRD includes stored exam/quiz **data/resources** in V1 while deferring interactive on-platform assessment; the storage format is not established.
- The original student flowchart specifies **three practice problems**; present-day acceptance tests deliberately preserve that detail.

## Privacy, licensing and disclosure review

- **Not reproduced:** proprietary PRD, timeline, original employer flowchart graphics, private communications, screenshots, employee identities, client information and implementation artifacts.
- **Newly authored:** simplified requirements descriptions, diagrams, architecture analysis, hypothetical quality tests and technical tradeoff discussion.
- **Publication premise:** The owner instructed this project to assume employer intellectual-property and disclosure authorization has been granted (2026-11-12). No approval paperwork is distributed or independently verified here. The package still requires editorial review of any newly introduced confidential details and separate authorization before a GitHub operation.
- **Publication review status:** the V18 local candidate received a bounded source-attribution, editorial and confidentiality review, recorded in the independently delivered remediation report. Employer IP/disclosure clearance is an explicit owner-provided premise rather than independently examined legal paperwork. Any change to publication scope requires renewed review; GitHub publication still requires a separate explicit instruction. Automated scanning is not a rights determination. See [publication safety](publication-safety.md).
- **Team attribution:** based on the project lead's account, four engineers built the application and he led requirements, architecture direction, coordination and delivery; the originals do not independently attest these personal role assignments. See [attribution](../ATTRIBUTION.md).

## Interview and recruiter phrasing

**Defensible:** “At Anvillent I led requirements, MVP scope, architecture direction and coordination of four engineers for a classroom platform with professor/student workflows and two AI tutoring experiences. Our team completed a functional MVP; the implementation was performed by the engineers.”

**Not established:** “I built the Flask code,” “we ran it in production,” “the application served X schools/students,” “it improved test scores,” “we passed a security audit,” or “we shipped in exactly six weeks.”

## Updating this artifact responsibly

If more primary evidence becomes available, add it to a private review first; update the evidence taxonomy and requirements/diagram claims only when the new material supports them. Never silently convert proposed quality criteria into historical system facts.

**Planning ambiguity retained:** PRD V1 §2.2 lists assignment downloads, while the Week 4 timeline describes generating downloadable assignments/tests. The original code is unavailable; neither generation delivery nor related test execution is verified.

## Independent change control

For proposed additions to outcome, technology, individual responsibility or historical implementation claims, consult the [evidence register](evidence-register.md) and obtain a documented human source review. The single source manifest records this document and other approved materials; an independent release digest anchors the manifest and ZIP bytes. It detects changes but does not validate their truth. A digest is a **change alarm**, not proof that a statement is true. The [review protocol](review-protocol.md) explains how an authorized review deliberately updates these baselines.
