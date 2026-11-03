# Reproducible security benchmark

Agent Assurance Lab uses small, deterministic fixtures instead of live agent execution. This makes the security boundary easy to review and repeat in CI.

| Scenario | Fixture | Expected result |
| --- | --- | --- |
| Approved surface remains unchanged | `approved.json` + `observed_pass.json` | `PASS` |
| A tool is added or modified | `approved.json` + `observed.json` | `FAIL` |
| A server announces a mid-session change | `list_changed_mid_session.json` | `listChanged` signal |
| A read-only declaration performs a write | `session.json` | `undeclaredRuntimeEffect` |
| A declared write effect violates policy | `read_only_declared_write_effect.json` | policy finding |
| The manifest version changes | versioned manifest pair | `manifestVersionChanged` |
| An AgentReplay JSONL export contains an undeclared effect | `agentreplay-session.jsonl` | `undeclaredRuntimeEffect` |

Run the full negative-control demo locally:

```bash
./scripts/attack-demo.sh
```

The benchmark deliberately uses synthetic events. It validates the assurance logic without making network calls, invoking tools, or requiring secrets.
