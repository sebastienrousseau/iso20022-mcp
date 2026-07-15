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

"""Tests for the ISO 20022 gateway meta-tool surface."""

import asyncio
import json

import pytest

pytest.importorskip("mcp")

import iso20022_mcp.server as srv  # noqa: E402
from iso20022_mcp import __version__  # noqa: E402

EXPECTED_TOOLS = {
    "search",
    "list_families",
    "list_servers",
    "describe",
    "validate",
    "generate",
    "parse",
}


def _registered_tool_names() -> set[str]:
    manager = getattr(srv.server, "_tool_manager", None)
    if manager is not None and hasattr(manager, "list_tools"):
        return {tool.name for tool in manager.list_tools()}
    tools = asyncio.run(srv.server.list_tools())  # pragma: no cover
    return {tool.name for tool in tools}  # pragma: no cover


def test_all_tools_registered():
    assert _registered_tool_names() == EXPECTED_TOOLS


def test_server_version_override():
    assert srv.server._mcp_server.version == __version__


def test_search_tool():
    out = srv.search("make a payment")
    assert any(r["message_type"] == "pain.001" for r in out["results"])


def test_search_tool_surfaces_servers():
    out = srv.search("reconciliation")
    assert any(s["name"] == "reconcile-mcp" for s in out["servers"])


def test_list_servers_tool(fake_backend):
    out = srv.list_servers()
    assert out["families"] and out["specialized"]
    assert any(
        e["message_type"] == "camt.056.001.12"
        for e in out["exceptions_and_investigations"]
    )


def test_generate_routes_ei_to_camt_exceptions(fake_backend):
    out = srv.generate("camt.056.001.12", [{"assignment_id": "C"}])
    assert out["message_type"] == "camt.056.001.12"


def test_generate_ei_with_empty_records(fake_backend):
    # Empty list -> passes {} to camt-exceptions (which would flag missing
    # fields); here the fake backend just echoes back.
    out = srv.generate("camt.029.001.14", [])
    assert out["message_type"] == "camt.029.001.14"


def test_generate_ei_missing_package(no_backend):
    err = srv.generate("camt.056.001.12", [{"assignment_id": "C"}])
    assert "pip install camt-exceptions" in err["error"]


def test_list_families_tool(fake_backend):
    out = srv.list_families()
    assert {f["prefix"] for f in out["families"]} == {
        "pain",
        "pacs",
        "camt",
        "acmt",
    }


def test_describe_tool_happy_and_error(fake_backend):
    ok = srv.describe("pacs.008")
    assert ok["family"] == "pacs.008"
    assert ok["required_fields"]["required"] == ["id", "amount"]
    assert ok["input_schema"]["schema"] == {"type": "object"}
    err = srv.describe("zzzz.001")
    assert "error" in err


def test_validate_tool_happy(fake_backend):
    ok = srv.validate("camt.053", [{"x": 1}])
    assert ok["valid"] is True and ok["count"] == 1


def test_validate_tool_missing_package(no_backend):
    err = srv.validate("pacs.008", [{}])
    assert "pip install pacs008-mcp" in err["error"]


def test_generate_tool_happy(fake_backend):
    # The backend returns the XML as a plain string; the gateway must wrap
    # it into its declared dict output shape.
    ok = srv.generate("pain.001", [{"a": 1}])
    assert ok == {"message_type": "pain.001", "xml": "<pain.001/>"}


def test_generate_tool_decodes_backend_json_error(fake_backend):
    # pain/pacs/acmt backends stringify failures as JSON-encoded
    # {"error": ...} payloads; the gateway surfaces them as real dicts.
    fake_backend.generate_message = lambda mt, recs: json.dumps(
        {"error": "boom"}
    )
    err = srv.generate("pain.001", [{"a": 1}])
    assert err == {"error": "boom"}


def test_generate_tool_passes_dict_results_through(fake_backend):
    # camt-exceptions (E&I) already returns a dict; it must not be wrapped.
    fake_backend.generate_message = lambda mt, rec: {
        "message_type": mt,
        "xml": f"<{mt}/>",
        "valid": True,
    }
    out = srv.generate("camt.056.001.12", [{"assignment_id": "C"}])
    assert out["valid"] is True and out["message_type"] == "camt.056.001.12"


def test_generate_tool_output_passes_mcp_validation(fake_backend):
    # Regression: calling through FastMCP exercises the declared output
    # model. With a string-returning backend this used to fail pydantic
    # validation ("Input should be a valid dictionary") instead of
    # returning the finished XML.
    result = asyncio.run(
        srv.server.call_tool(
            "generate",
            {"message_type": "pain.001", "records": [{"a": 1}]},
        )
    )
    structured = result[1] if isinstance(result, tuple) else result
    assert structured["xml"] == "<pain.001/>"


def test_generate_tool_unsupported_for_camt(fake_backend):
    err = srv.generate("camt.053", [{}])
    assert "inbound statement format" in err["error"]


def test_generate_tool_unknown_family():
    err = srv.generate("zzzz.001", [{}])
    assert "error" in err


def test_parse_tool_happy(fake_backend):
    ok = srv.parse("camt.053", "<Doc/>")
    assert ok["parsed_by"] == "camt"


def test_parse_tool_unsupported_for_pain(fake_backend):
    err = srv.parse("pain.001", "<Doc/>")
    assert "no inbound parser" in err["error"]


def test_parse_tool_unknown_family():
    err = srv.parse("zzzz.001", "<Doc/>")
    assert "error" in err


def test_main_runs_server(monkeypatch):
    called = {}
    monkeypatch.setattr(
        srv.server, "run", lambda: called.setdefault("ran", True)
    )
    srv.main()
    assert called["ran"] is True
