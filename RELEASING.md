<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Releasing iso20022-mcp

This document defines **what merits a release** and **how to cut one**,
so versions are deliberate rather than ad-hoc.

## Versioning scheme

iso20022-mcp carries its own version number, incremented by 0.0.1 per
release (`0.1.0` follows `0.0.999`). The family servers it routes to are
optional extras with version floors in `pyproject.toml`, not lockstep
siblings; `tests/test_extras_resolve.py` guards the floor shapes that
once made `[all]` unsatisfiable. The scheduled `Release Consistency`
workflow (`scripts/check_suite_consistency.py`) fails when the tree and
PyPI disagree, so a version bumped and never released is noticed.

## What merits a release

Cut a new version when there is user-visible change to ship - bug fixes,
security or dependency patches, new meta-tools / resources / prompts, a
new family or adapter, or documentation that ships in the package.

Do **not** cut a release that contains only a version-number bump with
no functional, security, or documentation change.

## Pre-flight checklist

A release is ready only when **all** of the following hold on `main`:

1. The gate is green: `pytest` (100% line+branch coverage),
   `ruff check`, `black --check`, `mypy iso20022_mcp/` and
   `python benches/bench_gateway.py --quick`, as `ci.yml` runs them.
2. Every Dependabot / CodeQL / Scorecard alert is resolved or has a
   documented, expiring suppression.
3. `CHANGELOG.md` has a dated section for the new version describing the
   change set.
4. The version is identical in `pyproject.toml`,
   `iso20022_mcp/__init__.py`, `CHANGELOG.md`, `glama.json` and
   `server.json` (enforced by `scripts/verify_versions.py`, which the
   `Version sources agree` workflow runs). The Glama directory and the
   MCP registry read those two manifests; a release that forgets them
   shows an old version to every agent that browses for the server.

## Cutting the release

1. Bump the version in `pyproject.toml`, `iso20022_mcp/__init__.py`,
   `glama.json` and `server.json`, and add the `CHANGELOG.md` section,
   in a single PR.
2. Merge the PR to `main` once CI is green.
3. Push a signed tag:

   ```bash
   git tag -s vX.Y.Z -m "iso20022-mcp vX.Y.Z" <merge-commit>
   git push origin vX.Y.Z
   ```

4. The tag triggers two workflows:
   - `release.yml` builds with Poetry, runs `twine check`, attaches a
     SLSA build provenance attestation, publishes to PyPI via OIDC
     trusted publishing (with PEP 740 attestations), signs every
     distribution keylessly with cosign, creates the GitHub release
     with generated notes, and attaches CycloneDX and SPDX SBOMs plus a
     licence manifest.
   - `publish-mcp.yml` stamps `server.json` from the tag, waits for
     PyPI to surface the version, and publishes to the MCP registry.

## After releasing

- Confirm the version is live on
  [PyPI](https://pypi.org/project/iso20022-mcp/) and the GitHub release
  is published (not draft).
- Verify a clean install: `pip install iso20022-mcp==X.Y.Z` and
  `iso20022-mcp --version`.
- Confirm the MCP registry and Glama show the new version.

## CI integrations

- **PyPI trusted publisher** (`release.yml`): configured at
  <https://pypi.org/manage/account/publishing/>. The publisher claim
  set is `repo:sebastienrousseau/iso20022-mcp:environment:pypi` with
  `workflow_ref` pointing at `.github/workflows/release.yml`.
- **MCP registry** (`publish-mcp.yml`): authenticates with the
  workflow's GitHub OIDC token; no secret to configure.
