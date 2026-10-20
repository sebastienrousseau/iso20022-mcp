# SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT

"""The one command line every server in the suite shares.

``_transports`` and ``_cli`` are copied verbatim into each server, so these
tests pin their contract: the flags, the defaults, and what ``run`` asks of the SDK on
either major. The listeners themselves are the SDK's; a fake server
records the call instead of opening a port.
"""

from __future__ import annotations

import argparse
from typing import Any

import pytest

from iso20022_mcp import _cli, _transports, server


class _Modern:
    """A server shaped like mcp 2.x: ``run(transport, **kwargs)``."""

    def __init__(self) -> None:
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def run(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append((args, kwargs))


class _Legacy(_Modern):
    """A server shaped like mcp 1.x: host and port live on ``settings``."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = argparse.Namespace(host="0.0.0.0", port=1)


def test_flags_and_defaults() -> None:
    parser = argparse.ArgumentParser()
    _cli.add_arguments(parser)
    args = parser.parse_args([])
    assert (args.transport, args.host, args.port) == (
        "stdio",
        "127.0.0.1",
        8000,
    )
    assert (args.ssl_certfile, args.ssl_keyfile) == (None, None)
    args = parser.parse_args(
        ["--transport", "sse", "--host", "0.0.0.0", "--port", "9"]
    )
    assert (args.transport, args.host, args.port) == ("sse", "0.0.0.0", 9)


def test_unknown_transport_is_rejected_by_the_parser() -> None:
    parser = argparse.ArgumentParser()
    _cli.add_arguments(parser)
    with pytest.raises(SystemExit):
        parser.parse_args(["--transport", "carrier-pigeon"])


def test_stdio_runs_with_no_arguments() -> None:
    srv = _Modern()
    _transports.run(srv)
    assert srv.calls == [((), {})]


def test_streamable_http_on_modern_sdk_passes_host_port_and_path() -> None:
    srv = _Modern()
    _transports.run(srv, "streamable-http", "0.0.0.0", 8080)
    assert srv.calls == [
        (
            ("streamable-http",),
            {"host": "0.0.0.0", "port": 8080, "streamable_http_path": "/mcp"},
        )
    ]


def test_sse_on_modern_sdk_passes_both_paths() -> None:
    srv = _Modern()
    _transports.run(srv, "sse", "127.0.0.1", 8001)
    assert srv.calls == [
        (
            ("sse",),
            {
                "host": "127.0.0.1",
                "port": 8001,
                "sse_path": "/sse",
                "message_path": "/messages/",
            },
        )
    ]


@pytest.mark.parametrize("transport", ["streamable-http", "sse"])
def test_legacy_sdk_is_configured_through_settings(transport: str) -> None:
    srv = _Legacy()
    _transports.run(srv, transport, "10.0.0.1", 7000)
    assert (srv.settings.host, srv.settings.port) == ("10.0.0.1", 7000)
    assert srv.calls == [((transport,), {})]


def test_run_rejects_a_bad_transport_and_port() -> None:
    with pytest.raises(ValueError, match="unknown transport 'carrier-pigeon'"):
        _transports.run(_Modern(), "carrier-pigeon")
    for bad in (0, 65536, -1):
        with pytest.raises(
            ValueError, match=f"between 1 and 65535, got {bad}"
        ):
            _transports.run(_Modern(), "sse", port=bad)


@pytest.mark.parametrize("port", [1, 65535])
def test_run_accepts_the_port_range_edges(port: int) -> None:
    srv = _Modern()
    _transports.run(srv, "sse", port=port)
    assert srv.calls[0][1]["port"] == port


def test_serve_wires_the_flags_to_run(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[Any, ...]] = []
    monkeypatch.setattr(
        _cli, "run", lambda s, t, h, p, **k: seen.append((s, t, h, p, k))
    )
    _cli.serve("srv", ["--transport", "sse", "--port", "8002"], "x", "1")
    _cli.serve(
        "srv",
        ["--transport", "sse", "--ssl-certfile", "c", "--ssl-keyfile", "k"],
        "x",
        "1",
    )
    assert seen == [
        ("srv", "sse", "127.0.0.1", 8002, {"certfile": None, "keyfile": None}),
        ("srv", "sse", "127.0.0.1", 8000, {"certfile": "c", "keyfile": "k"}),
    ]


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as info:
        _cli.serve("srv", ["--version"], "iso20022-mcp", "9.9.9")
    assert info.value.code == 0
    assert "iso20022-mcp 9.9.9" in capsys.readouterr().out


def test_main_defaults_to_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Any] = []
    monkeypatch.setattr(
        server.server, "run", lambda *a, **k: calls.append((a, k))
    )
    server.main([])
    assert calls == [((), {})]


class _ModernApps(_Modern):
    """mcp 2.x app builders: keyword arguments, no settings.host."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = argparse.Namespace(log_level="WARNING")

    def streamable_http_app(self, **kwargs: Any) -> tuple[str, dict[str, Any]]:
        return ("streamable-http", kwargs)

    def sse_app(self, **kwargs: Any) -> tuple[str, dict[str, Any]]:
        return ("sse", kwargs)


class _LegacyApps(_Legacy):
    """mcp 1.x app builders: no arguments, everything on settings."""

    def __init__(self) -> None:
        super().__init__()
        self.settings.transport_security = "sdk default"
        self.settings.log_level = "INFO"

    def streamable_http_app(self) -> str:
        return "streamable-http app"

    def sse_app(self) -> str:
        return "sse app"


@pytest.fixture
def uvicorn_calls(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    import uvicorn

    calls: list[Any] = []
    monkeypatch.setattr(
        uvicorn, "run", lambda app, **kwargs: calls.append((app, kwargs))
    )
    return calls


def test_tls_needs_both_files_and_an_http_transport() -> None:
    for cert, key in (("c", None), (None, "k")):
        with pytest.raises(ValueError, match="both a certificate"):
            _transports.run(_Modern(), "sse", certfile=cert, keyfile=key)
    with pytest.raises(ValueError, match="not stdio"):
        _transports.run(_Modern(), "stdio", certfile="c", keyfile="k")


def test_tls_serves_the_modern_app_under_uvicorn(
    uvicorn_calls: list[Any],
) -> None:
    srv = _ModernApps()
    _transports.run(
        srv, "streamable-http", "127.0.0.1", 8443, certfile="c", keyfile="k"
    )
    ((app, kwargs),) = uvicorn_calls
    assert srv.calls == []
    assert kwargs == {
        "host": "127.0.0.1",
        "port": 8443,
        "ssl_certfile": "c",
        "ssl_keyfile": "k",
        "log_level": "warning",
    }
    name, built = app
    assert name == "streamable-http"
    assert built["streamable_http_path"] == "/mcp"
    security = built["transport_security"]
    assert security.enable_dns_rebinding_protection
    assert "https://127.0.0.1:*" in security.allowed_origins
    assert "http://localhost:*" in security.allowed_origins


def test_tls_sse_on_a_routable_host_has_no_loopback_guard(
    uvicorn_calls: list[Any],
) -> None:
    _transports.run(
        _ModernApps(), "sse", "0.0.0.0", 8443, certfile="c", keyfile="k"
    )
    ((app, _),) = uvicorn_calls
    assert app == (
        "sse",
        {
            "sse_path": "/sse",
            "message_path": "/messages/",
            "host": "0.0.0.0",
            "transport_security": None,
        },
    )


@pytest.mark.parametrize("transport", ["streamable-http", "sse"])
def test_tls_configures_the_legacy_app_through_settings(
    transport: str, uvicorn_calls: list[Any]
) -> None:
    srv = _LegacyApps()
    _transports.run(srv, transport, "::1", 8443, certfile="c", keyfile="k")
    ((app, kwargs),) = uvicorn_calls
    assert app == f"{transport} app"
    assert (srv.settings.host, srv.settings.port) == ("::1", 8443)
    assert "https://[::1]:*" in srv.settings.transport_security.allowed_origins
    assert kwargs["log_level"] == "info"
    assert srv.calls == []


def test_tls_without_settings_defaults_the_log_level(
    uvicorn_calls: list[Any],
) -> None:
    srv = _ModernApps()
    del srv.settings
    _transports.run(srv, "sse", certfile="c", keyfile="k")
    assert uvicorn_calls[0][1]["log_level"] == "info"
