#!/usr/bin/env python3
"""Verify reviewed source bytes and, optionally, a Git commit.

Two independent assertions: (1) physical worktree files match the externally
pinned manifest, regardless of ignore/index/status/configuration; (2) native
Git object data contains those identical blobs and passes Git fsck.

No `git status`, filters, index flags, fsmonitor, or user/global Git settings are
trusted as a representation of working-file contents. Git runs only a short,
fixed list of read-only plumbing commands with a sanitized environment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_FILE_BYTES = 160_000
MAX_SOURCE_BYTES = 3_000_000
HEX_SHA256 = re.compile(r'[0-9a-f]{64}\Z')
HEX_OID = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_regular_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    total = 0
    # Never follow a symlink before size, mode and type are independently checked.
    with path.open('rb') as stream:
        while chunk := stream.read(65536):
            total += len(chunk)
            if total > MAX_FILE_BYTES:
                raise ValueError(f'oversized source file: {path}')
            h.update(chunk)
    return h.hexdigest(), total


def unsafe_mode(path: Path, *, directory: bool) -> bool:
    """Match tools/check_docs.py's POSIX release permission policy."""
    if os.name != 'posix':
        return False
    bits = stat.S_IMODE(path.lstat().st_mode)
    if bits & (0o5002 if directory else 0o7002):
        return True
    if directory:
        return (bits & 0o500) != 0o500
    return not (bits & 0o400) or bool(bits & 0o111)


def inventory(root: Path, allowed: set[str]) -> dict[str, Path]:
    """Walk the *physical* tree, disregarding Git ignore rules and index flags."""
    valid_dirs = {'/'.join(Path(name).parts[:i])
                  for name in allowed for i in range(1, len(Path(name).parts))}
    found: dict[str, Path] = {}
    seen_dirs: set[str] = set()
    if unsafe_mode(root, directory=True):
        raise ValueError('unsafe repository-root permissions')
    total_bytes = 0
    stack = [root]
    while stack:
        current = stack.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                path = Path(entry.path)
                rel = path.relative_to(root).as_posix()
                mode = entry.stat(follow_symlinks=False).st_mode
                if rel == '.git':
                    # Source-only mode may include a real Git directory. A
                    # symlink, gitfile or unusual entry is never silently skipped.
                    if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
                        raise ValueError('unsafe top-level .git entry')
                    continue
                if stat.S_ISDIR(mode):
                    if rel not in valid_dirs:
                        raise ValueError(f'unapproved directory: {rel}')
                    if unsafe_mode(path, directory=True):
                        raise ValueError(f'unsafe directory permissions: {rel}')
                    seen_dirs.add(rel)
                    stack.append(path)
                elif stat.S_ISREG(mode):
                    if rel not in allowed:
                        raise ValueError(f'unapproved file: {rel}')
                    if unsafe_mode(path, directory=False):
                        raise ValueError(f'unsafe file permissions: {rel}')
                    size = entry.stat(follow_symlinks=False).st_size
                    if size > MAX_FILE_BYTES:
                        raise ValueError(f'oversized source file: {rel}')
                    total_bytes += size
                    if total_bytes > MAX_SOURCE_BYTES:
                        raise ValueError('total source size exceeds release limit')
                    found[rel] = path
                else:
                    raise ValueError(f'non-regular file or symlink: {rel}')
    if set(found) != allowed:
        raise ValueError(f'source inventory differs: missing={sorted(allowed - set(found))}, '
                         f'extra={sorted(set(found) - allowed)}')
    if seen_dirs != valid_dirs:
        raise ValueError(f'source directories differ: missing={sorted(valid_dirs-seen_dirs)}')
    return found


def _git_env(home: str) -> dict[str, str]:
    """Remove inherited Git settings and other executable helper inputs."""
    keep = ('PATH', 'SYSTEMROOT', 'WINDIR', 'TMPDIR', 'TMP', 'TEMP')
    env = {k: os.environ[k] for k in keep if k in os.environ}
    env.update({
        'HOME': home, 'XDG_CONFIG_HOME': home,
        'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1',
        'GIT_CONFIG_SYSTEM': os.devnull, 'GIT_TERMINAL_PROMPT': '0',
        'GIT_NO_REPLACE_OBJECTS': '1', 'GIT_OPTIONAL_LOCKS': '0',
        'GIT_ATTR_NOSYSTEM': '1',
    })
    return env


def run_git(root: Path, env: dict[str, str], *cmd: str) -> bytes:
    # This list deliberately excludes status, diff, checkout, fetch, filters,
    # submodules, aliases, and every operation requiring credentials or hooks.
    args = ['git', '-C', str(root), '-c', 'core.hooksPath=/dev/null',
            '-c', 'core.fsmonitor=false', '-c', 'core.preloadIndex=false', *cmd]
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=30, env=env, check=False)
    if p.returncode:
        raise ValueError(f'Git {cmd[0]} failed: {p.stderr.decode(errors="replace")[:300]}')
    return p.stdout


