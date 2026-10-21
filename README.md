# Agent Assurance Lab

Deterministic assurance checks for AI agent tool definitions.

The first MVP compares an approved tool manifest with an observed `tools/list` snapshot. It detects added, removed, and modified tools by hashing each tool's name, description, and `inputSchema` using canonical JSON.

## Quick start

```bash
python -m unittest discover -s tests
PYTHONPATH=src python -m agent_assurance.cli \
  --approved examples/approved.json \
  --observed examples/observed.json \
  --format text
```

The example intentionally fails because the observed snapshot contains a changed `read_file` definition and an unexpected `delete_file` tool. Use `--format json`, `--format sarif`, or `--format html --output report.html` for machine-readable and human-readable reports.

## Signed approval evidence

Approval evidence uses Ed25519 signatures. Keep the private key outside the repository and publish only the evidence bundle or the public key.

```bash
agent-assurance-evidence generate-key --output approval-private.pem
agent-assurance-evidence export-public-key \
  --private-key approval-private.pem \
  --output approval-public.pem
agent-assurance-evidence sign \
  --manifest examples/approved.json \
  --private-key approval-private.pem \
  --output approval-evidence.json
agent-assurance-evidence verify --evidence approval-evidence.json
```

The bundle contains the canonical manifest hash, per-tool fingerprints, the signature algorithm, the signature, and the public key needed for local verification. In CI, pass the separately distributed `approval-public.pem`; the GitHub Action rejects an evidence bundle without it.

## GitHub Action

The repository includes a composite action that verifies signed evidence before comparing tool definitions and writes a SARIF report:

```yaml
- uses: pedronavarro-labs/agent-assurance-lab@main
  with:
    approved: security/approved.json
    observed: security/observed.json
    evidence: security/approval-evidence.json
    public-key: security/approval-public.pem
    report: agent-assurance.sarif
```

The example workflow in `.github/workflows/agent-assurance.yml` runs manually and uploads the SARIF report to GitHub Code Scanning.

## MVP scope

- Canonical SHA-256 fingerprints for tool definitions.
- Detection of added, removed, and modified tools.
- JSON, SARIF, HTML, and text reports.
- Non-zero exit status when the approved and observed surfaces differ.
- `listChanged` session signals are preserved in the result.
- No network access and no runtime agent execution.

## Roadmap

1. Add manifest versioning and policy-aware compatibility rules.
2. Integrate AgentReplay session evidence.
3. Expand the reproducible security benchmark.

## Synthetic fixtures

- `examples/list_changed_mid_session.json` demonstrates a changed tool definition after a `listChanged` event.
- `examples/read_only_declared_write_effect.json` documents the boundary between declarations and runtime behavior.
- See `docs/threat-model.md` for the interpretation of both cases.
