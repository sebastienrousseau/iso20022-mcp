<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

<p align="center">
  <img src="https://raw.githubusercontent.com/sebastienrousseau/iso20022-mcp/main/.github/logo.svg" alt="iso20022-mcp logo" width="128" />
</p>

<h1 align="center">iso20022-mcp</h1>

<p align="center">
  One MCP server with seven meta-tools that route across every ISO 20022 message family.
</p>

<p align="center">
  <a href="https://github.com/sebastienrousseau/iso20022-mcp/actions"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/iso20022-mcp/ci.yml?style=for-the-badge&logo=github" alt="Build" height="28" /></a>
  <a href="https://pypi.org/project/iso20022-mcp/"><img src="https://img.shields.io/pypi/v/iso20022-mcp?style=for-the-badge&color=fc8d62&logo=python" alt="Registry" height="28" /></a>
  <a href="docs/index.md"><img src="https://img.shields.io/badge/docs-source-blue?style=for-the-badge&labelColor=555555&logo=readthedocs" alt="Docs" height="28" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/sebastienrousseau/iso20022-mcp"><img src="https://img.shields.io/ossf-scorecard/github.com/sebastienrousseau/iso20022-mcp?style=for-the-badge&label=OpenSSF%20Scorecard&logo=openssf" alt="OpenSSF Scorecard" height="28" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg?style=for-the-badge" alt="License: Apache-2.0 OR MIT" height="28" /></a>
  <a href="https://github.com/sebastienrousseau/iso20022-mcp/blob/main/docs/POLICIES.md"><img src="https://img.shields.io/badge/Python-3.10%2B-93450a.svg?style=for-the-badge&logo=python" alt="Python 3.10 or newer" height="28" /></a>
  <a href="https://www.bestpractices.dev/projects/15699"><img src="https://img.shields.io/cii/level/15699?style=for-the-badge&label=OpenSSF%20Best%20Practices&logo=openssf" alt="OpenSSF Best Practices" height="28" /></a>
  <a href="https://glama.ai/mcp/servers/sebastienrousseau/iso20022-mcp"><img src="https://glama.ai/mcp/servers/sebastienrousseau/iso20022-mcp/badges/score.svg" alt="Glama MCP score" height="28" /></a>
</p>

<p align="center">
  <img src=".github/demo.gif" alt="iso20022-mcp demo: the command-line help, then list_families showing each family and whether its server is installed" width="100%" />
</p>

---

## Contents

**Getting started**

