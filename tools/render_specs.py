#!/usr/bin/env python3
"""Render human-readable requirements, scenarios and oracle coverage from canonical JSON.

No claims about the historical application's quality or execution are made.
Run from any directory: python3 tools/render_specs.py
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load() -> tuple[list[dict], list[dict]]:
    req = json.loads((ROOT / 'data/requirements.json').read_text(encoding='utf-8'))['requirements']
    cases = json.loads((ROOT / 'data/acceptance-cases.json').read_text(encoding='utf-8'))['scenarios']
    return req,cases


def quote(value: str) -> str:
    return value.replace('|', '\\|').replace('\n', ' ')


def render() -> dict[str,str]:
    req, cases = load()
    used = defaultdict(list)
    covered = defaultdict(lambda: defaultdict(list))
    for c in cases:
        for a in c['assertions']:
            for rid in a['requirements']:
                if c['id'] not in used[rid]:
                    used[rid].append(c['id'])
                covered[rid][a['kind']].append(a['id'])
    trace = [
      '# Requirements traceability and acceptance design',
      '',
      '**Evidence boundary:** The original PRD and six-week roadmap establish **planned V1 functions**, not proof of historical implementation, acceptance or deployment. The component groupings, dependencies, acceptance oracles and scenarios here are **newly proposed**. Roles and source locators are grounded in the original PRD when specified. The R18 row is extracted from its professor flowchart.',
      '',
      'This table is generated verbatim from [`data/requirements.json`](../data/requirements.json) and [`data/acceptance-cases.json`](../data/acceptance-cases.json) by [`tools/render_specs.py`](../tools/render_specs.py). A changed material field without regeneration fails the checker. Reviewed semantic-field digests in the checker require an explicit independent review when regenerated canonical data changes. Those fingerprints prevent silent drift but cannot establish the truth of a newly reviewed specification.',
      '',
      '`Prerequisites` means an enabling capability must precede another capability. It does **not** imply a separate click/transaction in every flow. The R10 skip-upload option is **an alternative branch of R18 creation**, not a post-creation requirement; both require professor authentication and R10 has no R18 prerequisite.',
      '',
      '## Source-to-acceptance matrix',
      '',
      '| ID | Actor / capability | Original source locator | Conceptual component | Prerequisites | Proposed acceptance oracle | Scenario IDs |',
      '| --- | --- | --- | --- | --- | --- | --- |'
    ]
    for r in req:
        deps = ', '.join(r['dependencies']) or 'None'
        use = ', '.join(used[r['id']]) or '**MISSING**'
        fields=[r['id'],f"{r['actor']} — {r['capability']}",r['source'],r['component'],deps,r['acceptance'],use]
        trace.append('| '+' | '.join(quote(f) for f in fields)+' |')
    trace += [
      '',
      '## Sequencing and conditional states',
      '',
      '- **Class creation:** R02 enables a single R18 creation event. R10 selects its no-upload branch during that same event; neither class code nor material upload is prerequisite to creating an empty classroom.',
      '- **Independent professor operations:** R03 class-code issuance and R06–R09/R11 material management require class existence. Issuing a code is optional until student enrollment is needed.',
      '- **Student enrollment:** R01 plus issued class code support R04 validation and R05 enrollment. A join code is not an ongoing content-access credential.',
      '- **Tutoring:** R05 → R12 → R13 then either R14 → R15 for Q&A, or R16 → R17 for concept practice. The concept path does not depend on Q&A-specific document retrieval.',
      '- **Source data states:** class existence, enrollment, authorization, material presence, material readability and provider availability are separate controls. Missing material and provider outage do not satisfy healthy Q&A.',
      '- **Original diagram:** the concept learner prepares **three practice problems**, retained in R16 as a specified interaction detail. Reconstructed tests are prospective and have never run against the original implementation.',
      '',
      '## What assertion coverage means',
      '',
      'Every requirement is assigned a concrete, observable **positive oracle**, and relevant denial/failure paths are tracked separately. [Assertion-level coverage](acceptance-coverage.md) maps IDs to outcomes. This is a **proposed test specification**, not test results, and structural checking alone does not validate an AI explanation or model grounding.',
      '',
      '## Evidence qualifications',
      '',
      'Source references point to the original private PRD/plan without redistributing employer documents. Requirements R01–R17 summarize documented V1 features; R18 makes classroom creation explicit from the professor flowchart. The timeline is a plan rather than execution evidence. Individual responsibilities and functional-MVP completion are the project lead’s first-hand report, not independently established by these documents. See [provenance](provenance.md) and [attribution](../ATTRIBUTION.md).',
      ''
    ]
    scen = [
      '# Synthetic acceptance scenarios — proposed, not executed',
      '',
      '**Status:** These are prospective tests designed for an implementation that can expose sufficient state and contextual evidence. No original application code, test run or deployment records were available. Do not label any scenario PASS until executed and reviewed against a real approved build.',
      '',
      '**Isolation:** Each Sxx starts in a fresh isolated state; fixtures are intentionally recreated for that case. A class, student enrollment, code, document or permission given in S01 is **not** presumed to exist in S02. Every test must record its own initial class IDs and sessions. Assertions below are proposed acceptance oracles, not historical observations.',
      '',
      '**Counterfactual Q&A fixtures (fictional):** In Calculus A, `calculus-a.txt` says “For checkpoint Willow-7, the instructor-defined answer is violet compass.” In Physics B, `physics-b.txt` uses the same checkpoint but says “copper lantern.” These invented facts are intentionally not general knowledge and are only used for controlled QA. Both source bodies must remain inside authorized test classes.',
      '',
      '**Grounding rubric:** Independently score output accuracy and permitted-document support as 0 (fails), 1 (partial) or 2 (fully correct and supported). S06 and the Q&A leg of S17 require **both score 2** plus inspected evidence of authorized model-visible context, the correct class marker and a no-context or swapped-class control. If content observability is unavailable, the grounding outcome is **INCONCLUSIVE**, even when a response happens to be correct. Such evidence supports the tested grounding behavior; it cannot demonstrate perfect causal dependence on a document for all model outputs.',
      '',
      '**Concept rubric:** Independently inspect the introductory mathematical explanation and verify **three distinct solvable** practice problems and their answer keys (2, 2x, 3 for the specified derivative prompts). Wrong and correct responses have separate state-transition tests. This is formative interaction, not historical proof of grading accuracy.',
      '',
      '**Test-result vocabulary:** PASS, FAIL, BLOCKED, INCONCLUSIVE, NOT RUN. A subcase requiring collision injection or AI context instrumentation is BLOCKED/INCONCLUSIVE if the build cannot support it; it must never be silently recorded as PASS.',
      ''
    ]
    for c in cases:
        scen += [
           f"## {c['id']} — {c['title']}",
           '',
           f"**Requirement scope:** {', '.join(c['requirements'])}",
           '',
           f"**Given:** {c['given']}",
           '',
           f"**When:** {c['when']}",
           '',
           f"**Then:** {c['then']}",
           '',
           f"**Must not:** {c['must_not']}",
           '',
           f"**Evidence to capture:** {c['evidence']}",
           '',
           '| Assertion ID | Mode | Requirement(s) | Independent oracle | Evidence |',
           '| --- | --- | --- | --- | --- |'
        ]
        for a in c['assertions']:
            scen.append('| '+' | '.join(map(quote,[a['id'],a['kind'],', '.join(a['requirements']),a['oracle'],a['evidence']]))+' |')
        scen.append('')
    scen += [
      '## Execution record — blank template',
      '',
      'For each assertion record: Sxx ID and A-Sxx-yy ID, commit/build, execution date, reviewer, initial isolated fixture state, action, observed outcome, server authorization or AI context evidence, rubric score if applicable, PASS/FAIL/BLOCKED/INCONCLUSIVE/NOT RUN, and defect reference. **No original-system tests were executed for this portfolio.**',
      ''
    ]
    cov=[
     '# Assertion-level coverage map',
     '',
     '**Generated prospective coverage, not executed results.** Each positive assertion identifies an observable expected outcome; negative assertions test denial/isolation, and failure assertions test degradation/recovery. Merely listing assertions does not prove they are implemented or that their oracles are valid: a reviewer must execute and inspect them.',
     '',
     'Source of truth: [`data/requirements.json`](../data/requirements.json) and [`data/acceptance-cases.json`](../data/acceptance-cases.json). Detailed setups, actions and evidence appear in [the synthetic scenarios](../examples/synthetic-acceptance-scenarios.md).',
     '',
     '| Requirement | Positive assertion IDs | Negative assertion IDs | Failure assertion IDs |',
     '| --- | --- | --- | --- |'
    ]
    for r in req:
      rid=r['id']; k=covered[rid]
      fields=[rid,', '.join(k.get('positive',[])) or 'None',', '.join(k.get('negative',[])) or 'None',', '.join(k.get('failure',[])) or 'None']
      cov.append('| '+' | '.join(fields)+' |')
    cov += ['',f'**Specification inventory:** {len(req)} requirements, {len(cases)} scenarios, {sum(len(c["assertions"]) for c in cases)} atomic proposed assertions. These are test design counts, not executed test counts.','', '## Review gate', '', 'Before treating coverage as meaningful, check each assertion’s initial state, independent action, expected result, prohibited side effect, evidence channel and eligibility for PASS. Validate source fidelity (including the three-problem learning flow), allow manual mathematical and AI-rubric review, and report BLOCKED/INCONCLUSIVE when observation is impossible.','']
    risk=json.loads((ROOT/'data/risk-scenarios.json').read_text(encoding='utf-8'))
    riskdoc=[
       '# Prospective risk-control acceptance tests', '',
       '**Status: PROPOSED, NOT EXECUTED.** These four tests elaborate K03/K04/K09/K11 in the '
       '[risk register](validation-and-risk.md). They are not V1 feature-completion or historical QA claims; '
       'they require an authorized test implementation and independently inspected evidence.', '',
       'These tests deliberately remain separate from the main source-derived V1 acceptance scenarios. '
       'If the required interface or observability is absent, record **BLOCKED** or **INCONCLUSIVE**, not PASS.', ''
    ]
    for c in risk['cases']:
       riskdoc.extend([
           f"## {c['id']} — {c['title']} ({c['risk_id']})",'',
           f"**Fixture:** {c['fixture']}",'',
           f"**Action:** {c['action']}",'',
           f"**Proposed pass/uncertainty oracle:** {c['oracle']}",'',
           f"**Evidence to collect:** {c['evidence']}",'',
           f"**Status:** {c['status']}",'',
       ])
    riskdoc.extend(['## Execution and approval record','',
      'For each risk case record build, tester, date, exact setup and actions, observations, evidence location, '
      'PASS/FAIL/BLOCKED/INCONCLUSIVE/NOT RUN and reviewer approval. '
      'No original classroom application was exercised to create these scenarios.',''])
    return {
       'docs/risk-acceptance-tests.md':'\n'.join(riskdoc),
       'docs/traceability.md':'\n'.join(trace),
       'examples/synthetic-acceptance-scenarios.md':'\n'.join(scen),
       'docs/acceptance-coverage.md':'\n'.join(cov)
    }


def main() -> None:
    for relative,text in render().items():
        p=ROOT/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
        print(f'Wrote {relative} ({len(text)} chars)')

if __name__=='__main__':
    main()
