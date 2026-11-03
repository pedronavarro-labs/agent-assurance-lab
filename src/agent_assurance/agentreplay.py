from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def _normalise_event(event: dict[str, Any]) -> dict[str, Any]:
    """Map common AgentReplay event names to the local session schema."""
    result = dict(event)
    event_type = result.get("type")
    if event_type in {"tool_call", "tool.call", "tool-call"}:
        result["type"] = "toolCall"
    if "tool" not in result and isinstance(result.get("name"), str):
        result["tool"] = result["name"]
    if "actualEffects" not in result and isinstance(result.get("effects"), list):
        result["actualEffects"] = result["effects"]
    return result


def session_from_agentreplay(
    tools: list[dict[str, Any]], events: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    """Build the session document consumed by :func:`analyze_session`."""
    return {
        "tools": tools,
        "events": [_normalise_event(event) for event in events],
        "source": "agentreplay",
    }


def load_agentreplay_jsonl(path: Path) -> dict[str, Any]:
    """Load a JSONL export containing tool snapshots and session events.

    The exporter convention is one JSON object per line. A line with
    ``{"tools": [...]}`` supplies the observed snapshot; all other lines are
    treated as session events.
    """
    tools: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number} is not valid JSON") from error
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            if isinstance(record.get("tools"), list):
                tools = record["tools"]
            else:
                events.append(record)
    return session_from_agentreplay(tools, events)
