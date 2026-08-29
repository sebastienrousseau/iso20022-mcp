<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.10] - 2026-08-29

### Fixed

- **`poetry install` no longer fails on Python 3.14.** The optional
  `crewai` extra caps Python at `<3.14` and carried no marker of its own,
  while this project allows `<4.0`. On a 3.14 interpreter the resolver
  therefore refused to solve at all — even though `crewai` is optional and
  nothing in the package imports it.

  That broke the **SBOM job** in the release workflow, which runs
  `poetry install --only main`. The 0.0.9 release published to PyPI
  successfully and the SBOM step failed beside it, which is the confusing
  combination this fixes: a green package and a red workflow.

  The fault was pre-existing rather than introduced by 0.0.9 — it
  reproduces on the previous commit — but it surfaced when 0.0.9's release
  ran on a 3.14 runner.

## [0.0.9] - 2026-08-29

Brings this repository onto the suite conformance gate. It had no
`CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `docs/` or `benches/`.

### Added

- **`benches/bench_gateway.py`**, which answers the only question a gateway
  has to: how much does the indirection add?

  **Routing is free.** The dearest step is about **11 µs** — negligible
  beside a family server parsing XML or compiling a schema. The gateway
  costs nothing to have.

  **The first call into a family is not.** Family servers are imported
  lazily, so the first request for each pays roughly **550–630 ms**, and
  about **2.3 s** to load all four. Thereafter it is ~6 µs.

  That is a deployment decision. A long-lived server pays each import once
  and can ignore it; a short-lived worker handling one message pays for
  whichever family it touches, every time, and should preload rather than
  discover families one request at a time.

  Measured in fresh interpreters — timing it in-process reports a warm
  cache and misses the point.

- **`docs/index.md`**, including a table of what each family actually
  offers. **Capabilities are not uniform**: `camt.053` declares no
  generator, `pain.001` and `acmt.001` no parse. A caller assuming
  uniformity meets an exception, which is the right way round but deserves
  writing down.

- **`SECURITY.md`**, recording that this package's posture is mostly its
  dependencies' posture, and the one property that keeps `resolve()` safe:
  the module and function names come from the registry table, never from
  the caller.

- **`CONTRIBUTING.md`**, which says to install `[all]` — without the family
  extras both the tests and the benchmark measure a degraded path.

- **`tests/test_suite_conformance.py`** — invariants shared across the
  suite, vendored from one canonical copy and checksummed by its own test.

### Changed

- CI lints, formats and runs `benches/` alongside everything else.

## [0.0.8] - 2026-08-28

### Fixed

- **`iso20022-mcp[all]` resolves again.** The `pain001-mcp` cap at
  `<0.0.61` is gone, because the reason for it is: `camt053` 0.0.17 and
  `acmt001` 0.0.5 both moved to `xmlschema >=4.3.2`, so the whole family
  now installs on a single `xmlschema` 4.x.

- **`__version__` matched the distribution.** 0.0.7 published to PyPI with
  `__version__` still reading `0.0.6`, so a client asking the server which
  version it was talking to got the wrong answer for a whole release.

### Added

- `tests/test_extras_resolve.py`, guarding both failures above.

[0.0.9]: https://github.com/sebastienrousseau/iso20022-mcp/releases/tag/v0.0.9
[0.0.8]: https://github.com/sebastienrousseau/iso20022-mcp/releases/tag/v0.0.8
