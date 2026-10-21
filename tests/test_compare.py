import unittest

from agent_assurance.compare import compare_documents, fingerprint_tool
from agent_assurance.evidence import create_signed_evidence, generate_ed25519_private_key, verify_signed_evidence


class CompareDocumentsTests(unittest.TestCase):
    def test_same_tool_is_pass(self):
        document = {"tools": [{"name": "read", "description": "Read", "inputSchema": {"type": "object"}}]}
        self.assertEqual(compare_documents(document, document)["status"], "pass")

    def test_description_change_is_modified(self):
        approved = {"tools": [{"name": "read", "description": "Read", "inputSchema": {}}]}
        observed = {"tools": [{"name": "read", "description": "Read and write", "inputSchema": {}}]}
        result = compare_documents(approved, observed)
        self.assertEqual(result["changes"][0]["type"], "modified")
        self.assertEqual(result["changes"][0]["changedFields"], ["description"])

    def test_added_and_removed_tools_are_reported(self):
        approved = {"tools": [{"name": "read"}]}
        observed = {"tools": [{"name": "write"}]}
        result = compare_documents(approved, observed)
        self.assertEqual([change["type"] for change in result["changes"]], ["removed", "added"])

    def test_fingerprint_is_order_independent(self):
        first = {"name": "read", "description": "Read", "inputSchema": {"b": 2, "a": 1}}
        second = {"inputSchema": {"a": 1, "b": 2}, "description": "Read", "name": "read"}
        self.assertEqual(fingerprint_tool(first), fingerprint_tool(second))

    def test_list_changed_is_exposed_as_a_signal(self):
        document = {"tools": [{"name": "read"}]}
        observed = {"tools": [{"name": "read"}], "events": [{"type": "listChanged"}]}
        result = compare_documents(document, observed)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["signals"], ["listChanged"])

    def test_static_comparison_does_not_claim_to_detect_runtime_effects(self):
        approved = {"tools": [{"name": "read", "declaredEffects": ["read"]}]}
        observed = {"tools": [{"name": "read", "declaredEffects": ["read"]}]}
        result = compare_documents(approved, observed)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["changes"], [])

    def test_signed_evidence_round_trip_and_tamper_detection(self):
        manifest = {"tools": [{"name": "read", "description": "Read", "inputSchema": {}}]}
        bundle = create_signed_evidence(manifest, generate_ed25519_private_key())
        self.assertTrue(verify_signed_evidence(bundle))
        bundle["evidence"]["manifestHash"] = "tampered"
        self.assertFalse(verify_signed_evidence(bundle))
