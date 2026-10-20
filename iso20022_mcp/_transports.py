# SPDX-FileCopyrightText: 2023-2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT

"""One command line for the three MCP transports.

Every server in the suite is started the same way::

    <server>                                   # stdio, for a client that spawns it
    <server> --transport streamable-http       # HTTP on 127.0.0.1:8000, path /mcp
    <server> --transport sse --port 8001       # the older HTTP+SSE transport

Over streamable HTTP the SDK speaks both current protocol revisions on
one endpoint: ``2026-07-28`` (stateless, ``server/discover``, per-request
``_meta``) and ``2025-11-25`` (``initialize`` handshake, ``Mcp-Session-Id``).
Responses stream as server-sent events; a ``GET`` on the same path opens
the server-to-client event stream. ``--transport sse`` serves the
2024-11-05 HTTP+SSE transport for clients that still expect it.

The listener binds the loopback interface unless told otherwise. Pass a
certificate and key (``--ssl-certfile``/``--ssl-keyfile``) and either HTTP
transport serves HTTPS instead; on loopback, DNS-rebinding protection then
admits ``https://`` origins too. There is no authentication here: put the
server behind a gateway you trust before binding a routable address.

This module holds the transport dispatch; the flags that drive it live
in :mod:`_cli`. Both files are copied verbatim into every server of the
suite and work on mcp 1.x and 2.x.
"""

from __future__ import annotations

from typing import Any

TRANSPORTS: tuple[str, ...] = ("stdio", "streamable-http", "sse")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
STREAMABLE_HTTP_PATH = "/mcp"
SSE_PATH = "/sse"
MESSAGE_PATH = "/messages/"
LOOPBACK_HOSTS: tuple[str, ...] = ("127.0.0.1", "localhost", "::1")


def run(
    server: Any,
    transport: str = "stdio",
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    certfile: str | None = None,
    keyfile: str | None = None,
) -> None:
    """Serve ``server`` over ``transport``; returns when the server stops.

    With ``certfile`` and ``keyfile`` an HTTP transport serves HTTPS.

    Raises:
        ValueError: If ``transport`` is not one of :data:`TRANSPORTS`,
            ``port`` is outside 1-65535, only one of ``certfile`` and
            ``keyfile`` is given, or TLS is asked of stdio.
    """
    _check(transport, port, certfile, keyfile)
    if transport == "stdio":
        server.run()
    elif certfile is not None and keyfile is not None:
        _serve_tls(server, transport, host, port, certfile, keyfile)
    else:
        _serve_http(server, transport, host, port)


def _check(
    transport: str, port: int, certfile: str | None, keyfile: str | None
) -> None:
    """Raise :class:`ValueError` for arguments :func:`run` cannot serve."""
    if transport not in TRANSPORTS:
        raise ValueError(
            f"unknown transport {transport!r}; choose from {', '.join(TRANSPORTS)}"
        )
    if not 1 <= port <= 65535:
        raise ValueError(f"port must be between 1 and 65535, got {port}")
    if (certfile is None) != (keyfile is None):
        raise ValueError("TLS needs both a certificate file and a key file")
    if certfile is not None and transport == "stdio":
        raise ValueError("TLS applies only to the HTTP transports, not stdio")


def _serve_http(server: Any, transport: str, host: str, port: int) -> None:
    """Serve plain HTTP through the SDK's own ``run()``."""
    settings = getattr(server, "settings", None)
    if settings is not None and hasattr(settings, "host"):
        # mcp 1.x: the listener reads host and port from the settings
        # object and run() takes no keyword arguments.
        settings.host = host
        settings.port = port
        server.run(transport)
        return
    if transport == "streamable-http":
        server.run(
            "streamable-http",
            host=host,
            port=port,
            streamable_http_path=STREAMABLE_HTTP_PATH,
        )
        return
    server.run(
        "sse",
        host=host,
        port=port,
        sse_path=SSE_PATH,
        message_path=MESSAGE_PATH,
    )


def _serve_tls(
    server: Any,
    transport: str,
    host: str,
    port: int,
    certfile: str,
    keyfile: str,
) -> None:
    """Run the SDK's ASGI app under uvicorn with TLS.

    The SDK's own ``run()`` takes no TLS options on either major, so the
    app is built here and handed to uvicorn, which the SDK depends on.
    """
    import uvicorn

    settings = getattr(server, "settings", None)
    log_level = str(getattr(settings, "log_level", "INFO")).lower()
    uvicorn.run(
        http_app(server, transport, host, port),
        host=host,
        port=port,
        ssl_certfile=certfile,
        ssl_keyfile=keyfile,
        log_level=log_level,
    )


def http_app(server: Any, transport: str, host: str, port: int) -> Any:
    """The SDK's ASGI app for ``transport``, served over HTTPS."""
    security = _https_loopback_security(host)
    settings = getattr(server, "settings", None)
    if settings is not None and hasattr(settings, "host"):
        # mcp 1.x: the app reads everything from the settings object.
        settings.host = host
        settings.port = port
        settings.transport_security = security
        if transport == "streamable-http":
            return server.streamable_http_app()
        return server.sse_app()
    if transport == "streamable-http":
        return server.streamable_http_app(
            streamable_http_path=STREAMABLE_HTTP_PATH,
            host=host,
            transport_security=security,
        )
    return server.sse_app(
        sse_path=SSE_PATH,
        message_path=MESSAGE_PATH,
        host=host,
        transport_security=security,
    )


def _https_loopback_security(host: str) -> Any:
    """DNS-rebinding protection for a loopback bind that admits HTTPS.

    The SDK enables the same protection on loopback by itself, but only
    for ``http://`` origins. A routable bind gets none, as in the SDK.
    """
    if host not in LOOPBACK_HOSTS:
        return None
    from mcp.server.transport_security import TransportSecuritySettings

    hosts = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=[
            f"{scheme}://{h}" for scheme in ("https", "http") for h in hosts
        ],
    )
