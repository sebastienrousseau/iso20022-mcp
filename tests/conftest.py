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

"""Shared fixtures: a fake backing-server module for gateway dispatch tests.

The gateway loads each family's server through ``registry._load_module``. Tests
patch that single indirection point with a fake module exposing the same core
API the real ``-mcp`` servers share, so routing is exercised end-to-end without
installing the heavy backing packages.
"""

import types

import pytest


def _make_fake_backend() -> types.ModuleType:
    """Build a fake backing-server module with the shared core API."""
    mod = types.ModuleType("fake_backend")

    def get_required_fields(message_type):
        return {"message_type": message_type, "required": ["id", "amount"]}

    def get_input_schema(message_type):
        return {"message_type": message_type, "schema": {"type": "object"}}

    def validate_records(message_type, records):
        return {
            "message_type": message_type,
            "valid": True,
            "count": len(records),
        }

    def generate_message(message_type, records):
        return {"message_type": message_type, "xml": f"<{message_type}/>"}

    def parse_message(xml):
        return {"parsed_by": "pacs", "length": len(xml)}

    def parse_statement(xml):
        return {"parsed_by": "camt", "length": len(xml)}

    mod.get_required_fields = get_required_fields
    mod.get_input_schema = get_input_schema
    mod.validate_records = validate_records
    mod.generate_message = generate_message
    mod.parse_message = parse_message
    mod.parse_statement = parse_statement
    return mod


@pytest.fixture
def fake_backend(monkeypatch):
    """Patch registry._load_module to return the fake backend for any family."""
    from iso20022_mcp import registry

    backend = _make_fake_backend()
    monkeypatch.setattr(registry, "_load_module", lambda name: backend)
    return backend


@pytest.fixture
def no_backend(monkeypatch):
    """Patch registry._load_module to simulate an uninstalled backing package."""
    from iso20022_mcp import registry

    def _raise(name):
        raise ImportError(f"No module named {name!r}")

    monkeypatch.setattr(registry, "_load_module", _raise)
