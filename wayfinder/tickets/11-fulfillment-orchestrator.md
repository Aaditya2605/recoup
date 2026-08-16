---
id: 11
title: Build the fulfillment orchestrator
type: task
status: open
assignee:
blocked-by: [04, 05, 07, 08]
---

## Goal

Implement the purchased-case workflow approved in ticket 04.

## Required behavior

- Run LLM extraction through Pioneer.
- Run deterministic deadline and money calculations.
- Run independent evidence verification.
- Request missing records when policy requires them.
- Request customer consent where required.
- Perform only approved external actions.
- Continue until a defined terminal outcome or professional escalation.

Every step must be restartable and idempotent. A retry must not duplicate a payment, message, notice, or professional request.
