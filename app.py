#!/usr/bin/env python3
"""Recoup web application and workflow ledger."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import mimetypes
import os
import sqlite3
import subprocess
import shutil
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from recoup import (
    FailedClosed,
    TERMINAL_STATES,
    choose_distribution_strategy,
    dodo_checkout,
    eligibility,
    now,
    resend_email,
    run_audit,
    synthetic_documents,
    terac_budget_ok,
    verify_dodo_signature,
    valid_email,
)


ROOT = Path(__file__).parent.resolve()
DB = Path(os.getenv("RECOUP_DB", ROOT / "recoup.db"))
UPLOADS = Path(os.getenv("RECOUP_UPLOADS", ROOT / "uploads"))
MAX_BODY = 20 * 1024 * 1024
ALLOWED_TRANSITIONS = {
    "intake_incomplete": {"deadline_at_risk", "audit_in_progress", "failed_closed"},
    "deadline_at_risk": {"audit_in_progress", "professional_review", "failed_closed"},
    "audit_in_progress": {"waiting_for_records", "findings_verified", "professional_review", "failed_closed"},
    "waiting_for_records": {"audit_in_progress", "failed_closed"},
    "findings_verified": {"waiting_for_customer_consent", "confirmed_charge", "professional_review", "failed_closed"},
    "waiting_for_customer_consent": {"external_action_pending", "professional_review", "failed_closed"},
    "external_action_pending": {"notice_sent", "failed_closed"},
    "notice_sent": {"waiting_for_landlord_reply", "failed_closed"},
    "waiting_for_landlord_reply": {"escalation_approved", *TERMINAL_STATES},
    "escalation_approved": {"waiting_for_landlord_reply", *TERMINAL_STATES},
}


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db() -> None:
    UPLOADS.mkdir(exist_ok=True)
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS cases (
              id TEXT PRIMARY KEY, tenant TEXT NOT NULL, email TEXT NOT NULL,
              state TEXT NOT NULL, synthetic INTEGER NOT NULL DEFAULT 0,
              paid INTEGER NOT NULL DEFAULT 0, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
              id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT, actor TEXT NOT NULL,
              trigger TEXT NOT NULL, input_evidence TEXT NOT NULL, tool_call TEXT,
              output TEXT NOT NULL, acceptance_decision TEXT NOT NULL, next_state TEXT,
              created_at TEXT NOT NULL, FOREIGN KEY(case_id) REFERENCES cases(id)
            );
            CREATE TABLE IF NOT EXISTS actions (
              id TEXT PRIMARY KEY, case_id TEXT, kind TEXT NOT NULL, idempotency_key TEXT UNIQUE NOT NULL,
              status TEXT NOT NULL, payload TEXT NOT NULL, external_evidence TEXT, created_at TEXT NOT NULL,
              FOREIGN KEY(case_id) REFERENCES cases(id)
            );
            CREATE TABLE IF NOT EXISTS distribution_cycles (
              id TEXT PRIMARY KEY, status TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL
            );
            """
        )


def record_event(db: sqlite3.Connection, *, case_id: str | None, actor: str, trigger: str, input_evidence: object, tool_call: object | None, output: object, decision: str, next_state: str | None) -> None:
    db.execute(
        "INSERT INTO events(case_id,actor,trigger,input_evidence,tool_call,output,acceptance_decision,next_state,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (case_id, actor, trigger, json.dumps(input_evidence), json.dumps(tool_call) if tool_call else None, json.dumps(output), decision, next_state, now()),
    )


def get_case(db: sqlite3.Connection, case_id: str) -> dict:
    row = db.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
    if not row:
        raise KeyError(case_id)
    item = dict(row)
    item["data"] = json.loads(item["data"])
    item["synthetic"] = bool(item["synthetic"])
    item["paid"] = bool(item["paid"])
    item["events"] = [dict(e) for e in db.execute("SELECT * FROM events WHERE case_id=? ORDER BY id", (case_id,))]
    for event in item["events"]:
        for key in ("input_evidence", "tool_call", "output"):
            event[key] = json.loads(event[key]) if event[key] else None
    item["actions"] = [dict(a) for a in db.execute("SELECT * FROM actions WHERE case_id=? ORDER BY created_at", (case_id,))]
    return item


