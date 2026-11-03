#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "== 1. Static surface check =="
if PYTHONPATH=src python -m agent_assurance.cli \
  --approved examples/approved.json \
  --observed examples/observed.json \
  --policy examples/policy.yml \
  --format text; then
  echo "ERROR: static drift should have been blocked" >&2
  exit 1
fi

echo
echo "== 2. Runtime evidence check =="
if PYTHONPATH=src python -m agent_assurance.cli \
  --approved examples/approved.json \
  --observed examples/observed_pass.json \
  --session examples/session.json \
  --format text; then
  echo "ERROR: undeclared runtime effect should have been blocked" >&2
  exit 1
fi

echo
echo "Both negative controls were detected as expected."
