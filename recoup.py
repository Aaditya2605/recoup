"""Recoup domain logic: evidence, calculations, audits, and policy gates."""

from __future__ import annotations

import hashlib
import hmac
import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


MONEY = Decimal("0.01")
PIONEER_URL = "https://api.pioneer.ai/v1/chat/completions"
PIONEER_MODEL = os.getenv(
    "PIONEER_MODEL", "moonshotai/Kimi-K3"
)
PIONEER_VERIFY_MODEL = os.getenv("PIONEER_VERIFY_MODEL", PIONEER_MODEL)
TERMINAL_STATES = {
    "corrected_bill",
    "credit",
    "refund",
    "confirmed_charge",
    "rejected_dispute",
    "professional_review",
    "failed_closed",
}


def valid_email(value: object) -> bool:
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", str(value).strip()))


def valid_phone(value: object) -> bool:
    return bool(re.fullmatch(r"\+[1-9]\d{7,14}", str(value).strip()))


class FailedClosed(ValueError):
    """The workflow cannot proceed safely from the available evidence."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def money(value: Any) -> Decimal:
    try:
        cleaned = str(value).strip().replace("$", "").replace(",", "")
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]
        return Decimal(cleaned).quantize(MONEY, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError) as exc:
        raise FailedClosed(f"Invalid money value: {value!r}") from exc


def ratio(value: Any) -> Decimal:
    text = str(value).strip()
    try:
        return Decimal(text[:-1]) / 100 if text.endswith("%") else Decimal(text)
    except InvalidOperation as exc:
        raise FailedClosed(f"Invalid percentage value: {value!r}") from exc


def evidence(value: Any, quote: str, document: str, location: str) -> dict[str, Any]:
    item = {"value": value, "quote": quote.strip(), "document": document, "location": location}
    if not all((item["quote"], item["document"], item["location"])):
        raise FailedClosed("Every extracted fact needs a quote, document, and location.")
    return item


def require_evidence(item: Any, name: str) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise FailedClosed(f"Missing evidence for {name}.")
    for key in ("value", "quote", "document", "location"):
        if key not in item or item[key] in (None, ""):
            raise FailedClosed(f"Missing {key} for {name}.")
    return item


def deadline(statement_date: dict[str, Any], objection_days: dict[str, Any]) -> dict[str, Any]:
    stated = require_evidence(statement_date, "statement date")
    window = require_evidence(objection_days, "objection window")
    try:
        start = date.fromisoformat(str(stated["value"]))
        days = int(window["value"])
    except (ValueError, TypeError) as exc:
        raise FailedClosed("The statement date or objection window is invalid.") from exc
    if not 1 <= days <= 730:
        raise FailedClosed("The objection window is outside the supported range.")
    result = start + timedelta(days=days)
    return {
        "value": result.isoformat(),
        "formula": f"{start.isoformat()} + {days} calendar days",
        "inputs": [stated, window],
    }


def eligibility(payload: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if payload.get("country") != "US":
        reasons.append("Version 1 serves United States cases only.")
    if payload.get("lease_type") != "NNN retail":
        reasons.append("Version 1 serves triple-net retail leases only.")
    required = set(payload.get("document_kinds", []))
    missing = {"lease", "reconciliation"} - required
    if missing:
        reasons.append("Missing required documents: " + ", ".join(sorted(missing)) + ".")
    if payload.get("requires_professional"):
        reasons.append("The case already requires qualified professional review.")
    return {
        "eligible": not reasons,
        "price_cents": 49900 if not reasons else None,
        "reasons": reasons,
        "refund_rule": "Full refund if a paid case is later outside scope or cannot be processed.",
    }


def synthetic_documents() -> dict[str, str]:
    return {
        "lease": """SYNTHETIC DOCUMENT — NOT A REAL LEASE
