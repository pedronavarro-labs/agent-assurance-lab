from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from .compare import compare_documents
from .evidence import build_evidence, verify_signed_evidence


def _load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return document


def _sarif(result: dict[str, Any]) -> dict[str, Any]:
    rules = {
        change["type"]: {
            "id": f"tool-{change['type']}",
            "shortDescription": {"text": f"Tool {change['type']}"},
        }
        for change in result["changes"]
    }
    sarif_results = [
        {
            "ruleId": f"tool-{change['type']}",
            "level": "error",
            "message": {"text": f"Tool '{change['name']}' was {change['type']}."},
        }
        for change in result["changes"]
    ]
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
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Agent Assurance report</title>
<style>body{{font:16px system-ui;max-width:900px;margin:40px auto;padding:0 20px}}.status{{font-weight:700;color:{'#14804a' if status == 'PASS' else '#b42318'}}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}</style>
<h1>Agent Assurance report</h1>
<p>Status: <span class="status">{status}</span></p>
<p>Approved tools: {result['approvedToolCount']} · Observed tools: {result['observedToolCount']}</p>
<table><thead><tr><th>Type</th><th>Tool</th><th>Changed fields</th></tr></thead><tbody>{rows or '<tr><td colspan="3">No changes detected.</td></tr>'}</tbody></table>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare approved and observed AI agent tools.")
    parser.add_argument("--approved", required=True, type=Path)
    parser.add_argument("--observed", required=True, type=Path)
    parser.add_argument("--format", choices=("text", "json", "sarif", "html"), default="text")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence", type=Path, help="Signed approval evidence bundle")
    parser.add_argument("--public-key", type=Path, help="Optional external Ed25519 public key")
    args = parser.parse_args()

    try:
        approved = _load(args.approved)
        observed = _load(args.observed)
        result = compare_documents(approved, observed)
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

    if args.output:
        args.output.write_text(rendered + ("\n" if not rendered.endswith("\n") else ""), encoding="utf-8")
    else:
        print(rendered)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
