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

import pytest

pytest.importorskip("mcp")

import iso20022_mcp.server as srv  # noqa: E402
from iso20022_mcp import __version__  # noqa: E402

EXPECTED_TOOLS = {
    "search",
    "list_families",
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
    ok = srv.generate("pain.001", [{"a": 1}])
    assert ok["xml"] == "<pain.001/>"


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
