import json
import hmac
import base64
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from recoup import FailedClosed, calculate_audit, evidence, linq_send_message, money, ratio, resend_email, run_audit, synthetic_documents, synthetic_extraction, terac_budget_ok, valid_email, valid_phone, verify_dodo_signature, verify_linq_signature


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
        verify_linq_signature(body, headers, secret, current_time=2000000001)
        with self.assertRaises(FailedClosed):
            verify_dodo_signature(body, {**headers, "webhook-signature": "v1,bad"}, secret, current_time=2000000001)

    def test_model_number_formats(self):
        self.assertEqual(str(ratio("4.2%")), "0.042")
        self.assertEqual(str(money("$14,400.00")), "14400.00")

    @patch("recoup.urllib.request.urlopen")
    def test_resend_email(self, urlopen):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b'{"id":"email_test"}'
        urlopen.return_value = response
        with patch.dict("os.environ", {"RESEND_API_KEY": "re_test", "RESEND_FROM_EMAIL": "Recoup <onboarding@resend.dev>"}):
            self.assertEqual(resend_email("landlord@example.com", "Notice", "Body", "case-test"), "email_test")
        request = urlopen.call_args.args[0]
        self.assertEqual(json.loads(request.data)["to"], ["landlord@example.com"])
        self.assertEqual(request.headers["Idempotency-key"], "case-test")
        self.assertTrue(valid_email("landlord@example.com"))
        self.assertFalse(valid_email("not-an-email"))

    @patch("recoup.urllib.request.urlopen")
    def test_linq_message(self, urlopen):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = b'{"chat":{"id":"chat_test","message":{"id":"message_test","delivery_status":"queued","service":"iMessage"}}}'
        urlopen.return_value = response
        with patch.dict("os.environ", {"LINQ_API_KEY": "linq_test", "LINQ_FROM_NUMBER": "+14155550100"}):
            result = linq_send_message("+14155550123", "Follow-up", "case-test")
        self.assertEqual(result, {"chat_id": "chat_test", "message_id": "message_test", "status": "queued", "service": "iMessage"})
        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(payload["to"], ["+14155550123"])
        self.assertEqual(payload["message"]["idempotency_key"], "case-test")
        self.assertTrue(valid_phone("+14155550123"))
        self.assertFalse(valid_phone("415-555-0123"))


if __name__ == "__main__":
    unittest.main()
