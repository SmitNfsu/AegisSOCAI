"""Alias Robotics OpenAI-compatible bridge router.

Translates standard OpenAI /v1/chat/completions and /v1/models endpoints to the
Alias Robotics API endpoints (/chat/completions and /models on port 666).
"""

from __future__ import annotations

import logging
import os

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from core.routing import Auth, RouterMeta

logger = logging.getLogger(__name__)

router = APIRouter()

ROUTER_META = RouterMeta(
    prefix="/api/llm/alias-proxy",
    tags=["alias-proxy"],
    auth=Auth.ROUTER_MANAGED,
    reason="Self-authenticating LLM bridge for Alias Robotics API",
)

DEFAULT_ALIAS_BASE_URL = "https://api.aliasrobotics.com:666"


def _get_target_base_url() -> str:
    url = os.environ.get("ALIAS_BASE_URL") or os.environ.get("CAI_BASE_URL")
    if not url:
        try:
            from dotenv import dotenv_values

            env_vals = dotenv_values(".env")
            url = env_vals.get("ALIAS_BASE_URL") or env_vals.get("CAI_BASE_URL")
        except Exception:
            pass
    return (url or DEFAULT_ALIAS_BASE_URL).rstrip("/")


def _get_api_key(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token and token.lower() != "unused" and token.lower() != "bearer":
            return token

    # Check process environment
    for env_var in ("ALIAS_API_KEY", "CAI_API_KEY", "OPENAI_API_KEY"):
        val = os.environ.get(env_var, "").strip()
        if val:
            return val

    # Check encrypted secret store
    try:
        from core.secrets import get_secret

        for secret_name in (
            "ALIAS_API_KEY",
            "OPENAI_API_KEY",
            "llm_provider_bifrost-openai_api_key",
        ):
            val = (get_secret(secret_name) or "").strip()
            if val:
                return val
    except Exception:
        pass

    # Check .env file directly as fallback
    try:
        from dotenv import dotenv_values

        env_vals = dotenv_values(".env")
        for env_key in ("ALIAS_API_KEY", "CAI_API_KEY", "OPENAI_API_KEY"):
            val = (env_vals.get(env_key) or "").strip()
            if val:
                return val
    except Exception:
        pass

    return ""


@router.get("/v1/models")
@router.get("/models")
async def list_models(request: Request):
    base_url = _get_target_base_url()
    key = _get_api_key(request)
    if not key:
        logger.error("Alias proxy: No API key found in request, secrets, or .env")
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "message": "Alias API key not configured",
                    "type": "auth_error",
                }
            },
        )

    headers = {"Authorization": f"Bearer {key}"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            r = await client.get(f"{base_url}/models", headers=headers)
            return Response(
                content=r.content,
                status_code=r.status_code,
                media_type="application/json",
            )
        except Exception as exc:
            logger.error("Alias proxy models error: %s", exc)
            return JSONResponse(
                status_code=502,
                content={"error": {"message": str(exc), "type": "proxy_error"}},
            )


@router.post("/v1/chat/completions")
@router.post("/chat/completions")
async def chat_completions(request: Request):
    base_url = _get_target_base_url()
    key = _get_api_key(request)
    if not key:
        logger.error("Alias proxy: No API key found in request, secrets, or .env")
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "message": "Alias API key not configured",
                    "type": "auth_error",
                }
            },
        )

    body = await request.body()
    is_stream = False
    try:
        data = await request.json()
        is_stream = bool(data.get("stream", False))
    except Exception:
        pass

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    if not is_stream:
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                r = await client.post(
                    f"{base_url}/chat/completions",
                    content=body,
                    headers=headers,
                )
                return Response(
                    content=r.content,
                    status_code=r.status_code,
                    media_type="application/json",
                )
            except Exception as exc:
                logger.error("Alias proxy chat error: %s", exc)
                return JSONResponse(
                    status_code=502,
                    content={"error": {"message": str(exc), "type": "proxy_error"}},
                )

    # Streaming mode
    client = httpx.AsyncClient(timeout=120.0)

    async def stream_generator():
        try:
            req = client.build_request(
                "POST",
                f"{base_url}/chat/completions",
                content=body,
                headers=headers,
            )
            resp = await client.send(req, stream=True)
            async for chunk in resp.aiter_bytes():
                yield chunk
        finally:
            await client.aclose()

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
