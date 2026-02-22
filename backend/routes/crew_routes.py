"""API routes for kicking off and streaming a FalconEye Crew run."""

from __future__ import annotations

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

        def _step_callback(step_output: Any) -> None:
            """Push each agent step into the async queue."""
            message = str(step_output)
            log_queue.put_nowait(message)

        yield _sse_format({"run_id": run_id, "type": "start", "message": "Crew launched."})

        try:
            from backend.services.crew import build_crew

            crew = build_crew(
                target=req.target,
                pinecone_index=req.pinecone_index,
                step_callback=_step_callback,
            )

            loop = asyncio.get_event_loop()
            task = loop.run_in_executor(None, crew.kickoff)

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
