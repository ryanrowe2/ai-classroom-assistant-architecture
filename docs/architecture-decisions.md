# Architectural decisions and tradeoffs

> **Interpretation:** The PRD/timeline document a product direction and staged priorities. The entries below separate **source-backed direction** from **present-day alternative/guardrail analysis**. They are not contemporaneous, employer-approved ADRs or proof of implemented technologies.

## D1 — Constrain the first release to a functional learning loop

**Source-backed direction:** V1 focuses on professor setup, classroom joining, course resources, Q&A and concept practice. Media generation, LMS connections, on-platform assessment and adaptation are deferred.

**Reasoning:** Deliver an end-to-end teaching-to-learning workflow before increasing the number of integrations and stateful systems. **Tradeoff:** fewer automated teaching and assessment workflows in V1, but a smaller integration and QA surface. **Risk:** the UI's future placeholders could create incorrect expectations; visibly label them as unavailable.

## D2 — Separate professor administration from student learning

**Source-backed direction:** The PRD and flowcharts describe different role experiences; the timeline schedules the professor foundation before the student AI interface.

**Reasoning:** A classroom must exist before enrollment, but a class code and uploaded course materials are separate capabilities: a professor may prepare materials before issuing a code, or create an empty classroom. **Proposed design implication:** Enforce role and class ownership server-side. **Alternative:** a single unrestricted dashboard would lower UI complexity but undermine course confidentiality. **Open question:** the actual authentication/authorization system is not documented.

## D3 — Use a class code for enrollment

**Source-backed direction:** Professor-generated unique codes and student code search/join are explicit V1 requirements.

**Reasoning:** A short join path avoids direct LMS dependence. **Tradeoff:** easy onboarding versus code guessing, unintended sharing and membership management. **Proposed control:** unpredictable revocable codes, rate limits, clear access boundaries and validation feedback that limits information leakage. Actual token format and policies are unknown.

## D4 — Treat professor resources as the source of course context

**Source-backed direction:** Uploaded materials/topics/outlines and subject-data retrieval are part of the course-oriented learning design. **The source does not state that a file upload is always required before concept explanations can occur.**

**Reasoning:** A course-aware assistant is more useful than a generic chatbot. **Tradeoff:** added processing, freshness, access control and error handling. **Alternatives not resolved by sources:** direct document context, retrieval over passages or structured topic summaries. **Open question:** the mechanism that fed content into the original model is unverified.

## D5 — Provide two tutoring behaviors rather than one undifferentiated chat

**Source-backed direction:** The V1 PRD and student flowchart distinguish Q&A from concept learning with practice/evaluation.

**Reasoning:** Answering questions and guiding practice have different user goals and acceptance criteria. **Tradeoff:** separate interaction logic and test cases, but more understandable experiences. **Proposed control:** distinguish formative feedback from authoritative grades. Actual prompt orchestration and state handling remain unknown.

## D6 — Store assessment resources without building on-platform assessment

**Source-backed direction:** V1 professor capabilities include storing exam/quiz resources, while interactive on-platform quizzes/exams are postponed.

**Reasoning:** Distributing teaching files is bounded resource management; running assessments introduces attempt states, grading semantics, integrity and privacy obligations. **Tradeoff:** reduced workflow coverage but lower V1 risk. **Issue identified:** the source professor diagram includes some future-platform branches; explicit PRD scope governs interpretation.

## D7 — Prioritize integrated QA before release

**Source-backed direction:** The six-week plan schedules module-specific tests followed by final integration/QA and deployment preparation.

**Reasoning:** The primary risks span boundaries: professor role → file → class member → AI. **Proposed enhancement:** release gates for cross-class isolation, invalid enrollment codes, context loss, prompt injection, ambiguous practice evaluation and third-party API failures. **Open question:** historical coverage and execution outcomes are unavailable.

## Decision ownership and evidence

These entries are a **retrospective explanation** of documented scope and reconstructed architectural reasoning. They do not imply signed decision records, implementation commits or authorization from Anvillent. Refer to [provenance](provenance.md) before using individual claims in recruiting discussions.
