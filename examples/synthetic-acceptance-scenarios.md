# Synthetic acceptance scenarios — proposed, not executed

**Status:** These are prospective tests designed for an implementation that can expose sufficient state and contextual evidence. No original application code, test run or deployment records were available. Do not label any scenario PASS until executed and reviewed against a real approved build.

**Isolation:** Each Sxx starts in a fresh isolated state; fixtures are intentionally recreated for that case. A class, student enrollment, code, document or permission given in S01 is **not** presumed to exist in S02. Every test must record its own initial class IDs and sessions. Assertions below are proposed acceptance oracles, not historical observations.

**Counterfactual Q&A fixtures (fictional):** In Calculus A, `calculus-a.txt` says “For checkpoint Willow-7, the instructor-defined answer is violet compass.” In Physics B, `physics-b.txt` uses the same checkpoint but says “copper lantern.” These invented facts are intentionally not general knowledge and are only used for controlled QA. Both source bodies must remain inside authorized test classes.

**Grounding rubric:** Independently score output accuracy and permitted-document support as 0 (fails), 1 (partial) or 2 (fully correct and supported). S06 and the Q&A leg of S17 require **both score 2** plus inspected evidence of authorized model-visible context, the correct class marker and a no-context or swapped-class control. If content observability is unavailable, the grounding outcome is **INCONCLUSIVE**, even when a response happens to be correct. Such evidence supports the tested grounding behavior; it cannot demonstrate perfect causal dependence on a document for all model outputs.

**Concept rubric:** Independently inspect the introductory mathematical explanation and verify **three distinct solvable** practice problems and their answer keys (2, 2x, 3 for the specified derivative prompts). Wrong and correct responses have separate state-transition tests. This is formative interaction, not historical proof of grading accuracy.

**Test-result vocabulary:** PASS, FAIL, BLOCKED, INCONCLUSIVE, NOT RUN. A subcase requiring collision injection or AI context instrumentation is BLOCKED/INCONCLUSIVE if the build cannot support it; it must never be silently recorded as PASS.

## S01 — Professor login and ordinary class creation

**Requirement scope:** R02, R18, R06, R07

**Given:** A fresh isolated environment contains Professor Alpha and no class named Calculus A; professor authentication is valid.

**When:** Alpha signs in, creates Calculus A, saves an outline with two units and uploads a readable course handout.

**Then:** One classroom is created and owned by Alpha; the outline and handout are readable from Alpha’s own classroom dashboard.

**Must not:** No duplicate class, foreign-owner privilege or publication of private files occurs.

**Evidence to capture:** Authorized login record, class owner before/after, outline retrieval, scoped file metadata and bytes.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S01-01 | positive | R02 | Professor Alpha is authenticated and can access only their authorized professor workspace. | Session principal and role observed server side. |
| A-S01-02 | positive | R18 | One new classroom is created with Alpha as the sole owner. | Before/after class records and owner ID. |
| A-S01-03 | positive | R06 | Readable handout is stored against Calculus A and accessible to Alpha. | Stored class association plus successful authorized read. |
| A-S01-04 | positive | R07 | Two-unit outline is saved and round-trips without change. | Persisted outline and retrieval comparison. |

## S02 — Two-class class-code issuance and uniqueness

**Requirement scope:** R03

**Given:** Two different classes, Calculus A (owned by Alpha) and Physics B (owned by Beta), already exist; neither class has a join code.

**When:** Each owner independently requests code generation for their initially uncoded class. Separately, in a proposed instrumented test environment, force a code-candidate collision and issue many codes concurrently across independent classes; inspect the backing uniqueness constraint or equivalent atomic issuance rule and the state after restart.

**Then:** Two normal issued codes are nonempty, distinct and class-specific. In the proposed collision/concurrency test, every committed code maps to exactly one class, no duplicate survives concurrent requests or restart, and conflicting transactions retry or fail safely. Without a controllable harness and backing-state inspection, robustness is BLOCKED—not PASS.

**Must not:** A code alone may not read class files, rosters or authorize professor mutations.

