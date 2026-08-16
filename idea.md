# Recoup

## One-line idea

Recoup audits a commercial tenant's annual common-area maintenance (CAM) reconciliation and handles the correction process with the landlord.

## Problem

Commercial tenants often pay estimated building operating costs each month in addition to base rent. After the year ends, the landlord issues a reconciliation that compares those estimated payments with the tenant's share of the actual costs.

The reconciliation can contain:

- Costs that the lease does not permit
- Incorrect allocation percentages
- Expenses above a contractual cap
- Gross-up adjustments that do not follow the lease
- Capital expenses that are not permitted or not amortized as the lease requires
- An administrative fee stacked on a management fee for the same service
- Duplicate or previously reimbursed expenses
- Arithmetic errors
- Charges without adequate supporting records

The tenant must read a long lease, check the calculations, request evidence, follow the lease's notice procedure, and continue the discussion with the landlord. Small businesses often lack a dedicated lease-audit team for this work.

Most small tenants do not dispute a reconciliation at all. The realistic alternative to Recoup is not a self-managed audit. It is no review. Recoup competes with inaction, and its job is to remove the work and the negotiation burden that cause the inaction.

## Customer

The initial customer is a small commercial tenant, such as a:

- Restaurant
- Retail shop
- Clinic
- Office
- Warehouse operator
- Nonprofit organization
- Multi-location operator or franchisee

The customer already knows what rent and CAM it pays. An owner, bookkeeper, accountant, or accounts-payable employee supplies the documents.

The same pipeline serves one location and a portfolio. A multi-location customer supplies many cases from one sale, which lowers the acquisition cost per case. Early sales data will show which segment converts better. The product does not select one segment now.

## Customer workflow

1. The customer visits the landing page and creates an account.
2. The customer opens a case in the dashboard.
3. The customer uploads:
   - The commercial lease and amendments
   - The latest projected CAM statement, if separate from the lease
   - The annual CAM reconciliation
   - A tenant ledger or CAM payment total when the reconciliation does not show estimated payments already made
4. The system reads the statement date and the lease's objection clause first. The dashboard immediately shows the dispute deadline.
5. The customer confirms the landlord or property manager's contact details.
6. The customer authorizes Recoup to request records and communicate about the reconciliation.
7. Recoup performs the audit and manages the correction process. The customer signs each formal notice electronically and approves each escalation step.
8. The customer forwards landlord replies that arrive by postal mail or telephone. The dashboard has an upload point for them.
9. The dashboard reports the final result and keeps the supporting calculations and communication history.

## Agent workflow

### 1. Read the lease and set the deadline

The agent extracts:

- Permitted and excluded operating-cost categories
- The tenant's allocation method
- Gross-up provisions and the stated occupancy level
- Expense caps, with the cap type: controllable or non-controllable costs, cumulative or non-cumulative, compounding or flat
- Capital-expense rules and amortization requirements
- Audit rights and their conditions: the objection window, who may perform an audit, auditor fee restrictions, and any pay-first requirement
- Whether the lease permits the tenant to withhold a disputed amount
- Dispute deadlines and any clause that makes the statement final after a date
- Required notice method and address
- Rules for credits, refunds, and additional payments

The agent computes the dispute deadline before any other analysis. The deadline controls the case schedule.

The agent also checks for a recently signed estoppel certificate. A signed estoppel can waive claims. The agent reports that risk before the dispute starts.

The current projected CAM amount can be in a separate landlord notice. It is not assumed to be in the lease.

### 2. Reconstruct the account

The agent determines:

- Estimated CAM billed during the year
- Estimated CAM paid during the year
- Actual CAM claimed by the landlord
- Additional amount billed or credit offered

If the annual reconciliation already states the estimated payments, separate monthly statements are not required.

Where the lease and the law permit, the agent also reviews prior years. A multi-year review increases the possible recovery from the same document set.

### 3. Check the reconciliation

The agent compares the reconciliation with the lease and checks:

