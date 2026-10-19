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

"""Property-based fuzzing of the gateway's tool surface.

An agent sends whatever it likes. Each meta-tool must answer with a dict
-- a result or an ``{"error": ...}`` payload -- and never raise, whatever
the message type, query or XML it is handed.
"""

import pytest

pytest.importorskip("mcp")
hypothesis = pytest.importorskip("hypothesis")

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

import iso20022_mcp.server as srv  # noqa: E402

FUZZ = settings(max_examples=200, deadline=None)

# Real family prefixes mixed with noise, so routing is reached as well as
# rejected.
message_types = st.one_of(
    st.text(max_size=40),
    st.sampled_from(
        ["pain.001", "pacs.008", "camt.053", "acmt.001", "camt.056"]
    ).flatmap(lambda base: st.text(max_size=12).map(lambda s: base + s)),
)
records = st.lists(
    st.dictionaries(
        st.text(max_size=20),
        st.one_of(st.none(), st.booleans(), st.integers(), st.text()),
        max_size=6,
    ),
    max_size=3,
)


@FUZZ
@given(query=st.text(max_size=80))
def test_search_never_raises(query):
    out = srv.search(query)
    assert isinstance(out["results"], list)
    assert isinstance(out["servers"], list)


@FUZZ
@given(message_type=st.text(max_size=40))
def test_describe_never_raises(message_type):
    assert isinstance(srv.describe(message_type), dict)


@FUZZ
@given(message_type=message_types, records=records)
def test_validate_and_generate_never_raise(message_type, records):
    assert isinstance(srv.validate(message_type, records), dict)
    assert isinstance(srv.generate(message_type, records), dict)


@FUZZ
@given(message_type=message_types, xml=st.text(max_size=200))
def test_parse_never_raises(message_type, xml):
    assert isinstance(srv.parse(message_type, xml), dict)
