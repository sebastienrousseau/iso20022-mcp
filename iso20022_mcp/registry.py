# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Family registry and dispatch for the unified ISO 20022 gateway.

The gateway presents ONE small set of meta-tools that route across the ISO
20022 message families -- ``pain`` (initiation), ``pacs`` (interbank), ``camt``
(statements) and ``acmt`` (account management) -- so an agent sees a handful of
verbs instead of the 60+ tools spread across the five individual servers.

Each family is backed by its dedicated ``-mcp`` server, imported *lazily and
optionally*: the gateway core depends only on ``mcp``, and a family's server is
installed on demand (``pip install pacs008-mcp``). Dispatch loads the backing
module through :func:`_load_module` -- a single indirection point -- and raises
a clear, actionable :class:`ValueError` if the family is unknown, the backing
package is not installed, or the requested operation is unsupported for that
family (e.g. generating a ``camt.053`` statement, which is an inbound format).

The backing servers share identical signatures for the core verbs, discovered
from their source:

* ``list_message_types()``
* ``get_required_fields(message_type)``
* ``get_input_schema(message_type)``
* ``validate_records(message_type, records)``
* ``generate_message(message_type, records)``  (pain / pacs / acmt only)
* parse: ``parse_message(xml)`` (pacs) / ``parse_statement(xml)`` (camt)
"""

from __future__ import annotations

import importlib
import re
from collections.abc import Callable
from typing import Any, cast

# Family prefix -> backing server and capabilities. ``parse`` names the backing
# parse function (parse signatures differ per family) or is None when the
# family exposes no parser through its server.
FAMILIES: dict[str, dict[str, Any]] = {
    "pain": {
        "family": "pain.001",
        "title": "Customer Credit Transfer Initiation",
        "module": "pain001_mcp.server",
        "package": "pain001-mcp",
        "generate": True,
        "parse": None,
    },
    "pacs": {
        "family": "pacs.008",
        "title": "FI to FI Customer Credit Transfer",
        "module": "pacs008_mcp.server",
        "package": "pacs008-mcp",
        "generate": True,
        "parse": "parse_message",
    },
    "camt": {
        "family": "camt.053",
        "title": "Bank to Customer Statement",
        "module": "camt053_mcp.server",
        "package": "camt053-mcp",
        "generate": False,
        "parse": "parse_statement",
    },
    "acmt": {
        "family": "acmt.001",
        "title": "Account Opening Instruction",
        "module": "acmt001_mcp.server",
        "package": "acmt001-mcp",
        "generate": True,
        "parse": None,
    },
}

# Exceptions & Investigations message types are routed to the camt-exceptions
# server (not camt053-mcp, which handles statements). Its generate_message
# takes a single record and validates against the XSD internally.
EI_MESSAGE_TYPES: dict[str, str] = {
    "camt.056.001.12": "FI to FI Payment Cancellation Request",
    "camt.029.001.14": "Resolution of Investigation",
}
_EI_MODULE = "camt_exceptions.server"
_EI_PACKAGE = "camt-exceptions"

# Specialized suite servers that are not message-family generators. The gateway
# surfaces them for discovery (search / list_servers); they are invoked
# directly via their own tools rather than the gateway's generate/validate.
SPECIALIZED_SERVERS: list[dict[str, Any]] = [
    {
        "name": "reconcile-mcp",
        "package": "reconcile-mcp",
        "title": "Statement/payment reconciliation",
        "does": (
            "Match camt.053 statement entries against expected pain.001 "
            "payments: exact, partial, one-to-many and many-to-one, with "
            "explainable results."
        ),
        "keywords": [
            "reconcile",
            "reconciliation",
            "matching",
            "statement vs payment",
            "unmatched",
        ],
    },
    {
        "name": "camt-exceptions",
        "package": "camt-exceptions",
        "title": "Exceptions & Investigations",
        "does": (
            "Generate XSD-valid camt.056 payment cancellation and camt.029 "
            "resolution-of-investigation messages."
        ),
        "keywords": [
            "cancel",
            "cancellation",
            "recall",
            "investigation",
            "exception",
            "camt.056",
            "camt.029",
        ],
    },
    {
        "name": "ap2-iso20022",
        "package": "ap2-iso20022",
        "title": "Agent-payment mandate bridge",
        "does": (
            "Bridge AP2 / x402 agent-payment mandates into wire-valid "
            "pain.001 / pacs.008 records, with spending-cap and expiry "
            "guardrails."
        ),
        "keywords": [
            "ap2",
            "x402",
            "agent payment",
            "agentic",
            "mandate",
            "authorisation",
        ],
    },
]

# Curated catalogue for keyword/use-case search. Kept small and human: it maps
# what people *say they want to do* to the right message type and family.
CATALOG: list[dict[str, Any]] = [
    {
        "message_type": "pain.001",
        "family": "pain",
        "name": "Customer Credit Transfer Initiation",
        "keywords": [
            "payment initiation",
            "credit transfer",
            "make a payment",
            "outgoing payment",
            "pay supplier",
            "salary",
            "payroll",
            "initiate",
        ],
    },
    {
        "message_type": "pacs.008",
        "family": "pacs",
        "name": "FI to FI Customer Credit Transfer",
        "keywords": [
            "interbank",
            "settlement",
            "wire",
            "correspondent banking",
            "cbpr+",
            "swift mx",
            "fi to fi",
        ],
    },
    {
        "message_type": "camt.053",
        "family": "camt",
        "name": "Bank to Customer Statement",
        "keywords": [
            "statement",
            "end of day",
            "reconciliation",
            "booked entries",
            "closing balance",
            "eod",
        ],
    },
    {
        "message_type": "camt.052",
        "family": "camt",
        "name": "Bank to Customer Account Report",
        "keywords": [
            "intraday",
            "account report",
            "provisional",
            "interim balance",
        ],
    },
    {
        "message_type": "acmt.001",
        "family": "acmt",
        "name": "Account Opening Instruction",
        "keywords": [
            "account opening",
            "onboarding",
            "open an account",
            "kyc",
            "account management",
        ],
    },
]


def _load_module(module_name: str) -> Any:
    """Import a backing server module by name.

    Single indirection point for dispatch, so tests can inject fake family
    modules without installing the real (heavy) servers.
    """
    return importlib.import_module(module_name)


def family_for(message_type: str) -> dict[str, Any]:
    """Return the family record for a message type (matched on its prefix).

    Raises:
        ValueError: if the prefix is not one of the known families.
    """
    prefix = str(message_type).split(".")[0].strip().lower()
    fam = FAMILIES.get(prefix)
    if fam is None:
        known = ", ".join(sorted(FAMILIES))
        raise ValueError(
            f"unknown ISO 20022 family for {message_type!r}; "
            f"supported prefixes: {known}"
        )
    return fam


def resolve(message_type: str, func_name: str) -> Callable[..., Any]:
    """Resolve a backing callable for ``message_type``'s family.

    Loads the family's server module (installing guidance in the error if it is
    absent) and returns the named function.

    Raises:
        ValueError: unknown family, backing package not installed, or the
            function is missing on the backing module.
    """
    fam = family_for(message_type)
    try:
        module = _load_module(fam["module"])
    except ImportError as exc:
        raise ValueError(
            f"{fam['family']} operations need the '{fam['package']}' package. "
            f"Install it with: pip install {fam['package']}"
        ) from exc
    func = getattr(module, func_name, None)
    if func is None:  # pragma: no cover - defensive; siblings share the API
        raise ValueError(
            f"backing server for {fam['family']} has no {func_name!r}"
        )
    return cast("Callable[..., Any]", func)


def family_summary() -> list[dict[str, Any]]:
    """Summarise every family: capabilities, backing package, install status."""
    rows: list[dict[str, Any]] = []
    for prefix, fam in FAMILIES.items():
        try:
            _load_module(fam["module"])
            installed = True
        except ImportError:
            installed = False
        rows.append(
            {
                "prefix": prefix,
                "family": fam["family"],
                "title": fam["title"],
                "package": fam["package"],
                "installed": installed,
                "operations": _operations(fam),
            }
        )
    return rows


def _operations(fam: dict[str, Any]) -> list[str]:
    """The verbs supported for a family, given its capabilities."""
    ops = ["describe", "validate"]
    if fam["generate"]:
        ops.append("generate")
    if fam["parse"]:
        ops.append("parse")
    return ops


def _matches(query: str, haystack: str) -> bool:
    """Token-aware match: any query word (>=3 chars) appearing in ``haystack``.

    Handles natural-language queries ("cancel a payment"), not just single
    keywords. Empty query matches everything; a query of only short words falls
    back to a raw substring test.
    """
    q = query.strip().lower()
    if not q:
        return True
    hay = haystack.lower()
    tokens = [t for t in re.split(r"[^0-9a-z.]+", q) if len(t) >= 3]
    if not tokens:
        return q in hay
    return any(t in hay for t in tokens)


def search_catalog(query: str) -> list[dict[str, Any]]:
    """Return catalogue entries matching ``query`` by name, type or keyword.

    Token-aware, case-insensitive; empty/whitespace query returns the whole
    catalogue so an agent can browse.
    """
    results: list[dict[str, Any]] = []
    for entry in CATALOG:
        haystack = " ".join(
            [entry["message_type"], entry["name"], *entry["keywords"]]
        ).lower()
        if _matches(query, haystack):
            results.append(
                {
                    "message_type": entry["message_type"],
                    "family": entry["family"],
                    "name": entry["name"],
                    "package": FAMILIES[entry["family"]]["package"],
                }
            )
    return results


def search_servers(query: str) -> list[dict[str, Any]]:
    """Return specialized suite servers matching ``query`` (empty = all)."""
    results: list[dict[str, Any]] = []
    for srv in SPECIALIZED_SERVERS:
        haystack = " ".join(
            [srv["name"], srv["title"], srv["does"], *srv["keywords"]]
        ).lower()
        if _matches(query, haystack):
            results.append(
                {
                    "name": srv["name"],
                    "package": srv["package"],
                    "title": srv["title"],
                    "does": srv["does"],
                }
            )
    return results


def resolve_ei(func_name: str) -> Callable[..., Any]:
    """Resolve a callable on the camt-exceptions server for E&I message types.

    Raises:
        ValueError: if the camt-exceptions package is not installed.
    """
    try:
        module = _load_module(_EI_MODULE)
    except ImportError as exc:
        raise ValueError(
            f"Exceptions & Investigations messages need the '{_EI_PACKAGE}' "
            f"package. Install it with: pip install {_EI_PACKAGE}"
        ) from exc
    return cast("Callable[..., Any]", getattr(module, func_name))


def list_all_servers() -> dict[str, Any]:
    """Full map of the suite: message families plus specialized servers.

    Gives an agent one view of everything the gateway can route to or point at.
    """
    return {
        "families": family_summary(),
        "exceptions_and_investigations": [
            {"message_type": mt, "name": name, "package": _EI_PACKAGE}
            for mt, name in EI_MESSAGE_TYPES.items()
        ],
        "specialized": [
            {
                "name": s["name"],
                "package": s["package"],
                "title": s["title"],
                "does": s["does"],
            }
            for s in SPECIALIZED_SERVERS
        ],
    }
