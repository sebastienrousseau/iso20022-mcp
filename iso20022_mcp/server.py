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

"""Unified Model Context Protocol (MCP) gateway for ISO 20022.

One server, one small set of meta-tools -- ``search``, ``list_families``,
``describe``, ``validate``, ``generate`` and ``parse`` -- that route across the
ISO 20022 message families (pain / pacs / camt / acmt) to their dedicated
backing servers. An agent installs one thing and discovers the whole suite,
instead of wiring up five servers and choosing between 60+ tools.

Each family's backing server is an optional dependency, imported on demand;
install only the families you need (``pip install iso20022-mcp[all]`` for
everything). Tools return JSON-serializable data; on a :class:`ValueError`
(unknown family, backing package missing, or an unsupported operation) they
return an ``{"error": ...}`` payload rather than raising.

Launching the server:
    * As a console script::

        iso20022-mcp

    * In an MCP client config (e.g. Claude Desktop)::

        {
          "mcpServers": {
            "iso20022": {
              "command": "iso20022-mcp"
            }
          }
        }

The server communicates over stdio (FastMCP's default transport).
"""

import json
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from iso20022_mcp import __version__, registry

server = FastMCP("iso20022")
# FastMCP does not expose a version kwarg; without this override the MCP SDK's
# own version leaks into serverInfo.version, breaking manifest/runtime
# coherence checks (e.g. Glama scoring).
server._mcp_server.version = __version__

# Every tool routes to a pure, side-effect-free reader on a backing server (or
# reads the gateway's own catalogue). Nothing opens a caller-supplied path or
# reaches an external system, so all are marked readOnly + idempotent, never
# destructive, and closed-world.
_PURE_READ = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

_MT_DESC = (
    "ISO 20022 message type, e.g. 'pain.001.001.09', 'pacs.008' or "
    "'camt.053'. For pain messages a fully-versioned type is preferred; "
    "the bare family name 'pain.001' resolves to 'pain.001.001.09'."
)
_RECORDS_DESC = (
    "List of flat record objects (field name → value). Field names come "
    "from the family's input schema — call describe(message_type) for the "
    "required fields. For pain.001 credit transfers the key fields are: "
    "id, date ('YYYY-MM-DD' accepted), initiator_name, payment_id, "
    "requested_execution_date ('YYYY-MM-DD'), debtor_name, "
    "debtor_account_IBAN, debtor_agent_BIC, creditor_name, "
    "creditor_account_IBAN, creditor_agent_BIC, payment_amount (alias "
    "'amount'), currency (alias 'payment_currency'), "
    "remittance_information; batch_booking takes JSON true/false, and "
    "nb_of_txs/ctrl_sum are computed automatically. IBAN and BIC values "
    "are strictly validated, never coerced."
)


@server.tool(
    annotations=_PURE_READ,
    description=(
        "Search the ISO 20022 catalogue by use-case, message type or keyword "
        "(e.g. 'reconciliation', 'make a payment', 'pacs.008') and get the "
        "matching message types, their family, and which package provides them."
    ),
)
def search(
    query: Annotated[
        str,
        Field(description="Use-case, message type or keyword. Empty = all."),
    ] = "",
) -> dict[str, Any]:
    """Find ISO 20022 message types and suite servers matching a query."""
    return {
        "results": registry.search_catalog(query),
        "servers": registry.search_servers(query),
    }


@server.tool(
    annotations=_PURE_READ,
    description=(
        "List every ISO 20022 family the gateway routes to (pain, pacs, camt, "
        "acmt): its capabilities, backing package, and whether that package is "
        "installed in this environment."
    ),
)
def list_families() -> dict[str, Any]:
    """List the supported families and their install status."""
    return {"families": registry.family_summary()}


@server.tool(
    annotations=_PURE_READ,
    description=(
        "List the whole ISO 20022 suite the gateway knows: the message "
        "families (pain/pacs/camt/acmt), the Exceptions & Investigations "
        "messages (camt.056/camt.029), and the specialized servers "
        "(reconciliation, agent-payment bridge) with what each does."
    ),
)
def list_servers() -> dict[str, Any]:
    """Return the full suite map: families, E&I messages and specialized servers."""
    return registry.list_all_servers()


@server.tool(
    annotations=_PURE_READ,
    description=(
        "Describe a message type: its required fields and input JSON Schema, "
        "resolved from the family's backing server."
    ),
)
def describe(
    message_type: Annotated[str, Field(description=_MT_DESC)],
) -> dict[str, Any]:
    """Return the required fields and input schema for a message type."""
    try:
        required = registry.resolve(message_type, "get_required_fields")
        schema = registry.resolve(message_type, "get_input_schema")
        return {
            "message_type": message_type,
            "family": registry.family_for(message_type)["family"],
            "required_fields": required(message_type),
            "input_schema": schema(message_type),
        }
    except ValueError as exc:
        return {"error": str(exc)}


