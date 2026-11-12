# Review protocol — evidence, changes, and publication

## Purpose

The V18 release contract deliberately separates **artifact identity** from **document correctness** and **Git repository health**. This reduces redundant audit surfaces. A passing SHA-256 check does not certify historical application behavior or legal permissions.

## Material change process

1. Review the original nonpublic PRD and six-week plan for any historical change; record the E1–E6 source class in [provenance](provenance.md) and the [evidence register](evidence-register.md). Avoid attributing implementation code to the architect or treating planned milestones as executed outcomes.
2. Inspect source-derived requirements, prospective acceptance oracles, ownership boundaries, and deferred functionality. A changed security oracle must be checked for inverted results. Regenerate the four derived Markdown files using `python3 tools/render_specs.py` after an approved source change.
3. Inspect every changed `.md`, `.json`, `.svg`, `.dot` and `.py` file, including confidentiality and authorship. Render all eight diagrams and check their named arrows, labels, role-specific branches, and mobile readability. Run `python3 tools/check_docs.py --strict-release` and both test suites.
4. Only after review, explicitly run `python3 tools/build_release.py --refresh-manifest --output <new-zip>`. Produce a new independently supplied ZIP SHA-256 and source-manifest SHA-256. Both SHA values belong outside the ZIP; values printed by packaged code are not a separate trust anchor.
5. Verify the new ZIP digest **before executing packaged Python**, independently rebuild it to confirm reproducible bytes, and compare the source manifest. Record review evidence in a private release report and review the [release coverage matrix](release-coverage-matrix.md).
6. **Do not create or modify GitHub without separate express authorization.** Once published, inspect the hosted README/diagrams, verify CI, and publish the actual remote commit/tree identifier in the public release record. No hosted CI success or remote commit is claimed before publication.

## Trust-policy limits

The previous external V16 ZIP/Git metadata parser is retired. The V18 contract verifies exactly one approved ZIP byte sequence, or the canonical Git committed source using native Git commands. Arbitrarily repacked ZIP files are **new artifacts** and not automatically approved. See [release verification](release-verification.md).

The owner instructed this work to assume employer IP/disclosure clearance on November 12, 2026. No original source document, original implementation code, or sensitive approval paperwork is included in the public artifact. Human content review and separate GitHub publication authorization remain required checkpoints.
