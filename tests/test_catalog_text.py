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

"""Catalogue-text gates mirroring passmcp's catalog checks.

The model reads every description it is given with the same authority,
whichever tool it is attached to. A description that sets a rule for a
sibling ("do not use ... use 'parse' instead", "before calling 'generate'")
is what passmcp's ``catalog.text.shadowing`` check fails, so these tests
apply the same cue list and window to the gateway's own catalogue. The
budget test mirrors ``catalog.budget.tokens`` (chars / 4, 500 per tool).
"""

import asyncio
import json
import re
from typing import Any

import pytest

pytest.importorskip("mcp")

import iso20022_mcp.server as srv  # noqa: E402

# passmcp 0.0.7 internal/probe/shadow.go: shadowCues and shadowWindow.
SHADOW_CUES = (
    "whenever you call",
    "whenever you use",
    "whenever calling",
    "whenever using",
    "prior to calling",
    "prior to invoking",
    "before calling",
    "before invoking",
    "before you call",
    "before you use",
    "before using",
    "after calling",
    "after invoking",
    "after you call",
    "after using",
    "when calling",
    "when invoking",
    "when you call",
    "when using",
    "do not call",
    "do not use",
    "do not invoke",
    "don't call",
    "don't use",
    "don't invoke",
    "never call",
    "never use",
    "never invoke",
    "always call",
    "always use",
    "always invoke",
    "must call",
    "must use",
    "must invoke",
    "must first call",
    "must always call",
    "instead of calling",
    "in place of calling",
    "ignore the",
    "disregard the",
    "override the",
)
SHADOW_WINDOW = 120
SNAKE_REF = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
TOOL_TOKEN_BUDGET = 500


def _tools() -> list[Any]:
    return asyncio.run(srv.server.list_tools())


def _schema_text(node: Any, out: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("description", "title") and isinstance(value, str):
                out.append(value)
            else:
                _schema_text(value, out)
    elif isinstance(node, list):
        for value in node:
            _schema_text(value, out)


def _tool_fields(tool: Any) -> list[str]:
    fields = [tool.description or "", tool.title or ""]
    for attr in ("inputSchema", "outputSchema"):
        _schema_text(getattr(tool, attr, None), fields)
    return fields


def _catalogue_fields() -> list[tuple[str, str]]:
    """Every (owner, text) pair the model reads, as passmcp collects them."""
    fields = [(t.name, text) for t in _tools() for text in _tool_fields(t)]
    resources = asyncio.run(srv.server.list_resources())
    templates = asyncio.run(srv.server.list_resource_templates())
    for res in [*resources, *templates]:
        fields += [
            (res.name, res.description or ""),
            (res.name, res.title or ""),
        ]
    for prompt in asyncio.run(srv.server.list_prompts()):
        fields += [(prompt.name, prompt.description or "")]
        fields += [(prompt.name, prompt.title or "")]
        fields += [
            (prompt.name, a.description or "") for a in prompt.arguments or []
        ]
    return fields


def _refs(window: str, names: set[str]) -> set[str]:
    refs = set(SNAKE_REF.findall(window))
    refs |= {
        n for n in names if re.search(rf"(?<!\w){re.escape(n)}(?!\w)", window)
    }
    return refs


def _shadow_hits(owner: str, text: str, names: set[str]) -> list[str]:
    lower = text.lower()
    hits = []
    for cue in SHADOW_CUES:
        for match in re.finditer(re.escape(cue), lower):
            window = lower[match.end() : match.end() + SHADOW_WINDOW]
            for ref in sorted(_refs(window, names) - {owner.lower()}):
                hits.append(f"{owner}: {cue!r} -> {ref}")
    return hits


def test_catalogue_text_governs_only_its_own_tool():
    names = {t.name.lower() for t in _tools()}
    hits = [
        hit
        for owner, text in _catalogue_fields()
        for hit in _shadow_hits(owner, text, names)
    ]
    assert hits == []


def test_every_tool_fits_the_per_tool_token_budget():
    for tool in _tools():
        wire = tool.model_dump(mode="json", by_alias=True, exclude_none=True)
        size = len(json.dumps(wire, ensure_ascii=False).encode())
        assert (size + 3) // 4 <= TOOL_TOKEN_BUDGET, (tool.name, size)
