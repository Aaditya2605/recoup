# Recoup

Recoup is an agent-operated CAM reconciliation service for United States triple-net retail tenants. It checks eligibility, extracts lease rules with exact evidence, performs deterministic date and money calculations, independently verifies findings, prepares a customer-signed notice, and keeps an auditable case ledger.

## Run

```bash
python -m pip install -r requirements.txt
cp .env.example .env
set -a; source .env; set +a
python app.py
```

Open `http://127.0.0.1:8000`. Select **Test Kimi on synthetic case**, open the case, and select **Run verified audit**. The documents and answer key are synthetic, but extraction and verification are live Kimi K3 calls. Date and money calculations remain deterministic by design.

```bash
python -m unittest -v
```

The synthetic case is always labeled. It is not evidence of a real customer, payment, model call, Terac submission, notice, landlord reply, or outcome.

## Live boundaries

- `PIONEER_API_KEY` enables two separate Kimi K3 calls: one extracts and one independently checks the extraction. Missing, conflicting, or unsupported evidence moves the case to `failed_closed`.
- Dodo Payments checkout starts after a successful free eligibility check. The app places the case ID in checkout metadata. A live audit stays blocked until a signed `payment.succeeded` event reaches `/api/dodo/webhook` and proves the `$499 USD` product payment.
- `TERAC_API_KEY` identifies the existing founder-controlled Terac account. The local manager selects a job and enforces the $125 credit-only limit. Launch stays external until authenticated Terac tools are available.
- `/study` collects the five Terac-linked message-comparison responses. The distribution manager fails closed until all five exist, then selects the next message from their recorded preference and trust scores.
- Formal notices enter an idempotent `pending_external` outbox after customer authorization and signature. The case stays in `external_action_pending`. A certified-mail provider and delivery webhook are required before the system can record `notice_sent` as externally confirmed.
- `RESEND_API_KEY` and `RESEND_FROM_EMAIL` send the signed courtesy copy to the landlord email entered at intake. Resend acceptance does not replace certified-mail delivery when the lease requires it.
- `LINQ_API_KEY` sends an idempotent iMessage, RCS, or SMS follow-up to the optional landlord phone only after confirmed notice delivery. `/api/linq/webhook` verifies `LINQ_WEBHOOK_SECRET` and stores inbound landlord replies in the case ledger. Set `LINQ_FROM_NUMBER` to force one assigned line; otherwise the app selects a healthy assigned line.
- Jurisdiction-specific professional and representation rules are not configured. Live cases that need legal or accounting judgment must stop for a qualified professional.

## Stored proof

SQLite stores every case transition with actor, trigger, input evidence, tool call, output, acceptance decision, next state, and timestamp. External actions also have stable idempotency keys. The system does not convert a pending action into proof of payment, delivery, human work, or case resolution.

## Security and privacy

Uploaded documents stay on the local or mounted server disk. Pioneer requests use `store: false`. Do not use production documents on an unencrypted development machine. Add authenticated tenant access, encrypted object storage, retention deletion, webhook signature checks, rate limits, and jurisdiction policy before commercial launch.
