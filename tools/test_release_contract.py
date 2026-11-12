#!/usr/bin/env python3
"""Executable release-contract matrix: local files, exact bytes, and native Git.

The historical application is not present and is not exercised by this suite.
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from verify_sources import verify


def digest(data): return hashlib.sha256(data).hexdigest()


class ReleaseContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest_digest = digest((ROOT/'release/source-manifest.json').read_bytes())

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='classroom-release-contract-')
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)/ROOT.name
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))

    def test_reviewed_files_pass(self):
        count,_ = verify(self.repo, self.manifest_digest, False, None)
        self.assertGreaterEqual(count, 34)

    def test_extra_file_rejected(self):
        (self.repo/'unapproved.py').write_text('print("not approved")')
        with self.assertRaisesRegex(ValueError, 'unapproved file'):
            verify(self.repo, self.manifest_digest, False, None)

    def test_missing_file_rejected(self):
        (self.repo/'RIGHTS.md').unlink()
        with self.assertRaisesRegex(ValueError, 'source inventory differs'):
            verify(self.repo, self.manifest_digest, False, None)

    def test_modified_file_rejected(self):
        (self.repo/'README.md').write_text('unreviewed change')
        with self.assertRaisesRegex(ValueError, 'source digest differs'):
            verify(self.repo, self.manifest_digest, False, None)

    def test_modified_manifest_rejected_by_external_anchor(self):
        with (self.repo/'release/source-manifest.json').open('ab') as f: f.write(b' ')
        with self.assertRaisesRegex(ValueError, 'external trust anchor'):
            verify(self.repo, self.manifest_digest, False, None)

    @unittest.skipUnless(os.name == 'posix', 'POSIX symlink semantics required')
    def test_symlink_rejected(self):
        (self.repo/'README.md').unlink()
        (self.repo/'README.md').symlink_to('RIGHTS.md')
        with self.assertRaisesRegex(ValueError, 'non-regular file'):
            verify(self.repo, self.manifest_digest, False, None)

    def git(self, *args, ok=True):
        p = subprocess.run(['git', *args], cwd=self.repo, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=15,
                           env={**os.environ, 'GIT_CONFIG_GLOBAL':os.devnull, 'GIT_CONFIG_NOSYSTEM':'1'})
        if ok and p.returncode: raise AssertionError(p.stderr.decode(errors='replace'))
        return p

    def init_git(self):
        self.git('init','-q')
        self.git('config','user.email','synthetic' + chr(64) + 'example.invalid')
        self.git('config','user.name','Synthetic Audit')
        self.git('add','-A')
        self.git('commit','-q','-m','certified content')

    def test_git_checkout_and_crlf_config(self):
        self.init_git()
        count,tree=verify(self.repo,self.manifest_digest,True,None)
        self.assertEqual(count,len(json.loads((ROOT/'release/source-manifest.json').read_text())['files'])+1)
        self.assertEqual(tree,self.git('rev-parse','HEAD^{tree}').stdout.decode().strip())
        self.git('config','core.autocrlf','true')
        self.git('reset','--hard','-q','HEAD')
        verify(self.repo,self.manifest_digest,True,tree)
        with self.assertRaisesRegex(ValueError,'tree OID differs'):
            verify(self.repo,self.manifest_digest,True,'0'*40)

    def test_corrupt_git_metadata_rejected(self):
        self.init_git()
        # Damage a mandatory Git metadata file without recursively removing
        # Git's object database (which may change during traversal).
        git_head = self.repo/'.git/HEAD'
        self.assertTrue(git_head.is_file(), 'test fixture was not initialized')
        git_head.unlink()
        with self.assertRaisesRegex(ValueError, 'Git rev-parse failed'):
            verify(self.repo,self.manifest_digest,True,None)

    def test_dirty_tracked_checkout_rejected(self):
        self.init_git()
        (self.repo/'README.md').write_text('damaged')
        with self.assertRaisesRegex(ValueError, 'source digest differs'):
            verify(self.repo,self.manifest_digest,True,None)

    def test_untracked_file_in_checkout_rejected(self):
        self.init_git()
        (self.repo/'extra.txt').write_text('unapproved')
        with self.assertRaisesRegex(ValueError,'unapproved file'):
            verify(self.repo,self.manifest_digest,True,None)


    def test_git_index_assume_unchanged_does_not_hide_change(self):
        self.init_git()
        self.git('update-index', '--assume-unchanged', 'README.md')
        (self.repo/'README.md').write_text('an unapproved mutation')
        with self.assertRaisesRegex(ValueError, 'source digest differs: README.md'):
            verify(self.repo, self.manifest_digest, True, None)

    def test_git_index_skip_worktree_does_not_hide_change(self):
        self.init_git()
        self.git('update-index', '--skip-worktree', 'README.md')
        (self.repo/'README.md').write_text('an unapproved mutation')
        with self.assertRaisesRegex(ValueError, 'source digest differs: README.md'):
            verify(self.repo, self.manifest_digest, True, None)

    def test_ignored_unapproved_file_is_rejected(self):
        self.init_git()
        (self.repo/'.git/info/exclude').write_text('unapproved.py\n')
        (self.repo/'unapproved.py').write_text('print("unexpected")\n')
        with self.assertRaisesRegex(ValueError, 'unapproved file: unapproved.py'):
            verify(self.repo, self.manifest_digest, True, None)

    @unittest.skipUnless(os.name == 'posix', 'POSIX symlinks required')
    def test_top_level_dotgit_symlink_rejected(self):
        target=Path(self.tmp.name)/'external-git'
        target.mkdir()
        (self.repo/'.git').symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'unsafe top-level .git entry'):
            verify(self.repo, self.manifest_digest, False, None)

    @unittest.skipUnless(os.name == 'posix', 'POSIX permissions required')
    def test_unapproved_file_permissions_rejected(self):
        (self.repo/'tools/check_docs.py').chmod(0o777)
        with self.assertRaisesRegex(ValueError, 'unsafe file permissions'):
            verify(self.repo, self.manifest_digest, False, None)

    @unittest.skipUnless(os.name == 'posix', 'POSIX permissions required')
    def test_unapproved_directory_permissions_rejected(self):
        (self.repo/'docs').chmod(0o777)
        with self.assertRaisesRegex(ValueError, 'unsafe directory permissions'):
            verify(self.repo, self.manifest_digest, False, None)

    def test_extra_empty_directory_rejected(self):
        (self.repo/'unapproved-empty-dir').mkdir()
        with self.assertRaisesRegex(ValueError, 'unapproved directory'):
            verify(self.repo, self.manifest_digest, False, None)

    @unittest.skipUnless(os.name == 'posix', 'POSIX shell probe required')
    def test_fsmonitor_and_inherited_git_config_cannot_execute(self):
        self.init_git()
        marker=Path(self.tmp.name)/'UNEXPECTED_EXECUTION'
        hook=Path(self.tmp.name)/'fsmonitor.sh'
        hook.write_text('#!/bin/sh\nprintf touched > "'+str(marker)+'"\n')
        hook.chmod(0o700)
        self.git('config','core.fsmonitor',str(hook))
        old={k:os.environ.get(k) for k in ('GIT_CONFIG_COUNT','GIT_CONFIG_KEY_0','GIT_CONFIG_VALUE_0')}
        os.environ.update({'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'core.fsmonitor',
                           'GIT_CONFIG_VALUE_0':str(hook)})
        try:
            verify(self.repo, self.manifest_digest, True, None)
        finally:
            for k,v in old.items():
                if v is None: os.environ.pop(k,None)
                else: os.environ[k]=v
        self.assertFalse(marker.exists(), 'Verifier launched an untrusted Git helper')
        # Even if Git is deceived into a clean status, the independent physical
        # file hash must still detect a changed worktree before Git is invoked.
        self.git('update-index','--assume-unchanged','README.md')
        marker.unlink(missing_ok=True)  # only execution by the verifier counts
        (self.repo/'README.md').write_text('modified but ignored by Git index')
        with self.assertRaisesRegex(ValueError, 'source digest differs'):
            verify(self.repo, self.manifest_digest, True, None)
        self.assertFalse(marker.exists(), 'Verifier launched Git config during rejection')

    def test_mutated_git_blob_worktree_mismatch_rejected(self):
        self.init_git()
        self.git('config','core.autocrlf','true')
        self.git('reset','--hard','-q','HEAD')
        verify(self.repo,self.manifest_digest,True,None)
        with (self.repo/'README.md').open('ab') as stream: stream.write(b'\r\nUNREVIEWED\r\n')
        with self.assertRaisesRegex(ValueError, 'source digest differs'):
            verify(self.repo,self.manifest_digest,True,None)

    def test_semantic_oracle_inversion_rejected_even_after_manifest_refresh(self):
        # Simulate a reviewer refreshing file hashes, while deliberately not
        # approving changed security/behavior contracts.
        requirements = self.repo/'data/acceptance-cases.json'
        obj = json.loads(requirements.read_text())
        scenario = next(c for c in obj['scenarios'] if c['id'] == 'S09')
        scenario['then'] = 'An incorrect calculus answer shall be graded correct.'
        requirements.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n')
        regen = subprocess.run([sys.executable, str(self.repo/'tools/render_specs.py')],
                               cwd=self.repo, capture_output=True, text=True, timeout=20)
        self.assertEqual(regen.returncode, 0, regen.stderr)
        mpath = self.repo/'release/source-manifest.json'
        m = json.loads(mpath.read_text())
        for rel in m['files']:
            m['files'][rel] = digest((self.repo/rel).read_bytes())
        mpath.write_text(json.dumps(m, sort_keys=True, indent=2)+'\n')
        result = subprocess.run([sys.executable,str(self.repo/'tools/check_docs.py')],
                                cwd=self.repo,capture_output=True,text=True,timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue('review_lock:' in result.stdout or 'scenario_semantics:' in result.stdout,
                        result.stdout[-1500:])

    def test_deterministic_archive_and_digest_tamper(self):
        builder=ROOT/'tools/build_release.py'
        a=Path(self.tmp.name)/'a.zip';b=Path(self.tmp.name)/'b.zip'
        for target in (a,b):
            p=subprocess.run([sys.executable,str(builder),'--output',str(target)],
                             cwd=ROOT,text=True,capture_output=True,timeout=20)
            self.assertEqual(p.returncode,0,p.stderr)
        baseline=digest(a.read_bytes())
        self.assertEqual(a.read_bytes(),b.read_bytes())
        with a.open('ab') as f:f.write(b'junk after archive')
        self.assertNotEqual(digest(a.read_bytes()),baseline)

if __name__=='__main__':unittest.main(verbosity=2)
