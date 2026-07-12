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
