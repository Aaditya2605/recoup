# Wayfinder Map: Recoup as an Agent-Run Company

## Destination

Build and demonstrate one operating business loop with three connected parts:

1. **Product:** a commercial tenant submits a CAM reconciliation case and receives a verified case result.
2. **Distribution:** company agents acquire a real prospective customer without the founder performing the routine work.
3. **Fulfillment:** company agents operate the purchased case through a defined external outcome, with customer consent and qualified-professional escalation where required.

The founder can build the system and set policy. The founder is not the routine salesperson, case operator, reviewer, or messenger.

## Current truth

- The product thesis in `idea.md` remains the source of truth.
- The three-part business test in `HACKATHON_UNDERSTANDING.md` remains the acceptance standard.
- The previous Wayfinder mixed the product demo with hackathon sponsor compliance. It is preserved in `../wayfinder-superseded-20260815/` and is not an active plan.
- Recoup is a managed CAM reconciliation case, not only a document summary.
- LLMs interpret documents, verify evidence, and draft communications. Deterministic code performs date and money calculations.
- Terac must perform real human work that measurably improves the company. The manager agent decides what marketing expertise or production work to commission after it inspects the business state.
- Terac is not required in fulfillment. Qualified CPA or legal work must use a properly qualified professional, whether or not Terac can source that person.
- The offer is approved: free eligibility check, then $499 per eligible managed case, with the documented full-refund rule.
- The distribution authority is approved: United States only, connected accounts only, no paid-media cash, and up to the full $125 Terac credit balance with zero personal cash charge.
- Pioneer model identifiers and jurisdiction-specific professional rules still require live verification.
- Perflo is deferred until after version 1. The hackathon build will not require the founder to fund an agent wallet and will not claim the Perflo track.
- Composio is not part of the architecture. Do not add it only because it is available in the local environment. Use the direct service connection selected for each required business action.
- `idea.md` already defines the customer, version-1 scope, customer workflow, audit checks, evidence limits, notice process, case outcomes, autonomy boundary, pricing model, distribution channels, and success metrics. Tickets must treat these as requirements, not new questions.

## Anti-drift rules

- Product implementation can begin from `idea.md`. Distribution implementation needs a manager policy, not a fixed audience or campaign.
- No tool is included only for a sponsor track. Every included tool must cause a required business state change.
- Every agent or human job needs an input, output, acceptance check, retry path, and next state.
- Human work is allowed. The company agent must request it, brief it, assess it, and continue the workflow.
- Customer approval is allowed for the customer's money, signature, legal rights, and settlement decisions.
- The system stops when evidence is missing or ambiguous. It does not invent a finding.
- No fake customer, payment, landlord reply, human submission, or external action is presented as real.
- A dashboard is not proof. The demonstration must include an external business consequence.

## Active plan

| ID | Ticket | Purpose | Blocked by |
|---|---|---|---|
| 01 | [Confirm the three-part company loop](tickets/01-three-part-company-loop.md) | Record the settled loop and approve the manager's authority envelope | - |
| 02 | [Finish the offer and payment contract](tickets/02-offer-and-payment.md) | Select the exact price and payment point | - |
| 03 | [Define the distribution manager policy](tickets/03-distribution-agent-terac.md) | Define autonomy, budgets, controls, and evidence without fixing an audience or channel | - |
| 04 | [Implement the fulfillment contract](tickets/04-fulfillment-contract.md) | Use the case workflow already defined in `idea.md` | - |
| 05 | [Define the company state machine](tickets/05-company-state-machine.md) | Connect acquisition, purchase, case work, and outcome | 02, 03, 04 |
| 06 | [Implement the LLM audit contract](tickets/06-llm-audit-contract.md) | Implement the extraction, calculation, verification, and drafting requirements from `idea.md` | - |
| 07 | [Define evidence, consent, and escalation rules](tickets/07-evidence-consent-escalation.md) | Make the service fail closed at legal and accounting boundaries | 04, 06 |
| 08 | [Build the synthetic case and evaluation gate](tickets/08-synthetic-case-eval.md) | Test the product core against an exact answer key | 06, 07 |
| 09 | [Build the customer product](tickets/09-customer-product.md) | Implement intake, evidence, approval, and case status | 02, 05, 08 |
| 10 | [Build the distribution manager](tickets/10-distribution-worker.md) | Let the agent research, commission work, select channels, execute, and adapt | 03, 05 |
| 11 | [Build the fulfillment orchestrator](tickets/11-fulfillment-orchestrator.md) | Implement the approved case operation loop | 04, 05, 07, 08 |
| 12 | [Prove measurable Terac improvement](tickets/12-terac-measurement.md) | Measure how accepted Terac work improves the manager's selected business metric | 10 |
| 13 | [Connect external actions](tickets/13-external-actions.md) | Connect approved payment, communication, and delivery tools | 05, 09, 10, 11 |
| 14 | [Run the zero-founder business proof](tickets/14-end-to-end-proof.md) | Run one trace across all three business parts | 12, 13 |
| 15 | [Prepare the submission](tickets/15-submission.md) | Report only verified integrations, actions, and outcomes | 14 |

## Required proof trace

The final trace must answer these questions with stored evidence:

1. What caused the distribution agent to act?
2. Why did the agent select a target, channel, or human job?
3. What work did the agent assign through Terac, and how did it assess the return?
4. What made a prospect become a qualified buyer?
5. What exactly did the customer purchase?
6. How did the product turn the customer's documents into verified findings?
7. What human or professional work did fulfillment require, if any?
8. How did the agent assess and use that work?
9. Which actions required customer consent?
10. What external result ended the case?

If any answer is only a mock screen or an unsupported claim, the business loop is incomplete.
