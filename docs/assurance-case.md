<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Assurance case

The claim: **iso20022-mcp does not let a caller do anything other than ask
a registered ISO 20022 family package to search, describe, validate,
generate or parse a message, and it does not weaken the security of the
process it runs in.**

This document argues that claim from the threat model, the trust
boundaries, the design principles applied and the common weaknesses
countered, and points to the evidence for each. It is reviewed with every
release that changes `iso20022_mcp/`; the last full review is recorded in
[`security-review.md`](security-review.md).

## What the software is

A Model Context Protocol server that exposes seven read-only meta-tools
(`search`, `list_families`, `list_servers`, `describe`, `validate`,
`generate`, `parse`), two resources, one resource template and one prompt.
It routes each call to one of four optional family packages (`pain001-mcp`,
`pacs008-mcp`, `camt053-mcp`, `acmt001-mcp`), which do the parsing, schema
validation and XML generation. See [`ARCHITECTURE.md`](../ARCHITECTURE.md).

## Threat model

| Actor | Can reach | Wants |
| :--- | :--- | :--- |
| The model or agent calling tools | Every tool argument | Run code, read files, reach the network, or make the agent act on attacker text |
| A document the agent was given (prompt injection) | Tool arguments, through the model | Same as above, at one remove |
| A network peer, when an HTTP transport is used | The listening socket | Call tools without being the intended client |
| A compromised dependency or build step | The installed package | Ship code users did not review |
| A malicious contributor | Pull requests | Land a change that widens what a caller can do |

Out of scope: the confidentiality of payment data inside the model's
context (the gateway passes it through by design), and vulnerabilities
inside the family packages themselves, which are separate projects with
their own policies. Their versions are floored and monitored here.

## Trust boundaries

1. **Client to server.** Over stdio, the boundary is the client process
   that spawned the server: anything that can write to its stdin already
   runs as the same user. Over `streamable-http` and `sse`, the boundary is
   the socket, which binds `127.0.0.1` by default and has no
   authentication or TLS of its own ([`SECURITY.md`](../SECURITY.md#transports)).
2. **Server to family package.** Crossed only through `registry.resolve`,
   which maps a message type to a module and function named in the
   registry table.
3. **Source to distribution.** Crossed by `release.yml` on a signed tag,
   with hash-pinned tooling, producing reproducible, signed and attested
   files.

## Design principles applied

| Principle | How |
| :--- | :--- |
| Least privilege | Tools are read-only, idempotent and closed-world; workflows start read-only (`contents: read`; `read-all` for Scorecard) and grant write per job; publishing uses OIDC, no stored token. |
| Fail-safe defaults | Stdio by default; HTTP transports bind loopback; a family that is missing or lacks a capability returns a structured error, never a fallback. |
| Complete mediation | Every call goes through `registry.resolve`; there is no second path to a family module. |
| Economy of mechanism | One routing table, no plugins, no dynamic configuration, no state between calls. |
| Separation of privilege | Releases need a signed tag, a green CI run and the PyPI trusted-publisher binding. |
| Open design | All code, workflows, tests and this case are public; verification needs no secret. |
| Psychological acceptability | One `pip install`, no configuration needed to run safely. |

## Common weaknesses countered

| Weakness | Countered by | Evidence |
| :--- | :--- | :--- |
| CWE-94/CWE-470 code injection through dynamic import | Module and function names come only from the registry table | `registry.py`; `tests/test_registry.py` |
| CWE-20 improper input validation | Arguments validated against each tool's JSON Schema (pydantic); records validated by the family's schema; unknown message types rejected | `tests/test_server.py`; fuzzing below |
| CWE-22 path traversal, CWE-918 SSRF | No tool opens a path or a URL | passmcp `egress.hosts`: no outbound connection during a full run |
| CWE-611 XXE and XML bombs | XML is parsed only by the family packages with XSD validation; the gateway does not parse | Family package policies |
| CWE-248 uncaught exceptions as denial of service | Every tool returns a dict or an `{"error": ...}` payload | `tests/test_fuzz.py` (Hypothesis), `fuzz/fuzz_tools.py` (Atheris) |
| Tool-description injection and shadowing | Each description governs only its own tool; per-tool token budget | `tests/test_catalog_text.py`; passmcp 100 A |
| CWE-1395 vulnerable dependencies | Floors and exclusions in `pyproject.toml`; Dependabot; `pip-audit`; zero open alerts before a release | `pyproject.toml` (`mcp` excludes GHSA-84m7-p3x7-pcfv) |
| CWE-829 untrusted build inputs | Every action pinned by SHA; every workflow `pip install` hash-pinned | OpenSSF Scorecard Pinned-Dependencies 10 |
| CWE-798 hard-coded credentials | None held; OIDC publishing; secret scanning on | Zero secret-scanning alerts |
| CWE-306 missing authentication on HTTP transports | Documented: loopback by default, a gateway with authentication and TLS required for any routable address | `SECURITY.md#transports` |

## Assurance evidence

- 100% line and branch coverage, enforced in CI, on Python 3.10 to 3.14.
- `mypy` in strict mode, `ruff`, `black` and CodeQL on every change.
- Hypothesis property tests and Atheris coverage-guided fuzzing of every
  tool on every change, 30 minutes weekly.
- passmcp protocol, catalogue, execution and egress checks: 100 A.
- OpenSSF Scorecard; `reuse lint` for licensing; reproducible builds
  checked against PyPI; signed tags, SLSA provenance and sigstore
  signatures on every release ([`SECURITY.md`](../SECURITY.md#verifying-a-release)).

## Residual risks

- A single maintainer: review of changes is by CI and the maintainer
  only ([`GOVERNANCE.md`](../GOVERNANCE.md)).
- The HTTP transports rely on the operator placing an authenticating TLS
  gateway in front of any non-loopback bind.
- Payment data passed to the tools reaches the model's context.
