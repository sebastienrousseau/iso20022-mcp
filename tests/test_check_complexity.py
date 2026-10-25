# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The complexity gate catches each limit, and the tree passes it."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_complexity", ROOT / "scripts" / "check_complexity.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _branchy() -> str:
    body = "".join(
        f"    if x == {i}:\n        return {i}\n" for i in range(11)
    )
    return f"def branchy(x):\n{body}    return -1\n"


def _long() -> str:
    body = "".join(f"    y{i} = {i}\n" for i in range(60))
    return f"def long():\n{body}    return 0\n"


def _difficult() -> str:
    # Halstead difficulty is (distinct operators / 2) * (operands /
    # distinct operands): one operand under twelve operators.
    ops = ["+", "-", "*", "/", "//", "%", "**", "<<", ">>", "&", "|", "^"]
    body = "".join(f"    c = c {op} c\n" for op in ops * 2)
    return f"def difficult(c):\n{body}    return c\n"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (_branchy(), "cyclomatic 12"),
        (_long(), "62 lines (max 60)"),
        (_difficult(), "Halstead difficulty"),
        ("x = 1\n" * 501, "501 lines (max 500)"),
    ],
    ids=["cyclomatic", "function-lines", "halstead", "file-lines"],
)
def test_each_limit_is_caught(
    tmp_path: Path, source: str, expected: str
) -> None:
    path = tmp_path / "offender.py"
    path.write_text(source, encoding="utf-8")
    problems = _gate().problems_in(path)
    assert any(expected in p for p in problems), problems


def test_the_tree_is_within_the_limits(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _gate().main([]) == 0
    assert "OK" in capsys.readouterr().out


def test_an_offender_fails_the_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "bad.py").write_text(_branchy(), encoding="utf-8")
    assert _gate().main([str(tmp_path)]) == 1
    assert "ERROR" in capsys.readouterr().out
