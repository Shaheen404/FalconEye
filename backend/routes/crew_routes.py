"""API routes for kicking off and streaming a FalconEye Crew run."""

from __future__ import annotations

import ast
import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.services.safety_filter import SafetyFilter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["crew"])

safety = SafetyFilter()


# ------------------------------------------------------------------ #
# Request / Response models
# ------------------------------------------------------------------ #
class CrewRequest(BaseModel):
    """Payload to launch a FalconEye crew run."""

    target: str = Field(
        ..., min_length=1, max_length=200, description="OSINT target (domain, name …)"
    )
    pinecone_index: str | None = Field(
        default=None, description="Optional Pinecone index name for RAG."
    )


class CrewResult(BaseModel):
    run_id: str
    status: str
    result: str | None = None


# ------------------------------------------------------------------ #
# Log formatting helpers
# ------------------------------------------------------------------ #
def _format_log_message(raw: str) -> str:
    """Parse raw step output and format Serper results as Resource/URL/Info.

    Falls back to the raw string when parsing is not possible.
    """
    try:
        data = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    if isinstance(data, dict):
        results = data.get("organic") or data.get("results") or []
        if not isinstance(results, list):
            return raw
    elif isinstance(data, list):
        results = data
    else:
        return raw

    if not results:
        return raw

    lines: list[str] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        title = item.get("title", "N/A")
        link = item.get("link", item.get("url", "N/A"))
        snippet = item.get("snippet", item.get("description", "N/A"))
        lines.append(f"Resource: {title}")
        lines.append(f"URL: {link}")
        lines.append(f"Info: {snippet}")
        lines.append("")
    return "\n".join(lines).strip() if lines else raw


# ------------------------------------------------------------------ #
# SSE streaming endpoint
# ------------------------------------------------------------------ #
@router.post("/crew/stream")
async def stream_crew(req: CrewRequest) -> StreamingResponse:
    """Launch the crew and stream real-time agent logs via SSE."""
    try:
        safety.validate(req.target)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    run_id = str(uuid.uuid4())

    async def event_generator():
        log_queue: asyncio.Queue[str] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _step_callback(step_output: Any) -> None:
            """Push each agent step into the async queue (thread-safe)."""
            message = _format_log_message(str(step_output))
            loop.call_soon_threadsafe(log_queue.put_nowait, message)

        yield _sse_format({"run_id": run_id, "type": "start", "message": "Crew launched."})

        try:
            from backend.services.crew import build_crew

            crew = build_crew(
                target=req.target,
                pinecone_index=req.pinecone_index,
                step_callback=_step_callback,
            )

            task = asyncio.ensure_future(asyncio.to_thread(crew.kickoff))

            while not task.done():
                try:
                    msg = await asyncio.wait_for(log_queue.get(), timeout=1.0)
                    yield _sse_format({"run_id": run_id, "type": "log", "message": msg})
                except asyncio.TimeoutError:
                    yield _sse_format({"run_id": run_id, "type": "ping"})

            # Drain remaining messages
            while not log_queue.empty():
                msg = log_queue.get_nowait()
                yield _sse_format({"run_id": run_id, "type": "log", "message": msg})

            result = task.result()
            yield _sse_format(
                {"run_id": run_id, "type": "result", "message": str(result)}
            )
        except ValueError as exc:
            yield _sse_format(
                {"run_id": run_id, "type": "error", "message": str(exc)}
            )
        except Exception as exc:
            logger.exception("Crew run failed")
            yield _sse_format(
                {"run_id": run_id, "type": "error", "message": f"Internal error: {exc}"}
            )

        yield _sse_format({"run_id": run_id, "type": "done"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ------------------------------------------------------------------ #
# Health check
# ------------------------------------------------------------------ #
@router.get("/health")
async def health_check():
    return {"status": "ok"}


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #
def _sse_format(data: dict) -> str:
    """Format a dict as an SSE ``data:`` line."""
    return f"data: {json.dumps(data)}\n\n"
