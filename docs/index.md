# iso20022-mcp

One gateway across every ISO 20022 family, so an agent learns one tool
instead of four.

```sh
pip install "iso20022-mcp[all]"
```

## What it is for

An agent that handles payments does not know in advance whether the next
message is a `pain.001`, a `pacs.008`, a `camt.053` or an `acmt.007`. Making
it learn a separate tool per family pushes routing into the prompt, which is
the worst place for it.

This gateway takes the message type and routes to the family server that
handles it. The agent asks once.

| Tool | What it does |
|---|---|
| `describe` | What a message type is, and which server owns it |
| `generate` | Build a message, routed to the owning family |
| `list_families` | Every family the gateway knows |
| `list_servers` | Every server in the suite, including the specialised ones |

## Capabilities differ by family

Worth knowing before you route: **not every family does everything.**

| Family | Generate | Parse |
|---|---|---|
| `pain.001` | yes | — |
| `pacs.008` | yes | `parse_message` |
| `camt.053` | — | `parse_statement` |
| `acmt.001` | yes | — |

`family_for(message_type)` returns the entry, including which functions are
available. Asking for a capability a family does not declare raises rather
than returning an empty result, which is the right way round — but it means
a caller that assumes uniformity will meet an exception.

## Installing families

The gateway itself is light. Families are extras, so you install only what
you route to:

```sh
pip install "iso20022-mcp[pain]"     # just pain.001
pip install "iso20022-mcp[all]"      # every family
```

`[all]` installs `pain001-mcp`, `pacs008-mcp`, `camt053-mcp` and
`acmt001-mcp`. The whole family tree resolves on a single `xmlschema` 4.x.

## Performance

[`benches/bench_gateway.py`](../benches/bench_gateway.py) answers the only
question a gateway has to: **how much does the indirection add?**

**Routing is free.** The dearest step is about 11 µs:

```
                    call        us     calls/sec
              family_for      1.5       ~660,000
          search_catalog      6.5       ~154,000
          search_servers     11.2        ~87,000
```

Beside a family server's own work — parsing XML, compiling a schema — that
is not measurable. The gateway costs nothing to have.

**The first call into a family is not free.** Family servers are imported
*lazily*, so the first request for each pays the import:

```
        message type          resolved    cold ms    warm us
     pain.001.001.09  generate_message      586        5.8
     pacs.008.001.13     parse_message      559        5.8
     camt.053.001.08   parse_statement      626        6.1
     acmt.007.001.05  generate_message      536        5.4
```

About **550–630 ms per family**, and roughly **2.3 s to load all four** —
paid once per process, then ~6 µs thereafter.

That is a deployment decision, not a curiosity:

- **A long-lived server** pays each import once. Nothing to do.
- **A short-lived worker** handling one message and exiting pays the import
  for whichever family it touches, every time. If that matters, preload the
  families you expect at start-up rather than discovering them one request
  at a time.

Measured in fresh interpreters, because timing it in-process reports a warm
cache and misses the point entirely.

## Related

Every family server can also be used directly:
[`pain001-mcp`](https://pypi.org/project/pain001-mcp/),
[`pacs008-mcp`](https://pypi.org/project/pacs008-mcp/),
[`camt053-mcp`](https://pypi.org/project/camt053-mcp/),
[`acmt001-mcp`](https://pypi.org/project/acmt001-mcp/).

## Licence

Apache-2.0 OR MIT, at your option.
