#!/usr/bin/env python3
"""Deterministically package a reviewed, manifest-matching documentation repository.

No ZIP security parser. Exact release verification is an external SHA-256 match.
--refresh-manifest is an explicit reviewer operation, never part of CI validation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import stat
import zipfile
from pathlib import Path

from verify_sources import inventory

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'release/source-manifest.json'
ROOT_NAME = 'ai-classroom-assistant-architecture'
FILE_TYPES = {'.md', '.json', '.svg', '.dot', '.py', '.yml', ''}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect() -> dict[str, str]:
    output = {}
    if (ROOT / ".git").is_symlink():
        raise ValueError("unsafe .git symlink")
    for dirpath, dirs, names in os.walk(ROOT, followlinks=False):
        current = Path(dirpath)
        dirs[:] = sorted(d for d in dirs if not (current == ROOT and d == '.git'))
        for directory in dirs:
            if (current / directory).is_symlink():
                raise ValueError(f'symlink directory: {current / directory}')
        for name in sorted(names):
            p = current / name
            rel = p.relative_to(ROOT).as_posix()
            if rel == 'release/source-manifest.json':
                continue  # manifest is authenticated by an EXTERNAL digest
            if p.is_symlink() or not p.is_file() or p.suffix not in FILE_TYPES:
                raise ValueError(f'unexpected file type: {rel}')
            if p.stat().st_size > 160_000:
                raise ValueError(f'oversized source: {rel}')
            output[rel] = sha(p.read_bytes())
    return dict(sorted(output.items()))


def manifest() -> dict:
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    if data['schema_version'] != 1 or data['release'] != 'V18':
        raise ValueError('manifest version mismatch')
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--refresh-manifest', action='store_true', help='Requires deliberate review; rewrites SHA registry')
    args = parser.parse_args()
    current = collect()
    data = manifest()
    # Enforce the SAME physical-tree safety policy in both normal builds and
    # explicit reviewer refreshes. The manifest itself is included in the scan.
    inventory(ROOT, set(current) | {"release/source-manifest.json"})
    if args.refresh_manifest:
        data['files'] = current
        MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
    elif current != data['files']:
        missing = sorted(data['files'].keys() - current.keys())
        extra = sorted(current.keys() - data['files'].keys())
        changed = sorted(n for n in current.keys() & data['files'].keys() if current[n] != data['files'][n])
        raise SystemExit(f'FAIL: approved file manifest differs: missing={missing}, extra={extra}, modified={changed}')
    # For deterministic release, store each byte exactly without compression, fixed
    # metadata, no directory entries or external sources, and sorted source paths.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', compression=zipfile.ZIP_STORED, allowZip64=False) as z:
        for rel in sorted(data['files'] | {'release/source-manifest.json': ''}):
            p = ROOT / rel
            info = zipfile.ZipInfo(f'{ROOT_NAME}/{rel}', (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, p.read_bytes())
    print(f'PASS: deterministic archive: {args.output} ({len(data["files"])+1} files)')
    print('ZIP SHA-256:', sha(args.output.read_bytes()))
    print('Manifest SHA-256:', sha(MANIFEST.read_bytes()))

if __name__ == '__main__':
    main()
