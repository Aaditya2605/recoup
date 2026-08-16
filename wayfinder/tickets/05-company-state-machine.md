---
id: 05
title: Define the company state machine
type: task
status: open
assignee:
blocked-by: [02, 03, 04]
---

## Goal

Join distribution, purchase, product work, and fulfillment into one auditable system.

## Required states

Use the workflow in `idea.md`. At minimum, the model must distinguish:

- Intake incomplete
- Deadline at risk
- Audit in progress
- Waiting for records
- Findings verified
- Waiting for customer consent
- Notice sent
- Waiting for landlord reply
- Escalation approved
- Corrected bill, credit, refund, confirmed charge, or rejected dispute
- Escalated to a qualified professional
- Failed closed

## Required behavior

Each transition records its actor, trigger, input evidence, tool call, output, acceptance decision, next state, and timestamp. No UI-only state is accepted as evidence of an external action.
