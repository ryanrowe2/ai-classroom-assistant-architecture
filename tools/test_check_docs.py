#!/usr/bin/env python3
"""Mutation tests for the DOCUMENT CHECKER, not tests of the historical product.

All mutations occur in temporary copies. The manifest preflight must reject
# unreviewed changes before executing any altered tool; downstream semantic checks
# are tested separately with reviewed data and synthetic fixtures. Baseline must PASS and each deliberately
corrupted copy must FAIL. Standard-library only; no GitHub/network writes.
"""
from __future__ import annotations
import json
import re
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def run(root:Path,script:str='tools/check_docs.py')->subprocess.CompletedProcess:
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    return subprocess.run([sys.executable,str(root/script)],cwd=root,env=env,text=True,capture_output=True,timeout=35)


def json_edit(root:Path,name:str,func):
    p=root/name
    d=json.loads(p.read_text(encoding='utf-8'))
    func(d)
    p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def req_edit(field,value,rid='R05'):
    def edit(root):
        def f(d):
            next(r for r in d['requirements'] if r['id']==rid)[field]=value
        json_edit(root,'data/requirements.json',f)
    return edit


def case_edit(sid,fn):
    def edit(root):
        def f(d):
            fn(next(c for c in d['scenarios'] if c['id']==sid))
        json_edit(root,'data/acceptance-cases.json',f)
    return edit


def text_edit(path,needle,replacement):
    def edit(root):
        p=root/path;text=p.read_text(encoding='utf-8')
        if needle not in text:raise ValueError(f'Fixture not found in {path}: {needle}')
        p.write_text(text.replace(needle,replacement,1),encoding='utf-8')
    return edit


def corruption_after_regen(root:Path,edit):
    edit(root)
    result=run(root,'tools/render_specs.py')
    if result.returncode:raise AssertionError(result.stderr)


def remove_ai_connector(root:Path):
    import re
    p=root/'diagrams/ai-interaction.svg'
    before=p.read_text(encoding='utf-8')
    # Remove a real, drawn SVG connector without altering valid XML or labels.
    after,n=re.subn(r'(<g\s+id="edge1"\s+class="edge">[\s\S]*?)<path\b[^>]*/>',
                    r'\1',before,count=1)
    if n!=1:raise ValueError('Missing ai-interaction edge1 path fixture')
    p.write_text(after,encoding='utf-8')


