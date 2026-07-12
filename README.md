# iso20022-mcp: The Unified MCP Gateway for ISO 20022

**One [Model Context Protocol][mcp] server, one small set of meta-tools —
`search`, `list_families`, `describe`, `validate`, `generate`, `parse` — that
route across every ISO 20022 message family (`pain` · `pacs` · `camt` ·
`acmt`).** Install one thing, discover the whole suite: an agent sees a handful
of verbs instead of the 60+ tools spread across five individual servers.

> **Latest release: v0.0.1** — 6 routing meta-tools over stdio, light core
> (only `mcp`), backing family servers as optional extras, for Python 3.10+.
> The front door to the [ISO 20022 MCP suite](#the-suite).

## Why a gateway

The suite has a dedicated, best-in-class server per message family. That depth
is the point — but an agent shouldn't have to know *which* of five servers and
*which* of sixty tools it needs before it can act. `iso20022-mcp` is the thin
routing layer on top: ask it in plain terms ("I need to reconcile a
statement", "generate a credit transfer"), and it points you at — or executes
against — the right family. Small tool surface, whole-suite reach.

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

## The meta-tools

| Tool | What it does | Families |
| --- | --- | --- |
| `search` | Find message types by use-case / keyword ("reconciliation", "pacs.008"). | all (catalogue) |
| `list_families` | List families, their capabilities, and which backing packages are installed. | all |
| `describe` | Required fields + input JSON Schema for a message type. | all |
| `validate` | Validate records against a message type's schema. | all |
| `generate` | Generate a validated ISO 20022 XML message from records. | pain · pacs · acmt |
| `parse` | Parse an inbound ISO 20022 XML message into structured data. | pacs · camt |

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

## The suite

`iso20022-mcp` is the front door to a family of vendor-neutral, Python-native
ISO 20022 MCP servers:

- [`pain001-mcp`][pain001-mcp] — customer credit transfer initiation.
- [`pacs008-mcp`][pacs008-mcp] — FI-to-FI credit transfers.
- [`camt053-mcp`][camt053-mcp] — bank-to-customer statements.
- [`acmt001-mcp`][acmt001-mcp] — account opening instructions.
- [`reconcile-mcp`][reconcile-mcp] — explainable statement/payment reconciliation.
- [`bankstatementparser-mcp`][bsp-mcp] — MT94x / BAI2 / OFX parsing.

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