**Evidence to capture:** Normal two-code issuance log and class mapping; for proposed robustness testing, schema/atomicity evidence, overlapping issuance traces, deliberately forced collision, committed code set, post-restart lookup, duplicate count and any BLOCKED reason.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S02-01 | positive | R03 | Issuing a code separately for both classes yields two distinct usable codes with correct class mapping. | Two issuance outputs, distinctness and lookup assertions. |
| A-S02-02 | negative | R03 | Knowledge of either code alone does not permit resource or roster access. | Denied server-side resource requests with no leaked payload. |
| A-S02-04 | failure | R03 | Proposed collision-injection case does not persist a duplicate code across classes. | Unique-index/conflict result or retry event if controllable; otherwise BLOCKED, not silently PASS. |
| A-S02-05 | failure | R03 | Proposed concurrent issuance and forced-collision cases must show an atomic/persistent uniqueness invariant: each committed code maps to one class, no duplicate survives retries or restart; otherwise FAIL, or BLOCKED without an instrumented implementation. | Backing uniqueness constraint or equivalent transactional proof, simultaneous issuance trace, collision-injection log, persistent readback after restart and exact duplicate-count assertion; mark BLOCKED if unavailable. |

## S03 — Enrollment, idempotency and invalid-code denial

**Requirement scope:** R01, R04, R05

**Given:** Student One has valid student credentials but no active session and is not enrolled in either Calculus A or Physics B; a valid join code for Calculus A and a made-up code are available.

**When:** Student One authenticates into an empty student workspace, attempts a private class-material read before joining, looks up the valid join code, joins Calculus A twice, and tries the unknown code. Revocation is not exercised as a core V1 requirement.

**Then:** Authentication succeeds before enrollment without exposing private class materials. The valid code identifies Calculus A, exactly one membership is created, repeat join is idempotent, and unknown codes are rejected without disclosure.

**Must not:** No Physics B membership, private roster details or materials are revealed by an invalid code.

**Evidence to capture:** Before/after authentication and empty-workspace state, denied pre-enrollment private read, session role, lookup target, membership counts, error classifications and absence of private data disclosure.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S03-01 | positive | R01 | Student One signs in successfully while belonging to zero classes and sees an empty authorized workspace, with private class material access denied until joining. | Authenticated student session trace, zero-membership state before code use, empty workspace, server-side denial and zero private document bytes from pre-enrollment attempt. |
| A-S03-02 | positive | R04 | Valid code lookup identifies only the intended class join target. | Lookup result class ID with private payload redacted. |
| A-S03-03 | positive | R05 | First and repeated joins leave exactly one membership in Calculus A. | Membership rows counted before and after both requests. |
| A-S03-04 | negative | R04, R05 | Unknown or invalid class codes do not create memberships or disclose private data; revocation is reserved for a separately proposed lifecycle control. | Denied unknown-code requests, unchanged memberships, and inspected response bodies. Revocation intentionally not required for V1. |

## S04 — Skip-upload is a class-creation branch

**Requirement scope:** R10, R18, R12, R14, R15

**Given:** Alpha has a valid professor session, no classroom named Empty Seminar exists, and no course materials have been uploaded.

**When:** During one creation operation Alpha selects “skip initial uploads”, creates Empty Seminar, issues a code and Student One joins, opens Q&A and asks for an allegedly uploaded handout.

**Then:** Exactly one owned classroom exists with zero materials; student session is class-bound; Q&A clearly reports no uploaded handout rather than pretending to quote one.

**Must not:** Skip upload may not create an extra class, require a prior completed classroom creation, or invent source citations.

**Evidence to capture:** Single creation event/owner, zero-resource inventory, membership/tutor selected class and explicit no-context response.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S04-01 | positive | R10 | Skip upload is selected as a parameter or branch of the same new-class creation action. | Creation command and single returned class ID. |
| A-S04-02 | positive | R18 | The empty branch creates one usable class owned by Alpha. | Class count and owner ID. Independent recorded observation. |
| A-S04-03 | positive | R12 | An enrolled student initializes a session bound to Empty Seminar despite zero materials. | Selected class and enrollment association. |
| A-S04-04 | failure | R14, R15 | Missing context is reported without claiming the nonexistent document was used. | Zero-resource state and visible abstention/error classification. |

