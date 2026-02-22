"""API routes for kicking off and streaming a FalconEye Crew run."""

from __future__ import annotations

import ast
import asyncio
import json
import logging
import re
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
_TOOL_RESULT_RE = re.compile(
    r"^ToolResult\(result=['\"](.+?)['\"],\s*result_as_answer=", re.DOTALL
)
_AGENT_ACTION_RE = re.compile(
    r"^AgentAction\(thought=['\"](.+?)['\"],\s*tool=['\"](.+?)['\"]", re.DOTALL
)


def _parse_search_results(data: Any) -> list[dict] | None:
    """Extract a list of result dicts from parsed Serper-style data."""
    if isinstance(data, dict):
        results = data.get("organic") or data.get("results") or []
        if not isinstance(results, list) or not results:
            return None
    elif isinstance(data, list) and data:
        results = data
    else:
        return None
    return [r for r in results if isinstance(r, dict)] or None


def _format_results_block(results: list[dict]) -> str:
    """Render a list of search-result dicts into clean formatted text."""
    lines: list[str] = []
    for idx, item in enumerate(results, 1):
        title = item.get("title", "N/A")
        link = item.get("link", item.get("url", "N/A"))
        snippet = item.get("snippet", item.get("description", "N/A"))
        lines.append(f"### {idx}. {title}")
        lines.append(f"**URL:** {link}")
        lines.append(f"**Details:** {snippet}")
        lines.append("")
    return "\n".join(lines).strip()


def _try_parse_data(raw: str) -> Any | None:
    """Attempt to parse *raw* as a Python literal or JSON object."""
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        pass
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _format_log_message(raw: str) -> str:
    """Parse raw step output and return clean, structured text.

    Handles three shapes:
      1. Serper JSON / Python-repr with ``organic`` or ``results`` keys.
      2. ``ToolResult(result=…)`` wrappers emitted by CrewAI.
      3. ``AgentAction(thought=…, tool=…, …)`` wrappers.
    Falls back to the raw string when none of the above match.
    """

    # --- try to unwrap CrewAI ToolResult / AgentAction wrappers ----------
    tr_match = _TOOL_RESULT_RE.match(raw)
    if tr_match:
        inner = tr_match.group(1)
        parsed = _try_parse_data(inner)
        if parsed is not None:
            results = _parse_search_results(parsed)
            if results:
                return f"## 🔍 Search Results\n\n{_format_results_block(results)}"
        return raw

    aa_match = _AGENT_ACTION_RE.match(raw)
    if aa_match:
        thought = aa_match.group(1).strip()
        tool = aa_match.group(2).strip()
        header = f"## 🤖 Agent Action — {tool}\n\n**Thought:** {thought}"
        # Try to extract and format the embedded result if present
        result_marker = "result='"
        result_idx = raw.find(result_marker)
        if result_idx != -1:
            inner = raw[result_idx + len(result_marker):]
            inner = inner.rstrip(")")
            if inner.endswith("'"):
                inner = inner[:-1]
            parsed = _try_parse_data(inner)
            if parsed is not None:
                results = _parse_search_results(parsed)
                if results:
                    return f"{header}\n\n{_format_results_block(results)}"
        return header

    # --- direct Serper payload (dict / list) ----------------------------
    parsed = _try_parse_data(raw)
    if parsed is not None:
        results = _parse_search_results(parsed)
        if results:
            return f"## 🔍 Search Results\n\n{_format_results_block(results)}"

    return raw


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

            task = asyncio.create_task(asyncio.to_thread(crew.kickoff))

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
