<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.0.11   | :white_check_mark: |
| < 0.0.11 | :x:                |

## Reporting a vulnerability

Report privately through
[GitHub Security Advisories](https://github.com/sebastienrousseau/iso20022-mcp/security/advisories/new).
Please do not open a public issue for a security problem.

## What this package is

A router. It resolves a message type to the family server that owns it and
delegates. It parses no XML, validates no schema, and holds no credentials.

That means **its security posture is mostly its dependencies' posture.** A
vulnerability in `pain001`, `pacs008`, `camt053` or `acmt001` reaches a user
through this package. Floors are kept current for that reason, and
`cryptography` is floored at 50.0.0 explicitly because nothing else in the
tree constrained it and a resolver was free to pick a version carrying a
high-severity advisory.

## Resolution is the thing to get right

`resolve(message_type, func_name)` imports a family module and looks up a
function by name. Two properties matter:

- **The name comes from the registry, not the caller.** Message types map to
  a fixed table of modules and function names in `registry.py`. A caller
  cannot ask the gateway to import an arbitrary module or call an arbitrary
  attribute.
- **A capability a family does not declare raises.** `camt.053` declares no
  generator; asking for one is refused rather than silently resolving to
  something else.

If you extend the registry, keep both. The moment a caller-supplied string
reaches an import, this becomes a very different package.

## Transports

The server speaks MCP over stdio by default. `--transport
streamable-http` and `--transport sse` open a listener that binds
`127.0.0.1` unless `--host` says otherwise and carries no authentication
or TLS of its own. Do not bind a routable address without a gateway in
front of it that adds both. Records handed to the tools are routed, not
executed; treat payment data passed through them as PII that reaches the
model's context and any transcript kept of it.

## Availability

Family servers are imported lazily, and each import costs roughly 550–630 ms
(see `benches/bench_gateway.py`). A caller that cycles through message types
it does not need can therefore force several seconds of import work in a
fresh process. It is bounded — four families, once each per process — but
worth knowing if you spawn a process per request.

## Continuous integration

- `ci.yml` runs ruff, black, mypy --strict, pytest with the 100%
  line+branch coverage gate and the benchmark on every push and pull
  request, on Python 3.10 to 3.14.
- `codeql.yml` runs GitHub's CodeQL Python analysis on every push, pull
  request and weekly.
- `scorecard.yml` publishes the OpenSSF Scorecard weekly; every action
  in every workflow is pinned by commit SHA.
- `dco.yml` requires a `Signed-off-by:` trailer on every commit.
- `mcp-inspect.yml` lists the tools through the MCP Inspector over
  stdio, streamable HTTP and SSE.
- `versions.yml` checks that every restatement of the version agrees;
  `release-consistency.yml` checks daily that the tree agrees with PyPI.
- Dependabot (`.github/dependabot.yml`) proposes pip and GitHub Actions
  updates weekly.
- `release.yml` publishes to PyPI through OIDC trusted publishing with
  SLSA build provenance, cosign signatures and SBOMs.