## S05 — Student cross-class resource and AI-context isolation

**Requirement scope:** R05, R14

**Given:** Alpha owns Calculus A with student One enrolled; Beta owns Physics B with student Two enrolled. Both classes contain different synthetic handouts.

**When:** One requests Physics B document bytes and separately attempts to supply the Physics B resource ID as Q&A context.

**Then:** The service rejects both cross-class requests before any document text is delivered to the model.

**Must not:** One must not receive Physics B files, extracted text or protected metadata; a join code is not a substitute for membership.

**Evidence to capture:** Denial decisions, unchanged class-scoped memberships and recorded absence of Physics B content in outbound model context.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S05-01 | negative | R05 | Enrollment in Calculus A does not grant Physics B resource privileges. | Membership data and denied resource request. |
| A-S05-02 | negative | R14 | Reading a resource from Physics B is denied because Student One belongs to Calculus A only. | Zero unauthorized response bytes. |
| A-S05-03 | negative | R14 | Disallowed context cannot reach AI provider. | Authorization decision and outbound context inspection. |

## S06 — Document-grounded Q&A with counterfactual controls

**Requirement scope:** R12, R13, R14, R15

**Given:** Fresh Calculus A has readable allowed `calculus-a.txt`: `For checkpoint Willow-7, the instructor-defined answer is violet compass.` Physics B has readable but inaccessible `physics-b.txt` with the same checkpoint keyed to `copper lantern`. Student One belongs only to Calculus A. The labels are fictional and not derivable from general knowledge.

**When:** Ask “For checkpoint Willow-7, what answer does this class handout prescribe?” in Calculus A Q&A mode. Repeat in an isolated no-context control and a separately authorized Physics B control using another enrolled student. Record selected authorized source and the material actually passed to AI if inspectable.

**Then:** Calculus A answer matches `violet compass`, authorized Physics B answer matches `copper lantern`, and no-context case abstains or states no source. Healthy source selection and passing context must be observed; if the context pathway cannot be inspected, retrieval efficacy is INCONCLUSIVE.

**Must not:** Neither class answer may leak the other class’s marker; generic prior knowledge or source-selection logging alone is not proof that the model causally relied on the supplied content.

**Evidence to capture:** Two synthetic fixture hashes, membership/context authorization, per-run selected text or evidence channel, output comparison and reviewer score (accuracy=2, supported grounding=2).

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S06-01 | positive | R12 | Q&A session remains bound to selected class during all trials. | Session/class mapping and controlled student identities. |
| A-S06-02 | positive | R13 | Q&A mode can be selected explicitly. | Mode transition trace. Independent recorded observation. |
| A-S06-03 | positive | R14 | Authorized class-specific canary content is delivered as model-visible context in healthy trials. | Context payload hash or equivalent instrumentation; BLOCKED/INCONCLUSIVE if unavailable. |
| A-S06-04 | positive | R15 | Outputs match each class’s distinct marker under authorized context, and no-context control does not assert either marker. | Per-class answer transcript, negative control and reviewer rubric. |
| A-S06-05 | negative | R14, R15 | Wrong-class marker and source content do not appear in the other class’s response or context. | Cross-class transcript diff and context audit. |

## S07 — Concept explanation and three answerable exercises

**Requirement scope:** R12, R13, R16

**Given:** Student One is enrolled in a newly created class with zero uploaded files and requests a derivative lesson in concept mode.

**When:** Tutor introduces the linear and power derivative rules, then provides three distinct practice items: d/dx(2x), d/dx(x²), d/dx(3x+1).

**Then:** The explanation is coherent and mathematically accurate. Exactly three distinct answerable exercises appear with expected mathematical outcomes 2, 2x and 3; the practice remains formative.

**Must not:** The tutor must not require a document upload for this proposed concept-mode fixture, invent source citations or record official grades.

