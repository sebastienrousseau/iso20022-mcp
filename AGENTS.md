<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# AGENTS.md

Invariants for AI-assisted contributions to `iso20022-mcp`. Read this before changing anything.

Everything here applies equally to humans and automated agents. It is addressed to agents because agents can make breaking changes across multiple files before anyone notices.

## 1. Core Invariants

1. **Strict SemVer sequencing policy**: Public releases stay on the `0.0.x` line and increment strictly by `0.0.1`. Never manually edit version numbers outside the active release branch `feat/v<next-version>`. `v0.1.0` is forbidden until `v0.0.999` exists.
2. **Single Active Release PR Invariant**: Across all repositories, there MUST be at most ONE active pull request targeting `main`, which MUST be the release iteration branch `feat/v<next-version>`.
3. **Dual licensing**: The repository is dual-licensed under Apache-2.0 OR MIT. All files must declare an SPDX license header.
4. **Single source of truth**: The version in `pyproject.toml` is the single source of truth. It must agree with `__version__`, `glama.json`, `server.json`, `CITATION.cff`, and `CHANGELOG.md` (verified by `scripts/verify_versions.py`).
5. **No breaking changes to meta-tools**: The core meta-tools (`search`, `list_families`, `list_servers`, `describe`, `validate`, `generate`, `parse`) provide the unified gateway facade. They must remain side-effect-free, read-only, and idempotent.

## 2. Before You Claim To Be Done (Verification Gates)

Before concluding any task or preparing a commit, run:

```console
make check
```

Or run the individual gates:

```console
pytest --cov=iso20022_mcp --cov-branch --cov-report=term-missing --cov-fail-under=100
ruff check .
black --check .
mypy iso20022_mcp
python3 scripts/verify_versions.py
```

All unit tests and conformance tests must pass with 0 failures, 0 warnings, and 100% line and branch coverage.

## 3. Hygiene First

Before any feature, fix, or release work, check repository health:
1. Verify CI is green on `main`.
2. Ensure linter and formatter pass without warnings or new suppressions.
3. Every function must remain within the complexity ceilings (Cyclomatic ≤ 10, Cognitive ≤ 15, Halstead ≤ 30, Lines of code ≤ 60 per function, ≤ 500 per file).

## 4. Things That Look Like Bugs and Are Not

- **`parse` has no parser for `pain` or `acmt`**: Initiation and account-opening messages are outbound-only in this gateway; they do not have an inbound parser.
- **`generate` fails on `camt.053`**: Statement messages are inbound-only; the gateway purposefully does not generate bank statements.
- **Backing servers are optional dependencies**: `pain001-mcp`, `pacs008-mcp`, `camt053-mcp`, and `acmt001-mcp` are imported lazily. When not installed, the tool returns an actionable `{"error": ...}` payload rather than raising an uncaught `ImportError`.
