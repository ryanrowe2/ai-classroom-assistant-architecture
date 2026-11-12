# Release verification and reproducibility

## Trust boundary

This portfolio certifies **one exact, reviewed ZIP artifact** using an SHA-256 digest published separately from the archive. It does **not** certify arbitrary ZIP containers or implement its own ZIP/Git parser. Changing one byte anywhere in the archive, including invisible metadata or trailing bytes, changes the digest and requires a newly reviewed release certificate. Never execute Python contained in an unverified archive.

The source tree has a single `release/source-manifest.json` recording every approved file's SHA-256. The manifest itself is anchored by a **second SHA-256 published outside the ZIP**. The portable `tools/verify_sources.py` can compare an extracted tree with that independently supplied manifest digest. Its Git mode uses direct enumeration and SHA-256 hashing of every **physical working file** before executing Git. Git mode separately runs sanitized, read-only `git fsck`, `git rev-parse`, `git ls-tree` and `git cat-file` commands to verify committed blobs. Git status, index flags, ignore rules, fsmonitor and inherited Git helper settings are not trusted to represent worktree content. It can optionally compare a separately pinned Git tree OID.

## Verify without running repository code

1. Obtain the ZIP SHA-256 from the separately supplied release certificate through a trusted channel; it is not a value read from the ZIP itself.
2. Run `sha256sum ai-classroom-assistant-architecture-v18.zip` (or `shasum -a 256` on macOS; `Get-FileHash` on Windows) and compare it to that certificate.
3. Only after the digest matches, extract the exact ZIP to a clean folder. Read `README.md` and run `python3 tools/check_docs.py --strict-release` if desired.

To verify a separate source tree, invoke an independently obtained copy of `tools/verify_sources.py` with `--root /path/to/checkout --manifest-sha256 <published-manifest-digest>`. Add `--git` for a committed Git checkout and optionally `--tree-oid <published-tree-oid>`. This is a distinct verification mode from bytewise ZIP identity. Every working file must match its approved SHA-256 exactly; `.gitattributes` enforces LF checkouts even if `core.autocrlf=true`. A worktree with manually changed line endings is rejected until restored to the reviewed bytes.

**No public Git commit or remote Git tree has yet been certified.** After explicit GitHub publication approval, verify the new remote commit and published tree and add their values to a new publication record. Do not infer a remote commit ID from this local release.

## Rebuild deterministically

The source is standard-library Python plus Graphviz for diagram renderability checks. From the reviewed source directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/check_docs.py --strict-release
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_check_docs.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/test_release_contract.py
python3 tools/build_release.py --output ../ai-classroom-assistant-architecture-v18.zip
sha256sum ../ai-classroom-assistant-architecture-v18.zip release/source-manifest.json
```

The builder requires all approved paths and hashes to match. It writes sorted, **Stored** ZIP entries with fixed timestamps and permissions; independent rebuilds from identical files produce identical bytes. A new reviewed revision requires an explicit `--refresh-manifest` operation and a new external digest; it cannot silently preserve the old release identity. No checksum computed by the packaged code is itself an independent trust anchor.

## Hosted checks

`.github/workflows/validate.yml` runs documentation QA, mutation tests, and the release-contract tests on a declared `ubuntu-24.04` runner with Python 3.12. It installs Graphviz and reports the actual version. DOT validation checks rendering and directed graph topology, not renderer-specific pixel bytes. Workflow execution in GitHub is **not yet demonstrated**; it can only be observed after publication.

## Scope limitations

- Source and ZIP hashes verify identity to an independently trusted approval record. They do **not** prove historical application behavior or employer rights.
- Git mode additionally checks physical files, directory inventory, symlinks and safe file modes. It isolates read-only Git plumbing calls from inherited configuration and never relies on `git status`; it does not claim to audit every possible `.git` internal entry.
- A ZIP of the same source files made with different compression/metadata is **not** the certified ZIP; it must be treated as a different artifact. Use Git-tree verification for GitHub-generated archives instead of a homegrown ZIP compatibility parser.
- The original application code, deployment environment and historical acceptance-test evidence are unavailable. Tests in this repository concern the documentation and release contract only.

See [release threat and coverage matrix](release-coverage-matrix.md) and [publication safety review](publication-safety.md).