**Evidence to capture:** Initial explanation transcript, three-item inventory, independent mathematical review and gradebook state.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S07-01 | positive | R12 | An empty but enrolled classroom can initialize concept interaction. | Session/class binding and material count=0. |
| A-S07-02 | positive | R13 | Concept learning path can be selected independently of Q&A. | Selected tutoring mode. Independent recorded observation. |
| A-S07-03 | positive | R16 | Tutor provides an accurate conceptual explanation before asking questions. | Human-scored explanation against derivative rules. |
| A-S07-04 | positive | R16 | Exactly three distinct practice problems are presented with verifiable answers 2, 2x and 3. | Three exercise prompts, answer-key review and item count. |

## S08 — Wrong practice answer preserves retry state

**Requirement scope:** R17

**Given:** Student One is in concept mode with the three-problem set from S07 independently initialized; the first item is d/dx(2x).

**When:** One submits `1` for the first problem.

**Then:** System explains the correct derivative is 2 and offers retry on the same concept/problem without creating a grade.

**Must not:** Incorrect answer must not be accepted, advance automatically or become an official assessment score.

**Evidence to capture:** Original item, submitted answer, feedback, unchanged current-problem state and gradebook absence.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S08-01 | positive | R17 | Submitted value 1 is correctly identified as an incorrect derivative of 2x, with useful formative feedback. | Reviewed feedback and math oracle. |
| A-S08-02 | positive | R17 | Retry remains available on the same problem and no official grade is created. | Next-step state and gradebook query. |

## S09 — Correct practice answer allows progression

**Requirement scope:** R17

**Given:** Independent initialized concept lesson displays d/dx(2x) as active first item.

**When:** Student One submits the correct value `2` as the derivative answer for the active first item.

**Then:** Answer is accepted as correct and an observable next-problem/next-concept transition becomes available.

**Must not:** Do not mark the true answer wrong or create official course grades.

**Evidence to capture:** Active problem, accepted answer, next-step state and absence of grading side effects.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S09-01 | positive | R17 | The correct answer 2 is accepted with an available next-step transition. | Math oracle, feedback and transition state. |

## S10 — Exam/quiz information, textbook topics, and homework download

**Requirement scope:** R08, R09, R11

**Given:** Alpha owns Calculus A; Beta owns Physics B. Neither a class code nor student enrollment is necessary for professor resource administration.

**When:** Alpha stores exam information (`Midterm 1, week 6`) and quiz information (`Quiz 2, limits`), creates and retrieves three topics Limits, Differentiation, Integration, uploads synthetic `homework-01.pdf` identified as homework, and downloads the saved file.

**Then:** Exam and quiz entries each round-trip without assuming file-only storage. All three topic records persist. Downloaded homework matches its saved SHA-256; Beta is denied access.

**Must not:** No interactive student quiz/grade workflow is implied; Beta must not download Alpha’s material.

**Evidence to capture:** Stored exam and quiz records, three-topic retrieval, homework type and byte hashes, and a denied cross-owner request. Topic ordering controls are deliberately not in V1 acceptance.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S10-01 | positive | R08 | Exam information and quiz material are both stored and retrieved as class-linked data or resources. | Two records/resource views and class associations. |
| A-S10-02 | positive | R09 | Three textbook topics are stored, retrieved and preserved. | Three-item list with names and IDs. |
| A-S10-03 | positive | R11 | Explicit homework-01.pdf downloads byte-for-byte from the correct class. | Document classification and matching SHA-256. |
| A-S10-04 | negative | R11 | Other class owner cannot read/download the homework. | Denied Beta request and no bytes returned. |

## S11 — Malformed upload creates no resource

**Requirement scope:** R06

**Given:** Alpha owns a classroom with N valid resources; a deliberately malformed or unsupported synthetic file is prepared.

**When:** Alpha attempts to upload that file.

**Then:** A safe understandable validation or parsing error appears; resource count stays N; no corrupted file becomes visible.

**Must not:** Do not disclose internal paths or partially commit a bad file.

**Evidence to capture:** Response/error classification and before/after resource count.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S11-01 | failure | R06 | Malformed/unsupported upload is denied without partial storage or leakage. | Response plus unchanged persisted resource inventory. |

## S12 — Previously present material becomes unreadable

**Requirement scope:** R14, R15

