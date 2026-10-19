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

"""Coverage-guided fuzzing of the gateway's meta-tools with Atheris.

Each input is split into a message type, a list of records and an XML
string, and fed to every tool. A tool must answer with a dict -- a result
or an ``{"error": ...}`` payload -- and never raise; anything else is a
crash libFuzzer reports and minimises.

Run (Linux x86_64, Python 3.11-3.13)::

    pip install --require-hashes -r requirements/fuzz.txt
    pip install --no-deps -e .
    python fuzz/fuzz_tools.py -max_total_time=60
"""

import sys

import atheris

with atheris.instrument_imports():
    import iso20022_mcp.server as srv

# Real family prefixes, so routing is reached as well as rejected.
FAMILIES = ("pain.001", "pacs.008", "camt.053", "acmt.001", "camt.056", "")


def _records(fdp: atheris.FuzzedDataProvider) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for _ in range(fdp.ConsumeIntInRange(0, 3)):
        record: dict[str, object] = {}
        for _ in range(fdp.ConsumeIntInRange(0, 6)):
            key = fdp.ConsumeUnicodeNoSurrogates(20)
            record[key] = fdp.PickValueInList(
                [
                    None,
                    fdp.ConsumeBool(),
                    fdp.ConsumeInt(8),
                    fdp.ConsumeUnicodeNoSurrogates(40),
                ]
            )
        out.append(record)
    return out


def test_one_input(data: bytes) -> None:
    fdp = atheris.FuzzedDataProvider(data)
    family = fdp.PickValueInList(list(FAMILIES))
    message_type = family + fdp.ConsumeUnicodeNoSurrogates(12)
    records = _records(fdp)
    xml = fdp.ConsumeUnicodeNoSurrogates(4096)

    for result in (
        srv.search(message_type),
        srv.describe(message_type),
        srv.validate(message_type, records),
        srv.generate(message_type, records),
        srv.parse(message_type, xml),
    ):
        if not isinstance(result, dict):
            raise TypeError(f"tool returned {type(result).__name__}")


def main() -> None:
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
