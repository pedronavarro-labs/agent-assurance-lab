from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evidence import (
    create_signed_evidence,
    generate_ed25519_private_key,
    public_key_from_private_key,
    verify_signed_evidence,
)


def _json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and verify signed Agent Assurance evidence.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    key_parser = subparsers.add_parser("generate-key", help="Generate an Ed25519 private key")
    key_parser.add_argument("--output", required=True, type=Path)

    public_parser = subparsers.add_parser("export-public-key", help="Export the public key from a private key")
    public_parser.add_argument("--private-key", required=True, type=Path)
    public_parser.add_argument("--output", required=True, type=Path)

    sign_parser = subparsers.add_parser("sign", help="Sign an approved manifest")
    sign_parser.add_argument("--manifest", required=True, type=Path)
    sign_parser.add_argument("--private-key", required=True, type=Path)
    sign_parser.add_argument("--output", required=True, type=Path)

    verify_parser = subparsers.add_parser("verify", help="Verify signed evidence")
    verify_parser.add_argument("--evidence", required=True, type=Path)
    verify_parser.add_argument("--public-key", type=Path)

    args = parser.parse_args()
    if args.command == "generate-key":
        args.output.write_bytes(generate_ed25519_private_key())
        return 0
    if args.command == "export-public-key":
        args.output.write_bytes(public_key_from_private_key(args.private_key.read_bytes()))
        return 0
    if args.command == "sign":
        bundle = create_signed_evidence(_json(args.manifest), args.private_key.read_bytes())
        _write(args.output, bundle)
        return 0

    valid = verify_signed_evidence(_json(args.evidence), args.public_key.read_bytes() if args.public_key else None)
    print("VALID" if valid else "INVALID")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
