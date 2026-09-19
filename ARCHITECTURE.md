<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# iso20022-mcp Architecture

A map of the codebase for new contributors and maintainers. The goal is
that anyone can navigate, extend, and reason about iso20022-mcp without
prior context.

## The pipeline

```
MCP client (Claude Desktop, IDE, agent)
        |  stdio, streamable HTTP or SSE (JSON-RPC)
        v
iso20022_mcp/server.py       (MCP server: 7 meta-tools, 3 resources, 1 prompt)
        |  message type -> family
        v
iso20022_mcp/registry.py     (FAMILIES table, CATALOG, lazy import, resolve)
        |  one backing server per family, imported on first use
        v
pain001_mcp / pacs008_mcp / camt053_mcp / acmt001_mcp / camt_exceptions
        v
ISO 20022 XML / structured data
```

The gateway does no ISO 20022 work of its own. Every meta-tool maps a
message type to the family that owns it and delegates to that family's
`-mcp` server, which is an optional extra (`pip install
"iso20022-mcp[all]"` installs the four families). The core depends only
on `mcp`; a family that is not installed reports as such and returns an
actionable `{"error": ...}` payload naming the package to install.

## Module map

| Area | Module | Responsibility |
| :--- | :--- | :--- |
| **Server** | `iso20022_mcp/server.py` | The MCP server, all tool / resource / prompt registrations |
| **Entry point** | `iso20022_mcp.server:main` (console script: `iso20022-mcp`) | Launches the server over stdio, or over streamable HTTP / SSE with `--transport` (`_cli.py` + `_transports.py`, ADR 0001) |
| **Registry** | `iso20022_mcp/registry.py` | The `FAMILIES` table (module, package, capabilities per family), the `CATALOG` that `search` scans, the specialised-server map, and `resolve()`: lazy import plus function lookup, both keyed by the table and never by the caller |
| **SDK shim** | `iso20022_mcp/_mcp_compat.py` | Builds the server on either supported major of the `mcp` SDK (2.x `MCPServer`, 1.x `FastMCP`) |
| **Adapters** | `iso20022_mcp/adapters.py` | Wraps the registered tools as LangChain, CrewAI or LlamaIndex tools; each framework is an optional extra imported only when its adapter is called |
| **Version** | `iso20022_mcp/__init__.py` | Single source of truth (`__version__`) |
| **Tests** | `tests/test_server.py`, `tests/test_registry.py`, `tests/test_adapters.py`, `tests/test_transports.py`, `tests/test_mcp_sdk_compat.py`, `tests/test_extras_resolve.py`, `tests/test_suite_conformance.py` | Meta-tool surface (backends faked through `registry._load_module`), dispatch, adapters, the command line, the SDK shim, the extras' constraint shapes, and the shared suite conformance gate |
| **Examples** | `examples/mcp_tools.py` | Runnable in-process walkthrough of the meta-tools |
| **Benchmarks** | `benches/bench_gateway.py` | What the indirection adds (routing) and what the first call into a family costs (lazy import); `docs/index.md` explains the result |
| **Release helpers** | `scripts/verify_versions.py`, `scripts/check_suite_consistency.py` | Assert every restatement of the version agrees; compare the tree against what PyPI has published |

## Tools, resources, prompts

The current MCP surface:

- **Tools** - `search`, `list_families`, `list_servers`, `describe`,
  `validate`, `generate` (pain, pacs, acmt and the camt.056/camt.029
  exceptions messages) and `parse` (pacs and camt). All seven are
  read-only, idempotent and closed-world: nothing opens a caller-supplied
  path or reaches the network.
- **Resources** - `iso20022://families` (the family catalogue as JSON),
  `iso20022://servers` (the whole suite map) and
  `iso20022://describe/{message_type}` (required fields plus the input
  JSON Schema of one type).
- **Prompts** - `route_iso20022_task(goal=...)`, which teaches the model
  the search -> describe -> validate -> generate / parse order.

## Key design decisions

- **Routing, not duplication.** The gateway resolves a message type to a
  family and calls that family's server. New behaviour belongs in the
  family server; the gateway only learns where to send it.
- **The table decides what can be imported.** `resolve()` reads the
  module and function name from `registry.FAMILIES`, never from the
  caller. A capability a family does not declare raises rather than
  resolving to something approximate (`camt.053` has no generator;
  `pain.001` has no parser).
- **Errors as data.** Tools never raise. A `ValueError` from the
  registry, and any exception a backing server raises, is turned into an
  `{"error": ...}` payload so the agent can act on it.
- **Lazy, optional families.** Importing a family costs roughly
  550-630 ms once per process (see `benches/`); a long-lived server pays
  it once, a per-request worker should preload.
- **Loopback by default.** stdio needs no socket. The HTTP transports
  bind `127.0.0.1` unless told otherwise and add no authentication of
  their own; a routable deployment sits behind a gateway (ADR 0001).
- **Coverage enforced at 100%** line+branch; only the branches of the SDK
  shim that the installed major cannot reach are `# pragma: no cover`.

## Extension points

- **Add a family:** add an entry to `registry.FAMILIES` (module, package,
  `generate`, `parse`), a CATALOG entry per message type, an extra in
  `pyproject.toml`, and the constraint-shape assertions in
  `tests/test_extras_resolve.py`.
- **Add a meta-tool:** add a function under `@server.tool(...)` in
  `iso20022_mcp/server.py`; pair it with tests in `tests/test_server.py`
  and add it to `EXPECTED_TOOLS` there.
- **Add a resource:** `@server.resource("iso20022://...")` decorator.
- **Add a prompt:** `@server.prompt()` decorator.
- **Add a framework adapter:** an `as_<framework>_tools()` function in
  `iso20022_mcp/adapters.py` with a matching optional extra.

## Where to look first

- Runnable example: [`examples/`](examples/)
- Decisions: [`docs/adr/`](docs/adr/index.md)
- Roadmap: [`ROADMAP.md`](ROADMAP.md)
- Release process: [`RELEASING.md`](RELEASING.md)
- Family servers: [`pain001-mcp`](https://github.com/sebastienrousseau/pain001-mcp),
  [`pacs008-mcp`](https://github.com/sebastienrousseau/pacs008-mcp),
  [`camt053-mcp`](https://github.com/sebastienrousseau/camt053-mcp),
  [`acmt001-mcp`](https://github.com/sebastienrousseau/acmt001-mcp)
