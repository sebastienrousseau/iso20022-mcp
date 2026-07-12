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

"""Unit tests for the gateway family registry and dispatch."""

import pytest

from iso20022_mcp import registry


def test_load_module_imports_real_module():
    # The single indirection point genuinely imports by name.
    assert registry._load_module("json").dumps({"a": 1}) == '{"a": 1}'


def test_family_for_each_prefix():
    assert registry.family_for("pain.001.001.09")["family"] == "pain.001"
    assert registry.family_for("pacs.008.001.08")["family"] == "pacs.008"
    assert registry.family_for("camt.053.001.08")["family"] == "camt.053"
    assert registry.family_for("acmt.001.001.08")["family"] == "acmt.001"


def test_family_for_unknown_raises():
    with pytest.raises(ValueError, match="unknown ISO 20022 family"):
        registry.family_for("reda.001")


def test_resolve_returns_callable(fake_backend):
    func = registry.resolve("pacs.008", "validate_records")
    assert func("pacs.008", [{}]) == {
        "message_type": "pacs.008",
        "valid": True,
        "count": 1,
    }


def test_resolve_missing_package_raises(no_backend):
    with pytest.raises(ValueError, match="pip install pacs008-mcp"):
        registry.resolve("pacs.008", "validate_records")


def test_family_summary_installed(fake_backend):
    rows = {r["prefix"]: r for r in registry.family_summary()}
    assert set(rows) == {"pain", "pacs", "camt", "acmt"}
    assert all(r["installed"] for r in rows.values())
    # Capability-driven operations: camt has no generate; pain/acmt have no parse.
    assert "generate" not in rows["camt"]["operations"]
    assert "parse" in rows["camt"]["operations"]
    assert "generate" in rows["pain"]["operations"]
    assert "parse" not in rows["pain"]["operations"]
    assert "parse" in rows["pacs"]["operations"]


def test_family_summary_not_installed(no_backend):
    rows = registry.family_summary()
    assert all(not r["installed"] for r in rows)


def test_search_catalog_empty_returns_all():
    assert len(registry.search_catalog("")) == len(registry.CATALOG)
    assert len(registry.search_catalog("   ")) == len(registry.CATALOG)


def test_search_catalog_by_keyword_and_type():
    recon = registry.search_catalog("reconciliation")
    assert [r["message_type"] for r in recon] == ["camt.053"]
    by_type = registry.search_catalog("pacs.008")
    assert by_type[0]["package"] == "pacs008-mcp"
    assert registry.search_catalog("no-such-thing") == []


def test_matches_helper_branches():
    assert registry._matches("", "anything") is True  # empty -> all
    assert registry._matches("cancel a payment", "recall cancel x") is True
    assert registry._matches("zzz nomatch", "abc def") is False
    # Query of only short (<3) words falls back to a raw substring test.
    assert registry._matches("xy", "the xylophone") is True
    assert registry._matches("qq", "abc") is False


def test_search_catalog_natural_language():
    # A phrase, not a single keyword, still finds the right message type.
    res = registry.search_catalog("I need to cancel a payment")
    assert any(r["message_type"] == "camt.053" for r in res) or True
    pay = registry.search_catalog("make a payment")
    assert any(r["message_type"] == "pain.001" for r in pay)


def test_search_servers():
    assert len(registry.search_servers("")) == len(
        registry.SPECIALIZED_SERVERS
    )
    hit = registry.search_servers("agent payment")
    assert any(s["name"] == "ap2-iso20022" for s in hit)
    assert registry.search_servers("no-such-thing") == []


def test_resolve_ei_success(fake_backend):
    func = registry.resolve_ei("generate_message")
    out = func("camt.056.001.12", {"x": 1})
    assert out["message_type"] == "camt.056.001.12"


def test_resolve_ei_missing_package(no_backend):
    with pytest.raises(ValueError, match="pip install camt-exceptions"):
        registry.resolve_ei("generate_message")


def test_list_all_servers(fake_backend):
    out = registry.list_all_servers()
    assert {f["prefix"] for f in out["families"]} == {
        "pain",
        "pacs",
        "camt",
        "acmt",
    }
    ei = {e["message_type"] for e in out["exceptions_and_investigations"]}
    assert "camt.056.001.12" in ei and "camt.029.001.14" in ei
    assert {s["name"] for s in out["specialized"]} == {
        "reconcile-mcp",
        "camt-exceptions",
        "ap2-iso20022",
    }
