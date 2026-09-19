<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Getting support

Thanks for using iso20022-mcp. Here's the fastest way to get help, by need.

## Questions & how-to

- **Read first:** the [README](README.md), the runnable
  [`examples/`](examples/) walkthrough, and the family server that owns
  your message type ([`pain001-mcp`](https://github.com/sebastienrousseau/pain001-mcp),
  [`pacs008-mcp`](https://github.com/sebastienrousseau/pacs008-mcp),
  [`camt053-mcp`](https://github.com/sebastienrousseau/camt053-mcp),
  [`acmt001-mcp`](https://github.com/sebastienrousseau/acmt001-mcp))
  for message-type background.
- **Still stuck?** Open a question issue at
  <https://github.com/sebastienrousseau/iso20022-mcp/issues/new>. Include
  your Python version, the `iso20022-mcp` version
  (`iso20022-mcp --version`), which family extras are installed
  (`list_families` reports it), your MCP client (Claude Desktop / IDE /
  agent), the transport you run, and a minimal reproducer.

## Bugs

Open a bug report at
<https://github.com/sebastienrousseau/iso20022-mcp/issues/new> with a
minimal reproducer, the meta-tool name, the message type, the arguments,
and the full error payload. If the error comes from a family server, the
payload names it; a report there may be the faster route.

## Feature requests

Open a feature request at
<https://github.com/sebastienrousseau/iso20022-mcp/issues/new>. New
catalogue entries, families and framework adapters are especially
welcome - see [ARCHITECTURE.md](ARCHITECTURE.md) for the extension
points and [ROADMAP.md](ROADMAP.md) for what's planned.

## Security

**Do not** open public issues for vulnerabilities. Follow the private
disclosure process in [SECURITY.md](SECURITY.md).

## Contributing & maintaining

See [CONTRIBUTING.md](CONTRIBUTING.md) and [GOVERNANCE.md](GOVERNANCE.md).

## Supported versions

Fixes land on the latest release line. See [SECURITY.md](SECURITY.md) for
the supported-version policy. iso20022-mcp requires Python 3.10+.
