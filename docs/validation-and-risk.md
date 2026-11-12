# Validation strategy and risk register

**Evidence boundary:** No historical source code, application build, automated-test output, bug log, release checklist or deployment logs were available for this review. The checks below specify **what should be validated against an implementation**, not what has been tested or proven in the original application.

## Acceptance layers

| Layer | Example checks | Success evidence if later executed |
| --- | --- | --- |
| Requirements | Trace all 18 V1 capability rows to source, actors, prerequisites and assertion-level positive oracles; reject dependency cycles | Reviewed [traceability matrix](traceability.md), [oracle coverage](acceptance-coverage.md) and structured JSON specs |
| Role/access | Student cannot upload; professor cannot act on foreign class | Denied API operation and no state mutation |
| Course isolation | Class A's student cannot retrieve Class B's file or tutor context | Rejected resource request and independent context test |
| Enrollment | Valid join, unknown/invalid-code denial, duplicate membership; separate optional revocation lifecycle test | Correct state and non-disclosing error |
| Resource lifecycle | Upload, empty class, update, download, invalid type, error | Correct access/availability and recoverability |
| AI behavior | Healthy Q&A requires a class-specific synthetic checkpoint with swapped-class and no-context controls; concept mode explains a topic and gives three practice problems; test retry and advancement | Model-visible context observation, output contrasts, math review and two separate 0–2 AI rubric scores |
| Integration | Professor creates class/material → student enrolls → AI modes function | End-to-end run with recorded observations |
| Operational | Provider timeout, document-processing error, interrupted upload | Graceful error and no unauthorized content exposure |

## Prioritized risk register — prospective architecture review

| ID | Risk | Severity | Evidence or uncertainty | Proposed mitigation / test |
| --- | --- | --- | --- | --- |
| K01 | Cross-class content exposure | Critical | PRD lacks access rules beyond role flows | Server-side membership/ownership checks on every resource/context retrieval |
| K02 | Unauthorized professor mutations | High | Role-based UI described, enforcement mechanism unknown | Authorization matrix, API negative tests, object ownership tests |
| K03 | Class-code enumeration or reuse | High | Code generation/search/join in scope; lifecycle unspecified | Guess-resistant codes, throttling, non-disclosing lookup; optional proposed revocation/renewal lifecycle |
| K04 | Prompt injection via uploaded class files | High | Course document content intended as AI context | Separate trusted instructions from untrusted documents; adversarial fixture tests |
| K05 | Hallucinated course facts | High | No grounding implementation documented | Context fidelity rubric, uncertainty language, avoid fake sources |
| K06 | Misleading practice evaluation | High | Model can evaluate answers; grading policy unknown | Human review, ambiguous answer handling, no official-grade claims |
| K07 | Student data exposure/retention | High | Privacy/data handling unspecified | Data inventory, legal/institutional review, minimization, deletion policy |
| K08 | Unusable malformed/unsupported uploads | Medium | Upload capability defined, formats/limits undefined | Validation, safe parser errors, status reporting |
| K09 | Material freshness mismatch | Medium | Update paths exist, propagation to AI undefined | Edit a resource, verify later tutor queries use permitted current context |
| K10 | GPT-4 failure or delayed response | Medium | External model integration reported | Timeout/retry and user-facing recoverability tests |
| K11 | Placeholder functionality misrepresented | Medium | Full UI with future placeholders explicitly planned | Confirm unavailable features are labeled and not accessible |
| K12 | Unverified release claims | High | No deployment or adoption records | Avoid production/user/scale claims; seek evidence before asserting |

Severity expresses **potential consequence**, not a claim that these defects occurred in the delivered MVP.

## Example quality oracles

For a reviewer to accept future test results, each case should state the **setup**, **request**, **expected observable behavior**, **forbidden behavior**, and **evidence captured**. Examples:

