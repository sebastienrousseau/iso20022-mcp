<!-- SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Benchmarks

`benches/bench_gateway.py` measures what the gateway adds on top of the
family server it delegates to. CI runs it with `--quick` as a smoke test.
Nothing asserts a threshold: wall-clock depends on hardware, Python and
dependency versions, and no hardware-independent claim is made.

```sh
pip install -e ".[all]"
python benches/bench_gateway.py           # full run
python benches/bench_gateway.py --quick   # what CI runs
python benches/bench_gateway.py --json
```

## Results, 2026-10-20

Apple A18 Pro (arm64), macOS, Python 3.12.15, mcp 2.3.0, `--quick`, with
every family installed.

### Routing: the bookkeeping every call pays

| Call | Time | Calls per second |
| :--- | ---: | ---: |
| `family_for` | 0.54 µs | 1,848,888 |
| `family_for` (unknown prefix) | 0.96 µs | 1,043,734 |
| `search_catalog` | 7.29 µs | 137,158 |
| `search_catalog` (miss) | 6.83 µs | 146,351 |
| `search_servers` | 14.54 µs | 68,767 |
| `family_summary` | 173.96 µs | 5,749 |
| `list_all_servers` | 182.63 µs | 5,476 |

### First call into a family, in a fresh interpreter

| Message type | Resolved to | Cold | Warm |
| :--- | :--- | ---: | ---: |
| `pain.001.001.09` | `generate_message` | 528.4 ms | 5.04 µs |
| `pacs.008.001.13` | `parse_message` | 500.3 ms | 4.71 µs |

Family servers are imported lazily, so the first request into each family
pays its import, about half a second here; later calls pay microseconds. A
long-lived server pays each import once. A worker that handles one message
and exits pays it every time, so preload the families you expect if
first-request latency matters.
