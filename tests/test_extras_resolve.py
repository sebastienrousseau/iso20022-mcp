# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Guards for the two things this package has already shipped wrong.

Neither failure was visible from inside the repository, which is why both
reached PyPI.

**`[all]` was unsatisfiable.** 0.0.6 raised the `pain001-mcp` floor past the
release where `pain001` moved to `xmlschema` 4, while `camt053` and `acmt001`
were still capped below it. Nothing here failed — the family servers are
optional, so the test suite never installs them. A user running
``pip install iso20022-mcp[all]`` got `ResolutionImpossible` with no
indication of which of the four constraints was responsible.

**`__version__` disagreed with the distribution.** 0.0.7 published to PyPI
with ``__version__ = "0.0.6"`` still in the source, so a client asking the
server which version it was talking to got the wrong answer.

These tests read `pyproject.toml` rather than a resolver, so they run offline
and in a few milliseconds. They cannot prove a resolution succeeds; they catch
the specific shape of constraint that made it fail.
"""

from __future__ import annotations

import sys
from pathlib import Path

import iso20022_mcp

if sys.version_info >= (3, 11):  # pragma: no cover - version dependent
    import tomllib
else:  # pragma: no cover - version dependent
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"

# The release at which each family library moved to xmlschema >=4.3.2, and the
# first server release that requires it. Below these, the package pulls in
# xmlschema 3 and cannot be installed beside the others.
XMLSCHEMA_4_FLOORS = {
    "pain001-mcp": "0.0.62",
    "camt053-mcp": "0.0.17",
    "acmt001-mcp": "0.0.8",
}


def _poetry() -> dict:
    with PYPROJECT.open("rb") as handle:
        return dict(tomllib.load(handle)["tool"]["poetry"])


def _dependencies() -> dict:
    return dict(_poetry()["dependencies"])


def _spec(name: str) -> str:
    raw = _dependencies()[name]
    spec = raw if isinstance(raw, str) else raw["version"]
    # Poetry accepts space-separated constraints as an implicit AND; PEP 440
    # does not. Normalise so an unparseable spec fails the assertion rather
    # than raising out of the parser.
    return ",".join(str(spec).split())


def test_the_family_servers_all_require_xmlschema_4() -> None:
    """Every server in `[all]` must sit at or above its xmlschema-4 floor.

    A single one left behind takes the whole extra down, and it takes it down
    for the user rather than for CI.
    """
    from packaging.requirements import Requirement
    from packaging.version import Version

    behind = []
    for name, floor in XMLSCHEMA_4_FLOORS.items():
        requirement = Requirement(f"{name}{_spec(name)}")
        if requirement.specifier.contains(Version("0.0.1")):
            behind.append(f"{name} has no floor at all")
        elif not requirement.specifier.contains(Version(floor)):
            behind.append(f"{name}{_spec(name)} excludes {floor}")

    assert not behind, (
        "these constraints cannot resolve together, so "
        "`pip install iso20022-mcp[all]` fails: " + "; ".join(behind)
    )


def test_no_family_server_is_capped_below_its_xmlschema_4_release() -> None:
    """An upper cap is how 0.0.6 broke, and it broke silently.

    A floor that is too low still resolves — to the wrong thing. A cap that
    excludes the xmlschema-4 release resolves to nothing at all.
    """
    from packaging.requirements import Requirement
    from packaging.version import Version

    for name, floor in XMLSCHEMA_4_FLOORS.items():
        specifier = Requirement(f"{name}{_spec(name)}").specifier
        assert specifier.contains(Version(floor)), (
            f"{name}{_spec(name)} excludes {floor}, the release that moved "
            f"to xmlschema 4 — `iso20022-mcp[all]` cannot resolve"
        )
        # And nothing newer is excluded either: a cap added later would
        # reintroduce exactly the 0.0.6 failure.
        assert specifier.contains(Version("9.9.9")), (
            f"{name}{_spec(name)} carries an upper cap. That is what made "
            f"0.0.6 unsatisfiable; add one only with a test that says why"
        )


def test_every_server_in_the_all_extra_is_a_declared_dependency() -> None:
    """An extra naming an undeclared package is a poetry error at build time.

    Cheap to assert, and it fails here rather than in a release job.
    """
    poetry = _poetry()
    declared = set(poetry["dependencies"])
    for name in poetry["extras"]["all"]:
        assert name in declared, f"[all] names {name}, which is not declared"


def test_the_all_extra_covers_every_family_server() -> None:
    """`[all]` must mean all of them, or the name is a lie."""
    poetry = _poetry()
    listed = set(poetry["extras"]["all"])
    assert set(XMLSCHEMA_4_FLOORS) <= listed, (
        f"[all] is missing {set(XMLSCHEMA_4_FLOORS) - listed}"
    )


def test_dunder_version_matches_pyproject() -> None:
    """0.0.7 shipped to PyPI with `__version__` still reading 0.0.6.

    Nothing failed: the number is only ever read by a client asking the
    server what it is talking to, and it answered wrongly for a whole release.
    """
    declared = str(_poetry()["version"])
    assert iso20022_mcp.__version__ == declared, (
        f"iso20022_mcp.__version__ is {iso20022_mcp.__version__!r} but "
        f"pyproject.toml says {declared!r}"
    )
