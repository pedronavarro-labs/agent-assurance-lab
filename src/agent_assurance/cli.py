from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

import yaml

from .compare import compare_documents
from .agentreplay import load_agentreplay_jsonl
from .evidence import build_evidence, verify_signed_evidence
from .policy import evaluate_policy
from .session import analyze_session


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return document


def _load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"{path} must contain a configuration object")
    return document


def _load_session(path: Path, session_format: str) -> dict[str, Any]:
    if session_format == "agentreplay-jsonl":
        return load_agentreplay_jsonl(path)
    return _load(path)


def _sarif(result: dict[str, Any]) -> dict[str, Any]:
    rules = {
        change["type"]: {
            "id": f"tool-{change['type']}",
            "shortDescription": {"text": f"Tool {change['type']}"},
        }
        for change in result["changes"]
    }
    for finding in result.get("policyFindings", []) + result.get("runtimeFindings", []):
        rule = finding.get("rule", finding.get("type", "runtime-finding"))
        rules[rule] = {"id": rule, "shortDescription": {"text": finding.get("message", rule)}}
    sarif_results = [
        {
            "ruleId": f"tool-{change['type']}",
            "level": "error",
            "message": {"text": f"Tool '{change['name']}' was {change['type']}."},
        }
        for change in result["changes"]
    ]
    for finding in result.get("policyFindings", []) + result.get("runtimeFindings", []):
        rule = finding.get("rule", finding.get("type", "runtime-finding"))
        sarif_results.append({
            "ruleId": rule,
            "level": "error",
            "message": {"text": finding.get("message", rule)},
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "agent-assurance", "rules": list(rules.values())}}, "results": sarif_results}],
    }


def _html(result: dict[str, Any]) -> str:
    status = html.escape(result["status"].upper())
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(change['type'])}</td>"
        f"<td><code>{html.escape(change['name'])}</code></td>"
        f"<td>{html.escape(', '.join(change.get('changedFields', [])))}</td>"
        "</tr>"
        for change in result["changes"]
    )
    findings = result.get("policyFindings", []) + result.get("runtimeFindings", [])
    finding_rows = "".join(
        f"<tr><td>{html.escape(item.get('severity', 'error'))}</td>"
        f"<td><code>{html.escape(item.get('rule', item.get('type', 'finding')))}</code></td>"
        f"<td>{html.escape(item.get('message', ''))}</td></tr>"
        for item in findings
    )
    timeline_rows = "".join(
        f"<tr><td>{item.get('sequence', '')}</td><td>{html.escape(str(item.get('type', '')))}</td>"
        f"<td>{html.escape(str(item.get('tool', '')))}</td><td>{html.escape(str(item.get('status', '')))}</td></tr>"
        for item in result.get("timeline", [])
    )
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Agent Assurance report</title>
<style>body{{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 20px;background:#f8fafc;color:#172033}}section{{background:#fff;border:1px solid #dbe3ef;border-radius:12px;padding:20px;margin:18px 0}}.status{{font-weight:700;color:{'#14804a' if status == 'PASS' else '#b42318'}}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}th{{background:#f1f5f9}}</style>
<h1>Agent Assurance report</h1>
<section><p>Status: <span class="status">{status}</span></p>
<p>Approved tools: {result['approvedToolCount']} · Observed tools: {result['observedToolCount']}</p>
<p>Signals: {html.escape(', '.join(result.get('signals', [])) or 'None')} · Evidence: {html.escape(str(result.get('evidenceVerified', False)))}</p></section>
<section><h2>Tool surface changes</h2>
<table><thead><tr><th>Type</th><th>Tool</th><th>Changed fields</th></tr></thead><tbody>{rows or '<tr><td colspan="3">No changes detected.</td></tr>'}</tbody></table>
</section>
<section><h2>Policy and runtime findings</h2><table><thead><tr><th>Severity</th><th>Rule</th><th>Message</th></tr></thead><tbody>{finding_rows or '<tr><td colspan="3">No findings.</td></tr>'}</tbody></table></section>
<section><h2>Session timeline</h2><table><thead><tr><th>#</th><th>Event</th><th>Tool</th><th>Status</th></tr></thead><tbody>{timeline_rows or '<tr><td colspan="4">No session events.</td></tr>'}</tbody></table></section>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare approved and observed AI agent tools.")
    parser.add_argument("--approved", required=True, type=Path)
    parser.add_argument("--observed", required=True, type=Path)
    parser.add_argument("--format", choices=("text", "json", "sarif", "html"), default="text")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence", type=Path, help="Signed approval evidence bundle")
    parser.add_argument("--public-key", type=Path, help="Optional external Ed25519 public key")
    parser.add_argument("--policy", type=Path, help="Policy YAML or JSON file")
    parser.add_argument("--session", type=Path, help="Session evidence JSON file")
    parser.add_argument(
        "--session-format",
        choices=("json", "agentreplay-jsonl"),
        default="json",
        help="Format used by --session",
    )
    args = parser.parse_args()

    try:
        approved = _load(args.approved)
        observed = _load(args.observed)
        result = compare_documents(approved, observed)
        if args.session:
            session = _load_session(args.session, args.session_format)
            session_result = analyze_session(approved, session)
            result.update({
                "runtimeFindings": session_result["runtimeFindings"],
                "timeline": session_result["timeline"],
            })
            if session_result["status"] == "fail":
                result["status"] = "fail"
        policy = _load_config(args.policy) if args.policy else None
        if policy:
            policy_findings = evaluate_policy(approved, observed, result, policy)
            result["policyFindings"] = policy_findings
            if policy_findings:
                result["status"] = "fail"
        if args.evidence:
            bundle = _load(args.evidence)
            public_key = args.public_key.read_bytes() if args.public_key else None
            if not verify_signed_evidence(bundle, public_key):
                raise ValueError("Signed approval evidence is invalid")
            if bundle.get("evidence") != build_evidence(approved):
                raise ValueError("Signed approval evidence does not match the approved manifest")
            result["evidenceVerified"] = True
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))

    if args.format == "json":
        rendered = json.dumps(result, indent=2, ensure_ascii=False)
    elif args.format == "sarif":
        rendered = json.dumps(_sarif(result), indent=2, ensure_ascii=False)
    elif args.format == "html":
        rendered = _html(result)
    else:
        rendered = result["status"].upper()
        if result.get("signals"):
            rendered += f"\nSignals: {', '.join(result['signals'])}"
        for change in result["changes"]:
            fields = f" ({', '.join(change.get('changedFields', []))})" if change.get("changedFields") else ""
            rendered += f"\n- {change['type']}: {change['name']}{fields}"
        for finding in result.get("policyFindings", []) + result.get("runtimeFindings", []):
            rendered += f"\n- {finding.get('rule', finding.get('type'))}: {finding.get('message')}"

    if args.output:
        args.output.write_text(rendered + ("\n" if not rendered.endswith("\n") else ""), encoding="utf-8")
    else:
        print(rendered)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