def save_case(db: sqlite3.Connection, case: dict) -> None:
    case["updated_at"] = now()
    db.execute("UPDATE cases SET state=?,paid=?,data=?,updated_at=? WHERE id=?", (case["state"], int(case["paid"]), json.dumps(case["data"]), case["updated_at"], case["id"]))


def transition(db: sqlite3.Connection, case: dict, next_state: str, *, actor: str, trigger: str, evidence: object, output: object, tool: object | None = None, decision: str = "accepted") -> None:
    if next_state not in ALLOWED_TRANSITIONS.get(case["state"], set()):
        raise FailedClosed(f"Transition from {case['state']} to {next_state} is not allowed.")
    record_event(db, case_id=case["id"], actor=actor, trigger=trigger, input_evidence=evidence, tool_call=tool, output=output, decision=decision, next_state=next_state)
    case["state"] = next_state
    save_case(db, case)


def decode_document(case_id: str, item: dict) -> tuple[str, str]:
    name = Path(item.get("name", "document.txt")).name
    kind = item.get("kind", "other")
    raw = base64.b64decode(item.get("base64", ""), validate=True)
    if len(raw) > MAX_BODY:
        raise FailedClosed("A document is too large.")
    destination = UPLOADS / f"{case_id}-{uuid.uuid4().hex}-{name}"
    destination.write_bytes(raw)
    suffix = destination.suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        text = raw.decode("utf-8", errors="strict")
    elif suffix == ".pdf":
        if shutil.which("pdftotext"):
            result = subprocess.run(["pdftotext", "-layout", str(destination), "-"], capture_output=True, text=True, timeout=30)
            text = result.stdout if result.returncode == 0 else ""
        else:
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages)
        if not text.strip():
            raise FailedClosed("The PDF has no readable text. Upload a text-searchable PDF.")
    else:
        raise FailedClosed("Use PDF, TXT, MD, or CSV documents.")
    return kind, text


def action(db: sqlite3.Connection, case: dict, kind: str, payload: dict) -> dict:
    key = hashlib.sha256(f"{case['id']}:{kind}:{json.dumps(payload, sort_keys=True)}".encode()).hexdigest()
    existing = db.execute("SELECT * FROM actions WHERE idempotency_key=?", (key,)).fetchone()
    if existing:
        return dict(existing)
    item = {"id": uuid.uuid4().hex, "status": "pending_external", "idempotency_key": key}
    db.execute("INSERT INTO actions(id,case_id,kind,idempotency_key,status,payload,created_at) VALUES(?,?,?,?,?,?,?)", (item["id"], case["id"], kind, key, item["status"], json.dumps(payload), now()))
    return item


