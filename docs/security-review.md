<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Security review

## 2026-10-19, releases 0.0.13 to 0.0.16

**Reviewer:** Sebastien Rousseau (maintainer), with AI assistance. Not an
independent third-party review.

**Scope:** the gateway package (`iso20022_mcp/`), its MCP surface as an
agent sees it, its dependencies, CI and release pipeline. The family
packages were exercised but not reviewed.

**Security requirements and boundary considered:** those in
[`SECURITY.md`](../SECURITY.md#what-you-can-expect) and
[`assurance-case.md`](assurance-case.md).

### Method

| Method | Tool | Result |
| :--- | :--- | :--- |
| MCP protocol, catalogue, execution, egress and planted-credential checks | passmcp 0.0.7 over stdio, `--watch-egress --plant-canaries` | 91.56 A on 0.0.13; 100 A on 0.0.14 from PyPI |
| Coverage-guided fuzzing of every tool | Atheris (4,620 runs locally, 2 minutes per CI run) | No crash |
| Property-based testing | Hypothesis | No failure |
| Static analysis | CodeQL, mypy strict, ruff | Zero open alerts |
| Supply chain | OpenSSF Scorecard, Dependabot, pip-audit | 3 Scorecard findings and 1 advisory, all fixed |
| Licensing | reuse lint | Compliant (REUSE 3.3) |
| Build integrity | Two local builds compared with PyPI | Byte-identical SHA-256 |
| Manual review | `registry.resolve`, tool annotations, transports | No caller input reaches an import |

### Findings

| Finding | Severity | Fixed in |
| :--- | :--- | :--- |
| Tool descriptions set rules for sibling tools (passmcp `catalog.text.shadowing`, 12 instances) | Major | 0.0.14 |
| `generate` definition over the 500-token per-tool budget | Minor | 0.0.14 |
| `mcp` resolvable to releases affected by GHSA-84m7-p3x7-pcfv | Medium | 0.0.14 (excluded in `pyproject.toml`) |
| Unpinned `pip install` in workflows (Scorecard) | Low | 0.0.14, 0.0.15 |
| No fuzzer integration (Scorecard) | Low | 0.0.15 |
| Private vulnerability reporting not enabled though `SECURITY.md` pointed to it | Medium | Enabled 2026-10-19 |
| Supported-versions table out of date | Low | 0.0.16 |
| Python file headers declared Apache-2.0 only, not `Apache-2.0 OR MIT` | Low | 0.0.16 |

### Residual risks

As listed in the [assurance case](assurance-case.md#residual-risks). The
next review is due with any change to `registry.py` or the transports, and
at least yearly.
