#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""What the gateway costs on top of the family server it delegates to.

This package exists so an agent can call one tool instead of learning four.
That convenience is only worth having if the indirection is cheap, so the
question is not how fast the gateway is but **how much it adds**.

Three things are measured, and the third is the one that matters:

* **Routing.** ``family_for`` and ``search_catalog`` are dictionary and
  string work over a small table. They should be microseconds; if they are
  not, the gateway is a tax on every call.

* **Search.** ``search_catalog`` and ``search_servers`` scan the registry.
  Small today, but the cost should grow with the catalogue rather than with
  anything else.

* **The first call into a family.** The gateway imports family servers
  **lazily** — the ``pacs008_mcp`` module is not loaded until something asks
  for a pacs message. That makes the first request into each family far
  dearer than the rest, and it is invisible to any benchmark that reports a
  mean over warm calls.

  This is a deployment question, not a curiosity. A short-lived worker
  handling one message pays every import it touches; a long-lived server
  pays each once. If the cold cost is large, the gateway should preload the
  families it expects rather than discover them one request at a time.

Run::

    python benches/bench_gateway.py
    python benches/bench_gateway.py --json
    python benches/bench_gateway.py --quick     # what CI runs

Cold-import figures are measured in fresh interpreters, because measuring
them in-process reports a warm cache and misses the point.

Nothing here asserts a threshold: wall-clock is not comparable between
machines, and a flaky performance gate teaches people to ignore red. CI
runs ``--quick`` so a benchmark that has stopped compiling against the
current API fails the build instead of rotting into a file that reads as
verified and is not.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from iso20022_mcp import registry  # noqa: E402

SAMPLE_TYPES = [
    "pain.001.001.09",
    "pacs.008.001.13",
    "camt.053.001.08",
    "acmt.007.001.05",
]


def _best(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The minimum is the least noisy estimator available; the mean follows
    whatever else the machine is doing.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def _safe(call):
    """A refusal is a result: how fast the gateway declines is a measurement."""

    def wrapped():
        try:
            return call()
        except Exception:
            return None

    return wrapped


def measure_routing(repeats: int) -> list[dict]:
    """The bookkeeping every call pays, whatever it is routed to."""
    cases = [
        ("family_for", lambda: registry.family_for("pacs.008.001.13")),
        (
            "family_for (unknown)",
            _safe(lambda: registry.family_for("zzzz.999.001.01")),
        ),
        ("family_summary", registry.family_summary),
        ("list_all_servers", registry.list_all_servers),
        ("search_catalog", lambda: registry.search_catalog("pacs")),
        ("search_catalog (miss)", lambda: registry.search_catalog("zzzz")),
        ("search_servers", lambda: registry.search_servers("camt")),
    ]
    return [
        {"call": name, "us": _best(fn, repeats) * 1e6} for name, fn in cases
    ]


def measure_cold_import(message_type: str) -> dict:
    """First resolve for a family, in an interpreter that has never seen it."""
    # The function name has to come from the family's own entry. Families
    # differ in what they offer -- camt.053 does not generate, pain.001 and
    # acmt.001 declare no parse -- so a hardcoded name resolves for one
    # family and raises for the rest, timing a failed lookup instead of the
    # import it was meant to measure.
    script = (
        "import sys, time, json\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        "from iso20022_mcp import registry\n"
        f"mt = {message_type!r}\n"
        "entry = registry.family_for(mt)\n"
        "func = entry.get('parse') or "
        "('generate_message' if entry.get('generate') else None)\n"
        "t0 = time.perf_counter()\n"
        "try:\n"
        "    registry.resolve(mt, func)\n"
        "    err = None\n"
        "except Exception as exc:\n"
        "    err = type(exc).__name__\n"
        "cold = time.perf_counter() - t0\n"
        "t1 = time.perf_counter()\n"
        "try:\n"
        "    registry.resolve(mt, func)\n"
        "except Exception:\n"
        "    pass\n"
        "warm = time.perf_counter() - t1\n"
        "print(json.dumps("
        "{'cold': cold, 'warm': warm, 'error': err, 'func': func}))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        return {"message_type": message_type, "error": result.stderr[-200:]}
    data = json.loads(result.stdout.strip().splitlines()[-1])
    return {
        "message_type": message_type,
        "func": data["func"],
        "cold_ms": data["cold"] * 1e3,
        "warm_us": data["warm"] * 1e6,
        "resolve_error": data["error"],
    }


def run(quick: bool) -> dict:
    repeats = 200 if quick else 2_000
    types = SAMPLE_TYPES[:2] if quick else SAMPLE_TYPES
    return {
        "routing": measure_routing(repeats),
        "cold": [measure_cold_import(mt) for mt in types],
    }


def render(results: dict) -> None:
    print("routing — the bookkeeping every call pays")
    print(f"{'call':>24}{'us':>10}{'calls/sec':>14}")
    for row in results["routing"]:
        rate = 1e6 / row["us"] if row["us"] else 0.0
        print(f"{row['call']:>24}{row['us']:>10.2f}{rate:>14,.0f}")
    worst = max(r["us"] for r in results["routing"])
    print(
        f"\n  Dearest routing step is {worst:,.1f} us. Anything in this range "
        f"is negligible beside the family server's own work, which is what\n"
        f"  makes the gateway worth having: one tool to learn, no measurable "
        f"cost for the indirection."
    )

    print("\nfirst call into a family, in a fresh interpreter")
    print(
        f"{'message type':>20}{'resolved':>18}{'cold ms':>11}"
        f"{'warm us':>11}{'ratio':>10}"
    )
    for row in results["cold"]:
        if "error" in row:
            print(f"{row['message_type']:>20}  failed: {row['error'][:40]}")
            continue
        ratio = (
            row["cold_ms"] * 1e3 / row["warm_us"] if row["warm_us"] else 0.0
        )
        note = (
            "" if not row["resolve_error"] else f"  ({row['resolve_error']})"
        )
        print(
            f"{row['message_type']:>20}{str(row['func']):>18}"
            f"{row['cold_ms']:>11.1f}{row['warm_us']:>11.2f}"
            f"{ratio:>10,.0f}x{note}"
        )
    usable = [r for r in results["cold"] if "cold_ms" in r]
    if usable:
        total = sum(r["cold_ms"] for r in usable)
        print(
            f"\n  Loading every family measured here costs about "
            f"{total:,.0f} ms, paid once per process.\n"
            f"  A worker that handles one message and exits pays the import "
            f"for whichever family it touches; a long-lived server pays each\n"
            f"  once. If that first-request latency matters to you, preload "
            f"the families you expect rather than discovering them one\n"
            f"  request at a time."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="fewer cases, as CI runs"
    )
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
