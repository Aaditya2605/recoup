---
id: 06
title: Implement the LLM audit contract
type: task
status: open
assignee:
blocked-by: []
---

## Confirmed architecture

1. A Pioneer-hosted LLM reads the lease, amendments, reconciliation, and ledger.
2. It extracts structured facts with exact source quotations and document locations.
3. Deterministic code calculates deadlines and money with explicit date and decimal rules.
4. An independent LLM verifies each candidate finding against the source and calculation.
5. Unsupported findings are removed.
6. An LLM drafts the customer communication from verified findings only.

## Required extraction fields from `idea.md`

- Permitted and excluded expense categories
- Allocation method
- Gross-up provisions and occupancy
- Expense caps and cap type
- Capital-expense and amortization rules
- Audit rights, objection window, auditor restrictions, and pay-first requirements
- Withholding restrictions
- Deadlines and finality clauses
- Notice method and address
- Credit, refund, and additional-payment rules
- Estimated CAM billed and paid, actual CAM claimed, and additional bill or credit

Implementation must still verify the live Pioneer model identifiers, define the structured schema, and set explicit failed-closed behavior for missing or conflicting evidence.

## Safety rule

No deadline, charge, clause, or notice instruction is shown as verified without a source quote, document location, and successful independent check.