- [Install](#install) — pip extras per family, `uvx`, MCP client config
- [Requirements](#requirements) — toolchain floor, platforms
- [Quick Start](#quick-start) — search, describe, validate, generate and parse from one server

**The iso20022-mcp ecosystem**

- [The iso20022-mcp ecosystem](#the-iso20022-mcp-ecosystem) — the ISO 20022 MCP Suite and the family servers this gateway routes to

**Library reference**

- [Capabilities at a glance](#capabilities-at-a-glance) — the current surface by theme
- [Ecosystem comparison](#ecosystem-comparison) — short matrix; full table at [`docs/COMPARISON.md`](docs/COMPARISON.md)
- [Benchmarks](#benchmarks) — headline numbers; full table at [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md)
- [Features](#features) — module-level capability list
- [Configuration](#configuration) — core options
- [Examples](#examples) — runnable example index

**Operational**

- [When not to use iso20022-mcp](#when-not-to-use-iso20022-mcp) — limitations
- [Development](#development) — make targets, fuzzing, CI
- [Security](#security) — guarantees and compliance
- [Documentation](#documentation) — all reference docs
- [Stability guarantees](#stability-guarantees) — SemVer axis, output stability, minimum toolchain discipline
- [License](#license)

---

## Install

### As a Python library

```sh
pip install "iso20022-mcp[all]"
```

> **Latest release: v0.0.18**: 7 routing meta-tools over stdio, streamable
> HTTP or SSE (optionally over HTTPS), light core (only `mcp`), backing
> family servers as optional extras, actionable structured errors on every
> `validate`/`generate` failure, for Python 3.10+.

The core is light. Add the families you need as extras:

```sh
pip install "iso20022-mcp[pacs,camt]" # just interbank + statements
pip install iso20022-mcp              # core only; families report as not installed
uvx --from "iso20022-mcp[all]" iso20022-mcp   # run without installing
```

MCP client config (e.g. Claude Desktop):

```json
{
  "mcpServers": {
    "iso20022": {
      "command": "iso20022-mcp"
    }
  }
}
```

---

## Requirements

- Python 3.10 or newer, tested in CI on 3.10, 3.11, 3.12, 3.13 and 3.14 on
  Linux ([toolchain policy](docs/POLICIES.md)).
- `mcp` 1.30 or newer on the 1.x line, or 2.2 or newer on the 2.x line.
  Releases affected by GHSA-84m7-p3x7-pcfv cannot be resolved.
- The family servers are optional extras: `pain`, `pacs`, `camt`, `acmt`,
  or `all`.

---

## Quick Start

```text
search(query="reconciliation")
  → [{ "message_type": "camt.053", "family": "camt", "package": "camt053-mcp" }]

describe(message_type="pacs.008")           # required fields + input schema
validate(message_type="pacs.008", records=[…])
generate(message_type="pain.001", records=[…])   # → { "xml": "<Document>…" }
  # bare "pain.001" resolves to pain.001.001.09; on failure the payload is
  # { "error": "Missing required fields for pain.001.001.09: …" } listing
  # every missing or invalid field at once — fix them all and retry once
parse(message_type="camt.053", xml="<Document>…")
  # parse covers pacs + camt only; pain and acmt are outbound-only
```

Start with `search` or `list_families` to find a message type, `describe` it
for its required fields and input schema, then `validate`, `generate` or
`parse`. Each call is routed to the family server for that message type's
prefix.

---

## The iso20022-mcp ecosystem

`iso20022-mcp` is the generic message toolkit of the ISO 20022 MCP Suite:
eight coordinated, vendor-neutral MCP servers that cover the ISO 20022
bank-statement workflow and the November 2026 structured-address cutover,
plus an orchestration layer for readiness scoring, clearing-profile linting
and audit evidence. Dependency ranges are kept aligned across the suite, so
the servers co-install cleanly in one Python environment: start with one,
add the rest as your workflow grows.

| Component | Purpose | Use case |
| :--- | :--- | :--- |
| [`camt053-mcp`][camt053-mcp] | ISO 20022 `camt.053`/`camt.052` bank statements: parse, validate, filter, reverse; MT940/MT942 migration; CBPR+ readiness; journal export (24 tools, 4 prompts, 3 resources) | You work with bank-to-customer statements end to end; the suite's flagship |
| [`iso20022-mcp`](#install) | Unified gateway: `search` / `describe` / `validate` / `generate` / `parse` meta-tools routed across the `pain` · `pacs` · `camt` · `acmt` families (7 meta-tools) | You want one entry point to every message family: **this package** |
| [`reconcile-mcp`][reconcile-mcp] | Matches expected `pain.001` payments against observed `camt.053` entries: exact, partial, one-to-many, many-to-one, every match scored and explained (7 tools) | You need explainable statement/payment reconciliation |
| [`bankstatementparser-mcp`][bsp-mcp] | Multi-format statement ingestion: ISO 20022 CAMT.053 and pain.001, SWIFT MT940, OFX/QFX, CSV (5 tools, 1 prompt, 1 resource) | Your statements arrive in mixed or legacy formats |
| [`structured-address-fix-mcp`][saf-mcp] | ISO 20022 postal-address classification, assessment and remediation for the November 2026 structured-address cutover (9 tools) | You need debtor/creditor addresses ready before 14 Nov 2026 |
| [`iso20022-readiness-suite-mcp`](https://github.com/sebastienrousseau/iso20022-readiness-suite-mcp) | Orchestration: detect, validate, clearing-profile lint and readiness score, plus remediation and `pacs.002` response simulation (4 tools) | You want one high-level readiness entry point over the suite |
| [`iso20022-bank-profile-mcp`](https://github.com/sebastienrousseau/iso20022-bank-profile-mcp) | Manages, validates and serves bank clearing profiles and rule packs (CBPR+, SEPA_Instant, FedNow, Generic) (4 tools) | You lint payments against your institution's market practice |
| [`iso20022-evidence-pack-mcp`](https://github.com/sebastienrousseau/iso20022-evidence-pack-mcp) | Compiles findings, remediation diffs and simulated responses into a sealed, Ed25519-signable audit evidence pack (6 tools) | You need tamper-evident audit or certification artifacts |
| [`pain001-mcp`][pain001-mcp], [`pacs008-mcp`][pacs008-mcp], [`acmt001-mcp`][acmt001-mcp], [`camt-exceptions`][camt-exceptions] | The per-family servers this gateway routes to, installed as extras | Installed for you by `iso20022-mcp[all]`; see [Features](#features) |

---

## Capabilities at a glance

| Area | Capability | Status |
| :--- | :--- | :--- |
| Discovery | `search`, `list_families`, `list_servers` over the whole catalogue | Released; works with the core install |
| Schemas | `describe` returns required fields and the input JSON Schema | Released; needs the family's extra |
| Validation | `validate` checks records against a message type's schema | Released; every family |
| Generation | `generate` builds validated XML for `pain`, `pacs`, `acmt` and `camt.056`/`camt.029` | Released |
| Parsing | `parse` reads inbound `pacs` and `camt` XML | Released; `pain` and `acmt` are outbound-only |
| Transports | stdio, streamable HTTP and SSE, with optional HTTPS | Released; HTTPS since 0.0.18 |

---

## Ecosystem comparison

The alternative to this gateway is connecting an agent to each family server
directly. Measured over stdio with `list_tools` on 2026-10-20:

| Project | Servers to configure | Tools the agent sees | Estimated catalogue tokens |
| :--- | :---: | :---: | :---: |
| **iso20022-mcp** | 1 | 7 | ~2,200 |
| All four family servers directly | 4 | 73 | ~36,400 |

See [`docs/COMPARISON.md`](docs/COMPARISON.md) for the evidence and complete matrix.

---

## Benchmarks

Routing costs microseconds; the first call into a family pays its lazy
import once per process. Measured with `benches/bench_gateway.py --quick`.

| Scenario | Result | Environment |
| :--- | ---: | :--- |
| `family_for` routing | 0.54 µs | Apple A18 Pro, Python 3.12.15, mcp 2.3.0 |
| `search_catalog` | 7.29 µs | Apple A18 Pro, Python 3.12.15, mcp 2.3.0 |
| First `pain.001` call (cold import) | 528 ms | Apple A18 Pro, Python 3.12.15, fresh interpreter |
| Later `pain.001` call (warm) | 5.04 µs | Apple A18 Pro, Python 3.12.15 |

See [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) for methodology and full results.

---

## Features

The 7 routing meta-tools:

- `search` — Find message types by use-case / keyword ("reconciliation", "pacs.008"). *(families: all — catalogue)*
- `list_families` — List families, their capabilities, and which backing packages are installed. *(families: all)*
- `list_servers` — Full suite map: families + E&I messages + specialized servers (reconcile, agent-payment bridge). *(families: all)*
- `describe` — Required fields + input JSON Schema for a message type. *(families: all)*
- `validate` — Validate records against a message type's schema. *(families: all)*
- `generate` — Generate a validated ISO 20022 XML message from records. *(families: pain · pacs · acmt)*
- `parse` — Parse an inbound ISO 20022 XML message into structured data. *(families: pacs · camt)*

Operations are capability-aware: `generate` on a `camt.053` statement (an
inbound format) returns a clear, explanatory error rather than failing
obscurely, and every "package not installed" case tells you exactly what to
`pip install`.

Three ergonomics guarantees hold across the routed families:

- **Actionable structured errors.** Any error a backing server raises —
  not just the ones it returns — reaches the agent as an
  `{"error": "<Type>: <message>"}` payload instead of an opaque
  tool-execution failure. For `pain` generation the error lists every
  missing or invalid field at once, so one fix-and-retry suffices.
- **Family aliases for `message_type`.** Bare family names resolve to a
  concrete version via the backing server: `pain.001` →
  `pain.001.001.09`, `pain.008` → `pain.008.001.02`. Fully-versioned
  types are still preferred where you know them.
- **Per-family parse coverage, stated up front.** `parse` covers the
  inbound families only: `pacs` (e.g. `pacs.008`) and `camt` (e.g.
  `camt.053`). The initiation families `pain` and `acmt` are
  outbound-only — they have no parser here, so don't attempt a
  generate→parse round-trip for `pain.001` or `acmt.001`; use `validate`
  (or the backing server's XSD validation) instead.

### Routing

| Prefix | Family | Backing server | generate | parse |
| --- | --- | --- | :---: | :---: |
| `pain` | Customer Credit Transfer Initiation | [`pain001-mcp`][pain001-mcp] | ✅ | — |
| `pacs` | FI-to-FI Customer Credit Transfer | [`pacs008-mcp`][pacs008-mcp] | ✅ | ✅ |
| `camt` | Bank-to-Customer Statement | [`camt053-mcp`][camt053-mcp] | — | ✅ |
| `acmt` | Account Opening Instruction | [`acmt001-mcp`][acmt001-mcp] | ✅ | — |
| `camt.056`/`camt.029` | Cancellation / Resolution (E&I) | [`camt-exceptions`][camt-exceptions] | ✅ | — |

`generate("camt.056.001.12", …)` routes to `camt-exceptions`. The gateway also
surfaces the specialized servers — [`reconcile-mcp`][reconcile-mcp] and
[`ap2-iso20022`][ap2-iso20022] — via `search` and `list_servers` for discovery
(they're invoked through their own tools).

The gateway imports each backing server **lazily and optionally** — the core
depends only on `mcp`, and a family's server is loaded on first use. Message
types are matched on their prefix (`pacs.008.001.08` → `pacs`). The `pain`
extra requires `pain001-mcp >= 0.0.56`, the release that carries the
LLM-ergonomic generate surface (field aliases, computed `nb_of_txs` /
`ctrl_sum`, all-at-once field errors) the gateway's guarantees build on.

---

## Configuration

One command line, three transports:

| Command | Transport | Endpoint | Protocol revisions |
| :--- | :--- | :--- | :--- |
| `iso20022-mcp` | stdio | the client spawns the process | 2026-07-28, 2025-11-25 |
| `iso20022-mcp --transport streamable-http` | Streamable HTTP | `http://127.0.0.1:8000/mcp` | 2026-07-28 (stateless, `server/discover`) and 2025-11-25 (`initialize`, `Mcp-Session-Id`) on the same endpoint; responses stream as server-sent events, `GET` opens the server-to-client stream |
| `iso20022-mcp --transport sse` | HTTP+SSE (2024-11-05) | `http://127.0.0.1:8000/sse` and `/messages/` | for clients that still expect the older transport |

`--host` and `--port` change the bind address (defaults `127.0.0.1` and
`8000`). `--ssl-certfile cert.pem --ssl-keyfile key.pem` serves either HTTP
transport over HTTPS instead, on mcp 1.x and 2.x alike. The HTTP transports
carry no authentication of their own: bind loopback, or put the server
behind a gateway you trust before binding a routable address. Every release
is verified over streamable HTTP with
[passmcp](https://github.com/sebastienrousseau/passmcp) in both protocol
eras and over SSE with the MCP SDK client; see
[ADR 0001](docs/adr/0001-three-transports-one-command-line.md).

```json
{
  "mcpServers": {
    "iso20022": { "url": "http://127.0.0.1:8000/mcp" }
  }
}
```

Run `iso20022-mcp --help` for every option.

---

## Examples

- [`examples/mcp_tools.py`](examples/mcp_tools.py): discovery with the core
  install, then routed `describe`, `validate`, `generate` and `parse` calls
  (`python examples/mcp_tools.py` after `pip install -e ".[all]"`).
- [`benches/bench_gateway.py`](benches/bench_gateway.py): what the gateway
  adds on top of each family server.
- For the dedicated engine that matches `camt.053` statements against
  expected `pain.001` payments, see [`reconcile-mcp`][reconcile-mcp].

---

## When not to use iso20022-mcp

- **You need a family's specialist tools.** The gateway exposes the
  operations every family shares. camt053-mcp's MT940 migration or journal
  export, for example, are only on that server: connect it directly.
- **You need to round-trip `pain` or `acmt`.** They are outbound-only here,
  with no parser.
- **You need a bank, a settlement engine or a payment approver.** This
  routes and validates messages; it sends nothing anywhere and is not bank
  certification.
- **You need authentication on the HTTP transports.** There is none built
  in; put an authenticating gateway in front.

---

## Development

```bash
git clone https://github.com/sebastienrousseau/iso20022-mcp
cd iso20022-mcp
python -m venv .venv && . .venv/bin/activate
make dev
make check                         # lint, mypy strict, tests, version agreement
python benches/bench_gateway.py --quick
```

`make check` runs ruff, black, mypy in strict mode, pytest with a 100% line
and branch coverage gate (backends faked), and the version-agreement check.
CI also runs CodeQL, OpenSSF Scorecard, `reuse lint`, the MCP Inspector,
Hypothesis property tests, and Atheris fuzzing of every tool (two minutes per
change, 30 minutes weekly). See [`DEVELOPMENT.md`](DEVELOPMENT.md) and
[`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Security

Tools are read-only, idempotent and closed-world: no tool opens a path, a URL
or a socket, and every call is routed through one registry table, so no
caller input reaches an import. Stdio is the default; the HTTP transports
bind loopback, can serve HTTPS, and carry no authentication of their own.
Releases are built reproducibly from a signed tag, with SLSA provenance and
sigstore signatures you can verify. The threat model and evidence are in the
[assurance case](docs/assurance-case.md) and the
[security review](docs/security-review.md). The project holds the
[OpenSSF Best Practices](https://www.bestpractices.dev/projects/15699)
passing badge.

Report vulnerabilities according to [`SECURITY.md`](SECURITY.md).

---

## Documentation

[User manual](docs/index.md) · [API reference: the tools](#features) ·
[Developer guide](DEVELOPMENT.md) · [Architecture](ARCHITECTURE.md) ·
[Family map](#the-iso20022-mcp-ecosystem) · [Changelog](CHANGELOG.md) ·
[Roadmap](ROADMAP.md)

---

## Stability guarantees

The project is pre-1.0 and versions advance in `0.0.1` steps. The breaking
axis is the MCP surface an agent sees: tool names, their arguments, and the
shape of what they return, including the `{"error": ...}` payload. A change
to any of these is breaking even when no Python signature moves, and is
called out in the [changelog](CHANGELOG.md). Generated XML comes from the
family servers and follows their own stability rules. The Python floor moves
only as described in the [toolchain policy](docs/POLICIES.md).

---

## License

This project is dual-licensed under either:

* Apache License, Version 2.0 ([`LICENSE-APACHE`](LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
* MIT License ([`LICENSE-MIT`](LICENSE-MIT) or <https://opensource.org/licenses/MIT>)

at your option. Dependencies keep their own licences.

---

`mcp-name: io.github.sebastienrousseau/iso20022-mcp`

[mcp]: https://modelcontextprotocol.io
[pain001-mcp]: https://github.com/sebastienrousseau/pain001-mcp
[pacs008-mcp]: https://github.com/sebastienrousseau/pacs008-mcp
[camt053-mcp]: https://github.com/sebastienrousseau/camt053-mcp
[acmt001-mcp]: https://github.com/sebastienrousseau/acmt001-mcp
[reconcile-mcp]: https://github.com/sebastienrousseau/reconcile-mcp
[bsp-mcp]: https://github.com/sebastienrousseau/bankstatementparser-mcp
[saf-mcp]: https://github.com/sebastienrousseau/structured-address-fix-mcp

[camt-exceptions]: https://github.com/sebastienrousseau/camt-exceptions
[ap2-iso20022]: https://github.com/sebastienrousseau/ap2-iso20022
