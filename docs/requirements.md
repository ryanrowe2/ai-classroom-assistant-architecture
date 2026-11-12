# Product requirements and release boundaries

**Evidence:** original five-page *AI-Powered Classroom Assistant* PRD, V1 §§2.1–2.3 (pp. 2–3), future vision §3 (pp. 3–4), and professor/student flowcharts (p. 5). The newly authored specification below is an analysis of historical **planned V1 functionality**, not an independently verified feature inventory of the completed application.

## Product, actors and foundational rules

Professors set up class spaces, curate teaching resources, and issue enrollment codes. Students authenticate, join a class, and select subject Q&A or concept practice. The historical documents specify role-oriented workflows but not the mechanism for sessions, permissions, file parsing, AI orchestration or a production identity system.

**Class lifecycle:** The professor source flow explicitly shows *new class → course setup → class dashboard*. `R18` captures ordinary classroom creation as a separately testable requirement discovered in the re-audit. The original 17 IDs `R01–R17` are retained for continuity. `R10` captures the **skip-upload branch during the same R18 creation event**, not a second post-creation operation. Code issuance (`R03`) is a separate class operation and is not a prerequisite for uploading course content.

## V1 requirements

| ID | Actor | Source-backed capability | Release scope |
| --- | --- | --- | --- |
| R01 | Student | Student authentication | Foundation |
| R02 | Professor | Professor authentication | Foundation |
| R18 | Professor | Create an ordinary classroom with an owning professor | Foundation; explicit from source flow |
| R03 | Professor | Generate a unique class enrollment code | Foundation |
| R04 | Student | Find/validate a supplied class code | Foundation |
| R05 | Student | Join intended classroom via code | Foundation |
| R06 | Professor | Upload course materials | Core resources |
| R07 | Professor | Save course outline | Core resources |
| R08 | Professor | Store exam and quiz data or related resources | Core resources; not live quizzes |
| R09 | Professor | Store textbook topics | Core resources; no reorder control stated in source |
| R10 | Professor | Choose skip upload **while creating** a classroom | Alternative branch of R18 |
| R11 | Professor | Download available assignments/tests/learning materials | Core resources; Week 4 **planned generation** as well, but implementation unverified |
| R12 | Student | Prepare tutoring interaction for selected enrolled class | AI setup |
| R13 | Student | Choose Q&A or concept-learning mode | AI setup |
| R14 | Q&A | Obtain relevant permitted subject data | Q&A |
| R15 | Q&A | Answer questions using subject context | Q&A |
| R16 | Concept | Explain topics and supply **three** practice problems (source diagram) | Concept practice |
| R17 | Concept | Evaluate practice attempts and guide retry/progression | Concept practice |

**Interpretation boundary:** R08 supports storing exam/quiz **information or resources**, while the original does not constrain storage to files alone; on-platform quizzes, automated assessment and official grading were explicitly deferred. R11's professor download function is explicit in the original V1 table. The six-week plan's **Week 4** additionally proposes *generating downloadable assignments and tests*, so the originals are ambiguous about on-demand generation. This portfolio preserves that planning intent without presenting generation as an independently verified V1 capability or a passed acceptance test. Student direct downloads also remain unspecified. R14's context-selection mechanism is unknown. R16’s three practice problems are explicit in the student source diagram. It may operate on a selected topic with no uploaded files in our **proposed** fixture; the historical source does not specify its empty-context behavior.

## User and data state — conceptual contracts

1. An authenticated professor creates **one** owned class (`R02 → R18`); during creation they may select the R10 skip-upload branch. Afterwards they can save materials (`R06–R09`), issue a join code (`R03`) or download existing materials (`R11`) independently. No upload requires a code.
2. An authenticated student uses an issued code to locate and join an eligible class (`R01 + R03 → R04 → R05`). A valid student must authenticate successfully even with zero memberships, and private class resources remain inaccessible before joining. The code is **not** treated as blanket authorization to read files.
3. Once enrolled, a student can start a class-bound tutor and choose a mode (`R05 → R12 → R13`). Q&A retrieves authorized content if available (`R14 → R15`); concept practice proceeds through explanation and response evaluation (`R16 → R17`).
4. Empty-class creation (`R10`, a branch of `R18`) means **zero files**, not a nonexistent class. Absent uploaded content must be explicitly distinguishable from failed retrieval and unauthorized access in *proposed* tests.

## Deferred full-product work

| Future capability | Source | Boundary |
| --- | --- | --- |
| AI-produced lectures/video via Murf.ai | PRD §§2.3, 3.1 | Media generation and video processing |
| Direct Canvas/LMS uploads | PRD §§2.3, 3.1 | External institutional integration |
| AI-generated tests/quizzes and on-platform assessment | PRD §§2.3, 3.1 | Stateful assessment UI and evaluation |
| Course-summary PDF generation | PRD §3.1 | Additional generated content |
| Adaptive learning recommendations | PRD §§2.3, 3.1 | Longitudinal personalization |
| Voice-based interaction | PRD §3.1 | Additional modalities |

Future UI placeholders were **planned** to be labeled unavailable, not working V1 features.

## Open engineering decisions — proposed, not historical assertions

- Authentication/session rules and professor ownership; membership revocation and multi-class isolation.
- Join-code length, uniqueness, rate limits, validity, renewal and revocation (proposed adversarial checks in [risk acceptance tests](risk-acceptance-tests.md)).
- Upload type/size restrictions, processing, storage lifecycle, malware screening and authorized download.
- How course materials are selected and made available to AI, including empty or stale contexts; and whether direct student resource viewing is exposed as a separate UI operation.
- How student text is processed and retained; age/education-record constraints and model data handling.
- Model unavailability, hallucinated citations, prompt injection, evaluation error and human review.

The direct student resource-view policy is a **conditional design choice**, not an independently source-backed or acceptance-covered V1 feature. The proposed policy should be evaluated separately before an implementation claims student resource-view support. These are design gaps **in the supplied planning evidence**, not proven flaws of the completed historical MVP. For a row-by-row evidence crosswalk, logical prerequisites and test mapping see [traceability](traceability.md). For a proposed executable review protocol, see [synthetic acceptance cases](../examples/synthetic-acceptance-scenarios.md) and [assertion-level coverage](acceptance-coverage.md).
