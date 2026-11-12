#!/usr/bin/env python3
"""Check prospective portfolio *documents*, not original application behavior.

Validates internal links, generated artifacts, source/requirement shape,
assertion coverage, dependency semantics, SVG structure and high-confidence
publication-safety patterns. This cannot replace human technical, legal or
visual review. Python 3.10+ standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
import hashlib
import os
import stat
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
CHECKS: Counter[str] = Counter()
ISSUES: list[str] = []
SKIPPED: list[str] = []
STRICT_RELEASE = False
EXPECTED = {f'R{i:02d}' for i in range(1,19)}
ALLOWED_EXTENSIONS = {'.md','.json','.svg','.py','.dot','.yml',''}
# This manifest is an inventory, not a trust root. Independently verify the
# release ZIP digest before executing this in-repository script.
MANIFEST_PATH = ROOT / 'release/source-manifest.json'
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
APPROVED_PATHS = tuple(sorted(set(MANIFEST['files']) | {'release/source-manifest.json'}))

# This pins tool dependencies BEFORE they are imported. This source tree must be authenticated using the independent release checksum
# before its Python is executed.
REVIEWED_TOOL_HASHES = {
    rel: digest for rel, digest in MANIFEST['files'].items()
    if rel.startswith('tools/') and rel.endswith('.py') and rel != 'tools/check_docs.py'
}

# Source-control internals are not portfolio release artifacts. A *normal* Git
# metadata directory may coexist with an otherwise exact approved source tree.
# No extra source files/directories are allowed, including untracked files.
def allowed_source_directories() -> set[str]:
    return {'/'.join(Path(rel).parts[:n])
            for rel in APPROVED_PATHS
            for n in range(1, len(Path(rel).parts))}


SOURCE_FILE_MAX_BYTES = 160_000
SOURCE_TOTAL_MAX_BYTES = 3_000_000


def metadata_dir_is_valid() -> bool:
    """Only exclude Git's metadata from source inventory.

    Git health and tracked-blob integrity are certified independently using
    Git native fsck/status/ls-tree commands, not by parsing Git internals here.
    """
    dotgit = ROOT / '.git'
    return (not dotgit.exists() and not dotgit.is_symlink()) or (
        dotgit.is_dir() and not dotgit.is_symlink()
    )


def unsafe_posix_mode(path: Path, *, directory: bool) -> bool:
    """Reject executable/source files, world-write and special POSIX bits.

    On Windows the OS does not expose reliable POSIX permissions; the separately
    distributed archive verifier checks the UNIX mode metadata in source ZIPs.
    """
    if os.name != 'posix':
        return False
    bits=stat.S_IMODE(path.lstat().st_mode)
    if bits & (0o5002 if directory else 0o7002):
        return True
    if directory:
        return (bits & 0o500) != 0o500
    return not (bits & 0o400) or bool(bits & 0o111)


def reviewed_worktree_entries() -> tuple[set[str],set[str],list[str]]:
    """Walk the source once, explicitly pruning top-level .git before descent."""
    files=set(); dirs=set(); unsafe=[]
    if unsafe_posix_mode(ROOT,directory=True):
        unsafe.append('Unsafe repository-root permissions')
    for current,subdirs,filenames in os.walk(ROOT,topdown=True,followlinks=False):
        directory=Path(current)
        if directory==ROOT and '.git' in subdirs:
            subdirs.remove('.git')
        for name in list(subdirs):
            entry=directory/name; relative=entry.relative_to(ROOT).as_posix()
            if entry.is_symlink() or not entry.is_dir():
                unsafe.append('Unsafe directory: '+relative)
                subdirs.remove(name)
            else:
                if unsafe_posix_mode(entry,directory=True):
                    unsafe.append('Unsafe directory permissions: '+relative)
                dirs.add(relative)
        for name in filenames:
            entry=directory/name; relative=entry.relative_to(ROOT).as_posix()
            if entry.is_symlink() or not entry.is_file():
                unsafe.append('Nonregular file: '+relative)
            else:
                if unsafe_posix_mode(entry,directory=False):
                    unsafe.append('Unsafe file permissions: '+relative)
                files.add(relative)
    if not metadata_dir_is_valid():
        unsafe.append('Invalid .git top-level metadata directory (Git health is checked separately)')
    return files,dirs,unsafe

# Reviewed-field digests pin *human-reviewed* semantic baselines independently of
# generated Markdown. Editing canonical JSON AND rerendering docs does not bypass
# this gate. Updating any fingerprint requires explicit source/fixture review.
REVIEWED_REQUIREMENTS = MANIFEST['contracts']['requirements']
REVIEWED_SCENARIOS = MANIFEST['contracts']['scenarios']
REVIEW_FIELDS_REQ = ('actor', 'capability', 'source', 'component', 'dependencies', 'acceptance', 'status', 'test_status')
REVIEW_FIELDS_CASE = ('title', 'requirements', 'given', 'when', 'then', 'must_not', 'evidence', 'assertions')
REVIEW_FIELDS_RISK = ('risk_id', 'title', 'fixture', 'action', 'oracle', 'evidence', 'status')
REVIEWED_RISK_SCENARIOS = MANIFEST['contracts']['risk_scenarios']
_GENERATED_DOCS = {
    'docs/traceability.md', 'docs/acceptance-coverage.md',
    'docs/risk-acceptance-tests.md', 'examples/synthetic-acceptance-scenarios.md'
}
REVIEWED_NARRATIVES = {
    rel: digest for rel, digest in MANIFEST['files'].items()
    if rel.endswith('.md') and rel not in _GENERATED_DOCS
}
REVIEWED_DIAGRAMS = {
    rel: digest for rel, digest in MANIFEST['files'].items()
    if rel.endswith(('.svg', '.dot'))
}
REVIEWED_EDGE_MANIFEST = MANIFEST['files']['data/diagram-edges.json']

def fingerprint(obj, fields):
    payload={k:obj[k] for k in fields}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf8')).hexdigest()

ALLOWED_KINDS = {'positive','negative','failure'}
VALID_RESULT_WORDS = ('NOT RUN','INCONCLUSIVE','BLOCKED')


def check(ok: bool, message: str, category: str) -> None:
    CHECKS[category] += 1
    if not ok:
        ISSUES.append(f'{category}: {message}')


def safe_read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def slug(text: str) -> str:
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    text = text.replace('`','')
    return re.sub(r'[^a-z0-9_\- ]','',text.casefold()).replace(' ','-')


def anchors(text: str) -> set[str]:
    known: set[str] = set()
    duplicates: Counter[str] = Counter()
    for header in re.findall(r'^#{1,6}\s+(.+?)\s*#*\s*$',text,flags=re.M):
        base=slug(header); n=duplicates[base]; duplicates[base]+=1
        known.add(base if n==0 else f'{base}-{n}')
    return known


def validate_links_and_headings() -> None:
    for file in sorted(ROOT/rel for rel in APPROVED_PATHS if rel.endswith('.md')):
        content=safe_read(file)
        headers=[len(match.group(1)) for match in re.finditer(r'^(#{1,6})\s+', content, re.M)]
        check(not headers or headers[0]==1, f'{file.relative_to(ROOT)} first heading should be level 1','headings')
        check(all(b<=a+1 for a,b in zip(headers,headers[1:])),f'{file.relative_to(ROOT)} heading level skip','headings')
        for match in re.finditer(r'!?\[[^\]\n]+\]\(([^\n)]+)\)',content):
            dest=match.group(1).strip().strip('<>')
            if dest.startswith(('https://','http://','mailto:')):
                continue
            pathpart,_,frag=dest.partition('#')
            target=(file.parent/unquote(pathpart)).resolve() if pathpart else file
            valid=target.is_relative_to(ROOT) and target.exists()
            check(valid,f'{file.relative_to(ROOT)} broken/escaping link {dest}','local_links')
            if valid and frag and target.suffix.lower()=='.md':
                check(unquote(frag) in anchors(safe_read(target)),f'{file.relative_to(ROOT)} invalid anchor {dest}','local_links')


def validate_required_paths() -> None:
    required = {
      'README.md','ATTRIBUTION.md','data/requirements.json',
      'data/acceptance-cases.json','data/risk-scenarios.json',
      'data/diagram-edges.json',
      'docs/requirements.md','docs/traceability.md','docs/acceptance-coverage.md',
      'docs/provenance.md','docs/publication-safety.md','docs/validation-and-risk.md',
      'docs/evidence-register.md','docs/review-protocol.md',
      'docs/risk-acceptance-tests.md','examples/synthetic-acceptance-scenarios.md',
      'tools/check_docs.py','tools/render_specs.py','tools/test_check_docs.py',
      'tools/build_release.py','tools/verify_sources.py','tools/test_release_contract.py',
      'release/source-manifest.json','docs/release-verification.md','RIGHTS.md',
      '.gitattributes','.github/workflows/validate.yml',
      'diagrams/source/professor-workflow.dot',
    } | {f'diagrams/{name}.svg' for name in (
       'system-context','professor-workflow','student-workflow','ai-interaction','delivery-roadmap')}
    for name in sorted(required):
        check((ROOT/name).is_file(),f'missing mandatory release artifact: {name}','required_paths')
    # A navigable README is a substantive portfolio requirement.
    p=ROOT/'README.md'
    if p.is_file():
        value=safe_read(p)
        for name in ('docs/requirements.md','docs/system-architecture.md',
                     'docs/traceability.md','docs/risk-acceptance-tests.md',
                     'docs/evidence-register.md','docs/review-protocol.md',
                     'ATTRIBUTION.md','docs/publication-safety.md'):
            check(name in value,f'README navigation omits {name}','required_paths')


def validate_release_integrity() -> bool:
    """Reject unreviewed files and executable tool changes before importing renderer."""
    files,dirs,unsafe=reviewed_worktree_entries()
    approved=set(APPROVED_PATHS)
    expected_dirs=allowed_source_directories()
    inventory_ok=files==approved and dirs==expected_dirs and not unsafe
    check(files==approved,
          'file inventory changed: added='+str(sorted(files-approved))+'; missing='+str(sorted(approved-files)),
          'release_inventory')
    check(dirs==expected_dirs,
          'directory inventory changed: added='+str(sorted(dirs-expected_dirs))+'; missing='+str(sorted(expected_dirs-dirs)),
          'release_inventory')
    check(not unsafe,'unsafe worktree entries: '+str(unsafe),'release_inventory')
    good=inventory_ok
    total=0
    for relative in sorted(files & approved):
        entry=ROOT/relative
        size=entry.stat().st_size
        total+=size
        check(size<=SOURCE_FILE_MAX_BYTES,
              f'{relative} exceeds permitted source-file byte limit', 'release_inventory')
        good &= size<=SOURCE_FILE_MAX_BYTES
    check(total<=SOURCE_TOTAL_MAX_BYTES, 'approved-source bytes exceed total limit', 'release_inventory')
    good &= total<=SOURCE_TOTAL_MAX_BYTES
    if not good:
        return False  # fail closed before opening arbitrary or oversized source files
    for relative, approved_sha in MANIFEST['files'].items():
        entry = ROOT / relative
        verified = entry.is_file() and not entry.is_symlink() and hashlib.sha256(entry.read_bytes()).hexdigest() == approved_sha
        check(verified, f'{relative}: file differs from reviewed release manifest', 'release_manifest')
        good &= verified
    for relative,approved_sha in REVIEWED_TOOL_HASHES.items():
        path=ROOT/relative
        ok=path.is_file() and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==approved_sha
        check(ok,relative+' executable source changed from manifest; independent review required', 'tool_integrity')
        good &= ok
    return good


def independent_generated_coverage() -> None:
    """Check generated table membership and cells without invoking render_specs."""
    data=json.loads(safe_read(ROOT/'data/requirements.json'))['requirements']
    cases=json.loads(safe_read(ROOT/'data/acceptance-cases.json'))['scenarios']
    risk=json.loads(safe_read(ROOT/'data/risk-scenarios.json'))['cases']
    def quoted(x):
        return str(x).replace('|','\\|').replace('\n',' ')
    def rows(relative,regex):
        source=safe_read(ROOT/relative)
        lines=[line for line in source.splitlines() if re.match(regex,line)]
        values=[]
        for line in lines:
            cells=[z.strip().replace('\\|','|') for z in re.split(r'(?<!\\)\|',line.strip())][1:-1]
            values.append(cells)
        return values
    expected_ids=[r['id'] for r in data]
    trace=rows('docs/traceability.md',r'^\| R\d\d \|')
    cover=rows('docs/acceptance-coverage.md',r'^\| R\d\d \|')
    check([r[0] for r in trace]==expected_ids,'traceability must contain every canonical requirement exactly once and in order','generated_coverage')
    check([r[0] for r in cover]==expected_ids,'acceptance coverage must contain every canonical requirement exactly once and in order','generated_coverage')
    used=defaultdict(list); categorized=defaultdict(lambda:defaultdict(list))
    expected_assertions=[]
    for c in cases:
        for a in c['assertions']:
            expected_assertions.append([a['id'],a['kind'],', '.join(a['requirements']),a['oracle'],a['evidence']])
            for rid in a['requirements']:
                if c['id'] not in used[rid]:used[rid].append(c['id'])
                categorized[rid][a['kind']].append(a['id'])
    for i,r in enumerate(data):
        if i>=len(trace) or i>=len(cover):break
        expected_row=[r['id'],r['actor']+' — '+r['capability'],r['source'],r['component'],', '.join(r['dependencies']) or 'None',r['acceptance'],', '.join(used[r['id']]) or '**MISSING**']
        check(trace[i]==expected_row,f'{r["id"]} traceability cell content differs from independently computed expectation','generated_coverage')
        expcov=[r['id']]+[', '.join(categorized[r['id']].get(k,[])) or 'None' for k in ('positive','negative','failure')]
        check(cover[i]==expcov,f'{r["id"]} coverage cell content differs from independently computed expectation','generated_coverage')
    scenario_text=safe_read(ROOT/'examples/synthetic-acceptance-scenarios.md')
    headings=re.findall(r'^## (S\d{2}) — ',scenario_text,re.M)
    check(headings==[c['id'] for c in cases],'scenario headings omitted, duplicated or reordered','generated_coverage')
    assertions=rows('examples/synthetic-acceptance-scenarios.md',r'^\| A-S\d\d-\d\d \|')
    check(assertions==expected_assertions,'scenario assertion rows differ from canonical assertions or are incomplete','generated_coverage')
    risk_text=safe_read(ROOT/'docs/risk-acceptance-tests.md')
    for match in re.finditer(r'\b(\d+)\s+(?:source-derived V1 |main )?acceptance scenarios\b',risk_text,re.I):
        check(int(match.group(1))==len(cases),
              'stale narrative acceptance-scenario count: '+match.group(0), 'generated_coverage')
    check('the main source-derived V1 acceptance scenarios' in risk_text,
          'risk document should use a count-neutral scenario reference', 'generated_coverage')
    risk_headings=re.findall(r'^## (RK\d{2}) — ',risk_text,re.M)
    check(risk_headings==[c['id'] for c in risk],'risk case headings omitted, duplicated or reordered','generated_coverage')


def validate_generated_docs() -> None:
    # All executable dependencies have been fingerprint-checked before reaching here.
    from render_specs import render
    generated=render()
    for name,expected in generated.items():
        p=ROOT/name
        check(p.is_file(),f'generated doc missing {name}','generated_docs')
        if p.is_file():
            check(safe_read(p)==expected,f'{name} differs from canonical requirement/assertion data; run tools/render_specs.py','generated_docs')


def validate_requirements() -> tuple[dict,list[dict]]:
    obj=json.loads(safe_read(ROOT/'data/requirements.json'))
    check(obj.get('schema_version')==2,'requirements schema_version must be 2','schema')
    req_list=obj.get('requirements',[])
    ids=[r.get('id') for r in req_list]
    req={r['id']:r for r in req_list if isinstance(r,dict) and isinstance(r.get('id'),str)}
    check(len(ids)==len(req)==18 and set(ids)==EXPECTED,'requirement identifiers must be unique R01..R18','schema')
    necessary={'id','actor','capability','source','component','dependencies','acceptance','status','test_status'}
    for r in req_list:
        rid=r.get('id','?')
        check(set(r)==necessary, f'{rid} unexpected/missing requirement keys {set(r)^necessary}', 'schema')
        for field in ('actor','capability','source','component','acceptance'):
            check(isinstance(r.get(field),str) and len(r[field].strip())>=5,f'{rid} {field} empty or invalid','schema')
        check(r.get('status')=='historical_planned_V1' and r.get('test_status')=='prospective_not_executed',f'{rid} claim status changed','provenance')
        check(isinstance(r.get('dependencies'),list) and len(set(r['dependencies']))==len(r['dependencies']) and r['id'] not in r['dependencies'] and set(r['dependencies'])<=EXPECTED,f'{rid} invalid prerequisites','dependencies')
        check(('PRD p.' in r['source'] or 'timeline Week' in r['source']),f'{rid} insufficient source locator','provenance')
        pages=[int(x) for x in re.findall(r'\bp\.\s*(\d+)',r['source'])]
        weeks=[int(x) for x in re.findall(r'\bWeek\s*(\d+)',r['source'],re.I)]
        check(bool(pages),f'{rid} missing original PRD page reference','source_locators')
        check(all(1<=p<=5 for p in pages),f'{rid} claims nonexistent PRD page(s): {pages}','source_locators')
        check(all(1<=w<=6 for w in weeks),f'{rid} claims nonexistent timeline week(s): {weeks}','source_locators')
        approved=REVIEWED_REQUIREMENTS.get(rid)
        check(bool(approved) and fingerprint(r,REVIEW_FIELDS_REQ)==approved,
              f'{rid} reviewed semantic contract changed; independently review primary source and refresh lock deliberately',
              'review_lock')

    color:dict[str,int]={}
    def dfs(u:str,trail:list[str]):
        if color.get(u)==1:
            check(False,'dependency cycle: '+' -> '.join(trail+[u]),'dependencies');return
        if color.get(u)==2:return
        color[u]=1
        for v in req[u]['dependencies']:
            if v in req:dfs(v,trail+[u])
        color[u]=2
    for rid in sorted(req):dfs(rid,[])
    check(all(color.get(i)==2 for i in req),'incomplete DAG traversal','dependencies')
    exact_deps={
       'R01':[],'R02':[],'R03':['R18'],'R04':['R01','R03'],'R05':['R04'],
       'R06':['R18'],'R07':['R18'],'R08':['R18'],'R09':['R18'],
       'R10':['R02'],'R11':['R18'],'R12':['R05'],'R13':['R12'],
       'R14':['R13'],'R15':['R14'],'R16':['R13'],'R17':['R16'],'R18':['R02']
    }
    for rid,dependencies in exact_deps.items():
        check(req.get(rid,{}).get('dependencies')==dependencies,f'{rid} unexpected capability prerequisite structure','dependencies')
    guard={
     'R01':('Student',('invalid','session','cannot')),
     'R02':('Professor',('student','server-denied','no state change')),
     'R03':('Professor',('two','distinct','resource access')),
     'R05':('Student',('one membership','idempotent')),
     'R08':('Professor',('exam/quiz information','no live student quiz')),
     'R09':('Professor',('multiple','ordering')),
     'R10':('Professor',('alternate R18 creation path','not a second')),
     'R14':('Student/Q&A',('authorized','missing/denied')),
     'R15':('Student/Q&A',('synthetic canary','no-context','provider outage')),
     'R16':('Student/concept',('three-problem','explanation')),
     'R17':('Student/concept',('Incorrect','correct','no official grade')),
     'R18':('Professor',('alternative','creation operation')),
    }
    for rid,(actor,phrases) in guard.items():
        if rid not in req:continue
        check(req[rid]['actor']==actor,f'{rid}: role changed unexpectedly','semantic_guards')
        joined=req[rid]['capability']+' '+req[rid]['acceptance']
        for term in phrases:
            check(term.casefold() in joined.casefold(),f'{rid} missing important acceptance constraint: {term}','semantic_guards')
    return req,req_list


def validate_scenarios(req:dict) -> None:
    obj=json.loads(safe_read(ROOT/'data/acceptance-cases.json'))
    check(obj.get('schema_version')==1,'acceptance scenario schema_version must be 1','schema')
    cases=obj.get('scenarios',[])
    caseids=[c.get('id') for c in cases]
    expected_cases={f'S{i:02d}' for i in range(1,19)}
    check(len(caseids)==len(set(caseids))==18 and set(caseids)==expected_cases,'unexpected/duplicate scenario IDs','schema')
    observed_ids=[]; req_types=defaultdict(set)
    assert_required={'id','requirements','kind','oracle','evidence'}
    case_required={'id','title','requirements','given','when','then','must_not','evidence','assertions'}
    for c in cases:
        cid=c['id']
        approved=REVIEWED_SCENARIOS.get(cid)
        check(bool(approved) and fingerprint(c,REVIEW_FIELDS_CASE)==approved,
              f'{cid} reviewed fixture/action/oracle changed; independent fixture review required',
              'review_lock')
        check(set(c)==case_required,f'{cid} missing/extra scenario properties','schema')
        check(set(c['requirements'])<=EXPECTED and len(c['requirements'])==len(set(c['requirements'])),f'{cid} invalid requirement scope','scenario_coverage')
        for field in ('title','given','when','then','must_not','evidence'):
            check(isinstance(c.get(field),str) and len(c[field].strip())>=25,f'{cid} {field} missing meaningful detail','scenario_coverage')
        mapped=[]
        for a in c.get('assertions',[]):
            aid=a['id']
            observed_ids.append(aid)
            check(set(a)==assert_required,f'{aid} assertion missing/extra properties','schema')
            check(bool(re.fullmatch(r'A-'+cid+r'-\d{2}',aid)),f'{aid} malformed assertion ID for {cid}','schema')
            check(a['kind'] in ALLOWED_KINDS,f'{aid} invalid assertion category','scenario_coverage')
            check(isinstance(a['requirements'],list) and bool(a['requirements']) and set(a['requirements'])<=EXPECTED,f'{aid} invalid requirements','scenario_coverage')
            for field in ('oracle','evidence'):
                check(isinstance(a.get(field),str) and len(a[field].strip())>=30,f'{aid} {field} missing substantive oracle','scenario_coverage')
            for rid in a['requirements']:
                req_types[rid].add(a['kind'])
                mapped.append(rid)
        check(set(mapped)==set(c['requirements']),f'{cid} advertised requirement coverage differs from its atomic assertions','scenario_coverage')
    check(len(observed_ids)==len(set(observed_ids)),'duplicate assertion IDs','schema')
    for rid in EXPECTED:
        check('positive' in req_types[rid],f'{rid} lacks positive test oracle','scenario_coverage')
    for rid in ('R01','R02','R03','R04','R05','R06','R11','R14'):
        check('negative' in req_types[rid],f'{rid} lacks applicable negative test oracle','scenario_coverage')
    for rid in ('R06','R14','R15','R17'):
        check('failure' in req_types[rid],f'{rid} lacks failure oracle','scenario_coverage')
    byid={c['id']:c for c in cases}
    for sid,phrases in {
       'S02':('two','distinct','collision','concurrent','restart','BLOCKED'),
       'S06':('violet compass','copper lantern','no-context','model-visible','INCONCLUSIVE'),
       'S07':('three','2x','3x+1','explanation'),
       'S10':('three','homework-01.pdf','SHA-256'),
       'S13':('Q&A','timeout'),
       'S14':('Concept','timeout'),
       'S15':('expired','malformed','professor-only'),
       'S18':('new session','reopen','persisted','Beta','denied'),
    }.items():
        if sid not in byid:continue
        txt=json.dumps(byid[sid],ensure_ascii=False)
        for phrase in phrases:
            check(phrase.casefold() in txt.casefold(),f'{sid} key coverage missing {phrase}','semantic_guards')
    # These independently reviewed invariants are necessary conditions, not proofs
    # that a free-text description constitutes a complete executable test.
    for sid,expected_scope in {
       'S02':{'R03'},'S03':{'R01','R04','R05'},
       'S05':{'R05','R14'},'S08':{'R17'},
       'S09':{'R17'},'S10':{'R08','R09','R11'}
    }.items():
        check(set(byid[sid]['requirements'])==expected_scope,
              f'{sid} incorrectly maps an unrelated capability or a fixture to a result',
              'scenario_semantics')
    for sid,field,required in [
       ('S03','given',('not enrolled in either','Calculus A','Physics B')),
       ('S05','given',('One enrolled','Physics B')),
       ('S05','when',('requests Physics B document','Physics B resource ID')),
       ('S05','then',('rejects both cross-class requests',)),
       ('S09','given',('d/dx(2x)',)),
       ('S09','when',('correct value `2`','derivative answer')),
       ('S09','then',('accepted as correct','next-problem')),
    ]:
        for phrase in required:
            check(phrase.casefold() in byid[sid][field].casefold(),
                  f'{sid}.{field} reviewed logical condition missing: {phrase}',
                  'scenario_semantics')
    # High-value case contracts bind the oracle to the *right field and polarity*.
    # These guards target regressions exposed by earlier independent audits.
    critical_fields={
      'S02':{'given':('neither class has a join code',),'when':('independently requests code generation','force a code-candidate collision','issue many codes concurrently'),'then':('distinct','every committed code','restart','BLOCKED')},
      'S06':{'given':('violet compass','copper lantern'),'when':('no-context control','Physics B control'),'then':('violet compass','copper lantern','INCONCLUSIVE')},
      'S07':{'when':('three distinct practice','2x','x²','3x+1'),'then':('Exactly three','explanation')},
      'S10':{'when':('three topics','homework-01.pdf'),'then':('round-trip','SHA-256')},
      'S13':{'when':('Q&A request',),'then':('provider-error',)},
      'S14':{'when':('concept-answer feedback',),'then':('provider-error',)},
      'S15':{'when':('missing, expired','professor session','valid student session'),'then':('server-side',)},
      'S18':{'given':('Alpha','Beta','existing class','saved outline'),'when':('new session','reopen','Beta'), 'then':('persisted','denied','unchanged')},
    }
    for sid,fields in critical_fields.items():
        c=byid.get(sid)
        if c is None:continue
        for field,terms in fields.items():
            for term in terms:
                check(term.casefold() in c[field].casefold(),f'{sid}.{field} missing required verified-contract phrase {term}','semantic_guards')
    def exact_oracle(sid:str,rid:str,kind:str,term:str)->bool:
        return any(a['kind']==kind and rid in a['requirements'] and term.casefold() in a['oracle'].casefold() for a in byid[sid]['assertions'])
    for sid,rid,kind,term in [
       ('S02','R03','positive','distinct usable codes'),
       ('S02','R03','failure','concurrent issuance'),
       ('S06','R14','positive','model-visible context'),
       ('S06','R15','positive','no-context'),
       ('S07','R16','positive','conceptual explanation'),
       ('S07','R16','positive','Exactly three distinct'),
       ('S10','R09','positive','Three textbook topics'),
       ('S10','R11','positive','homework-01.pdf'),
       ('S13','R15','failure','Q&A outage'),
       ('S14','R17','failure','Concept-feedback outage'),
       ('S15','R01','negative','expired'),
       ('S15','R02','negative','student cannot'),
       ('S15','R02','negative','Missing, expired and malformed professor'),
       ('S03','R01','positive','zero classes'),
       ('S18','R18','positive','reopens the existing class'),
       ('S18','R18','negative','Beta is denied access'),
    ]:
        check(exact_oracle(sid,rid,kind,term),f'{sid}: missing {kind} oracle for {rid}: {term}','semantic_guards')
    check('NOT RUN' in safe_read(ROOT/'examples/synthetic-acceptance-scenarios.md'),'must state non-execution of prospective tests','provenance')


def validate_risk_scenarios() -> None:
    p=ROOT/'data/risk-scenarios.json'
    data=json.loads(safe_read(p))
    check(data.get('schema_version')==1 and data.get('status')=='proposed_not_executed',
          'risk cases must be proposed-only with schema version 1','risk_cases')
    cases=data.get('cases',[])
    check({c.get('risk_id') for c in cases}=={'K03','K04','K09','K11'},
          'missing/duplicate important risk-control case','risk_cases')
    check(len(cases)==4 and len({c.get('id') for c in cases})==4,'risk IDs not unique','risk_cases')
    expected={'id','risk_id','title','fixture','action','oracle','evidence','status'}
    for c in cases:
        check(set(c)==expected,f'{c.get("id")} unexpected risk case shape','risk_cases')
        check(c.get('status')=='proposed_not_executed',
              f'{c.get("id")} cannot represent executed risk outcome','risk_cases')
        check(REVIEWED_RISK_SCENARIOS.get(c.get('id')) == fingerprint(c, REVIEW_FIELDS_RISK),
              f'{c.get("id")} reviewed risk-control oracle or case changed; human security review required',
              'review_lock')
        for key in ('fixture','action','oracle','evidence'):
            check(len(c.get(key,''))>=45,f'{c.get("id")} missing {key} evidence','risk_cases')
        check(any(v in c.get('oracle','') for v in ('BLOCKED','INCONCLUSIVE')),
              f'{c.get("id")} must define uncertainty policy','risk_cases')
    text=safe_read(ROOT/'docs/risk-acceptance-tests.md')
    for c in cases:
        check(c['id'] in text and c['risk_id'] in text,
              f'{c["id"]} omitted from generated risk cases','risk_cases')


def validate_svg() -> None:
    svg_files=sorted((ROOT/'diagrams').glob('*.svg'))
    check(len(svg_files)==8,f'expected five detailed and three compact SVG diagrams; got {len(svg_files)}','svg')
    for file in svg_files:
        try:
            tree=ET.parse(file)
            svg=tree.getroot()
            check(svg.tag.endswith('}svg') and bool(svg.attrib.get('viewBox')),f'{file.name} missing valid root/viewBox','svg')
            rendered_text=' '.join(e.text or '' for e in svg.iter() if e.tag.endswith('}text'))
            check(len(rendered_text)>=40,f'{file.name} likely lacks readable labels','svg')
            raw=safe_read(file)
            check(not re.search(r'<!\s*(?:DOCTYPE|ENTITY)\b',raw,re.I),
                  f'{file.name} DTD/entity declaration is prohibited','svg_safety')
            tags={'svg','g','title','path','polygon','polyline','rect','circle','ellipse','text','defs'}
            attrs={'width','height','viewBox','baseProfile','version','fill','stroke',
                   'stroke-width','stroke-dasharray','x','y','cx','cy','r','rx','ry',
                   'font-size','font-weight','font-family','text-anchor','id','class',
                   'transform','d','points'}
            bad_tags=[];bad_attrs=[];bad_values=[]
            for elem in svg.iter():
                local=elem.tag.rsplit('}',1)[-1]
                if local not in tags:bad_tags.append(local)
                for attr,val in elem.attrib.items():
                    attr_local=attr.rsplit('}',1)[-1]
                    if attr_local not in attrs or attr_local.lower().startswith('on') or attr.lower().endswith('}href'):
                        bad_attrs.append(attr)
                    if re.search(r'(?:url\s*\(|javascript:|data:|https?://)',val,re.I):
                        bad_values.append(attr)
            check(not bad_tags,f'{file.name} unsafe SVG elements {bad_tags[:4]}','svg_safety')
            check(not bad_attrs,f'{file.name} unsafe SVG attributes {bad_attrs[:4]}','svg_safety')
            check(not bad_values,f'{file.name} unsafe SVG values {bad_values[:4]}','svg_safety')
        except (ET.ParseError,OSError) as exc:
            check(False,f'{file.name} invalid SVG: {exc}','svg')
    professor=safe_read(ROOT/'diagrams/professor-workflow.svg')
    for phrase in ('Independent optional class operations','Choose skip upload','if student enrollment needed'):
        check(phrase in professor, f'professor diagram missing optionality statement: {phrase}','diagram_labels')
    context=safe_read(ROOT/'diagrams/system-context.svg')
    for phrase in ('request class data','permitted data / no context','tutoring request','output / error','response / error'):
        check(phrase in context,f'system-context diagram missing leg: {phrase}','diagram_labels')
    for name,phrase in [('ai-interaction.svg','3 practice tasks'),('student-workflow.svg','3 practice problems'),('student-overview.svg','Explain, 3 tasks'),('professor-overview.svg','Join code')]:
        check(phrase in safe_read(ROOT/'diagrams'/name),f'{name} missing source-prescribed three-problem learning detail','diagram_labels')
    compact=safe_read(ROOT/'diagrams/system-overview.svg')
    check('Classroom platform' in compact and 'Course materials' in compact and 'AI learning service' in compact, 'compact system overview missing architecture roles', 'diagram_labels')
    roadmap=safe_read(ROOT/'diagrams/delivery-roadmap.svg')
    check('Integration + QA execution' in roadmap,'roadmap Week 6 QA execution absent','diagram_labels')
    dot=ROOT/'diagrams/source/professor-workflow.dot'
    check(dot.is_file() and 'operations -> code [label="optional"]' in safe_read(dot),'professor editable source missing independent option','svg')
    review=safe_read(ROOT/'docs/diagram-review.md')
    for svg in svg_files:
        check(svg.name in review,f'no manual visual-review item for {svg.name}','visual_review')




def validate_reviewed_assets() -> None:
    """Detect unapproved revisions, NOT establish factual truth or grant rights."""
    from render_specs import render
    generated_names=set(render())
    actual_narratives = {
        rel for rel in APPROVED_PATHS if rel.endswith('.md')
        if rel not in generated_names
    }
    check(actual_narratives == set(REVIEWED_NARRATIVES),
          'added/removed free-form Markdown requires human claim review', 'reviewed_narratives')
    for relative,approved in REVIEWED_NARRATIVES.items():
        p=ROOT/relative
        check(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==approved,
              f'{relative}: human-reviewed narrative changed; verify against evidence register before reapproval',
              'reviewed_narratives')
    for relative,approved in REVIEWED_DIAGRAMS.items():
        p=ROOT/relative
        check(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==approved,
              f'{relative}: reviewed diagram/source changed; visual source and graph review required',
              'diagram_review')
    evidence=ROOT/'docs/evidence-register.md'
    if evidence.exists():
        txt=safe_read(evidence)
        for marker in ('EV01','EV02','EV03','EV04','EV05','EV06','EV07','OWNER-ASSUMED AUTHORIZATION'):
            check(marker in txt, f'evidence register missing material policy {marker}', 'reviewed_narratives')


def validate_diagram_edges() -> None:
    """Check stable directed graph semantics and drawn connectors, not only SVG XML validity."""
    p=ROOT/'data/diagram-edges.json'
    if not p.is_file():
        check(False,'missing reviewed edge manifest','diagram_edges');return
    check(hashlib.sha256(p.read_bytes()).hexdigest()==REVIEWED_EDGE_MANIFEST,
          'diagram edge manifest changed without review','diagram_review')
    manifest=json.loads(safe_read(p))
    check(manifest.get('schema_version')==1 and manifest.get('status')=='reviewed_conceptual_topology',
          'invalid graph-manifest metadata', 'diagram_edges')
    expectation=manifest.get('edges_by_diagram',{})
    check(set(expectation)=={f'{n}.svg' for n in (
          'ai-interaction','delivery-roadmap','professor-workflow','student-workflow','system-context',
          'professor-overview','student-overview','system-overview')},
          'graph-manifest diagram coverage changed','diagram_edges')
    from collections import Counter as _Counter
    ns={'s':'http://www.w3.org/2000/svg'}
    for filename,expected in expectation.items():
        path=ROOT/'diagrams'/filename
        if not path.is_file():continue
        try:
            tree=ET.parse(path)
            actual=[]
            for g in tree.getroot().iter():
                if g.attrib.get('class')!='edge':continue
                title=next((e.text for e in g if e.tag.endswith('}title')),None)
                actual.append(title)
                drawn=any(e.tag.endswith('}path') and bool(e.attrib.get('d')) for e in g)
                check(drawn,f'{filename}: edge {title} has no actual connector path','diagram_edges')
            check(_Counter(actual)==_Counter(expected),
                  f'{filename}: directed edge set differs from reviewed topology','diagram_edges')
        except ET.ParseError as exc:
            check(False,f'{filename}: invalid SVG for edge inspection: {exc}','diagram_edges')
    dotp=ROOT/'diagrams/source/professor-workflow.dot'
    if dotp.is_file():
        source=safe_read(dotp)
        dot_edges=re.findall(r'(?m)^\s*([A-Za-z]\w*)\s*->\s*([A-Za-z]\w*)\b',source)
        dot_edges=[a+'->'+b for a,b in dot_edges]
        check(_Counter(dot_edges)==_Counter(expectation.get('professor-workflow.svg',[])),
              'professor DOT source connectivity differs from shipped reviewed SVG','diagram_parity')
        # Renderability and directed connectivity matter; SVG bytes and font
        # placement can vary by Graphviz build. No bitwise-version requirement.
        reason = None
        if not shutil.which('dot'):
            reason = 'Graphviz dot missing; DOT render check skipped'
        else:
            try:
                result = subprocess.run(['dot', '-Tsvg', str(dotp)],
                                        capture_output=True, text=True, timeout=20)
                check(result.returncode == 0,
                      'Graphviz failed to render professor DOT', 'diagram_parity')
                if result.returncode == 0:
                    rendered = ET.fromstring(result.stdout)
                    rendered_edges = []
                    for group in rendered.iter():
                        if group.attrib.get('class') == 'edge':
                            edge_title = next((el.text for el in group
                                               if el.tag.endswith('}title')), None)
                            rendered_edges.append(edge_title)
                    check(_Counter(rendered_edges) == _Counter(expectation.get('professor-workflow.svg', [])),
                          'Graphviz-rendered DOT edges differ from approved directed topology', 'diagram_parity')
            except (OSError, subprocess.TimeoutExpired, ET.ParseError) as exc:
                reason = f'Graphviz render check failed: {exc}'
        if reason:
            SKIPPED.append(reason)
            if STRICT_RELEASE:
                check(False, 'strict release requires Graphviz rendering: ' + reason,
                      'diagram_parity')


def validate_publication_safety() -> None:
    reviewed_files,reviewed_dirs,unsafe=reviewed_worktree_entries()
    files=[ROOT/rel for rel in sorted(reviewed_files)]
    check(reviewed_files==set(APPROVED_PATHS) and reviewed_dirs==allowed_source_directories() and not unsafe,
          'approved source files/directories required; Git metadata is excluded only when structurally valid',
          'publication_safety')
    content_pairs=[]
    cumulative=0
    for path in files:
        relative=path.relative_to(ROOT)
        check(path.suffix in ALLOWED_EXTENSIONS,f'disallowed file extension: {relative}','publication_safety')
        if relative.as_posix() not in APPROVED_PATHS or path.is_symlink() or not path.is_file():
            check(False,f'unreviewed or unsafe source omitted from content scan: {relative}','publication_safety')
            continue
        size=path.stat().st_size
        cumulative+=size
        if size>SOURCE_FILE_MAX_BYTES or cumulative>SOURCE_TOTAL_MAX_BYTES:
            check(False,f'oversized potential pasted source file (not opened): {relative}','publication_safety')
            continue
        try:
            # bounded read independent of the stat preflight, for file-change safety
            data=path.open('rb').read(SOURCE_FILE_MAX_BYTES+1)
            if len(data)>SOURCE_FILE_MAX_BYTES:
                check(False,f'source grew during content scan: {relative}','publication_safety')
                continue
            content_pairs.append((relative,data.decode('utf-8')))
        except UnicodeError:
            check(False,f'non-text file included {relative}','publication_safety')
    signatures=[
      (re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),'private key'),
      (re.compile(r'AKIA[0-9A-Z]{16}'),'AWS key'),
      (re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b'),'GitHub access token'),
      (re.compile(r'\bsk-[A-Za-z0-9_-]{24,}\b'),'API key'),
      (re.compile(r'\b(?:xoxb|xoxp)-[0-9A-Za-z-]{20,}\b'),'Slack token'),
      (re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',re.I),'email address'),
      (re.compile('Now, here.s the combined PRD document with both '+'versions included:',re.I),'original PRD passage'),
      (re.compile('Week 1: Planning, Requirements Finalization, & '+'UI/UX Kickoff',re.I),'original roadmap passage')
    ]
    for rel,txt in content_pairs:
        for pattern,name in signatures:
            check(not pattern.search(txt),f'{rel} contains potential {name}; manual review required','publication_safety')
    req_phrase=['permission','ownership','not redistributed','not independently']
    pub=(ROOT/'docs/publication-safety.md')
    check(pub.is_file(),'missing rights/disclosure gate checklist','publication_safety')
    if pub.is_file():
        text=safe_read(pub).casefold()
        for phrase in req_phrase:
            check(phrase in text,f'publication gate missing {phrase}','publication_safety')
        check('assumed granted' in text and 'separate' in text and 'github' in text, 'owner-provided authorization premise and independent GitHub checkpoint must be explicit','publication_safety')


def main() -> int:
    global STRICT_RELEASE
    parser=argparse.ArgumentParser(description='Check documentary specifications; strict release requires Graphviz renderability.')
    parser.add_argument('--strict-release',action='store_true',help='Require Graphviz rendering and directed-topology checks')
    args=parser.parse_args()
    STRICT_RELEASE=args.strict_release
    try:
        can_import=validate_release_integrity()
        if not can_import:
            print('FAIL: release inventory / bounded source preflight failed; refusing to read or import unapproved source files')
            for issue in ISSUES: print(' -',issue)
            return 1
        validate_required_paths()
        independent_generated_coverage()
        if can_import:
            validate_generated_docs()
        else:
            check(False,'refusing to execute unreviewed renderer import','tool_integrity')
        validate_links_and_headings()
        req,_=validate_requirements()
        validate_scenarios(req)
        validate_risk_scenarios()
        validate_svg()
        if can_import:
            validate_reviewed_assets()
        validate_diagram_edges()
        validate_publication_safety()
    except Exception as exc:
        ISSUES.append(f'checker/data failure: {type(exc).__name__}: {exc}')
    print(f'Documentation QA: {sum(CHECKS.values())} assertions in {len(CHECKS)} categories')
    print('Checks:',', '.join(f'{k}={v}' for k,v in sorted(CHECKS.items())))
    for message in SKIPPED: print('SKIP:',message)
    if STRICT_RELEASE: print('Strict release: Graphviz renderability and directed topology required')
    if ISSUES:
        print(f'FAIL: {len(ISSUES)} issue(s)')
        for i in ISSUES: print(' -',i)
        return 1
    print('PASS: structural/specification consistency and defined controls; employer permission assumed on owner instruction, no historical app tests or GitHub publication.')
    return 0

if __name__=='__main__':sys.exit(main())