def verify(root: Path, expected_manifest_sha: str, git_mode: bool,
           tree_oid: str | None) -> tuple[int, str | None]:
    if not HEX_SHA256.fullmatch(expected_manifest_sha.lower()):
        raise ValueError('invalid externally pinned SHA-256')
    if tree_oid and not HEX_OID.fullmatch(tree_oid.lower()):
        raise ValueError('invalid externally pinned Git tree OID')
    if root.is_symlink():
        raise ValueError('symlink repository root')
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('source root is not a directory')
    manifest_file = root / 'release/source-manifest.json'
    if not manifest_file.exists() or manifest_file.is_symlink():
        raise ValueError('source manifest missing or symlinked')
    manifest_hash, _ = hash_regular_file(manifest_file)
    if manifest_hash != expected_manifest_sha.lower():
        raise ValueError('reviewed source manifest digest differs from external trust anchor')
    raw = manifest_file.read_bytes()
    manifest = json.loads(raw)
    if manifest.get('schema_version') != 1 or manifest.get('release') != 'V18':
        raise ValueError('unrecognized manifest schema or release')
    expected = manifest['files']
    if not isinstance(expected, dict) or any(not HEX_SHA256.fullmatch(h) for h in expected.values()):
        raise ValueError('invalid source manifest')
    allowed = set(expected) | {'release/source-manifest.json'}
    physical = inventory(root, allowed)
    for rel, wanted in expected.items():
        actual, _ = hash_regular_file(physical[rel])
        if actual != wanted:
            raise ValueError(f'source digest differs: {rel}')
    # The physical manifest was already checked against its external anchor.
    if not git_mode:
        return len(physical), None
    if not (root/'.git').is_dir():
        raise ValueError('Git mode requires a real, local .git directory')
    with tempfile.TemporaryDirectory(prefix='classroom-safe-git-home-') as home:
        env = _git_env(home)
        workdir = run_git(root, env, 'rev-parse', '--show-toplevel').decode().strip()
        if Path(workdir).resolve() != root:
            raise ValueError('Git worktree root differs from reviewed source root')
        if run_git(root, env, 'rev-parse', '--is-bare-repository').strip() != b'false':
            raise ValueError('bare Git repository cannot certify a worktree')
        run_git(root, env, 'rev-parse', '--verify', 'HEAD^{commit}')
        run_git(root, env, 'fsck', '--strict', '--full', '--no-reflogs')
        git_tree = run_git(root, env, 'rev-parse', 'HEAD^{tree}').decode().strip()
        if not HEX_OID.fullmatch(git_tree):
            raise ValueError('invalid Git tree OID')
        if tree_oid and git_tree != tree_oid.lower():
            raise ValueError(f'Git tree OID differs: got {git_tree}')
        listing = run_git(root, env, 'ls-tree', '-r', '-z', '--full-tree', 'HEAD')
        blobs: dict[str, str] = {}
        for item in listing.split(b'\0'):
            if not item:
                continue
            header, name_raw = item.split(b'\t', 1)
            mode, typ, oid = header.decode('ascii').split()
            name = name_raw.decode('utf-8', errors='strict')
            if name in blobs or typ != 'blob' or mode != '100644' or not HEX_OID.fullmatch(oid):
                raise ValueError(f'unsupported Git tree entry: {name}')
            blobs[name] = oid
        if set(blobs) != allowed:
            raise ValueError(f'Git paths differ from approved manifest: {sorted(set(blobs)^allowed)}')
        for name, oid in blobs.items():
            blob = run_git(root, env, 'cat-file', 'blob', oid)
            expected_hash = expected_manifest_sha.lower() if name == 'release/source-manifest.json' else expected[name]
            if digest(blob) != expected_hash:
                raise ValueError(f'Git committed blob hash mismatch: {name}')
        return len(blobs), git_tree


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--manifest-sha256', required=True,
                        help='manifest SHA-256 from an independently trusted release certificate')
    parser.add_argument('--git', action='store_true', help='also verify Git object store and committed blobs')
    parser.add_argument('--tree-oid', help='optional independently pinned commit-tree OID')
    args = parser.parse_args()
    try:
        count, tree = verify(args.root, args.manifest_sha256, args.git, args.tree_oid)
    except (ValueError, OSError, subprocess.TimeoutExpired, KeyError, TypeError,
            UnicodeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print('FAIL:', exc)
        return 1
    print(f'PASS: {count} approved physical files with verified SHA-256'
          + (f'; verified Git commit tree={tree}' if tree else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
