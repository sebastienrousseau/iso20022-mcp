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

"""Runnable examples for the iso20022-mcp gateway.

Run with ``python examples/mcp_tools.py`` after ``pip install -e .``. The
``search`` and ``list_families`` tools work with the core install; ``describe``
/ ``validate`` / ``generate`` / ``parse`` route to a family's backing server
and need that package installed (e.g. ``pip install pacs008-mcp``).
"""

import json

from iso20022_mcp import server


def main() -> None:
    """Demonstrate discovery (always available) and routed operations."""
    print("== search('reconciliation') ==")
    print(json.dumps(server.search("reconciliation")["results"]))

    print("\n== list_families (capabilities + install status) ==")
    for fam in server.list_families()["families"]:
        print(
            f"  {fam['prefix']}: {fam['family']:9} "
            f"installed={fam['installed']} ops={fam['operations']}"
        )

    print("\n== generate on camt.053 (capability-aware error) ==")
    print(json.dumps(server.generate("camt.053", [])))

    print("\n== describe pacs.008 (needs pacs008-mcp installed) ==")
    print(json.dumps(server.describe("pacs.008")))


if __name__ == "__main__":
    main()