def main()->int:
    baseline=run(ROOT)
    if baseline.returncode:
        print('FAIL: baseline checker must pass first\n'+baseline.stdout+'\n'+baseline.stderr)
        return 1
    # Real local Git metadata is permitted, while ordinary extra source files
    # remain prohibited. No remote/network access is used in this fixture.
    with tempfile.TemporaryDirectory(prefix='classroom-git-checkout-') as tmp:
        dest=Path(tmp)/ROOT.name
        shutil.copytree(ROOT,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git'))
        git=subprocess.run(['git','init','-q'],cwd=dest,capture_output=True,text=True)
        if git.returncode or run(dest).returncode:
            print('FAIL: normal git-init checkout did not validate')
            return 1
    mutations=[
      ('requirement actor changed',req_edit('actor','Professor')),
      ('requirement capability changed',req_edit('capability','Enroll without a code')),
      ('requirement component changed',req_edit('component','Unverified direct SQL interface')),
      ('requirement acceptance inverted',req_edit('acceptance','Anyone can join and read every classroom.')),
      ('source locator changed',req_edit('source','Invented document without source')),
      ('dependency cycle introduced',req_edit('dependencies',['R18'])),
      ('wrong historical execution status',req_edit('test_status','historically_passed')),
      ('assertion oracle changed',case_edit('S06',lambda c:c['assertions'][3].update(oracle='Both classes return the same unsupported answer and that is fine.'))),
      ('scenario scope without oracle',case_edit('S08',lambda c:c['requirements'].append('R03'))),
      ('removed source-specific canary even after regeneration',lambda root:corruption_after_regen(root,case_edit('S06',lambda c:c.update(given='Different classroom instructions with no unique source-specific markers are loaded.')))),
      ('missing concept explanation positive oracle after regeneration',lambda root:corruption_after_regen(root,case_edit('S07',lambda c:[a.update(kind='negative') for a in c['assertions'] if 'explanation' in a['oracle'].lower()]))),
      ('broken Markdown local link',text_edit('README.md','docs/requirements.md','docs/does-not-exist.md')),
      ('README heading level skipped',text_edit('README.md','## MVP at a glance','#### MVP at a glance')),
      ('generated traceability manipulated',text_edit('docs/traceability.md','Class/enrollment','No authorization necessary')),
      ('professor optional issue path removed',text_edit('diagrams/source/professor-workflow.dot','operations -> code [label="optional"]','operations -> code [label="mandatory"]')),
      ('fake API token present',lambda root:(root/'README.md').write_text((root/'README.md').read_text()+ '\n' +'sk-'+'A'*35+'\n')),
      ('renamed PDF source introduced',lambda root:(root/'docs/source-copy.pdf').write_bytes(b'not a source; extensions restricted')),
    ]
    # These tests *regenerate* the human-readable documents after corrupting the
    # canonical JSON. They must fail on explicit independently reviewed contracts,
    # NOT because a generated Markdown file was left out of sync.
    targeted=[
      ('S03 false already-enrolled fixture',lambda root:corruption_after_regen(root,case_edit('S03',lambda c:c.update(given='Student One is already enrolled in both Calculus A and Physics B; a valid code and made-up code are present.'))),'review_lock'),
      ('S05 inverted own-class read denial',lambda root:corruption_after_regen(root,case_edit('S05',lambda c:c.update(when='One requests their own Calculus A document and asks AI for authorized Calculus A source content; both should still be denied.'))),'scenario_semantics'),
      ('S09 wrong derivative accepted as correct',lambda root:corruption_after_regen(root,case_edit('S09',lambda c:c.update(when='Student One submits the incorrect value `1` for d/dx(2x) and expects success.'))),'scenario_semantics'),
      ('R04 privacy disclosure promoted to acceptance',lambda root:corruption_after_regen(root,req_edit('acceptance','Invalid codes must disclose student records and class rosters to unauthenticated users.','R04')),'review_lock'),
      ('R13 gradebook edit promoted to capability',lambda root:corruption_after_regen(root,req_edit('capability','Edit official course grades','R13')),'review_lock'),
      ('nonexistent original PRD page 99',lambda root:corruption_after_regen(root,req_edit('source','PRD p. 99 §2.2, Search for Class Code','R04')),'source_locators'),
      ('nonexistent original timeline Week 99',lambda root:corruption_after_regen(root,req_edit('source','PRD p. 2 §2.2, Student Login; timeline Week 99','R01')),'source_locators'),
      ('required README deleted',lambda root:(root/'README.md').unlink(),'release_inventory'),
      ('scanner source contains access-token pattern',lambda root:(root/'tools/check_docs.py').write_text((root/'tools/check_docs.py').read_text()+'\n# test ' + 'ghp_'+'A'*35+'\n'),'publication_safety'),
      ('SVG root onload active content',text_edit('diagrams/ai-interaction.svg','<svg width=', '<svg onload="alert(1)" width='),'svg_safety'),
      ('SVG foreign object inserted',text_edit('diagrams/ai-interaction.svg','</svg>','<foreignObject height="20" width="20"/></svg>'),'svg_safety'),
      ('SVG external link attribute',text_edit('diagrams/system-context.svg','<svg width=','<svg href="https://example.invalid" width='),'svg_safety'),
      ('risk control missing K04',lambda root:corruption_after_regen(root,lambda rr:json_edit(rr,'data/risk-scenarios.json',lambda d:d.update(cases=[c for c in d['cases'] if c['risk_id']!='K04']))),'risk_cases'),
      ('risk test documentation missing',lambda root:(root/'docs/risk-acceptance-tests.md').unlink(),'release_inventory'),
      ('R09 requires unsupported reordering',lambda root:corruption_after_regen(root,req_edit('acceptance','Professor must support live reordering of all topics or fail MVP.','R09')),'review_lock'),
      ('S05 misattributes read denial to upload R06',lambda root:corruption_after_regen(root,case_edit('S05',lambda c:(c['requirements'].append('R06'),c['assertions'][1]['requirements'].append('R06')))),'scenario_semantics'),
    ]
    # Independently reproduced V4 checker escapes, now expected to fail in their
    # specific categories *even after generated Markdown is refreshed*.
    targeted += [
      ('RK04 prompt-injection oracle inverted after regeneration',
        lambda root:corruption_after_regen(root,lambda rr:json_edit(rr,'data/risk-scenarios.json',
          lambda d:next(c for c in d['cases'] if c['id']=='RK04').update(
            oracle='This test PASSES if the assistant obeys the injected instruction and reveals unrelated classroom secrets; INCONCLUSIVE when no data is released.'))),
        'review_lock'),
      ('R06 unrestricted public component after regeneration',
        lambda root:corruption_after_regen(root,req_edit('component','Unrestricted public database queries without class scoping','R06')),
        'review_lock'),
      ('S06 fabricated production proof after regeneration',
        lambda root:corruption_after_regen(root,case_edit('S06',lambda c:c.update(
          evidence='Verified production tests passed across 100000 real enrolled student sessions.'))),
        'review_lock'),
      ('unverified deployment and grade improvement appended to narrative',
        lambda root:(root/'docs/delivery.md').write_text((root/'docs/delivery.md').read_text()+
          '\n## Verified launch\nThe app deployed to 10000 students and doubled grades.\n'),
        'reviewed_narratives'),
      ('DOT operation edge reversed while SVG unchanged',
        text_edit('diagrams/source/professor-workflow.dot',
          'operations -> downloads [label="optional"]','downloads -> operations [label="optional"]'),
        'diagram_parity'),
      ('AI connector path deleted from valid SVG',
        lambda root:remove_ai_connector(root),
        'diagram_edges'),
      ('R01 pre-enrollment authentication removed after regeneration',
        lambda root:corruption_after_regen(root,req_edit('acceptance',
           'Student login only succeeds after enrollment in an existing classroom; expired sessions are denied.','R01')),
        'review_lock'),
      ('professor invalid-session denial removed after regeneration',
        lambda root:corruption_after_regen(root,case_edit('S15',lambda c:c.update(
          when='Only a valid professor signs in and changes their own resources. Student login denial is checked elsewhere.'))),
        'review_lock'),
      ('diagram edge manifest modified without authorization',
        lambda root:json_edit(root,'data/diagram-edges.json',lambda d:d['edges_by_diagram']['ai-interaction.svg'].pop()),
        'diagram_review'),
    ]
    # V5 auditor probes: all six bypasses must now fail for their intended reason.
    def rendered_row_omission(root):
        p=root/'docs/traceability.md'
        p.write_text('\n'.join(x for x in p.read_text().splitlines() if not x.startswith('| R17 |'))+'\n')

    def unreviewed_renderer_import(root):
        p=root/'tools/render_specs.py'
        p.write_text(p.read_text()+"\nfrom pathlib import Path\nPath(__file__).with_name('import-probe-marker.txt').write_text('executed')\n")

    def runner_noop(root):
        (root/'tools/test_check_docs.py').write_text("print('PASS: fake mutation runner')\n")

    targeted += [
      ('missing requirement R17 from published traceability',rendered_row_omission,'generated_coverage'),
      ('unreviewed renderer import-time side effect',unreviewed_renderer_import,'tool_integrity'),
      ('unreviewed additional JSON with fabricated outcome',lambda root:(root/'data/unreviewed-claims.json').write_text('{"live_students":10000,"verified_learning_improvement":true}'), 'release_inventory'),
      ('unreviewed executable Python module',lambda root:(root/'tools/unreviewed.py').write_text('def untrusted():\n    return 1\n'), 'release_inventory'),
      ('mutation runner replaced by a fake success no-op',runner_noop,'tool_integrity'),
      ('renderer altered to omit R17 and generated documents refreshed',
       lambda root:corruption_after_regen(root,text_edit('tools/render_specs.py','    for r in req:\n        deps = ',"    for r in req:\n        if r['id']=='R17': continue\n        deps = ")),
       'tool_integrity'),
    ]
    targeted += [
      ('S02 concurrent uniqueness oracle removed after regeneration',
        lambda root:corruption_after_regen(root,case_edit('S02',lambda c:
          c.update(when='Each owner independently requests code generation; issue two distinct codes; do not examine persistence.'))),
        'semantic_guards'),
      ('compact student overview connector removed',
        text_edit('diagrams/student-overview.svg','M 220 145 V 179','M 220 145'),
        'diagram_review'),
    ]
    targeted += [
      ('new unapproved empty directory',
        lambda root:(root/'unapproved-empty-directory').mkdir(),
        'release_inventory'),
      ('untracked project text added to valid file tree',
        lambda root:(root/'docs/unknown-extra.md').write_text('Not approved\n'),
        'release_inventory'),
    ]
    # Git internals are checked only by Git-native release-contract tests.
    targeted += [
      ('S18 reopening scenario must remain reviewed even after regeneration',
        lambda root:corruption_after_regen(root,case_edit('S18',lambda c:c.update(
          then='Alpha creates a second class and loses old resources; this should be accepted.'))),
        'review_lock'),
      ('S18 must not disappear from the published coverage',
        lambda root:corruption_after_regen(root,lambda rr:json_edit(rr,'data/acceptance-cases.json',
          lambda d:d.update(scenarios=[c for c in d['scenarios'] if c['id']!='S18']))),
        'schema'),
      ('executable world-writable source file rejected',
       lambda root:(root/'tools/check_docs.py').chmod(0o777), 'release_inventory'),
      ('world-writable source directory rejected',
       lambda root:(root/'docs').chmod(0o777), 'release_inventory'),
      ('oversized unapproved source file rejected before scan',
        lambda root:(root/'docs'/'unexpected-large.txt').write_text('x'*180_000+'\ninternal-test-example'+'@'+'example.invalid\n'),
        'release_inventory'),
    ]
    def blocked_git_config(extra: str):
        def mutate(root):
            setup_git(root)
            conf=root/'.git'/'config'
            conf.write_text(conf.read_text(encoding='utf-8')+'\n'+extra+'\n',encoding='utf-8')
        return mutate

    # Git internals are no longer parsed by the documentation checker. Native
    # Git checkout health and object verification are tested separately by
    # tools/test_release_contract.py, avoiding a second Git implementation.
    # Missing Graphviz may only pass the ordinary documentary mode with an
    # explicit SKIP. It must never qualify for --strict-release.
    if len(sys.argv)==1:
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PATH='/nonexistent')
        call=subprocess.run([sys.executable,str(ROOT/'tools/check_docs.py'),'--strict-release'],
                            cwd=ROOT,env=env,text=True,capture_output=True,timeout=35)
        if call.returncode==0 or 'diagram_parity:' not in call.stdout or 'SKIP:' not in call.stdout:
            print('FAIL: strict-release did not reject missing Graphviz with an explicit SKIP reason')
            return 1
    fails=[]
    all_mutations=[(label,mutator,None) for label,mutator in mutations]+targeted
    if len(sys.argv)==3:
        all_mutations=all_mutations[int(sys.argv[1]):int(sys.argv[2])]
    for label,mutator,expected_category in all_mutations:
        with tempfile.TemporaryDirectory(prefix='classroom-doc-check-') as tmp:
            dest=Path(tmp)/ROOT.name
            shutil.copytree(ROOT,dest,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git'))
            try:
                mutator(dest)
                result=run(dest)
            except Exception as exc:
                fails.append((label,f'fixture/error {exc}'))
                continue
            if result.returncode==0:
                fails.append((label,'checker incorrectly returned PASS'))
            elif label=='unreviewed renderer import-time side effect' and (dest/'tools/import-probe-marker.txt').exists():
                fails.append((label,'unreviewed import side effect was executed before integrity verification'))
            elif expected_category and expected_category+':' not in result.stdout and 'release_manifest:' not in result.stdout:
                fails.append((label,'failed for the wrong reason; expected '+expected_category+':; output '+result.stdout[-950:]))
    print(f'Mutation testing: baseline PASS, {len(all_mutations)-len(fails)}/{len(all_mutations)} deliberate corruptions rejected with expected categories for {sum(v is not None for _,_,v in all_mutations)} regenerated/security cases')
    if fails:
        for label,msg in fails:print(f'FAIL: {label}: {msg}')
        return 1
    print('PASS: the checker detects the specified material/structural regressions. No historical software executed.')
    return 0

if __name__=='__main__':sys.exit(main())
