# iso20022-mcp: The Unified MCP Gateway for ISO 20022

**One [Model Context Protocol][mcp] server, one small set of meta-tools —
`search`, `list_families`, `describe`, `validate`, `generate`, `parse` — that
route across every ISO 20022 message family (`pain` · `pacs` · `camt` ·
`acmt`).** Install one thing, discover the whole suite: an agent sees a handful
of verbs instead of the 60+ tools spread across five individual servers.

> **Latest release: v0.0.3** — 7 routing meta-tools over stdio, light core
> (only `mcp`), backing family servers as optional extras, for Python 3.10+.
> The front door to the [ISO 20022 MCP Suite](#the-iso-20022-mcp-suite).

## Why a gateway

The suite has a dedicated, best-in-class server per message family. That depth
is the point — but an agent shouldn't have to know *which* of five servers and
*which* of sixty tools it needs before it can act. `iso20022-mcp` is the thin
routing layer on top: ask it in plain terms ("I need to reconcile a
statement", "generate a credit transfer"), and it points you at — or executes
against — the right family. Small tool surface, whole-suite reach.

## The ISO 20022 MCP Suite

`iso20022-mcp` is the **generic message toolkit** of four coordinated,
vendor-neutral MCP servers that together cover the ISO 20022 bank-statement
workflow — statement depth, whole-catalogue routing, reconciliation, and
multi-format ingestion. Dependency ranges are kept aligned across the suite,
so the servers co-install cleanly in a single Python environment: start with
one, add the rest as your workflow grows.

| Server | Scope | Surface | Install | Use it when |
| --- | --- | --- | --- | --- |
| [`camt053-mcp`][camt053-mcp] | ISO 20022 `camt.053`/`camt.052` bank statements: parse, validate, filter, reverse; MT940/MT942 migration; CBPR+ readiness; journal export | 22 MCP tools · 4 prompts · 3 resources | `pip install camt053-mcp` | You work with bank-to-customer statements end to end — the suite's flagship |
| [`iso20022-mcp`](#install) | Unified gateway: `search` / `describe` / `validate` / `generate` / `parse` meta-tools routed across the `pain` · `pacs` · `camt` · `acmt` families | 7 meta-tools | `pip install "iso20022-mcp[all]"` | You want one entry point to every message family — **this package** |
| [`reconcile-mcp`][reconcile-mcp] | Matches expected `pain.001` payments against observed `camt.053` entries — exact, partial, one-to-many, many-to-one, every match scored and explained | 7 MCP tools | `pip install reconcile-mcp` | You need explainable statement/payment reconciliation |
| [`bankstatementparser-mcp`][bsp-mcp] | Multi-format statement ingestion: ISO 20022 CAMT.053 and pain.001, SWIFT MT940, OFX/QFX, CSV | 5 MCP tools · 1 prompt · 1 resource | `pip install bankstatementparser-mcp` | Your statements arrive in mixed or legacy formats |

In one line each: **`camt053-mcp`** is the bank-statement flagship (deepest
camt.05x surface, stdio + authenticated streamable HTTP);
**`iso20022-mcp`** is the generic message toolkit (a handful of verbs over
the whole catalogue); **`reconcile-mcp`** is the reconciliation workflow
(did the money we expected actually arrive?); and
**`bankstatementparser-mcp`** is the ingestion layer (many formats in, one
transaction shape out).

The gateway also routes to the per-family servers —
[`pain001-mcp`][pain001-mcp], [`pacs008-mcp`][pacs008-mcp],
[`acmt001-mcp`][acmt001-mcp], and [`camt-exceptions`][camt-exceptions] —
installed as extras (see [Routing](#routing)).

## Install

The core is light. Add the families you need as extras (or `[all]`):

```sh
pip install "iso20022-mcp[all]"       # every family
pip install "iso20022-mcp[pacs,camt]" # just interbank + statements
pip install iso20022-mcp              # core only; families report as not installed
# or run without installing:
uvx --from "iso20022-mcp[all]" iso20022-mcp
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

## Tools

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

## Routing

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
types are matched on their prefix (`pacs.008.001.08` → `pacs`).

## Example

```
search(query="reconciliation")
  → [{ "message_type": "camt.053", "family": "camt", "package": "camt053-mcp" }]

describe(message_type="pacs.008")           # required fields + input schema
validate(message_type="pacs.008", records=[…])
generate(message_type="pain.001", records=[…])   # → validated XML
parse(message_type="camt.053", xml="<Document>…")
```

For the dedicated reconciliation engine that matches `camt.053` statements
against expected `pain.001` payments, see [`reconcile-mcp`][reconcile-mcp].

## Development

```sh
git clone https://github.com/sebastienrousseau/iso20022-mcp
cd iso20022-mcp
python -m venv .venv && . .venv/bin/activate
pip install -e . && pip install pytest pytest-cov ruff black mypy
pytest                      # 100% branch coverage gate (backends faked)
ruff check iso20022_mcp tests && black --check iso20022_mcp tests && mypy iso20022_mcp
```

## Licence

Licensed under the [Apache License, Version 2.0](LICENSE).

---

`mcp-name: io.github.sebastienrousseau/iso20022-mcp`

[mcp]: https://modelcontextprotocol.io
[pain001-mcp]: https://github.com/sebastienrousseau/pain001-mcp
[pacs008-mcp]: https://github.com/sebastienrousseau/pacs008-mcp
[camt053-mcp]: https://github.com/sebastienrousseau/camt053-mcp
[acmt001-mcp]: https://github.com/sebastienrousseau/acmt001-mcp
[reconcile-mcp]: https://github.com/sebastienrousseau/reconcile-mcp
[bsp-mcp]: https://github.com/sebastienrousseau/bankstatementparser-mcp

[camt-exceptions]: https://github.com/sebastienrousseau/camt-exceptions
[ap2-iso20022]: https://github.com/sebastienrousseau/ap2-iso20022
