# iso20022-mcp Roadmap

This roadmap tracks what is planned for the routing gateway of the ISO
20022 MCP suite. It summarises the CHANGELOG and the open issues; it
does not promise work that is not tracked there. Releases ship when the
gates pass, not on a calendar.

## v0.0.11 (current)

- Seven meta-tools routed across the `pain`, `pacs`, `camt` and `acmt`
  families: `search`, `list_families`, `list_servers`, `describe`,
  `validate`, `generate`, `parse`.
- Three resources (`iso20022://families`, `iso20022://servers`,
  `iso20022://describe/{message_type}`) and one prompt
  (`route_iso20022_task`).
- Family servers as optional extras, imported lazily; the core depends
  only on `mcp`.
- Optional LangChain, CrewAI and LlamaIndex adapters.
- 100% line+branch coverage gate, the shared suite conformance test, a
  gateway benchmark, and a scheduled check that the tree agrees with
  what PyPI has published.

## Next release (on `main`, unreleased)

- stdio, streamable HTTP (2026-07-28 and 2025-11-25) and SSE from one
  command line (ADR 0001).
- Runs on both supported majors of the `mcp` SDK through a
  compatibility shim; a fresh install gets 2.x.

## Beyond

No further work is scheduled. There are no open feature issues at the
time of writing. The gateway follows the family servers: when a family
gains a capability its server exposes through the shared core verbs, the
registry entry is updated here in the same release window.

## Out of scope (handled elsewhere)

- **Message generation, parsing and validation** - the family servers
  [`pain001-mcp`](https://github.com/sebastienrousseau/pain001-mcp),
  [`pacs008-mcp`](https://github.com/sebastienrousseau/pacs008-mcp),
  [`camt053-mcp`](https://github.com/sebastienrousseau/camt053-mcp) and
  [`acmt001-mcp`](https://github.com/sebastienrousseau/acmt001-mcp).
- **Reconciliation, ingestion and address remediation** - the
  specialised servers listed in the README's suite table; the gateway
  surfaces them through `search` and `list_servers` but does not invoke
  them.
