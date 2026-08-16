import json
import hmac
import base64
import unittest
from pathlib import Path

from recoup import FailedClosed, calculate_audit, evidence, money, ratio, run_audit, synthetic_documents, synthetic_extraction, terac_budget_ok, verify_dodo_signature


class RecoupTest(unittest.TestCase):
    def test_synthetic_gate(self):
        expected = json.loads(Path("synthetic/answer-key.json").read_text())
        result = run_audit(synthetic_documents(), synthetic=True, tenant="Synthetic Tenant")
        audit = result["audit"]
        for key in ("claimed_actual", "estimated_paid", "stated_balance", "verified_actual", "verified_balance", "correction"):
            self.assertEqual(expected[key], audit[key])
        self.assertEqual(expected["deadline"], audit["deadline"]["value"])
        self.assertEqual(expected["finding_codes"], [f["code"] for f in audit["findings"]])
        self.assertTrue(all(f["lease_evidence"]["quote"] and f["statement_evidence"]["location"] for f in audit["findings"]))
        self.assertNotIn("possible", result["draft_notice"].lower())

    def test_missing_evidence_fails_closed(self):
        extracted = synthetic_extraction()
        del extracted["tenant_share"]["quote"]
        with self.assertRaises(FailedClosed):
            calculate_audit(extracted)

    def test_conflicting_arithmetic_fails_closed(self):
        extracted = synthetic_extraction()
        extracted["claimed_actual"] = evidence("14000", "Tenant claimed actual CAM: $14,000", "reconciliation", "line 10")
        with self.assertRaises(FailedClosed):
            calculate_audit(extracted)

    def test_budget_never_uses_cash(self):
        self.assertTrue(terac_budget_ok(12500, 5000, 7500))
        self.assertFalse(terac_budget_ok(12500, 5000, 7501))
        self.assertFalse(terac_budget_ok(20000, 0, 12501))

    def test_dodo_signature_gate(self):
        import hashlib
        body, raw_secret, timestamp, message_id = b'{"type":"payment.succeeded"}', b"test-secret-value-1234567890", "2000000000", "msg_test"
        secret = "whsec_" + base64.b64encode(raw_secret).decode()
        signature = base64.b64encode(hmac.new(raw_secret, message_id.encode() + b"." + timestamp.encode() + b"." + body, hashlib.sha256).digest()).decode()
        headers = {"webhook-id": message_id, "webhook-timestamp": timestamp, "webhook-signature": f"v1,{signature}"}
        verify_dodo_signature(body, headers, secret, current_time=2000000001)
        with self.assertRaises(FailedClosed):
            verify_dodo_signature(body, {**headers, "webhook-signature": "v1,bad"}, secret, current_time=2000000001)

    def test_model_number_formats(self):
        self.assertEqual(str(ratio("4.2%")), "0.042")
        self.assertEqual(str(money("$14,400.00")), "14400.00")


if __name__ == "__main__":
    unittest.main()
