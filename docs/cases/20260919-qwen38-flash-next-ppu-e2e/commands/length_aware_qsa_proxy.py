#!/usr/bin/env python3
"""Fail-closed dual-TP8 proxy for fw-015; short requests use bounded QSA."""

from __future__ import annotations

import json
import logging
import os
import time

from aiohttp import ClientSession, ClientTimeout, TCPConnector, web

from qsa_length_router_core import BOUND_TOKENS, bounded_is_safe, build_tokenize_payload


BOUNDED_BACKEND = os.environ.get("FW015_BOUNDED_BACKEND", "http://127.0.0.1:8000")
UNBOUNDED_BACKEND = os.environ.get("FW015_UNBOUNDED_BACKEND", "http://127.0.0.1:8010")
LISTEN_PORT = int(os.environ.get("FW015_LISTEN_PORT", "8042"))
HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "content-length",
}


async def on_startup(app: web.Application) -> None:
    app["session"] = ClientSession(
        timeout=ClientTimeout(total=7300),
        connector=TCPConnector(limit=64, limit_per_host=32),
    )
    app["slots"] = {"bounded": __import__("asyncio").Semaphore(32),
                    "unbounded": __import__("asyncio").Semaphore(32)}


async def on_cleanup(app: web.Application) -> None:
    await app["session"].close()


async def choose_route(app: web.Application, path: str, payload: dict) -> tuple[str, str]:
    tokenize_payload = build_tokenize_payload(path, payload)
    if tokenize_payload is None:
        return "unbounded", "unsupported_or_ambiguous_request"
    try:
        async with app["session"].post(
            UNBOUNDED_BACKEND + "/tokenize", json=tokenize_payload
        ) as response:
            if response.status != 200:
                return "unbounded", f"tokenize_status_{response.status}"
            tokenized = await response.json()
        safe, reason = bounded_is_safe(payload, tokenized.get("count"), BOUND_TOKENS)
        return ("bounded" if safe else "unbounded"), reason
    except Exception as exc:  # fail closed by design
        logging.warning("tokenize failed; routing unbounded: %r", exc)
        return "unbounded", "tokenize_exception"


async def proxy(request: web.Request) -> web.StreamResponse:
    body = await request.read()
    route = "unbounded"
    reason = "non_generation_endpoint"
    payload = None
    if request.path.endswith("/chat/completions") or request.path.endswith("/completions"):
        try:
            payload = json.loads(body)
            if not isinstance(payload, dict):
                raise ValueError("request JSON must be an object")
        except Exception:
            route, reason = "unbounded", "invalid_json"
        else:
            route, reason = await choose_route(request.app, request.path, payload)

    backend = BOUNDED_BACKEND if route == "bounded" else UNBOUNDED_BACKEND
    target = backend + request.rel_url.path_qs
    headers = {
        key: value for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP and key.lower() != "host"
    }
    started = time.monotonic()
    async with request.app["slots"][route]:
        try:
            async with request.app["session"].request(
                request.method, target, data=body, headers=headers, allow_redirects=False
            ) as upstream:
                response_headers = {
                    key: value for key, value in upstream.headers.items()
                    if key.lower() not in HOP_BY_HOP
                }
                streaming = bool(payload and payload.get("stream"))
                logging.info(
                    "dispatch route=%s reason=%s status=%d stream=%s elapsed_to_headers=%.3f path=%s",
                    route, reason, upstream.status, streaming,
                    time.monotonic() - started, request.path,
                )
                if not streaming:
                    return web.Response(
                        status=upstream.status,
                        body=await upstream.read(),
                        headers=response_headers,
                    )
                downstream = web.StreamResponse(
                    status=upstream.status, headers=response_headers
                )
                await downstream.prepare(request)
                async for chunk in upstream.content.iter_chunked(64 * 1024):
                    await downstream.write(chunk)
                await downstream.write_eof()
                return downstream
        except Exception as exc:
            logging.exception("proxy route=%s failed=%r", route, exc)
            return web.json_response(
                {"error": {"message": repr(exc), "route": route}}, status=502
            )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = web.Application(client_max_size=16 * 1024**2)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.router.add_route("*", "/{path:.*}", proxy)
    web.run_app(app, host="127.0.0.1", port=LISTEN_PORT, access_log=None)


if __name__ == "__main__":
    main()
