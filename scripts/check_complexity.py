#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Fail when a function or file exceeds the complexity limits.

Per function: cyclomatic complexity at most 10, Halstead difficulty at most
30, at most 60 lines. Per file: at most 500 lines. Cognitive complexity (at
most 15) is checked by ``complexipy`` in the same CI job.

The baseline of accepted offenders is empty: every file checked today is
within the limits, so any offender is new and fails the build.

Run::

    python scripts/check_complexity.py              # the default paths
    python scripts/check_complexity.py some/dir     # anything else
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterator
from pathlib import Path

from radon.complexity import cc_visit
from radon.metrics import h_visit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = ("iso20022_mcp", "scripts", "benches", "fuzz", "examples")
MAX_CYCLOMATIC = 10
MAX_HALSTEAD_DIFFICULTY = 30.0
MAX_FUNCTION_LINES = 60
MAX_FILE_LINES = 500


def python_files(paths: list[str]) -> Iterator[Path]:
    """Every ``.py`` file under ``paths``, in a stable order."""
    for raw in paths:
        path = Path(raw)
        yield from sorted(path.rglob("*.py")) if path.is_dir() else [path]


def problems_in(path: Path) -> list[str]:
    """Every limit ``path`` exceeds, one line each."""
    source = path.read_text(encoding="utf-8")
    found: list[str] = []
    lines = len(source.splitlines())
    if lines > MAX_FILE_LINES:
        found.append(f"{path}: {lines} lines (max {MAX_FILE_LINES})")
    for block in cc_visit(source):
        if block.complexity > MAX_CYCLOMATIC:
            found.append(
                f"{path}:{block.lineno} {block.name}: cyclomatic "
                f"{block.complexity} (max {MAX_CYCLOMATIC})"
            )
    for name, report in h_visit(source).functions:
        if report.difficulty > MAX_HALSTEAD_DIFFICULTY:
            found.append(
                f"{path} {name}: Halstead difficulty "
                f"{report.difficulty:.1f} (max {MAX_HALSTEAD_DIFFICULTY:.0f})"
            )
    found += _long_functions(path, source)
    return found


def _long_functions(path: Path, source: str) -> list[str]:
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > MAX_FUNCTION_LINES:
                found.append(
                    f"{path}:{node.lineno} {node.name}: {length} lines "
                    f"(max {MAX_FUNCTION_LINES})"
                )
    return found


def main(argv: list[str]) -> int:
    paths = argv or [str(ROOT / p) for p in DEFAULT_PATHS]
    problems = [p for f in python_files(paths) for p in problems_in(f)]
    for problem in problems:
        print(f"ERROR: {problem}")
    if problems:
        return 1
    print("OK: every function and file is within the complexity limits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
