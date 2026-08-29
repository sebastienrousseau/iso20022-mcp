<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.0.9   | :white_check_mark: |
| < 0.0.9 | :x:               |

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

## Availability

Family servers are imported lazily, and each import costs roughly 550–630 ms
(see `benches/bench_gateway.py`). A caller that cycles through message types
it does not need can therefore force several seconds of import work in a
fresh process. It is bounded — four families, once each per process — but
worth knowing if you spawn a process per request.
