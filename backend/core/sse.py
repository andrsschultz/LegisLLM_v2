"""Server-Sent Events helpers for streaming progress updates."""
import json


def sse_event(event_type: str, data: dict) -> str:
    """Format a single SSE event."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def sse_step(step_index: int, message: str) -> str:
    """Send a step progress event."""
    return sse_event("step", {"step": step_index, "message": message})


def sse_thinking(token: str) -> str:
    """Send a thinking token event."""
    return sse_event("thinking", {"token": token})


def sse_result(data: dict) -> str:
    """Send the final result event."""
    return sse_event("result", data)


def sse_error(message: str) -> str:
    """Send an error event."""
    return sse_event("error", {"message": message})