class Handler(BaseHTTPRequestHandler):
    server_version = "Recoup/1"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def json(self, status: int, value: object) -> None:
        body = json.dumps(value, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY:
            raise FailedClosed("Invalid request size.")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise FailedClosed("Expected a JSON object.")
        return value

    def read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY:
            raise FailedClosed("Invalid request size.")
        return self.rfile.read(length)

    def static(self, name: str) -> None:
        path = ROOT / "web" / name
        if not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/":
                return self.static("index.html")
            if path in {"/app.js", "/styles.css", "/redesign.css"}:
                return self.static(path[1:])
            if path == "/api/state":
                with connect() as db:
                    cases = [dict(row) for row in db.execute("SELECT id,tenant,email,state,synthetic,paid,created_at,updated_at FROM cases ORDER BY created_at DESC")]
                    cycles = [{**dict(row), "data": json.loads(row["data"])} for row in db.execute("SELECT * FROM distribution_cycles ORDER BY created_at DESC")]
                return self.json(200, {"cases": cases, "distribution_cycles": cycles, "payment_configured": bool(os.getenv("DODO_PAYMENTS_API_KEY") and os.getenv("DODO_PAYMENTS_PRODUCT_ID")), "email_configured": bool(os.getenv("RESEND_API_KEY") and os.getenv("RESEND_FROM_EMAIL")), "pioneer_configured": bool(os.getenv("PIONEER_API_KEY")), "terac_configured": bool(os.getenv("TERAC_API_KEY"))})
            match = re_full(r"/api/cases/([a-f0-9]+)", path)
            if match:
                with connect() as db:
                    return self.json(200, get_case(db, match[1]))
            self.send_error(404)
        except KeyError:
            self.json(404, {"error": "Case not found."})
        except Exception as exc:
            self.json(500, {"error": str(exc)})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/dodo/webhook":
                return self.dodo_webhook()
            payload = self.read_json()
            if path == "/api/cases":
                return self.create_case(payload)
            if path == "/api/demo":
                return self.create_demo()
            if path == "/api/distribution/cycles":
                return self.create_cycle(payload)
            match = re_full(r"/api/cases/([a-f0-9]+)/(audit|authorize|sign|deliver|reply|outcome|pay)", path)
            if match:
                return self.case_action(match[1], match[2], payload)
            self.send_error(404)
        except (FailedClosed, ValueError, json.JSONDecodeError, base64.binascii.Error) as exc:
            self.json(422, {"error": str(exc), "failed_closed": True})
        except KeyError:
            self.json(404, {"error": "Case not found."})
        except Exception as exc:
            self.json(500, {"error": str(exc)})

    def create_case(self, payload: dict) -> None:
        case_id = uuid.uuid4().hex
        documents = dict(decode_document(case_id, item) for item in payload.get("documents", []))
        check = eligibility({**payload, "document_kinds": list(documents)})
        case = {
            "id": case_id,
            "tenant": str(payload.get("tenant", "")).strip(),
            "email": str(payload.get("email", "")).strip(),
            "state": "intake_incomplete",
            "synthetic": False,
            "paid": False,
            "data": {"eligibility": check, "documents": documents, "landlord_email": str(payload.get("landlord_email", "")).strip()},
            "created_at": now(),
            "updated_at": now(),
        }
        if not case["tenant"] or not valid_email(case["email"]):
            raise FailedClosed("Tenant name and a valid contact email are required.")
        if not valid_email(case["data"]["landlord_email"]):
            raise FailedClosed("A valid landlord or manager email is required.")
        with connect() as db:
            db.execute("INSERT INTO cases VALUES(?,?,?,?,?,?,?,?,?)", (case["id"], case["tenant"], case["email"], case["state"], 0, 0, json.dumps(case["data"]), case["created_at"], case["updated_at"]))
            record_event(db, case_id=case_id, actor="customer", trigger="intake submitted", input_evidence={"document_kinds": list(documents)}, tool_call=None, output=check, decision="eligible" if check["eligible"] else "rejected", next_state=case["state"])
        self.json(201, {"id": case_id, "eligibility": check})

    def create_demo(self) -> None:
        case_id = uuid.uuid4().hex
        created = now()
        data = {"eligibility": eligibility({"country": "US", "lease_type": "NNN retail", "document_kinds": ["lease", "reconciliation", "ledger"]}), "documents": synthetic_documents(), "contact": "Synthetic Property Manager", "model_mode": "live"}
        with connect() as db:
            db.execute("INSERT INTO cases VALUES(?,?,?,?,?,?,?,?,?)", (case_id, "Synthetic Market Street Tenant", "demo@example.invalid", "intake_incomplete", 1, 0, json.dumps(data), created, created))
            record_event(db, case_id=case_id, actor="system", trigger="synthetic evaluation loaded", input_evidence={"label": "synthetic"}, tool_call=None, output={"documents": list(data["documents"])}, decision="accepted for local evaluation only", next_state="intake_incomplete")
        self.json(201, {"id": case_id})

    def case_action(self, case_id: str, verb: str, payload: dict) -> None:
        with connect() as db:
            case = get_case(db, case_id)
            if verb == "audit":
                if not case["data"]["eligibility"]["eligible"]:
                    raise FailedClosed("The case is not eligible for version 1.")
                if not case["synthetic"] and not case["paid"]:
                    raise FailedClosed("Dodo payment confirmation is required before a live managed audit.")
                if case["state"] in TERMINAL_STATES:
                    raise FailedClosed("The case is already terminal.")
                if case["state"] != "audit_in_progress":
                    transition(db, case, "audit_in_progress", actor="fulfillment_agent", trigger="eligible case queued", evidence=case["data"]["eligibility"], output={"started": True})
                try:
                    result = run_audit(case["data"]["documents"], synthetic=case["synthetic"] and case["data"].get("model_mode") != "live", tenant=case["tenant"])
                except FailedClosed as exc:
                    transition(db, case, "failed_closed", actor="fulfillment_agent", trigger="audit failed", evidence={"documents": list(case["data"]["documents"])}, output={"error": str(exc)}, decision="rejected")
                    raise
                case["data"]["result"] = result
                save_case(db, case)
                transition(db, case, "findings_verified", actor="verification_agent", trigger="independent check complete", evidence=result["extraction"], tool=result["model_trace"], output=result["audit"], decision="verified")
                transition(db, case, "waiting_for_customer_consent", actor="fulfillment_agent", trigger="verified notice drafted", evidence=result["audit"]["findings"], output={"draft_notice": result["draft_notice"]}, decision="signature required")
            elif verb == "authorize":
                if case["state"] != "waiting_for_customer_consent":
                    raise FailedClosed("The case is not waiting for customer consent.")
                case["data"]["authorization"] = {"name": payload.get("name"), "records_requests": bool(payload.get("records_requests")), "communications": bool(payload.get("communications")), "at": now()}
                if not all((case["data"]["authorization"]["name"], case["data"]["authorization"]["records_requests"], case["data"]["authorization"]["communications"])):
                    raise FailedClosed("Named authorization for records requests and communication is required.")
                save_case(db, case)
                record_event(db, case_id=case_id, actor="customer", trigger="authorization submitted", input_evidence=case["data"]["authorization"], tool_call=None, output={"authorized": True}, decision="accepted", next_state=case["state"])
            elif verb == "sign":
                auth = case["data"].get("authorization")
                if case["state"] != "waiting_for_customer_consent" or not auth:
                    raise FailedClosed("Authorization is required before signature.")
                signature = {"name": payload.get("name"), "attested": payload.get("attested") is True, "at": now()}
                if not signature["name"] or not signature["attested"]:
                    raise FailedClosed("A typed signature and attestation are required.")
                case["data"]["signature"] = signature
                queued = action(db, case, "certified_mail", {"notice": case["data"]["result"]["draft_notice"], "signature": signature})
                landlord_email = case["data"].get("landlord_email")
                email_action = None
                if landlord_email:
                    email_action = action(db, case, "resend_email", {"to": landlord_email, "subject": f"CAM reconciliation notice from {case['tenant']}", "delivery_role": "courtesy_copy"})
                    email_id = resend_email(
                        landlord_email,
                        f"CAM reconciliation notice from {case['tenant']}",
                        f"{case['data']['result']['draft_notice']}\n\nSigned by: {signature['name']}\nSigned at: {signature['at']}",
                        f"recoup-notice-{case_id}",
                    )
                    db.execute("UPDATE actions SET status='accepted_external',external_evidence=? WHERE id=?", (json.dumps({"provider": "Resend", "email_id": email_id}), email_action["id"]))
                    record_event(db, case_id=case_id, actor="fulfillment_agent", trigger="courtesy email accepted by Resend", input_evidence={"recipient": landlord_email}, tool_call={"action_id": email_action["id"], "provider": "Resend"}, output={"email_id": email_id}, decision="accepted; certified delivery still required", next_state=case["state"])
                save_case(db, case)
                transition(db, case, "external_action_pending", actor="fulfillment_agent", trigger="customer signed notice", evidence=signature, tool={"certified_mail_action_id": queued["id"], "email_action_id": email_action["id"] if email_action else None}, output={"email_status": "accepted_external" if email_action else "not_requested", "certified_mail_status": "pending_external"}, decision="courtesy email accepted; certified mail queued, not sent" if email_action else "certified mail queued, not sent")
            elif verb == "deliver":
                if case["state"] != "external_action_pending":
                    raise FailedClosed("No notice is waiting for external delivery evidence.")
                evidence_text = str(payload.get("evidence", "")).strip()
                action_id = str(payload.get("action_id", "")).strip()
                pending = db.execute("SELECT * FROM actions WHERE id=? AND case_id=? AND status='pending_external'", (action_id, case_id)).fetchone()
                if not pending or not evidence_text:
                    raise FailedClosed("A pending action ID and delivery evidence are required.")
                db.execute("UPDATE actions SET status='confirmed_external',external_evidence=? WHERE id=?", (evidence_text, action_id))
                transition(db, case, "notice_sent", actor="delivery_webhook", trigger="notice delivery confirmed", evidence={"external_evidence": evidence_text}, tool={"action_id": action_id}, output={"external_status": "confirmed_external"})
            elif verb == "reply":
                if case["state"] not in {"notice_sent", "waiting_for_landlord_reply", "escalation_approved"}:
                    raise FailedClosed("A landlord reply is not expected in this state.")
                if case["state"] == "notice_sent":
                    transition(db, case, "waiting_for_landlord_reply", actor="fulfillment_agent", trigger="notice delivery pending", evidence={"action": "certified_mail"}, output={"waiting": True})
                reply = {"source": payload.get("source"), "text": str(payload.get("text", "")).strip(), "at": now()}
                if not reply["text"]:
                    raise FailedClosed("Reply text is required.")
                case["data"].setdefault("replies", []).append(reply)
                save_case(db, case)
                record_event(db, case_id=case_id, actor="customer", trigger="landlord reply forwarded", input_evidence=reply, tool_call=None, output={"stored": True}, decision="requires review", next_state=case["state"])
            elif verb == "outcome":
                outcome = payload.get("outcome")
                if outcome not in TERMINAL_STATES - {"failed_closed"}:
                    raise FailedClosed("Invalid case outcome.")
                evidence_text = str(payload.get("evidence", "")).strip()
                if not evidence_text:
                    raise FailedClosed("External outcome evidence is required.")
                if case["state"] == "notice_sent":
                    transition(db, case, "waiting_for_landlord_reply", actor="fulfillment_agent", trigger="notice action recorded", evidence={"source": "operator"}, output={"waiting": True})
                transition(db, case, outcome, actor="fulfillment_agent", trigger="external outcome received", evidence={"evidence": evidence_text}, output={"outcome": outcome})
            elif verb == "pay":
                if not case["data"]["eligibility"]["eligible"]:
                    raise FailedClosed("Only eligible cases can pay.")
                checkout = dodo_checkout(case_id, case["tenant"], case["email"])
                queued = action(db, case, "dodo_checkout", {"url": checkout["checkout_url"], "session_id": checkout["session_id"], "amount_cents": 49900})
                record_event(db, case_id=case_id, actor="payment_agent", trigger="eligible customer requested checkout", input_evidence=case["data"]["eligibility"], tool_call={"action_id": queued["id"], "provider": "Dodo Payments"}, output={"payment_link": checkout["checkout_url"], "session_id": checkout["session_id"], "status": "pending_external"}, decision="checkout created, payment not confirmed", next_state=case["state"])
            self.json(200, get_case(db, case_id))

    def dodo_webhook(self) -> None:
        secret = os.getenv("DODO_PAYMENTS_WEBHOOK_KEY")
        if not secret:
            raise FailedClosed("DODO_PAYMENTS_WEBHOOK_KEY is not configured.")
        body = self.read_body()
        webhook_id = verify_dodo_signature(body, {key.lower(): value for key, value in self.headers.items()}, secret)
        event = json.loads(body)
        if not isinstance(event, dict):
            raise FailedClosed("The Dodo event must be a JSON object.")
        if event.get("type") != "payment.succeeded":
            return self.json(200, {"received": True, "ignored": True})
        payment = event.get("data", {}).get("object", event.get("data", {}))
        case_id = payment.get("metadata", {}).get("case_id")
        product_id = os.getenv("DODO_PAYMENTS_PRODUCT_ID")
        products = {item.get("product_id") for item in payment.get("product_cart", [])}
        if int(payment.get("total_amount", 0)) != 49900 or str(payment.get("currency", "")).upper() != "USD" or (products and product_id not in products):
            raise FailedClosed("The Dodo event does not prove the expected $499 USD product payment.")
        with connect() as db:
            case = get_case(db, case_id)
            if case["paid"]:
                return self.json(200, {"received": True, "duplicate": True})
            case["paid"] = True
            case["data"]["payment"] = {"provider": "Dodo Payments", "payment_id": payment.get("payment_id"), "amount_cents": 49900, "confirmed_at": now()}
            db.execute("UPDATE actions SET status='confirmed_external',external_evidence=? WHERE case_id=? AND kind='dodo_checkout' AND status='pending_external'", (payment.get("payment_id"), case_id))
            save_case(db, case)
            record_event(db, case_id=case_id, actor="dodo_webhook", trigger="payment succeeded", input_evidence=case["data"]["payment"], tool_call={"webhook_id": webhook_id}, output={"paid": True}, decision="signature, product, currency, and amount verified", next_state=case["state"])
        self.json(200, {"received": True})

    def create_cycle(self, payload: dict) -> None:
        with connect() as db:
            prior = [json.loads(row["data"]) for row in db.execute("SELECT data FROM distribution_cycles ORDER BY created_at")]
            strategy = choose_distribution_strategy({"prior_cycles": prior})
            available = int(payload.get("available_terac_cents", 12500))
            committed = sum(int(c.get("terac_cost_cents", 0)) for c in prior)
            quote = int(payload.get("terac_quote_cents", 0))
            strategy.update({"qualified_prospects": int(payload.get("qualified_prospects", 0)), "case_starts": int(payload.get("case_starts", 0)), "paid_cases": int(payload.get("paid_cases", 0)), "terac_cost_cents": 0, "terac_status": "not_launched"})
            if quote:
                if not terac_budget_ok(available, committed, quote):
                    raise FailedClosed("The Terac quote exceeds the available credit-only budget.")
                strategy.update({"terac_cost_cents": quote, "terac_status": "feasibility_quote_recorded; launch requires authenticated Terac action"})
            cycle_id = uuid.uuid4().hex
            db.execute("INSERT INTO distribution_cycles VALUES(?,?,?,?)", (cycle_id, "planned", json.dumps(strategy), now()))
            record_event(db, case_id=None, actor="distribution_manager", trigger="distribution cycle requested", input_evidence={"prior_cycles": len(prior), "budget_cents": available}, tool_call=None, output=strategy, decision="planned within policy", next_state="planned")
        self.json(201, {"id": cycle_id, **strategy})


def re_full(pattern: str, value: str):
    import re
    return re.fullmatch(pattern, value)


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", "8000"))
    print(f"Recoup running at http://127.0.0.1:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
