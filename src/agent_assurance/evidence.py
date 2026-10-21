from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .compare import fingerprint_tool


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_evidence(manifest: dict[str, Any]) -> dict[str, Any]:
    tools = manifest.get("tools", [])
    fingerprints = {
        tool["name"]: fingerprint_tool(tool)
        for tool in tools
        if isinstance(tool, dict) and isinstance(tool.get("name"), str)
    }
    return {
        "formatVersion": 1,
        "hashAlgorithm": "SHA-256",
        "manifestHash": hashlib.sha256(_canonical_json(manifest)).hexdigest(),
        "toolFingerprints": dict(sorted(fingerprints.items())),
    }


def create_signed_evidence(manifest: dict[str, Any], private_key_pem: bytes) -> dict[str, Any]:
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        raise ValueError("Private key must be an Ed25519 PEM key")
    evidence = build_evidence(manifest)
    payload = _canonical_json(evidence)
    signature = private_key.sign(payload)
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return {
        "evidence": evidence,
        "signatureAlgorithm": "Ed25519",
        "signature": base64.b64encode(signature).decode("ascii"),
        "publicKey": public_key.decode("ascii"),
    }


def verify_signed_evidence(bundle: dict[str, Any], public_key_pem: bytes | None = None) -> bool:
    evidence = bundle.get("evidence")
    signature_text = bundle.get("signature")
    embedded_key = bundle.get("publicKey")
    if not isinstance(evidence, dict) or not isinstance(signature_text, str):
        raise ValueError("Invalid signed evidence bundle")
    key_pem = public_key_pem or (embedded_key.encode("utf-8") if isinstance(embedded_key, str) else None)
    if key_pem is None:
        raise ValueError("A public key is required")
    public_key = serialization.load_pem_public_key(key_pem)
    if not isinstance(public_key, Ed25519PublicKey):
        raise ValueError("Public key must be an Ed25519 PEM key")
    try:
        public_key.verify(base64.b64decode(signature_text), _canonical_json(evidence))
    except Exception:
        return False
    return True


def generate_ed25519_private_key() -> bytes:
    private_key = Ed25519PrivateKey.generate()
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def public_key_from_private_key(private_key_pem: bytes) -> bytes:
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        raise ValueError("Private key must be an Ed25519 PEM key")
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