Recoup Evaluation Lease
Section 6.2 — Tenant Share. Tenant's Proportionate Share is 4.2%.
Section 6.3 — Operating Costs. Common-area maintenance, insurance, utilities, and one management fee are permitted Operating Costs.
Section 6.4 — Exclusions. Structural roof replacement is excluded. An administrative fee is excluded when a management fee is also charged.
Section 6.5 — Gross-up. Variable Operating Costs may be grossed up to 95% occupancy.
Section 6.6 — Cap. Controllable Operating Costs may increase by no more than 5% per calendar year, non-cumulative and non-compounding.
Section 6.7 — Capital Costs. Permitted capital costs must be amortized over useful life with interest at the prime rate.
Section 8.1 — Audit. Tenant may object within 60 calendar days after the statement date. Records review must be performed by an independent CPA paid on a non-contingent basis.
Section 8.2 — Payment. Tenant must pay the billed amount while a dispute is pending and may not offset rent.
Section 8.3 — Notice. Formal notice must be sent by certified mail to 100 Landlord Way, San Francisco, CA 94107.
Section 8.4 — Resolution. An overpayment must be credited against the next rent payment; an underpayment is due within 30 days.
""",
        "reconciliation": """SYNTHETIC DOCUMENT — NOT A REAL BILL
2025 CAM Reconciliation — Statement date: January 15, 2026
Common-area maintenance: $200,000.00
Insurance and utilities: $40,000.00
Management fee: $10,000.00
Structural roof replacement: $40,000.00
Administrative fee: $10,000.00
Total claimed Operating Costs: $300,000.00
Tenant share used: 4.8%
Tenant claimed actual CAM: $14,400.00
Estimated CAM paid: $12,000.00
Additional amount billed: $2,400.00
""",
        "ledger": """SYNTHETIC DOCUMENT — NOT A REAL LEDGER