- Whether each expense category is permitted
- Whether the tenant's share was calculated correctly
- Whether gross-up adjustments follow the lease (a gross-up to a stated occupancy level can be legitimate)
- Whether contractual caps were followed, with the correct cap type
- Whether capital expenses are permitted and amortized as the lease requires
- Whether an administrative fee duplicates a management fee
- Whether an expense appears more than once
- Whether an expense was paid directly by the tenant or reimbursed by another party
- Whether totals and adjustments are mathematically correct
- Whether the landlord supplied the records required by the lease or applicable law

A flagged item is not treated as a proven overcharge until the relevant lease terms and supporting records confirm it.

Accuracy controls: the language model extracts lease terms into a structured record and drafts text. Deterministic code performs every calculation. An independent second pass verifies each flagged item before the item can enter a letter. A wrong claim in a formal letter harms the customer and the product, so no unverified flag leaves the system.

### 4. Request missing evidence

Recoup uses two tracks.

**Track 1 — Objection.** Some errors are visible on the statement itself: arithmetic, the share percentage, cap breaches, and excluded categories. An objection letter about these errors does not invoke the audit clause, so no clause restricts who prepares it.

**Track 2 — Records demand.** A demand for invoices and ledgers invokes the lease's audit clause. Standard clauses restrict who may perform the audit and how the auditor is paid. Many clauses require an independent CPA and prohibit a contingency-fee auditor. When the clause requires it, a partner CPA firm formally conducts and signs the audit, and Recoup prepares the work.

When records are needed, the agent asks the landlord for:

- Invoices and receipts
- Expense ledgers
- Allocation worksheets
- Insurance reimbursements
- Contractor records
- Explanations of material year-over-year changes

When the reconciliation is a one-page summary and no records arrive, the agent can verify only the arithmetic, the share percentage, the caps, and the category names. The dashboard states this limit to the customer.

### 5. Request a correction

The agent prepares a source-backed explanation that identifies:

- The disputed line item
- The amount in dispute
- The relevant lease clause
- The supporting calculation or missing evidence
- The requested correction

Leases require notice from the tenant, so the agent drafts each formal notice and the customer signs it electronically with one click. The system sends the notice through the method the lease requires, with a certified-mail service when physical delivery is required. A phone number or text message alone is not assumed to satisfy a contractual notice requirement. Calls and messages can be used for follow-up.

Payment guidance comes first. Many leases require payment of the billed amount during a dispute and forbid offset. Nonpayment can put the tenant in default, and a default can void the audit right. The agent checks the lease before it recommends any payment action. The default guidance is: pay under protest, then dispute.

### 6. Manage the case

The agent tracks replies, answers factual questions, requests overdue records, recalculates the account when new evidence arrives, and follows the case until it reaches one of the defined outcomes.

When the landlord does not respond, the agent escalates in order: the property manager, then the building owner, then timing around the lease renewal. The customer approves each escalation step and controls the tone, because the customer must keep a working relationship with the landlord.

## Why a landlord responds

Recoup cannot threaten legal action, and a small tenant rarely does either. The product relies on four pressure sources:

1. **Collection need.** When the tenant has not paid the additional bill, the landlord must engage to collect. These cases have the strongest position and receive priority at intake.
2. **Specificity.** A precise, verifiable claim — "the statement uses a 4.8% share; Exhibit B states 4.2%" — is easy to verify and difficult to ignore. A vague audit announcement is easy to ignore.
3. **Escalation.** A property manager does not want the building owner to see a documented error that stayed unanswered.
4. **Renewal timing.** A landlord engages more when a renewal decision is near.

Refund claims for amounts already paid have the weakest position. Intake scores each case on these factors and sets the customer's expectations. The landlord response rate is the product's largest unknown, and the first live cases must measure it.

## Case outcomes

- **Corrected unpaid bill:** The tenant has not paid the disputed amount, and the landlord reduces or withdraws it.
- **Rent credit:** The tenant already overpaid estimated CAM, and the landlord applies a credit to future rent or CAM.
- **Refund:** The tenant overpaid and the lease or case resolution requires money to be returned.
- **Charge confirmed:** The records and lease show that the landlord's charge is correct. This outcome still has value as assurance that the bill is correct.
- **Dispute rejected:** The landlord rejects the requested correction.
- **Professional review required:** The case depends on a material legal or accounting interpretation and is transferred to an appropriate qualified professional.

