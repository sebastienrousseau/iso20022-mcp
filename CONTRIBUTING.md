<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Contributing

Thanks for looking. This package routes; it does not do the work itself.

## Before you open a pull request

```sh
pip install -e ".[all]"
pip install pytest pytest-cov ruff black mypy
pytest                                     # tests plus the coverage gate
ruff check iso20022_mcp/ tests/ benches/
black --check iso20022_mcp/ tests/ benches/
mypy iso20022_mcp/
python benches/bench_gateway.py --quick    # the benchmark still runs
```

`pytest` fails below **100% branch coverage**.

**Install `[all]`.** Without the family extras the gateway resolves nothing,
and both the tests and the benchmark measure a degraded path rather than the
real one.

## The rule that keeps this package safe

`resolve()` imports a module and looks up a function by name. **Both come
from the registry table, never from the caller.** A change that lets a
caller-supplied string reach an import turns a router into an arbitrary-code
path. If you extend `registry.py`, extend the table.

## Adding a family

A family entry declares its module, its package, and which capabilities it
offers — `generate`, `parse`, or both. Families genuinely differ:
`camt.053` has no generator, `pain.001` no parse. Declare only what exists;
a capability a family does not have should raise rather than resolve to
something approximate.

`tests/test_extras_resolve.py` guards the constraint shapes that made
`[all]` unsatisfiable once before. If you add a family, add it there too.

## Benchmarks

`benches/` measures what the gateway *adds*, which is the only interesting
number for a router. Routing is currently ~11 µs at worst; the lazy family
import is ~550–630 ms and is the figure worth watching. It asserts no
threshold, but CI runs `--quick` so a benchmark that stops compiling fails
the build rather than rotting.

## The shared conformance file

`tests/test_suite_conformance.py` is generated from one canonical copy
shared across all 32 repositories. **Do not edit it here.**

## Versioning

**Versions increment by 0.0.1.** `0.1.0` follows `0.0.999`.

## Licence

Apache-2.0 OR MIT, at your option.
