<!-- SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
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

## Coding standards

- **Style:** [PEP 8](https://peps.python.org/pep-0008/), formatted by
  [black](https://black.readthedocs.io/) at 79 columns and linted by
  [ruff](https://docs.astral.sh/ruff/) (`E`, `W`, `F`, `I`, `B`, `C4`,
  `UP`). Configuration is in `pyproject.toml`.
- **Types:** [PEP 484](https://peps.python.org/pep-0484/) annotations on
  every function, checked by `mypy` in strict mode.
- **Docstrings:** [PEP 257](https://peps.python.org/pep-0257/).
- **Licensing:** every file carries SPDX copyright and licence lines
  ([REUSE](https://reuse.software/)); `reuse lint` checks it.

Style, types and licensing are CI gates: a pull request that does not
comply cannot be merged. Docstrings are checked in review. No blanket suppressions; a specific inline one needs a comment
saying why.

## Test policy

**Every change that adds or changes behaviour adds or changes an automated
test in the same pull request.** A bug fix adds a regression test that
fails without the fix. This is enforced: the suite must keep 100% line and
branch coverage, and CI fails otherwise. New tools and new families also
extend the fuzz targets in `tests/test_fuzz.py` and `fuzz/fuzz_tools.py`.

## Code review

Every change reaches `main` through a pull request. A reviewer checks:

1. **Safety:** no caller-supplied string reaches an import or attribute
   lookup (see below); tools stay read-only; no new network or file
   access.
2. **Tests:** the test policy above, and that new tests fail without the
   change.
3. **Catalogue text:** tool and parameter descriptions describe only their
   own tool (`tests/test_catalog_text.py`).
4. **Dependencies:** any new or loosened constraint is justified, and none
   admits a version with a published advisory.
5. **Docs and changelog:** user-visible changes are in `CHANGELOG.md`, and
   `SECURITY.md` or the assurance case are updated when the trust
   boundary moves.
6. **Gates:** CI, CodeQL, fuzzing, DCO and version checks are green.

The project currently has one maintainer, so review is by the maintainer
and the automated gates; a second reviewer is a standing goal (see
[`GOVERNANCE.md`](GOVERNANCE.md)).

## Sign-off (Required)

Every commit **must** carry a `Signed-off-by:` trailer, which is you
certifying the [Developer Certificate of Origin](DCO.txt). `git commit -s`
adds it; the `DCO` workflow fails a pull request that lacks one. To fix an
existing branch: `git rebase --signoff main && git push --force-with-lease`.

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

## Decisions

A change that shapes the server (a new transport, a new family, a new
registration pattern) gets a record in [`docs/adr/`](docs/adr/index.md).

## The shared conformance file

`tests/test_suite_conformance.py` is generated from one canonical copy
shared across all 32 repositories. **Do not edit it here.**

## Versioning

**Versions increment by 0.0.1.** `0.1.0` follows `0.0.999`.

## Governance

Roles, decision making and how to become a maintainer are in
[`GOVERNANCE.md`](GOVERNANCE.md); the release process is in
[`RELEASING.md`](RELEASING.md).

## Licence

Apache-2.0 OR MIT, at your option.