## Example

- Estimated CAM paid during the year: $12,000
- Landlord's claimed actual CAM: $15,000
- Additional bill: $3,000
- Recoup's verified permitted CAM: $13,000
- Correct result: the additional bill is reduced from $3,000 to $1,000
- Customer value: $2,000 of an unsupported charge is removed before payment

This result assumes the lease permits the tenant to hold the disputed amount. When the lease requires payment first, the tenant pays under protest and the $2,000 returns as a credit or refund.

If verified permitted CAM were $10,000 instead, the tenant would have already overpaid by $2,000 and Recoup would seek the credit or refund required by the lease and case circumstances.

## Autonomy boundary

Recoup performs the operational work without the company founder handling individual cases. The customer provides documents, signs formal notices, approves escalation steps, and forwards replies that arrive outside the system.

The agent can autonomously:

- Read documents
- Perform calculations
- Request records
- Draft formal notices and correction requests
- Send factual follow-up communications
- Maintain the case file
- Report the outcome

The agent does not autonomously waive the customer's rights, accept a compromise, sign a new agreement, send a formal notice without the customer's electronic signature, threaten legal action, or provide legal advice. A qualified professional handles cases that require those actions.

The professional-escalation network, and the partner CPA firm for audit clauses that require one, are launch requirements. They are not later additions, because ordinary cases reach these boundaries.

## Product promise

Recoup does not sell a lease summary or a list of possible errors. It owns the operational process from document review through a resolved reconciliation.

The primary success metric is money corrected:

- Invalid unpaid charges removed
- Rent credits issued
- Refunds issued

Secondary metrics include time to resolution, landlord response rate, recovered amount per case, and the percentage of flagged items confirmed by supporting evidence.

## Pricing

Recoup will not use a recovery (contingency) fee, for two reasons:

- Standard audit clauses prohibit an auditor compensated on a contingency basis. A contingency fee gives the landlord a valid contractual reason to refuse records.
- A confirmed correct charge still has value as assurance, and a contingency fee earns nothing from that outcome.

The candidate models are:

- A flat per-case fee. Initial hypothesis: $200–$500.
- An annual monitoring subscription: the lease stays on file, and the agent acts on the day each statement arrives.

The per-case fee is the version-1 model. The subscription is the year-two model, because a lease already on file removes the timing risk. Case data will set the final price levels.

## Economics and distribution

The marginal cost of a case is a few dollars of compute. Low revenue per case is acceptable when fulfillment costs almost nothing. Customer-acquisition cost is the constraint, not service cost.

Reconciliations arrive in a season, mostly in the first half of the year. Distribution follows the season:

- Search content for reconciliation-season queries, where competition is low
- Cold email to tenants, timed to statement season
- Referrals from bookkeepers, accountants, and fractional CFOs, who see the statements first
- The computed dispute deadline as the conversion tool: "your objection window closes in 23 days"

## Validation plan

Before the negotiation loop is built:

1. Collect 10–20 real lease-and-reconciliation pairs.
2. Measure the findings rate, the presence and conditions of audit clauses, and the deadline status of each statement.
3. Run the first live cases and measure the landlord response rate.

Two numbers decide the business: the landlord response rate and the findings rate per case. Every other risk in this document is a design choice.

## Open questions

- What landlord response rate do specific, tenant-signed objections achieve?
- What share of real cases contains a recoverable discrepancy?
- How often do small tenants receive adequate reconciliation detail without a records demand?
- Which formal notice and representation steps require a human professional in each jurisdiction?
- Which segment converts better: single-location tenants or multi-location operators?
- Does the name "Recoup" conflict with existing products? A trademark check is needed.

## Scope decision

The first version is for commercial triple-net (NNN) retail leases only. Base-year and expense-stop office leases use different error patterns and come later. Residential billing uses different lease structures and laws and is outside the initial scope.

Sponsor services and technical architecture do not define the product. They will be selected later to support the required hosting, model access, testing, payments, sandboxing, and human-expert escalation.