@server.tool(
    annotations=_PURE_READ,
    description=(
        "Validate records for a message type against its JSON Schema, via the "
        "family's backing server."
    ),
)
def validate(
    message_type: Annotated[str, Field(description=_MT_DESC)],
    records: Annotated[list[dict[str, Any]], Field(description=_RECORDS_DESC)],
) -> dict[str, Any]:
    """Validate records for a message type."""
    try:
        func = registry.resolve(message_type, "validate_records")
        return func(message_type, records)
    except ValueError as exc:
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - backend errors become payloads
        return {"error": f"{type(exc).__name__}: {exc}"}


def _normalize_generated(message_type: str, result: Any) -> dict[str, Any]:
    """Coerce a backing generate result into this tool's declared dict shape.

    The family backends (pain / pacs / acmt) return the validated XML
    document as a plain string -- or a JSON-encoded ``{"error": ...}``
    payload on failure -- while camt-exceptions returns a dict. The
    ``generate`` tool declares a dict output model, and FastMCP validates
    the return value against it, so a bare string must be wrapped (and a
    stringified error decoded) before it leaves the gateway.
    """
    if isinstance(result, dict):
        return result
    text = str(result)
    try:
        decoded = json.loads(text)
    except ValueError:
        decoded = None
    if isinstance(decoded, dict):
        return decoded
    return {"message_type": message_type, "xml": text}


@server.tool(
    annotations=_PURE_READ,
    description=(
        "Generate a validated ISO 20022 XML message from records; the XML "
        "document is returned in the 'xml' key. Supported for initiation "
        "and interbank families (pain, pacs, acmt); statement families "
        "(camt) are inbound-only and return an explanatory error. On "
        "failure the 'error' value lists every missing or invalid field "
        "at once — fix them all and retry once."
    ),
)
def generate(
    message_type: Annotated[str, Field(description=_MT_DESC)],
    records: Annotated[list[dict[str, Any]], Field(description=_RECORDS_DESC)],
) -> dict[str, Any]:
    """Generate an ISO 20022 message from records."""
    try:
        if message_type in registry.EI_MESSAGE_TYPES:
            # Exceptions & Investigations route to camt-exceptions, whose
            # generator takes a single record and XSD-validates internally.
            record = records[0] if records else {}
            func = registry.resolve_ei("generate_message")
            return _normalize_generated(
                message_type, func(message_type, record)
            )
        fam = registry.family_for(message_type)
        if not fam["generate"]:
            return {
                "error": (
                    f"{fam['family']} is an inbound statement format; generate "
                    f"is not supported. Use 'parse' or 'validate' instead."
                )
            }
        func = registry.resolve(message_type, "generate_message")
        return _normalize_generated(message_type, func(message_type, records))
    except ValueError as exc:
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - a raised backend error must
        # still reach the agent as a structured payload it can act on,
        # never as an opaque tool-execution failure.
        return {"error": f"{type(exc).__name__}: {exc}"}


@server.tool(
    annotations=_PURE_READ,
    description=(
        "Parse an inbound ISO 20022 XML message into structured data. "
        "Parse coverage is per-family: pacs (e.g. pacs.008) and camt "
        "(e.g. camt.053) only. The initiation families pain and acmt are "
        "outbound-only — they have NO parser here, so do not attempt a "
        "generate→parse round-trip for pain.001 or acmt.001; use "
        "'validate' or the backing server's XSD validation instead."
    ),
)
def parse(
    message_type: Annotated[str, Field(description=_MT_DESC)],
    xml: Annotated[str, Field(description="Raw ISO 20022 XML to parse.")],
) -> dict[str, Any]:
    """Parse an inbound ISO 20022 XML message."""
    try:
        fam = registry.family_for(message_type)
        parse_fn = fam["parse"]
        if not parse_fn:
            return {
                "error": (
                    f"{fam['family']} has no inbound parser in this gateway. "
                    f"Parsing is available for pacs and camt families."
                )
            }
        func = registry.resolve(message_type, parse_fn)
        return func(xml)
    except ValueError as exc:
        return {"error": str(exc)}


def main() -> None:
    """Run the ISO 20022 gateway MCP server over stdio (``iso20022-mcp``)."""
    server.run()


if __name__ == "__main__":
    main()
