<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Scope comparison

The comparison that matters for a gateway is with the alternative it
replaces: connecting an agent to each family server directly. No competitor
ranking or comparative performance claim is made.

Measured on 2026-10-20 over stdio with the MCP SDK client (`list_tools`),
mcp 2.3.0, Python 3.12. Catalogue size is the compact JSON of every tool
definition; tokens are estimated at four bytes per token.

| Setup | Servers to configure | Tools the agent sees | Catalogue size | Estimated tokens |
| :--- | ---: | ---: | ---: | ---: |
| **iso20022-mcp 0.0.17 with `[all]`** | 1 | 7 | 8,707 bytes | ~2,200 |
| pain001-mcp 0.0.73 | 1 | 26 | 63,142 bytes | ~15,800 |
| pacs008-mcp 0.0.14 | 1 | 16 | 27,054 bytes | ~6,800 |
| camt053-mcp 0.0.22 | 1 | 24 | 41,425 bytes | ~10,400 |
| acmt001-mcp 0.0.11 | 1 | 7 | 14,033 bytes | ~3,500 |
| All four family servers directly | 4 | 73 | 145,654 bytes | ~36,400 |

What the gateway gives up: it exposes the operations every family shares
(`describe`, `validate`, `generate`, `parse`), not each server's specialist
tools, such as camt053-mcp's MT940 migration or journal export. Connect a
family server directly when you need those.

To reproduce: install `iso20022-mcp[all]`, start each server's console
script over stdio, call `list_tools`, and measure the JSON of the result.
