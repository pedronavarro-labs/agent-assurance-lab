from __future__ import annotations

from typing import Any

from .compare import compare_documents


def analyze_session(approved: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    observed = {"tools": session.get("tools", [])}
    comparison = compare_documents(approved, observed)
    runtime_findings: list[dict[str, Any]] = []
    tools = {tool.get("name"): tool for tool in observed["tools"] if isinstance(tool, dict)}
    timeline: list[dict[str, Any]] = []

    for index, event in enumerate(session.get("events", [])):
        if not isinstance(event, dict):
            continue
        event_type = event.get("type", "unknown")
        item = {
            "sequence": index,
            "type": event_type,
        }
        for field in ("timestamp", "tool", "status", "requestId"):
            if field in event:
                item[field] = event[field]
        timeline.append(item)
        if event_type not in {"toolCall", "tool.call"}:
            continue
        name = event.get("tool") or event.get("name")
        tool = tools.get(name)
        actual_effects = set(event.get("actualEffects", event.get("effects", [])))
        declared_effects = set(tool.get("declaredEffects", [])) if tool else set()
        if not tool:
            runtime_findings.append({
                "type": "unknownToolCall",
                "tool": name,
                "message": f"Session called unknown tool '{name}'.",
                "sequence": index,
            })
        unsafe = sorted(actual_effects - declared_effects)
        if unsafe:
            runtime_findings.append({
                "type": "undeclaredRuntimeEffect",
                "tool": name,
                "message": f"Tool '{name}' produced undeclared effects: {', '.join(unsafe)}.",
                "effects": unsafe,
                "sequence": index,
            })

    return {
        "comparison": comparison,
        "runtimeFindings": runtime_findings,
        "timeline": timeline,
        "status": "fail" if runtime_findings else comparison["status"],
    }
