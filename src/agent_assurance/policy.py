from __future__ import annotations

from dataclasses import dataclass
from typing import Any


WRITE_EFFECTS = {"write", "delete", "execute", "admin", "network"}


@dataclass(frozen=True)
class PolicyFinding:
    rule: str
    severity: str
    message: str
    tool: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result = {
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
        }
        if self.tool:
            result["tool"] = self.tool
        return result


def default_policy() -> dict[str, Any]:
    return {
        "version": 1,
        "rules": {
            "block_added_tools": True,
            "block_removed_tools": False,
            "fail_on_list_changed": False,
            "blocked_tools": [],
            "read_only_tools": [],
            "deny_effects": ["write", "delete", "execute", "admin"],
        },
    }


def _rules(policy: dict[str, Any] | None) -> dict[str, Any]:
    result = default_policy()
    if not policy:
        return result["rules"]
    configured = policy.get("rules", policy)
    if not isinstance(configured, dict):
        raise ValueError("Policy rules must be an object")
    result["rules"].update(configured)
    return result["rules"]


def evaluate_policy(
    approved: dict[str, Any],
    observed: dict[str, Any],
    comparison: dict[str, Any],
    policy: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rules = _rules(policy)
    findings: list[PolicyFinding] = []
    severity = "error"

    for change in comparison.get("changes", []):
        change_type = change.get("type")
        name = change.get("name")
        if change_type == "added" and rules.get("block_added_tools", True):
            findings.append(PolicyFinding("block_added_tools", severity, f"Added tool '{name}' requires approval.", name))
        if change_type == "removed" and rules.get("block_removed_tools", False):
            findings.append(PolicyFinding("block_removed_tools", severity, f"Removed tool '{name}' is not allowed by policy.", name))

    blocked = set(rules.get("blocked_tools", []))
    observed_names = {tool.get("name") for tool in observed.get("tools", []) if isinstance(tool, dict)}
    for name in sorted(blocked & observed_names):
        findings.append(PolicyFinding("blocked_tools", severity, f"Tool '{name}' is blocked by policy.", name))

    if rules.get("fail_on_list_changed") and "listChanged" in comparison.get("signals", []):
        findings.append(PolicyFinding("fail_on_list_changed", severity, "The server announced a tool surface change."))

    read_only = set(rules.get("read_only_tools", []))
    deny_effects = set(rules.get("deny_effects", WRITE_EFFECTS))
    for tool in observed.get("tools", []):
        if not isinstance(tool, dict) or tool.get("name") not in read_only:
            continue
        effects = set(tool.get("declaredEffects", []))
        unsafe = sorted(effects & deny_effects)
        if unsafe:
            findings.append(PolicyFinding(
                "read_only_tools",
                severity,
                f"Read-only tool '{tool['name']}' declares unsafe effects: {', '.join(unsafe)}.",
                tool["name"],
            ))

    return [finding.as_dict() for finding in findings]