Tenant CAM ledger for 2025
Twelve monthly CAM payments of $1,000.00 were received.
Total estimated CAM paid: $12,000.00.
No additional reconciliation payment has been made.
""",
    }


def synthetic_extraction() -> dict[str, Any]:
    e = evidence
    return {
        "statement_date": e("2026-01-15", "Statement date: January 15, 2026", "reconciliation", "line 2"),
        "objection_days": e(60, "Tenant may object within 60 calendar days after the statement date.", "lease", "Section 8.1"),
        "tenant_share": e("0.042", "Tenant's Proportionate Share is 4.2%.", "lease", "Section 6.2"),
        "claimed_share": e("0.048", "Tenant share used: 4.8%", "reconciliation", "line 9"),
        "permitted_categories": e(["common-area maintenance", "insurance and utilities", "management fee"], "Common-area maintenance, insurance, utilities, and one management fee are permitted Operating Costs.", "lease", "Section 6.3"),
        "excluded_categories": e(["structural roof replacement", "administrative fee"], "Structural roof replacement is excluded. An administrative fee is excluded when a management fee is also charged.", "lease", "Section 6.4"),
        "gross_up": e({"allowed": True, "occupancy": "0.95"}, "Variable Operating Costs may be grossed up to 95% occupancy.", "lease", "Section 6.5"),
        "expense_cap": e({"rate": "0.05", "cumulative": False, "compounding": False}, "Controllable Operating Costs may increase by no more than 5% per calendar year, non-cumulative and non-compounding.", "lease", "Section 6.6"),
        "capital_rule": e("amortize over useful life at prime", "Permitted capital costs must be amortized over useful life with interest at the prime rate.", "lease", "Section 6.7"),
        "audit_rights": e({"independent_cpa": True, "contingency_allowed": False}, "Records review must be performed by an independent CPA paid on a non-contingent basis.", "lease", "Section 8.1"),
        "pay_first": e(True, "Tenant must pay the billed amount while a dispute is pending and may not offset rent.", "lease", "Section 8.2"),
        "withholding_allowed": e(False, "Tenant must pay the billed amount while a dispute is pending and may not offset rent.", "lease", "Section 8.2"),
        "notice": e({"method": "certified_mail", "address": "100 Landlord Way, San Francisco, CA 94107"}, "Formal notice must be sent by certified mail to 100 Landlord Way, San Francisco, CA 94107.", "lease", "Section 8.3"),
        "resolution_rule": e("credit overpayment; underpayment due in 30 days", "An overpayment must be credited against the next rent payment; an underpayment is due within 30 days.", "lease", "Section 8.4"),
        "claimed_expenses": e("300000.00", "Total claimed Operating Costs: $300,000.00", "reconciliation", "line 8"),
        "permitted_expenses": e("250000.00", "Common-area maintenance: $200,000.00\nInsurance and utilities: $40,000.00\nManagement fee: $10,000.00", "reconciliation", "lines 3-5"),
        "roof_expense": e("40000.00", "Structural roof replacement: $40,000.00", "reconciliation", "line 6"),
        "admin_expense": e("10000.00", "Administrative fee: $10,000.00", "reconciliation", "line 7"),
        "claimed_actual": e("14400.00", "Tenant claimed actual CAM: $14,400.00", "reconciliation", "line 10"),
        "estimated_paid": e("12000.00", "Total estimated CAM paid: $12,000.00.", "ledger", "line 3"),
        "additional_bill": e("2400.00", "Additional amount billed: $2,400.00", "reconciliation", "line 12"),
    }


REQUIRED_FIELDS = tuple(synthetic_extraction())


def validate_extraction(extracted: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if field not in extracted]
    if missing:
        raise FailedClosed("Missing extracted fields: " + ", ".join(missing))
    for field in REQUIRED_FIELDS:
        require_evidence(extracted[field], field)
    return extracted


def calculate_audit(extracted: dict[str, Any]) -> dict[str, Any]:
    x = validate_extraction(extracted)
    share = ratio(x["tenant_share"]["value"])
    claimed_share = ratio(x["claimed_share"]["value"])
    claimed_expenses = money(x["claimed_expenses"]["value"])
    permitted_expenses = money(x["permitted_expenses"]["value"])
    roof = money(x["roof_expense"]["value"])
    admin = money(x["admin_expense"]["value"])
    paid = money(x["estimated_paid"]["value"])
    claimed_actual = money(x["claimed_actual"]["value"])
    stated_bill = money(x["additional_bill"]["value"])
    if (claimed_expenses * claimed_share).quantize(MONEY) != claimed_actual:
        raise FailedClosed("The reconciliation arithmetic conflicts with the extracted totals.")
    if claimed_actual - paid != stated_bill:
        raise FailedClosed("The stated additional bill does not reconcile with payments.")
    correct_actual = (permitted_expenses * share).quantize(MONEY)
    correct_balance = correct_actual - paid
    findings = [
        {
            "code": "allocation_share",
            "title": "Incorrect tenant allocation percentage",
            "amount": str((claimed_expenses * (claimed_share - share)).quantize(MONEY)),
            "lease_evidence": x["tenant_share"],
            "statement_evidence": x["claimed_share"],
            "calculation": f"$300,000.00 × (4.8% − 4.2%) = $1,800.00",
        },
        {
            "code": "excluded_capital",
            "title": "Excluded structural roof replacement",
            "amount": str((roof * share).quantize(MONEY)),
            "lease_evidence": x["excluded_categories"],
            "statement_evidence": x["roof_expense"],
            "calculation": f"${roof:,.2f} × 4.2% = $1,680.00",
        },
        {
            "code": "duplicate_admin",
            "title": "Administrative fee charged with a management fee",
            "amount": str((admin * share).quantize(MONEY)),
            "lease_evidence": x["excluded_categories"],
            "statement_evidence": x["admin_expense"],
            "calculation": f"${admin:,.2f} × 4.2% = $420.00",
        },
    ]
    return {
        "deadline": deadline(x["statement_date"], x["objection_days"]),
        "claimed_actual": str(claimed_actual),
        "estimated_paid": str(paid),
        "stated_balance": str(stated_bill),
        "verified_actual": str(correct_actual),
        "verified_balance": str(correct_balance),
        "correction": str(claimed_actual - correct_actual),
        "outcome_if_accepted": "credit" if correct_balance < 0 else "corrected_bill",
        "findings": findings,
        "limits": ["Invoice-level testing requires landlord records.", "No jurisdiction-specific legal conclusion is made."],
        "professional_gate": bool(x["audit_rights"]["value"].get("independent_cpa")),
        "payment_guidance": "Pay under protest, then dispute." if x["pay_first"]["value"] else "Check the lease before withholding payment.",
    }


def verify_audit(extracted: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    verified: list[dict[str, Any]] = []
    for finding in audit.get("findings", []):
        require_evidence(finding.get("lease_evidence"), finding.get("code", "finding"))
        require_evidence(finding.get("statement_evidence"), finding.get("code", "finding"))
        if not finding.get("calculation") or money(finding.get("amount")) <= 0:
            continue
        verified.append({**finding, "verified": True})
    if not verified:
        raise FailedClosed("No candidate finding passed independent verification.")
    return {**audit, "findings": verified, "verified_at": now()}


def draft_notice(extracted: dict[str, Any], audit: dict[str, Any], tenant: str) -> str:
    x = validate_extraction(extracted)
    lines = [
        "DRAFT — CUSTOMER SIGNATURE REQUIRED",
        "Subject: Objection to 2025 CAM reconciliation",
        "",
        f"The tenant, {tenant}, objects to the CAM reconciliation dated {x['statement_date']['value']}.",
        f"The verified calculation shows a ${money(audit['correction']):,.2f} correction.",
        "",
    ]
    for finding in audit["findings"]:
        lines.append(
            f"• {finding['title']}: ${money(finding['amount']):,.2f}. "
            f"Lease {finding['lease_evidence']['location']}; statement {finding['statement_evidence']['location']}. "
            f"{finding['calculation']}"
        )
    lines += [
        "",
        "Please correct the reconciliation and provide the supporting expense ledger and invoices.",
        f"Required delivery: {x['notice']['value']['method']} to {x['notice']['value']['address']}.",
        "This draft does not waive rights, accept a compromise, threaten legal action, or give legal advice.",
    ]
    return "\n".join(lines)


def _json_from_model(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.S)
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise FailedClosed("Pioneer returned invalid JSON.") from exc
    if not isinstance(value, dict):
        raise FailedClosed("Pioneer returned the wrong JSON type.")
    return value


def pioneer(messages: list[dict[str, str]], *, model: str = PIONEER_MODEL) -> tuple[dict[str, Any], dict[str, Any]]:
    key = os.getenv("PIONEER_API_KEY")
    if not key:
        raise FailedClosed("PIONEER_API_KEY is not configured.")
    payload = json.dumps({"model": model, "messages": messages, "temperature": 0, "store": False}).encode()
    request = urllib.request.Request(
        PIONEER_URL,
        data=payload,
        headers={"X-API-Key": key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read())["error"]["message"]
        except (json.JSONDecodeError, KeyError, TypeError):
            detail = str(exc)
        raise FailedClosed(f"Pioneer inference failed: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise FailedClosed(f"Pioneer inference failed: {exc}") from exc
    try:
        content = raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise FailedClosed("Pioneer returned an unexpected response.") from exc
    return _json_from_model(content), {"provider": "Pioneer", "model": model, "inference_id": raw.get("inference_id"), "at": now()}


def live_extract(documents: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    value_formats = {
        "statement_date": "ISO date YYYY-MM-DD",
        "objection_days": "integer calendar days",
        "tenant_share": "decimal fraction or percent",
        "claimed_share": "decimal fraction or percent",
        "permitted_categories": "array of lowercase category names",
        "excluded_categories": "array of lowercase category names",
        "gross_up": {"allowed": "boolean", "occupancy": "decimal fraction or percent"},
        "expense_cap": {"rate": "decimal fraction or percent", "cumulative": "boolean", "compounding": "boolean"},
        "audit_rights": {"independent_cpa": "boolean", "contingency_allowed": "boolean"},
        "pay_first": "boolean",
        "withholding_allowed": "boolean",
        "notice": {"method": "string", "address": "string"},
    }
    money_fields = {"claimed_expenses", "permitted_expenses", "roof_expense", "admin_expense", "claimed_actual", "estimated_paid", "additional_bill"}
    schema = {
        field: {
            "value": value_formats.get(field, "plain decimal string without a currency symbol or commas" if field in money_fields else "string"),
            "quote": "exact source quote",
            "document": "document key",
            "location": "page, section, or line",
        }
        for field in REQUIRED_FIELDS
    }
    prompt = (
        "Extract this commercial NNN retail CAM case. Return JSON only. Do not infer missing facts. "
        "Each fact must include value, an exact source quote, document key, and location. "
        "permitted_expenses is the numeric subtotal of statement lines permitted by the lease, not lease text. "
        f"Required shape: {json.dumps(schema)}\nDOCUMENTS:\n{json.dumps(documents)}"
    )
    extracted, trace1 = pioneer([{"role": "system", "content": "You extract lease facts with exact evidence and fail closed."}, {"role": "user", "content": prompt}])
    validate_extraction(extracted)
    verifier_prompt = (
        "Independently check every extracted value against the supplied documents. Return JSON only as "
        '{"accepted": true, "conflicts": []}. Set accepted false for any missing, paraphrased, or conflicting evidence.\n'
        f"EXTRACTION: {json.dumps(extracted)}\nDOCUMENTS: {json.dumps(documents)}"
    )
    verdict, trace2 = pioneer([{"role": "system", "content": "You are an independent evidence verifier."}, {"role": "user", "content": verifier_prompt}], model=PIONEER_VERIFY_MODEL)
    if verdict.get("accepted") is not True or verdict.get("conflicts"):
        raise FailedClosed("Independent verification rejected the extraction: " + json.dumps(verdict.get("conflicts", [])))
    return extracted, [trace1, trace2]


def run_audit(documents: dict[str, str], *, synthetic: bool, tenant: str) -> dict[str, Any]:
    if synthetic:
        extracted, model_trace = synthetic_extraction(), [{"provider": "fixture", "label": "synthetic only", "at": now()}]
    else:
        extracted, model_trace = live_extract(documents)
    audit = verify_audit(extracted, calculate_audit(extracted))
    return {
        "extraction": extracted,
        "audit": audit,
        "draft_notice": draft_notice(extracted, audit, tenant),
        "model_trace": model_trace,
    }


def choose_distribution_strategy(state: dict[str, Any]) -> dict[str, Any]:
    cycles = state.get("prior_cycles", [])
    if not cycles:
        target, channel, hypothesis = (
            "bookkeepers and fractional CFOs serving retail tenants",
            "direct outreach",
            "Advisors with current CAM statements can produce qualified referrals at low cash cost.",
        )
        human_job = "Ask US small-business finance operators to rank three Recoup messages for clarity and trust."
    elif sum(c.get("qualified_prospects", 0) for c in cycles) == 0:
        target, channel, hypothesis = (
            "multi-location retail operators",
            "organic professional publishing",
            "Portfolio operators have repeated exposure and may respond better to a concrete deadline tool.",
        )
        human_job = "Test the deadline-led eligibility page with general-population small-business decision makers."
    else:
        best = max(cycles, key=lambda c: c.get("paid_cases", 0) * 100 + c.get("qualified_prospects", 0))
        target, channel = best["target"], best["channel"]
        hypothesis = "Repeat the best observed channel while the measured signal remains positive."
        human_job = "Review the best campaign artifact and identify the single largest trust barrier."
    return {
        "hypothesis": hypothesis,
        "target": target,
        "channel": channel,
        "human_job": human_job,
        "acceptance_rubric": ["specific to CAM reconciliation", "no legal or savings guarantee", "clear before-and-after rationale"],
        "next_decision": "measure qualified prospects, case starts, paid cases, and CAC before the next cycle",
    }


def terac_budget_ok(available_cents: int, committed_cents: int, quote_cents: int) -> bool:
    return quote_cents >= 0 and committed_cents + quote_cents <= min(available_cents, 12_500)


def resend_email(to: str, subject: str, text: str, idempotency_key: str) -> str:
    key = os.getenv("RESEND_API_KEY")
    sender = os.getenv("RESEND_FROM_EMAIL")
    if not key or not sender:
        raise FailedClosed("Resend API key and sender email are required.")
    if not valid_email(to):
        raise FailedClosed("A valid landlord email is required.")
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps({"from": sender, "to": [to], "subject": subject, "text": text}).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
            "User-Agent": "Recoup/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read()).get("message", str(exc))
        except json.JSONDecodeError:
            detail = str(exc)
        raise FailedClosed(f"Resend email failed: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise FailedClosed(f"Resend email failed: {exc}") from exc
    if not result.get("id"):
        raise FailedClosed("Resend returned an incomplete email response.")
    return str(result["id"])


def linq_send_message(to: str, text: str, idempotency_key: str) -> dict[str, str]:
    key = os.getenv("LINQ_API_KEY")
    sender = os.getenv("LINQ_FROM_NUMBER")
    if not key:
        raise FailedClosed("LINQ_API_KEY is required.")
    if not valid_phone(to):
        raise FailedClosed("The landlord phone must use E.164 format, such as +14155550123.")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Recoup/1.0"}
    if not sender:
        request = urllib.request.Request("https://api.linqapp.com/api/partner/v3/phone_numbers", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                numbers = json.load(response).get("phone_numbers", [])
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise FailedClosed(f"Linq phone-number lookup failed: {exc}") from exc
        healthy = [item for item in numbers if item.get("reputation", {}).get("status", "HEALTHY") == "HEALTHY"]
        sender = (healthy or numbers or [{}])[0].get("phone_number")
    if not valid_phone(sender):
        raise FailedClosed("Linq has no available sender phone number.")
    payload = json.dumps({
        "from": sender,
        "to": [to],
        "message": {"parts": [{"type": "text", "value": text}], "idempotency_key": idempotency_key},
    }).encode()
    request = urllib.request.Request("https://api.linqapp.com/api/partner/v3/chats", data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response).get("chat", {})
    except urllib.error.HTTPError as exc:
        try:
            error = json.loads(exc.read())
            detail = error.get("error", {}).get("message") or error.get("message") or str(exc)
        except json.JSONDecodeError:
            detail = str(exc)
        raise FailedClosed(f"Linq message failed: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise FailedClosed(f"Linq message failed: {exc}") from exc
    message = result.get("message", {})
    if not result.get("id") or not message.get("id"):
        raise FailedClosed("Linq returned an incomplete chat response.")
    return {"chat_id": str(result["id"]), "message_id": str(message["id"]), "status": str(message.get("delivery_status", "pending")), "service": str(message.get("service", "auto"))}


def dodo_checkout(case_id: str, tenant: str, email: str) -> dict[str, Any]:
    key = os.getenv("DODO_PAYMENTS_API_KEY")
    product_id = os.getenv("DODO_PAYMENTS_PRODUCT_ID")
    environment = os.getenv("DODO_PAYMENTS_ENVIRONMENT", "test_mode")
    if not key or not product_id:
        raise FailedClosed("Dodo Payments API key and product ID are required.")
    host = "test.dodopayments.com" if environment == "test_mode" else "live.dodopayments.com"
    payload = json.dumps({
        "product_cart": [{"product_id": product_id, "quantity": 1}],
        "customer": {"email": email, "name": tenant},
        "metadata": {"case_id": case_id, "offer": "recoup_v1"},
        "return_url": os.getenv("DODO_PAYMENTS_RETURN_URL", "http://127.0.0.1:8000/?checkout=complete"),
        "allowed_payment_method_types": ["credit", "debit"],
    }).encode()
    request = urllib.request.Request(
        f"https://{host}/checkouts",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read()).get("message", str(exc))
        except json.JSONDecodeError:
            detail = str(exc)
        raise FailedClosed(f"Dodo checkout failed: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise FailedClosed(f"Dodo checkout failed: {exc}") from exc
    if not result.get("session_id") or not result.get("checkout_url"):
        raise FailedClosed("Dodo returned an incomplete checkout session.")
    return result


def verify_webhook_signature(body: bytes, headers: dict[str, str], secret: str, provider: str, *, current_time: float | None = None) -> str:
    message_id = headers.get("webhook-id", "")
    timestamp = headers.get("webhook-timestamp", "")
    signatures = headers.get("webhook-signature", "").split()
    if not message_id or "." in message_id or not timestamp.isdigit() or abs((current_time or time.time()) - int(timestamp)) > 300:
        raise FailedClosed(f"The {provider} webhook metadata is invalid.")
    encoded_secret = secret[6:] if secret.startswith("whsec_") else secret
    try:
        key = base64.b64decode(encoded_secret)
    except ValueError as exc:
        raise FailedClosed(f"The {provider} webhook key is invalid.") from exc
    signed = message_id.encode() + b"." + timestamp.encode() + b"." + body
    expected = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
    if not any(signature.startswith("v1,") and hmac.compare_digest(expected, signature[3:]) for signature in signatures):
        raise FailedClosed(f"The {provider} webhook signature is invalid.")
    return message_id


def verify_dodo_signature(body: bytes, headers: dict[str, str], secret: str, *, current_time: float | None = None) -> str:
    return verify_webhook_signature(body, headers, secret, "Dodo", current_time=current_time)


def verify_linq_signature(body: bytes, headers: dict[str, str], secret: str, *, current_time: float | None = None) -> str:
    return verify_webhook_signature(body, headers, secret, "Linq", current_time=current_time)