**Given:** Student One is authorized in Calculus A. A previously valid document becomes unavailable or unreadable after the class was set up; run a specific failure state separately.

**When:** One asks the AI to quote or use that specific now-unavailable handout.

**Then:** Tutor reports a distinct document-unavailable/processing-error outcome and does not fabricate quotations.

**Must not:** Do not count this as successful healthy grounding or an authorization denial.

**Evidence to capture:** Recorded failure state, context fetch result and user-visible response.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S12-01 | failure | R14 | Unavailable material is not supplied as legitimate source context. | Context attempt and failure classification. |
| A-S12-02 | failure | R15 | No fabricated claim of having quoted inaccessible content. | Response inspection. Independent recorded observation. |

## S13 — Q&A provider outage is contained

**Requirement scope:** R15

**Given:** Valid student session and readable authorized Q&A document; simulate GPT provider timeout/5xx.

**When:** Student submits a Q&A request.

**Then:** User receives a distinct recoverable provider-error state; class files, membership and session remain unchanged.

**Must not:** No invented answer, access-policy bypass or provider tokens in the error message.

**Evidence to capture:** Injected failure, redacted user response and before/after state.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S13-01 | failure | R15 | Q&A outage shows safe explicit error and preserves resources and membership. | Fault flag, response and state diff. |

## S14 — Concept-feedback provider outage is contained

**Requirement scope:** R17

**Given:** Concept mode has active practice item and a submitted answer not yet evaluated; simulate GPT provider timeout/5xx.

**When:** Student requests concept-answer feedback.

**Then:** Feedback reports a recoverable provider-error state and retains the current problem and submitted attempt for retry.

**Must not:** Do not mark the answer wrong/correct without evidence, lose progress or issue an official grade.

**Evidence to capture:** Injected fault, error response, preserved student answer/problem and gradebook check.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S14-01 | failure | R17 | Concept-feedback outage is distinguishable and preserves retry state. | Fault trace and before/after tutor state. |

## S15 — Invalid student/professor sessions and cross-role write denial

**Requirement scope:** R01, R02

**Given:** Separate valid student and professor accounts exist. Prepare missing, expired and malformed sessions for each role, plus a valid student session and a valid professor session. Capture an unchanged class-state snapshot.

**When:** For each invalid student session attempt a private student-dashboard read; for each missing, expired and malformed professor session attempt the private professor dashboard, class creation and a resource write. Attempt professor-only writes with a valid student session, then run the permitted professor operation with valid credentials.

**Then:** Each invalid session is rejected server-side before data access or state changes. Student-role professor writes are denied; a valid professor is able to perform authorized class operations.

**Must not:** Invalid professor credentials or stale sessions must not reach the private professor dashboard, create classes or modify any file; valid student credentials must not confer professor privileges.

**Evidence to capture:** Per-role authentication and rejection records for each missing/expired/malformed session, private response classification, class counts and file hashes before/after denied operations, authorized professor success trace and explicit zero-disclosure review.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S15-01 | negative | R01 | Missing, expired and malformed student session requests cannot access private dashboard data. | Three server-side denial records and zero private response bytes. |
| A-S15-02 | negative | R02 | Authenticated student cannot create a class or mutate professor resources. | Both denied mutations and unchanged persisted state. |
| A-S15-03 | positive | R02 | Valid professor enters the authorized workspace and can perform own-class write. | Role-specific login and successful owned write. |
| A-S15-04 | negative | R02 | Missing, expired and malformed professor credentials/sessions are each denied server-side for professor dashboard access, class creation and resource upload; no class/file state changes or private details leak. | Nine isolated denial observations across three professor session conditions and three professor-only operations, with audit response, class-count diff, resource hash diff and no private bytes. |

## S16 — Professor cross-owner access is denied

**Requirement scope:** R02, R06, R07, R08, R09, R11

**Given:** Alpha and Beta each own different classrooms with own materials and metadata.

**When:** Alpha attempts to edit Beta’s outline, overwrite Beta’s exam/quiz information, modify Beta’s topics, upload into Beta’s class and download Beta’s homework.

**Then:** Every foreign-object read/write attempt is denied at server authorization with no mutation or leaked file.

