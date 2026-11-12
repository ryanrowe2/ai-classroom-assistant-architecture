# Release threat and coverage matrix

**Supported security contracts:** Exact ZIP digest equality; manifest-authenticated source-tree files; independent working-tree byte integrity plus sanitized Git object verification; documentation and conceptual-diagram checks. Arbitrary ZIP metadata equivalence is **not** a supported contract.

| Input / failure mode | Authority and required outcome | Automated evidence |
| --- | --- | --- |
| Exact approved ZIP | SHA-256 equals independently published digest | Deterministic rebuild and exact-hash regression |
| Different compression, creator, timestamps, flags or comments | ZIP digest changes; not the approved release | Changed-byte regression; no custom format parser |
| Added bytes in Stored or Deflate member | ZIP digest changes, regardless of extraction behavior | Exact-hash regression; old bypass eliminated by contract |
| Unapproved file, missing file or altered file | Source inventory and digest mismatch | Source-tree negative tests |
| Symlinks/special entries | Reject source-tree verification | POSIX symlink negative test and approved-file inspection |
| Git fsmonitor, index skip flags, `.git/info/exclude` | Never execute Git helpers; independently reject altered or ignored worktree files | Fsmonitor execution probe, assume-unchanged, skip-worktree and ignored-file tests |
| Unsafe source mode or `.git` symlink | Reject consistently with documentation QA | Source-tree permission, symlink and directory probes |
| Mutable CI action tag | Reject in reviewed workflow; pin complete upstream action SHAs | Immutable action commit review and CI workflow inspection |
| Changed in-ZIP manifest | Externally pinned manifest SHA mismatch | Negative manifest mutation |
| Clean Git checkout with platform line endings | Verify actual physical LF bytes and sanitized Git objects; do not trust index flags, status or Git settings | Git checkout test with `core.autocrlf=true`, `.gitattributes`, physical SHA-256 |
| Broken Git object database or invalid HEAD | Native Git validation fails | Corrupted `.git/objects` negative test |
| Dirty, staged or untracked files | Independent physical inventory or SHA-256 fails | Modified, staged, ignored and untracked-file tests |
| Replaced/unapproved Git commit | Committed blob hashes or independently pinned tree OID differ | Git blob/tree comparison tests |
| Dependency cycles, mismatched acceptance tables | Documentation QA rejects | Existing source/specification checks and mutation tests |
| Missing Graphviz or invalid DOT graph | Strict QA rejects; CI installs renderer | `--strict-release` and graph semantic validation |
| Misleading historical claims or confidential wording | Human review required; scanner only flags common patterns | Evidence register and publication review record |
| Historical app code, deployment and production outcomes | **Not certified / not claimed** | No implementation assets available |

## Regression method

The test suite starts with the supported trust boundary instead of enumerating all possible ZIP parser flags. Any unapproved byte change to an **exact ZIP** is rejected by one SHA-256 comparison. Committed Git objects are evaluated with sanitized read-only Git plumbing. All working files are checked independently of Git status and ignore/index rules. Source and semantic errors have separate fixtures. Changes to this contract require reviewing the entire table before publishing a new certificate.

The automated tests do not establish an absence of every possible defect. They ensure the release does not promise a broader trust boundary than it actually implements.
