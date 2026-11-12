# Diagram quality and semantic review

**Purpose:** SVG/XML validation does not prove that connectors, labels or flow semantics are correct. Use this manual publication-review checklist alongside `python3 tools/check_docs.py`. All eight diagrams (five detailed, three compact overviews) are newly authored conceptual reconstructions, not original product screenshots or verified deployment topology.

## Every diagram: reviewer checklist

- [ ] Render the SVG in a real browser or vector renderer at full size and approximately 900-pixel viewing width.
- [ ] Verify no text clipping, overlaps, inaccessible tiny labels, confusing crossings or low-contrast text.
- [ ] Follow each directed edge and check whether it represents a mandatory dependency, branch, or optional operation.
- [ ] Compare labels and sequence to the written requirement and relevant original PRD/timeline section.
- [ ] Confirm every proposed security/data-flow behavior is marked as conceptual; no diagram asserts actual infrastructure deployments or executed tests.
- [ ] Re-render after any substantive source or requirements change.

## Recorded rendering / inspection evidence

| Review item | Status | Evidence and limits |
| --- | --- | --- |
| Two compact SVGs at desktop width | **Completed, 2026-11-11** | `professor-overview.svg` and `student-overview.svg` separately rendered to 900-pixel PNGs and visually inspected for text fit, contrast and connectors; documentation QA reviewer role, not employer sign-off |
| Two compact SVGs at narrow mobile width | **Completed, 2026-11-11** | Both rendered to 390-pixel PNGs and visually inspected for readable labels and parallel/optional branch meaning; review previews supplied separately from public-source archive |
| Five detailed original V6 SVGs | **Carried forward from V6 review** | Previously rendered and examined at 1,200 pixels; the detailed versions remain for zoomable inspection, not inline-mobile display |
| Actual GitHub web and mobile rendering | **Pending publication review** | No public repository exists; inspect on GitHub after a separate repository-publication instruction, before external promotion |
| Employer source / intellectual-property clearance | **Assumed granted by owner, 2026-11-12** | No employer approval letter is included; does not imply endorsement |

The compact professor figure shows **independent optional** content/code actions. The compact student figure shows **alternative** Q&A/concept branches. Both link to the full detailed SVGs in `docs/workflows.md`. Retaining a compact summary and separately zoomable detail avoids forcing 10-point text into a 390-pixel-wide viewport.

## Diagram-by-diagram expected semantics

| Diagram | Required human interpretation | Source / caution |
| --- | --- | --- |
| `system-overview.svg` | Compact, mobile-readable relationship summary from both user roles into the platform, which accesses authorized resources and AI service; refer to detailed system context for data returns and boundaries. | Conceptual overview only, not physical deployment |
| `professor-overview.svg` | Mobile-readable professor sign-in, class creation/selection, optional content, independent optional join-code issuance. | Summary only; detailed professor workflow remains authoritative for branching |
| `student-overview.svg` | Mobile-readable sign-in, enrollment and alternative tutoring modes, including three practice tasks. | Summary only; detailed student workflow retains retry paths and feedback stages |
| `system-context.svg` | Student/professor messages reach conceptual platform services; authorized course-context request and return; AI request, model reply and student reply are bidirectional as appropriate. | Reported React/Flask/GPT-4/S3/EC2 stack; backend boundaries reconstructed, not verified deployment |
| `professor-workflow.svg` | Professor creates a single owned class; selecting skip-upload is a branch within creation; resource operations and code issuance are separate **optional** operations. Only the code issuance branch enables later joining. | PRD p. 5 professor diagram and §2.2; source `.dot` under `diagrams/source/` |
| `student-workflow.svg` | Login → code validation → enrollment → choose tutor mode; invalid login/code is a retry/denial path; subject Q&A and concept learning remain distinct. | PRD p. 5 student diagram; original implementation authorization unspecified |
| `ai-interaction.svg` | Course-specific context is authorized before use; Q&A and concept evaluation return to the student; empty/unavailable context is not a healthy-answer success. | Proposed architecture based on PRD §§2.2–2.3; no proof of actual model prompt or retrieval mechanism |
| `delivery-roadmap.svg` | Six-week plan progresses from requirements/auth through class resources and two tutoring modes; Week 6 explicitly includes **planned integration and QA execution**, not merely planning. | Six-week timeline is not an execution log |

## Reviewer record — this package revision

**Compact system overview:** The new `system-overview.svg` is hand-authored vector content with 15–20 px labels and a 520-unit viewBox, inspected after rendering at mobile and desktop widths. The detailed system-context SVG remains linked in the README for zoom and implementation boundaries. **Previous detailed-diagram review:** All five detailed SVGs were rendered at 1,200 pixels and inspected in a contact sheet and individually for legibility, arrow direction and source-consistent sequencing. The AI diagram now explicitly labels concept-context availability as optional. This visual inspection is not evidence of the original application implementation. A future publisher should repeat the checklist for the final GitHub-rendered assets; the preceding table records what is completed and what remains pending.

**Limit:** Browser-specific fonts and line wrapping can differ. If a GitHub-rendered SVG has clipping or unreadable labels, treat publication as blocked until corrected.

**Reproducibility note:** The professor DOT source and its committed SVG describe the same reviewed directed edges. The strict checker requires Graphviz to render the DOT successfully and compares graph topology. A particular Graphviz version may place text differently; byte-identical SVG output is not a release requirement. The eight committed SVGs remain approved content hashes in the single release manifest. Visual review at mobile widths and the hosted GitHub renderer is a separate human presentation check.

## V18 final local diagram review

All eight conceptual SVGs are unchanged in meaning from the previously rendered V16 release. During V18 local QA they were parsed, their expected directed edges were checked, and their compact overviews were rendered at narrow and desktop widths. No original-app screenshots or historically deployed topology is claimed. Final GitHub-specific rendering can only be checked after separately authorized publication; it is a post-publication validation step, not evidence of an unresolved source defect.
