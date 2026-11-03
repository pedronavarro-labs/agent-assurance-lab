# Boundary Signal — launch demo runbook

This runbook is the script for a five-minute product demonstration of Boundary Signal 1.0.

## 1. Start the local console

```bash
pip install -e '.[web]'
PYTHONPATH=src agent-assurance-web --port 8787
```

Open <http://127.0.0.1:8787>.

The console is local-first: manifests, policy decisions and run history remain on the host running the application.

## 2. Demo flow

### A. Establish the approved boundary

Open the **Baseline** scenario. Show the clean posture and point out that the approved tool surface is fingerprinted before the agent continues.

### B. Introduce static drift

Open **Static drift** and run the check. Highlight the changed schema and the unexpected tool. The decision center should move to a blocked state because the observed surface no longer matches the approved one.

### C. Prove runtime evidence matters

Open **Runtime write** and run the check. Explain that a tool declared read-only can still be unsafe at runtime; the session evidence catches the undeclared write effect.

### D. Connect the result to CI

Run the reproducible attack demo from a terminal:

```bash
./scripts/attack-demo.sh
```

The command exits non-zero for the negative controls. This is intentional: the failure is the security signal that a CI pipeline can enforce.

### E. Close with the value proposition

> Boundary Signal turns an agent's tool boundary into a verifiable, reviewable and CI-enforceable decision.

## 3. API inspection

Open <http://127.0.0.1:8787/api/docs> to show the typed FastAPI contract. The useful endpoints for the demo are:

- `GET /api/v1/health` — service status and version.
- `POST /api/v1/analyze` — evaluate a manifest, policy and optional session evidence.
- `GET /api/v1/runs` — inspect local run history.
- `GET /api/v1/runs/{run_id}` — retrieve a complete decision record.

## 4. Reset between demos

The scenarios are deterministic and do not require a live agent or network access. Restart the local process if you want a fresh run history.