- **Isolation:** Two classes have contradictory subject material. When an enrolled student asks a question in Class A, the assistant must not expose Class B's text or treat Class B as its source.
- **Code abuse:** Entering an unknown class code never returns course files, member lists, or professor contact details.
- **No course material:** A class created without uploads remains usable, but the tutor must not falsely say it consulted nonexistent teaching documents.
- **Practice correction:** An ambiguous response triggers clarification or qualified feedback; it is not silently marked as an official grade.
- **Third-party outage:** An AI provider error is distinguishable from a student authorization denial and does not leak internal configuration.

### Proposed, observable AI acceptance gate

The healthy Q&A test **must** return the class-specific `Willow-7` marker from the readable authorized synthetic document (distinct from another class), compare a no-context control and inspect the material actually supplied as model-visible context when possible. An unavailable-document message fails the healthy test; missing, unreadable and provider-outage cases are separate tests. For variable wording, a reviewer scores **accuracy** and **permitted-source grounding** from 0 to 2; both must receive **2**. Absent evidence of model-visible context, the retrieval-grounding result is **INCONCLUSIVE**, even if the generated wording is correct; observing context and the correct answer still does not establish universal causal reliance. For concept practice, independently verify a correct explanation plus **three distinct answerable exercises**, then test wrong-answer/retry and correct-answer/progression as distinct observable transitions, with the mathematical correctness of the fixed exercise verified by a reviewer. No official grades are inferred.

Detailed [synthetic acceptance scenarios](../examples/synthetic-acceptance-scenarios.md) specify the independent fixtures, failure states and capture fields; no application run is claimed.

## Prospective persistent class-code uniqueness test (not executed)

The PRD asks for unique class codes but does not identify the storage engine or atomic generation strategy. Two nonmatching generated codes are only a smoke test, **not** evidence of a uniqueness guarantee. Before claiming robust uniqueness in a future implementation, require an enforced uniqueness invariant over the complete set of committed active codes (for example a database uniqueness constraint or an equivalently atomic transaction), exercise forced candidate collisions, overlap simultaneous issuance across independent classes, and compare all persisted codes after a restart. Verify that retries or explicit conflicts never commit the same code for two classes. A concurrency run without conflict injection and backing-state evidence cannot establish a race-safe guarantee. If the original application or instrumented environment is unavailable, record this test as **BLOCKED**; no historical implementation claim follows.

## Independent documentation QA

The repository itself can be checked without access to application code: execute `python3 tools/check_docs.py` to validate rendered specifications against structured data, Markdown links, SVG XML, exact requirement set `R01–R18`, dependencies/acyclicity, substantive oracle references, expected scenario structure, independently reviewed semantic-field fingerprints, five-page source-locator bounds, required files, SVG active-content restrictions and high-confidence publication-safety patterns (including self-scanning). Run `python3 tools/test_check_docs.py` for mutation-test coverage. **This is documentation QA, not historical application testing.** [Visual diagram review](diagram-review.md), mathematical/model rubric quality and final public-facing wording still require human review; employer disclosure permission is treated as granted on the owner’s stated premise. The fingerprint lock requires deliberate review and update for any canonical behavior change; it is **not** a semantic theorem prover or a cryptographic signature from the employer. Structural checks cannot prove semantic correctness or independently attest legal authorization. Audit results are supplied in a **separate** review report.

## Definition of done for a future implementation audit

An audit of the *application* would require the code/build, environment details, permission to examine them, and reproducible end-to-end cases. This documentary portfolio cannot certify software security, model quality, code correctness, platform operations or production readiness.

## Prospective adversarial and lifecycle cases (not executed)

See [risk acceptance tests](risk-acceptance-tests.md) for separately scoped **K03 join-code enumeration**, **K04 uploaded-document prompt injection**, **K09 material freshness**, and **K11 deferred-feature placeholders**. These are proposed security/quality gates, not historical V1 acceptance results or evidence of deployed controls. An uninstrumented run is `INCONCLUSIVE` or `BLOCKED`, never `PASS`.