**Must not:** Ownership checks cannot be bypassed by changing a client-provided class ID.

**Evidence to capture:** Object-owner associations, explicit denial records, no bytes, unchanged foreign-resource state.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S16-01 | negative | R02, R06, R07, R08, R09, R11 | Foreign-owner operations are rejected across each identified resource type. | Per-operation denied response and before/after state. |

## S17 — Integrated class-to-two-bot smoke journey

**Requirement scope:** R01, R02, R03, R05, R12, R13, R14, R15, R16, R17, R18

**Given:** A fresh environment has Alpha and Student One, no classes and no memberships. No tests are asserted to have run historically.

**When:** Alpha authenticates, creates Calculus A, uploads the distinct Willow-7 handout and issues one code. One logs in and joins. One asks the class-canary question in Q&A, then chooses concept learning and receives an explanation plus three problems, submits wrong then correct first answer.

**Then:** Classes, sessions and resources are class-scoped; response matches the permitted canary with observable context; concept explanation and three problems are present; retry and progression work. Detailed corner-case coverage remains in S02–S16.

**Must not:** This integration smoke test may not replace uniqueness, outage, negative-role or class-isolation scenarios; no grade is recorded.

**Evidence to capture:** End-to-end event log, fixture hashes, authorized context record, answer review, three-problem inventory, feedback states and gradebook absence.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S17-00 | positive | R01, R02 | Student and professor both establish valid authenticated sessions before the workflow starts. | Two separate valid server-side role/session records. |
| A-S17-01 | positive | R18, R03, R05 | Class creation, code issuance and one student enrollment work in sequence. | State-transition sequence. Independent recorded observation. |
| A-S17-02 | positive | R12, R13, R14, R15 | Class-specific Q&A returns the Willow-7 canary with source evidence. | Context audit and answer transcript. |
| A-S17-03 | positive | R13, R16, R17 | Concept mode explains the topic, yields three exercises, and handles wrong/correct attempts. | Explanation, item count and feedback transition log. |

## S18 — Reopen existing classroom after a new professor session

**Requirement scope:** R02, R18, R06, R07

**Given:** A fresh isolated test environment has Professors Alpha and Beta. Alpha owns an existing class Calculus A with a saved outline and an uploaded synthetic handout with recorded content hash. Beta owns no part of that existing class.

**When:** Alpha ends the original login session, authenticates again in a new session, selects and reopens the existing class rather than creating it again, reads the saved outline and handout, and compares resource IDs and hashes. Beta then authenticates separately and attempts to select/reopen the same class and read its resources.

**Then:** Alpha reopens the same class ID under the new session, with the same owner and persisted outline and material bytes; the class count and content hashes are unchanged. Beta is denied both class selection and resource reads at the server; its denied requests cause no state changes or disclosure.

**Must not:** The test must not begin with the class already selected in Alpha's new session, accept a duplicate class as successful reopening, reuse a stale authenticated session, or treat UI hiding as proof of Beta authorization denial.

**Evidence to capture:** Persisted class and owner identifiers, logout/new-login session records, pre/post resource hashes and resource IDs, class count, denied Beta access log and before/after state evidence. No historical application test is asserted.

| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |
| --- | --- | --- | --- | --- |
| A-S18-01 | positive | R02, R18, R06, R07 | After a fresh authentication session, Alpha reopens the existing class ID and retrieves the unchanged persisted handout and outline without creating a second class. | Session IDs differ; pre/post class ID and owner match; handout SHA-256 and outline values match; class count unchanged. |
| A-S18-02 | negative | R02, R18 | Beta is denied access when selecting or reopening the class owned by Alpha, and cannot read its private resources. | Server-side denial logs for class selection and direct resource requests; no response bytes, owner or resource mutations. |

## Execution record — blank template

For each assertion record: Sxx ID and A-Sxx-yy ID, commit/build, execution date, reviewer, initial isolated fixture state, action, observed outcome, server authorization or AI context evidence, rubric score if applicable, PASS/FAIL/BLOCKED/INCONCLUSIVE/NOT RUN, and defect reference. **No original-system tests were executed for this portfolio.**
