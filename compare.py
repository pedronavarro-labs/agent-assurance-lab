from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolChange:
    change_type: str
    name: str
    approved_fingerprint: str | None = None
    observed_fingerprint: str | None = None
    changed_fields: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": self.change_type,
            "name": self.name,
        }
        if self.approved_fingerprint is not None:
            result["approvedFingerprint"] = self.approved_fingerprint
        if self.observed_fingerprint is not None:
            result["observedFingerprint"] = self.observed_fingerprint
        if self.changed_fields:
            result["changedFields"] = list(self.changed_fields)
        return result


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint_tool(tool: dict[str, Any]) -> str:
    material = {
        "name": tool.get("name"),
        "description": tool.get("description"),
        "inputSchema": tool.get("inputSchema"),
    }
    return hashlib.sha256(_canonical_json(material).encode("utf-8")).hexdigest()


def _tool_map(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tools = document.get("tools")
    if not isinstance(tools, list):
        raise ValueError("Document must contain a 'tools' list")
    result: dict[str, dict[str, Any]] = {}
    for tool in tools:
        if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
            raise ValueError("Every tool must be an object with a string 'name'")
        name = tool["name"]
        if name in result:
            raise ValueError(f"Duplicate tool name: {name}")
        result[name] = tool
    return result


def compare_documents(approved: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    approved_tools = _tool_map(approved)
    observed_tools = _tool_map(observed)
    changes: list[ToolChange] = []

    for name in sorted(approved_tools.keys() - observed_tools.keys()):
        changes.append(
            ToolChange(
                change_type="removed",
                name=name,
                approved_fingerprint=fingerprint_tool(approved_tools[name]),
            )
        )

    for name in sorted(observed_tools.keys() - approved_tools.keys()):
        changes.append(
            ToolChange(
                change_type="added",
                name=name,
                observed_fingerprint=fingerprint_tool(observed_tools[name]),
            )
        )

    for name in sorted(approved_tools.keys() & observed_tools.keys()):
        approved_tool = approved_tools[name]
        observed_tool = observed_tools[name]
        approved_fingerprint = fingerprint_tool(approved_tool)
        observed_fingerprint = fingerprint_tool(observed_tool)
        changed_fields = tuple(
            field
            for field in ("description", "inputSchema")
            if approved_tool.get(field) != observed_tool.get(field)
        )
        if approved_fingerprint != observed_fingerprint:
            changes.append(
                ToolChange(
                    change_type="modified",
                    name=name,
                    approved_fingerprint=approved_fingerprint,
                    observed_fingerprint=observed_fingerprint,
                    changed_fields=changed_fields,
                )
            )

    signals = []
    events = observed.get("events", [])
    if isinstance(events, list) and any(
        isinstance(event, dict) and event.get("type") == "listChanged" for event in events
    ):
        signals.append("listChanged")

    return {
        "status": "pass" if not changes else "fail",
        "approvedToolCount": len(approved_tools),
        "observedToolCount": len(observed_tools),
        "signals": signals,
        "changes": [change.as_dict() for change in changes],
    }
