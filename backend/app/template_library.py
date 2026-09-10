"""Built-in engagement templates transcribed from the supplied DOCX sources.

The visible wording and table-cell order are intentionally source-faithful.
The renderer consumes the [[H1]], [[H2]] and [[TABLE]] markers without showing
them in the generated PDF.
"""

from __future__ import annotations


def f(key, label, group, field_type="text", required=True, source=None, default=None, options=None):
    item = {"key": key, "label": label, "type": field_type, "required": required, "group": group}
    if source:
        item["source"] = source
    if default not in (None, ""):
        item["default"] = default
    if options:
        item["options"] = options
    return item


SIGNATURE_FIELDS = [
    f("SERVICE_PROVIDER_SIGNATORY_NAME", "Service Provider Authorized Signatory", "Signatures", source="company.representative"),
    f("SERVICE_PROVIDER_SIGNATORY_TITLE", "Service Provider Signatory Title", "Signatures"),
    f("SERVICE_PROVIDER_SIGNATURE_DATE", "Service Provider Signature Date", "Signatures", "date"),
    f("SERVICE_PROVIDER_SIGNATURE_IMAGE", "Service Provider Digital Signature", "Signatures", "signature", required=False),
    f("CLIENT_SIGNATORY_NAME", "Client Authorized Signatory", "Signatures", source="party.contact_person"),
    f("CLIENT_SIGNATORY_TITLE", "Client Signatory Title", "Signatures"),
    f("CLIENT_SIGNATURE_DATE", "Client Signature Date", "Signatures", "date"),
    f("CLIENT_SIGNATURE_IMAGE", "Client Digital Signature", "Signatures", "signature", required=False),
]


MSA_SCHEMA = [
    f("AGREEMENT_EFFECTIVE_DATE", "Agreement Effective Date", "Agreement", "date"),
    f("ENGAGEMENT_END_DATE", "Engagement End Date", "Agreement", "date"),
    f("SERVICE_PROVIDER_LEGAL_NAME", "Service Provider Legal Name", "Parties", source="company.legal_name"),
    f("SERVICE_PROVIDER_REGISTERED_ADDRESS", "Service Provider Registered Address", "Parties", "multiline", source="company.address"),
    f("CLIENT_LEGAL_NAME", "Client Legal Name", "Parties", source="party.legal_name"),
    f("CLIENT_REGISTERED_ADDRESS", "Client Registered Address", "Parties", "multiline", source="party.address"),
    f("PAYMENT_TERMS_DAYS", "Payment Terms Days", "Fees and Expenses", "number", default=30),
    f("CLIENT_PO_NUMBER", "Client PO Number", "Fees and Expenses", required=False),
    f("EXPENSE_POLICY", "Expense Policy", "Fees and Expenses", "multiline"),
    f("ACCEPTANCE_CRITERIA", "Acceptance Criteria", "Acceptance", "multiline"),
    f("ACCEPTANCE_REVIEW_DAYS", "Acceptance Review Days", "Acceptance", "number", default=5),
    f("NDA_REFERENCE", "NDA Reference", "Confidentiality", required=False),
    f("IP_OWNERSHIP_MODEL", "IP Ownership Model", "Intellectual Property", "multiline"),
    f("DATA_PROTECTION_ADDENDUM", "Data Protection Addendum", "Data Protection", required=False),
    f("LIABILITY_CAP", "Aggregate Liability Cap", "Liability"),
    f("BREACH_CURE_DAYS", "Breach Cure Days", "Termination", "number", default=30),
    f("TERMINATION_NOTICE_DAYS", "Termination Notice Days", "Termination", "number", default=30),
    f("NON_SOLICIT_PERIOD_MONTHS", "Non-Solicit Period Months", "Non-Solicitation", "number", required=False),
    f("NON_SOLICIT_SCOPE", "Non-Solicit Scope", "Non-Solicitation", "multiline", required=False),
    f("NON_SOLICIT_EXCEPTIONS", "Non-Solicit Exceptions", "Non-Solicitation", "multiline", required=False),
    f("NOTICE_EMAIL_PROVIDER", "Service Provider Notice Email", "Notices", source="company.email"),
    f("NOTICE_EMAIL_CLIENT", "Client Notice Email", "Notices", source="party.email"),
    f("GOVERNING_LAW", "Governing Law", "Governing Law and Disputes"),
    f("DISPUTE_RESOLUTION_METHOD", "Dispute Resolution Method", "Governing Law and Disputes"),
    f("DISPUTE_VENUE", "Dispute Venue or Seat", "Governing Law and Disputes"),
] + SIGNATURE_FIELDS

MSA_BODY = """[[H1]]1. Client Engagement / Master Services Agreement Template

This Client Engagement / Master Services Agreement ("Agreement") is entered into as of {{AGREEMENT_EFFECTIVE_DATE}} by and between {{SERVICE_PROVIDER_LEGAL_NAME}}, having its registered office at {{SERVICE_PROVIDER_REGISTERED_ADDRESS}} ("Service Provider"), and {{CLIENT_LEGAL_NAME}}, having its registered office at {{CLIENT_REGISTERED_ADDRESS}} ("Client").

[[H2]]1.1 Purpose and Structure
This Agreement establishes the general terms under which the Service Provider may provide technology, consulting, implementation, managed service, development, support, data, AI, analytics, cloud, integration or other professional services to the Client. Specific services will be documented in one or more Statements of Work (each an "SOW") signed or otherwise approved by authorized representatives of the parties.

[[H2]]1.2 Term
The Agreement commences on {{AGREEMENT_EFFECTIVE_DATE}} and remains in force until {{ENGAGEMENT_END_DATE}} unless earlier terminated in accordance with this Agreement. An SOW may have its own start date and end date. If an SOW continues beyond the Agreement term, the Agreement will continue to govern that SOW until completion or termination.

[[H2]]1.3 Statements of Work
Each SOW should identify, at a minimum, the project name, project type, scope, deliverables, assumptions, exclusions, responsibilities, project schedule, commercial model, rates or fees, invoicing, acceptance, change control and any project-specific security, service-level or data-protection requirements. If there is a conflict between this Agreement and an SOW, the precedence stated in the SOW will apply only to that SOW.

[[H2]]1.4 Client Responsibilities and Dependencies
- Provide timely access to personnel, systems, data, documentation, facilities, credentials and decisions required to perform the services.
- Ensure that Client-provided materials and instructions may lawfully be used by the Service Provider for the engagement.
- Review deliverables and provide consolidated feedback or acceptance within the time specified in the SOW.
- Maintain appropriate backups and production-change controls unless those responsibilities are explicitly assigned to the Service Provider.
- Inform the Service Provider promptly of changes that may affect scope, schedule, cost, security or compliance.

[[H2]]1.5 Fees, Invoicing and Taxes
Fees will be calculated according to the Project Type and commercial schedule stated in the applicable SOW. Unless otherwise stated, invoices are payable within {{PAYMENT_TERMS_DAYS}} days from invoice date. Fees exclude applicable taxes, duties and government charges, which will be handled in accordance with applicable law. Client will provide any required purchase order or billing reference, including {{CLIENT_PO_NUMBER}}, before invoice submission where required.

[[H2]]1.6 Expenses
Pre-approved, reasonable project expenses will be handled as follows: {{EXPENSE_POLICY}}. Travel or third-party costs requiring Client approval should be approved in writing before commitment.

[[H2]]1.7 Change Control
A change to scope, deliverables, assumptions, schedule, resource plan, acceptance criteria or commercials must be documented in a Change Request. Neither party is obligated to perform a material change until the Change Request is approved by authorized representatives. The Service Provider may pause affected work where a requested change materially alters the baseline and has not yet been approved.

[[H2]]1.8 Acceptance
Deliverables will be reviewed against {{ACCEPTANCE_CRITERIA}} or the acceptance criteria stated in the SOW. The Client should notify the Service Provider of material non-conformity within {{ACCEPTANCE_REVIEW_DAYS}} business days after delivery. If no material non-conformity is reported within that period, the deliverable may be treated as accepted to the extent permitted by the agreed SOW and applicable law. Any deemed-acceptance wording should be confirmed by legal counsel for the governing jurisdiction.

[[H2]]1.9 Confidentiality
Each party may receive Confidential Information from the other. Confidential Information will be protected in accordance with the applicable NDA or a separately executed NDA identified as {{NDA_REFERENCE}}. Where the NDA and this Agreement conflict, the document precedence defined by the parties will apply.

[[H2]]1.10 Intellectual Property
Unless otherwise stated in the SOW, each party retains ownership of intellectual property owned or developed independently of the engagement ("Background IP"). Ownership and licensing of project deliverables will follow {{IP_OWNERSHIP_MODEL}}. The Service Provider retains ownership of reusable know-how, methods, frameworks, accelerators, utilities, generic code, templates and pre-existing materials, subject to any license expressly granted to the Client.

[[H2]]1.11 Data Protection and Security
Each party will comply with applicable data-protection and security obligations relevant to its role. If the Service Provider processes personal data on behalf of the Client, the parties should execute or incorporate {{DATA_PROTECTION_ADDENDUM}}. Project-specific security controls, hosting locations, retention, access, breach-notification and subprocessors should be stated in the SOW or security schedule.

[[H2]]1.12 Warranties
The Service Provider will perform the services with reasonable skill and care consistent with generally accepted professional standards. Any additional warranties, support commitments, remediation periods or exclusions must be stated in the applicable SOW. Except to the extent prohibited by applicable law, implied warranties should be addressed by legal counsel in the final contract.

[[H2]]1.13 Limitation of Liability
Subject to exclusions that must be reviewed by legal counsel, the parties intend the aggregate liability cap for claims arising under the Agreement to be {{LIABILITY_CAP}}. The treatment of confidentiality breaches, data-protection breaches, fraud, wilful misconduct, infringement, unpaid fees and other legally non-excludable liabilities must be expressly agreed for the applicable jurisdiction.

[[H2]]1.14 Termination
Either party may terminate this Agreement or an SOW for material breach if the breach is not cured within {{BREACH_CURE_DAYS}} days after written notice, subject to applicable law. The parties may also agree convenience termination rights in the SOW, including notice period {{TERMINATION_NOTICE_DAYS}} days. On termination, the Client will pay undisputed fees for services performed, accepted milestones, committed non-cancellable costs and other amounts due under the applicable commercial model.

[[H2]]1.15 Non-Solicitation / Personnel
If the parties choose to include a non-solicitation provision, use the following parameters only after legal review: restricted period {{NON_SOLICIT_PERIOD_MONTHS}} months; scope {{NON_SOLICIT_SCOPE}}; permitted exceptions {{NON_SOLICIT_EXCEPTIONS}}.

[[H2]]1.16 Notices
Formal notices under this Agreement will be delivered to the addresses and emails below, or to any replacement address notified in writing: Service Provider - {{NOTICE_EMAIL_PROVIDER}}; Client - {{NOTICE_EMAIL_CLIENT}}.

[[H2]]1.17 Governing Law and Disputes
This Agreement will be governed by {{GOVERNING_LAW}}. The parties agree that disputes will be handled through {{DISPUTE_RESOLUTION_METHOD}} with venue / seat at {{DISPUTE_VENUE}}, subject to mandatory applicable law.

[[H2]]1.18 Entire Agreement and Order of Precedence
This Agreement, its schedules, applicable SOWs, signed Change Requests, the NDA and any incorporated data-processing or security addenda constitute the agreed contractual framework. A recommended order of precedence is: (1) signed Change Request for the affected scope, (2) applicable SOW, (3) data/security addendum for its subject matter, (4) this Agreement, and (5) other referenced documents, unless the parties expressly agree otherwise.

[[H2]]1.19 Signatures
[[TABLE]]
SERVICE PROVIDER ||  || CLIENT || 
Legal Name || {{SERVICE_PROVIDER_LEGAL_NAME}} || Legal Name || {{CLIENT_LEGAL_NAME}}
Authorized Signatory || {{SERVICE_PROVIDER_SIGNATORY_NAME}} || Authorized Signatory || {{CLIENT_SIGNATORY_NAME}}
Title || {{SERVICE_PROVIDER_SIGNATORY_TITLE}} || Title || {{CLIENT_SIGNATORY_TITLE}}
Signature || {{SERVICE_PROVIDER_SIGNATURE_IMAGE}} || Signature || {{CLIENT_SIGNATURE_IMAGE}}
Date || {{SERVICE_PROVIDER_SIGNATURE_DATE}} || Date || {{CLIENT_SIGNATURE_DATE}}
[[/TABLE]]"""


SOW_SCHEMA = [
    f("SOW_NUMBER", "SOW Number", "Project Details"),
    f("AGREEMENT_ID", "Agreement Reference", "Project Details"),
    f("SERVICE_PROVIDER_LEGAL_NAME", "Service Provider Legal Name", "Project Details", source="company.legal_name"),
    f("CLIENT_LEGAL_NAME", "Client Legal Name", "Project Details", source="party.legal_name"),
    f("PROJECT_NAME", "Project Name", "Project Details"),
    f("PROJECT_CODE", "Project Code", "Project Details"),
    f("PROJECT_TYPE", "Project Type", "Project Details"),
    f("PROJECT_START_DATE", "Project Start Date", "Project Details", "date"),
    f("PROJECT_END_DATE", "Project End Date", "Project Details", "date"),
    f("PROJECT_MANAGER_NAME", "Service Provider Project Manager", "Project Details"),
    f("CLIENT_PROJECT_MANAGER_NAME", "Client Project Manager", "Project Details"),
    f("CURRENCY", "Currency", "Project Details", default="INR"),
    f("CLIENT_PO_NUMBER", "Client PO Number", "Project Details", required=False),
    f("PROJECT_OBJECTIVES", "Project Objectives", "Scope and Delivery", "multiline"),
    f("SCOPE_SUMMARY", "Scope of Services", "Scope and Delivery", "multiline"),
    f("DELIVERABLES", "Deliverables", "Scope and Delivery", "multiline"),
    f("OUT_OF_SCOPE", "Out of Scope", "Scope and Delivery", "multiline"),
    f("ASSUMPTIONS", "Assumptions", "Scope and Delivery", "multiline"),
    f("CLIENT_DEPENDENCIES", "Client Dependencies", "Scope and Delivery", "multiline"),
    f("DELIVERY_METHODOLOGY", "Delivery Methodology", "Governance"),
    f("GOVERNANCE_CADENCE", "Governance Cadence", "Governance"),
    f("STATUS_REPORTING_METHOD", "Status Reporting Method", "Governance"),
    f("ESCALATION_CONTACTS", "Escalation Contacts", "Governance", "multiline"),
    f("ACCEPTANCE_CRITERIA", "Acceptance Criteria", "Acceptance", "multiline"),
    f("ACCEPTANCE_REVIEW_DAYS", "Acceptance Review Days", "Acceptance", "number", default=5),
] + SIGNATURE_FIELDS

SOW_BODY = """[[H1]]1. Statement of Work (SOW) - Common Template
[[TABLE]]
Field || Value
SOW Number || {{SOW_NUMBER}}
Agreement Reference || {{AGREEMENT_ID}}
Client || {{CLIENT_LEGAL_NAME}}
Project Name || {{PROJECT_NAME}}
Project Code || {{PROJECT_CODE}}
Project Type || {{PROJECT_TYPE}}
Start Date || {{PROJECT_START_DATE}}
End Date || {{PROJECT_END_DATE}}
Service Provider PM || {{PROJECT_MANAGER_NAME}}
Client PM || {{CLIENT_PROJECT_MANAGER_NAME}}
Currency || {{CURRENCY}}
Client PO || {{CLIENT_PO_NUMBER}}
[[/TABLE]]

[[H2]]1.1 Objectives
{{PROJECT_OBJECTIVES}}

[[H2]]1.2 Scope of Services
{{SCOPE_SUMMARY}}

[[H2]]1.3 Deliverables
{{DELIVERABLES}}

[[H2]]1.4 Out of Scope
{{OUT_OF_SCOPE}}

[[H2]]1.5 Assumptions and Dependencies
Assumptions: {{ASSUMPTIONS}}
Client dependencies: {{CLIENT_DEPENDENCIES}}

[[H2]]1.6 Delivery Plan and Governance
Delivery methodology: {{DELIVERY_METHODOLOGY}}. Governance cadence: {{GOVERNANCE_CADENCE}}. Status reporting: {{STATUS_REPORTING_METHOD}}. Escalation contacts: {{ESCALATION_CONTACTS}}.

[[H2]]1.7 Acceptance
Acceptance criteria: {{ACCEPTANCE_CRITERIA}}. Review period: {{ACCEPTANCE_REVIEW_DAYS}} business days unless otherwise stated below.

[[H2]]1.8 Commercial Schedule
The commercial terms for this SOW are governed by the selected Project Type commercial schedule.

[[H2]]1.9 Change Control
Changes will be documented using the Change Request template. Approved Change Requests will update the applicable scope, dates, effort, milestone, team or fees.

[[H2]]1.10 SOW Signatures
[[TABLE]]
SERVICE PROVIDER ||  || CLIENT || 
Legal Name || {{SERVICE_PROVIDER_LEGAL_NAME}} || Legal Name || {{CLIENT_LEGAL_NAME}}
Authorized Signatory || {{SERVICE_PROVIDER_SIGNATORY_NAME}} || Authorized Signatory || {{CLIENT_SIGNATORY_NAME}}
Title || {{SERVICE_PROVIDER_SIGNATORY_TITLE}} || Title || {{CLIENT_SIGNATORY_TITLE}}
Signature || {{SERVICE_PROVIDER_SIGNATURE_IMAGE}} || Signature || {{CLIENT_SIGNATURE_IMAGE}}
Date || {{SERVICE_PROVIDER_SIGNATURE_DATE}} || Date || {{CLIENT_SIGNATURE_DATE}}
[[/TABLE]]"""


FIXED_BID_SCHEMA = [
    f("PROJECT_TYPE", "Project Type", "Commercial Details", default="Fixed Bid"),
    f("FIXED_FEE", "Fixed Fee", "Commercial Details"),
    f("CURRENCY", "Currency", "Commercial Details", default="INR"),
    f("PROJECT_START_DATE", "Project Start Date", "Commercial Details", "date"),
    f("PROJECT_END_DATE", "Project End Date", "Commercial Details", "date"),
    f("PAYMENT_SCHEDULE", "Payment Schedule", "Commercial Details", "multiline"),
    f("ACCEPTANCE_CRITERIA", "Acceptance Criteria", "Commercial Details", "multiline"),
    f("CHANGE_CONTROL_THRESHOLD", "Change Control Threshold", "Commercial Details"),
]

FIXED_BID_BODY = """[[H1]]1. Fixed Bid Project
Use when the scope, deliverables and acceptance criteria can be sufficiently defined up front and the Service Provider commits to deliver the agreed scope for a fixed fee, subject to assumptions, dependencies and change control.
[[TABLE]]
Variable || Value / Template
Project Type || Fixed Bid
Fixed Fee || {{FIXED_FEE}} {{CURRENCY}}
Project Start Date || {{PROJECT_START_DATE}}
Project End Date || {{PROJECT_END_DATE}}
Payment Schedule || {{PAYMENT_SCHEDULE}}
Acceptance Criteria || {{ACCEPTANCE_CRITERIA}}
Change Control Threshold || {{CHANGE_CONTROL_THRESHOLD}}
[[/TABLE]]

Commercial clause: In consideration for the defined scope, the Client will pay a fixed fee of {{FIXED_FEE}} {{CURRENCY}}, invoiced according to {{PAYMENT_SCHEDULE}}. The fixed fee is based on the assumptions and dependencies in this SOW. Material changes, delayed Client dependencies or requirements outside the agreed scope will be managed through Change Control and may affect fees or dates."""


TM_SCHEMA = [
    f("PROJECT_TYPE", "Project Type", "Commercial Details", default="Time & Material"),
    f("RATE_CARD_REFERENCE", "Rate Card Reference", "Commercial Details"),
    f("BILLING_UNIT", "Billing Unit", "Commercial Details", "select", options=["Hourly", "Daily", "Monthly"]),
    f("BILLING_FREQUENCY", "Billing Frequency", "Commercial Details"),
    f("TIMESHEET_APPROVER", "Timesheet Approver", "Commercial Details"),
    f("MONTHLY_CAP", "Monthly Cap", "Commercial Details", required=False),
    f("EXPENSE_POLICY", "Expense Policy", "Commercial Details", "multiline"),
    f("TIMESHEET_FREQUENCY", "Timesheet Frequency", "Timesheets"),
    f("TIMESHEET_REVIEW_DAYS", "Timesheet Review Days", "Timesheets", "number"),
]

TM_BODY = """[[H1]]1. Time & Material (T&M) Project
Use when work is delivered based on actual approved effort at agreed rates and the exact volume or backlog may evolve.
[[TABLE]]
Variable || Value / Template
Project Type || Time & Material
Rate Card Reference || {{RATE_CARD_REFERENCE}}
Billing Unit || Hourly / Daily / Monthly
Billing Frequency || {{BILLING_FREQUENCY}}
Timesheet Approver || {{TIMESHEET_APPROVER}}
Monthly Cap || {{MONTHLY_CAP}} (optional)
Expense Policy || {{EXPENSE_POLICY}}
[[/TABLE]]

Commercial clause: Fees are calculated using actual approved time multiplied by the applicable rates in {{RATE_CARD_REFERENCE}}. Timesheets will be submitted {{TIMESHEET_FREQUENCY}} and reviewed by {{TIMESHEET_APPROVER}}. Unless disputed with reasonable detail within {{TIMESHEET_REVIEW_DAYS}} business days, approved timesheets will form the basis for invoicing. Any budget estimate is a planning estimate unless expressly stated as a cap."""


MILESTONE_SCHEMA = []
for number in (1, 2, 3):
    MILESTONE_SCHEMA.extend([
        f(f"MILESTONE_{number}_NAME", f"Milestone {number} Name", f"Milestone {number}"),
        f(f"MILESTONE_{number}_DATE", f"Milestone {number} Target Date", f"Milestone {number}", "date"),
        f(f"MILESTONE_{number}_ACCEPTANCE", f"Milestone {number} Deliverable or Acceptance", f"Milestone {number}", "multiline"),
        f(f"MILESTONE_{number}_FEE", f"Milestone {number} Fee", f"Milestone {number}"),
        f(f"MILESTONE_{number}_TRIGGER", f"Milestone {number} Invoice Trigger", f"Milestone {number}"),
    ])

MILESTONE_BODY = """[[H1]]1. Milestone-Based Project
Use when commercial payment is tied to defined delivery milestones, outputs or acceptance events.
[[TABLE]]
Milestone || Target Date || Deliverable / Acceptance || Fee || Invoice Trigger
{{MILESTONE_1_NAME}} || {{MILESTONE_1_DATE}} || {{MILESTONE_1_ACCEPTANCE}} || {{MILESTONE_1_FEE}} || {{MILESTONE_1_TRIGGER}}
{{MILESTONE_2_NAME}} || {{MILESTONE_2_DATE}} || {{MILESTONE_2_ACCEPTANCE}} || {{MILESTONE_2_FEE}} || {{MILESTONE_2_TRIGGER}}
{{MILESTONE_3_NAME}} || {{MILESTONE_3_DATE}} || {{MILESTONE_3_ACCEPTANCE}} || {{MILESTONE_3_FEE}} || {{MILESTONE_3_TRIGGER}}
[[/TABLE]]

Commercial clause: The Client will pay the milestone fees stated above when the applicable invoice trigger occurs. If a milestone is delayed due to Client dependency, approved change, third-party dependency outside the Service Provider’s reasonable control, or force majeure, the target date and dependent milestones will be re-baselined through the agreed governance process."""


MIXED_SCHEMA = []
for number in (1, 2, 3):
    MIXED_SCHEMA.extend([
        f(f"PHASE_{number}_NAME", f"Phase {number} Name", f"Phase {number}"),
        f(f"PHASE_{number}_MODEL", f"Phase {number} Commercial Model", f"Phase {number}"),
        f(f"PHASE_{number}_COMMERCIAL_BASIS", f"Phase {number} Commercial Basis", f"Phase {number}", "multiline"),
        f(f"PHASE_{number}_START", f"Phase {number} Start", f"Phase {number}", "date"),
        f(f"PHASE_{number}_END", f"Phase {number} End", f"Phase {number}", "date"),
    ])

MIXED_BODY = """[[H1]]1. Mixed Project
Use when different components require different commercial models, for example: discovery on T&M, implementation at fixed bid, and deployment payments by milestone.
[[TABLE]]
Workstream / Phase || Commercial Model || Commercial Basis || Start || End
{{PHASE_1_NAME}} || {{PHASE_1_MODEL}} || {{PHASE_1_COMMERCIAL_BASIS}} || {{PHASE_1_START}} || {{PHASE_1_END}}
{{PHASE_2_NAME}} || {{PHASE_2_MODEL}} || {{PHASE_2_COMMERCIAL_BASIS}} || {{PHASE_2_START}} || {{PHASE_2_END}}
{{PHASE_3_NAME}} || {{PHASE_3_MODEL}} || {{PHASE_3_COMMERCIAL_BASIS}} || {{PHASE_3_START}} || {{PHASE_3_END}}
[[/TABLE]]

Commercial clause: Each workstream will follow the commercial model stated in the table above. Where a dependency crosses commercial models, the SOW must specify which model governs the affected work. Change Requests must state the impact separately for fixed-fee, T&M and milestone components."""


CHANGE_SCHEMA = [
    f("CHANGE_REQUEST_NO", "Change Request Number", "Request Details"),
    f("PROJECT_NAME", "Project Name", "Request Details"),
    f("SOW_NUMBER", "SOW Number", "Request Details"),
    f("CHANGE_REQUESTED_BY", "Requested By", "Request Details"),
    f("CHANGE_REQUEST_DATE", "Request Date", "Request Details", "date"),
    f("CHANGE_PRIORITY", "Priority", "Request Details"),
    f("CHANGE_REASON", "Reason", "Request Details", "multiline"),
    f("CHANGE_DESCRIPTION", "Requested Change", "Requested Change", "multiline"),
]
for old_key, new_key, label in [
    ("OLD_SCOPE", "NEW_SCOPE", "Scope"),
    ("OLD_END_DATE", "NEW_END_DATE", "Schedule"),
    ("OLD_EFFORT", "NEW_EFFORT", "Effort"),
    ("OLD_COMMERCIAL", "NEW_COMMERCIAL", "Commercials"),
    ("OLD_MILESTONE_PLAN", "NEW_MILESTONE_PLAN", "Milestones"),
    ("OLD_RISKS", "NEW_RISKS", "Risks and Dependencies"),
]:
    CHANGE_SCHEMA.extend([
        f(old_key, f"{label} Before Change", "Impact Assessment", "multiline"),
        f(new_key, f"{label} After Change or Impact", "Impact Assessment", "multiline"),
    ])
CHANGE_SCHEMA += [
    f("SERVICE_PROVIDER_LEGAL_NAME", "Service Provider Legal Name", "Approval", source="company.legal_name"),
    f("CLIENT_LEGAL_NAME", "Client Legal Name", "Approval", source="party.legal_name"),
] + SIGNATURE_FIELDS

CHANGE_BODY = """[[H1]]1. Change Request Template
[[TABLE]]
Field || Value
Change Request No. || {{CHANGE_REQUEST_NO}}
Project / SOW || {{PROJECT_NAME}} / {{SOW_NUMBER}}
Requested By || {{CHANGE_REQUESTED_BY}}
Request Date || {{CHANGE_REQUEST_DATE}}
Change Type || Scope / Schedule / Cost / Resource / Technical / Other
Priority || {{CHANGE_PRIORITY}}
Reason || {{CHANGE_REASON}}
[[/TABLE]]

[[H2]]1.1 Requested Change
{{CHANGE_DESCRIPTION}}

[[H2]]1.2 Impact Assessment
[[TABLE]]
Impact Area || Before Change || After Change / Impact
Scope || {{OLD_SCOPE}} || {{NEW_SCOPE}}
Schedule || {{OLD_END_DATE}} || {{NEW_END_DATE}}
Effort || {{OLD_EFFORT}} || {{NEW_EFFORT}}
Commercials || {{OLD_COMMERCIAL}} || {{NEW_COMMERCIAL}}
Milestones || {{OLD_MILESTONE_PLAN}} || {{NEW_MILESTONE_PLAN}}
Risks / Dependencies || {{OLD_RISKS}} || {{NEW_RISKS}}
[[/TABLE]]

[[H2]]1.3 Approval
The approved Change Request becomes part of the applicable SOW and supersedes the affected baseline only to the extent expressly stated above.
[[TABLE]]
SERVICE PROVIDER APPROVAL ||  || CLIENT APPROVAL || 
Legal Name || {{SERVICE_PROVIDER_LEGAL_NAME}} || Legal Name || {{CLIENT_LEGAL_NAME}}
Authorized Signatory || {{SERVICE_PROVIDER_SIGNATORY_NAME}} || Authorized Signatory || {{CLIENT_SIGNATORY_NAME}}
Title || {{SERVICE_PROVIDER_SIGNATORY_TITLE}} || Title || {{CLIENT_SIGNATORY_TITLE}}
Signature || {{SERVICE_PROVIDER_SIGNATURE_IMAGE}} || Signature || {{CLIENT_SIGNATURE_IMAGE}}
Date || {{SERVICE_PROVIDER_SIGNATURE_DATE}} || Date || {{CLIENT_SIGNATURE_DATE}}
[[/TABLE]]"""


ACCEPTANCE_SCHEMA = [
    f("PROJECT_NAME", "Project Name", "Acceptance Details"),
    f("SOW_NUMBER", "SOW Number", "Acceptance Details"),
    f("MILESTONE_NAME", "Milestone or Deliverable", "Acceptance Details"),
    f("DELIVERABLE_SUBMISSION_DATE", "Deliverable Submission Date", "Acceptance Details", "date"),
    f("ACCEPTANCE_DUE_DATE", "Acceptance Due Date", "Acceptance Details", "date"),
    f("CLIENT_REVIEWER_NAME", "Client Reviewer", "Acceptance Details"),
    f("ACCEPTANCE_CRITERIA", "Acceptance Criteria", "Acceptance Decision", "multiline"),
    f("ACCEPTANCE_STATUS", "Acceptance Status", "Acceptance Decision", "select", options=["Accepted", "Accepted with Minor Actions", "Rejected"]),
    f("ACCEPTANCE_COMMENTS", "Comments or Actions", "Acceptance Decision", "multiline"),
    f("SERVICE_PROVIDER_LEGAL_NAME", "Service Provider Legal Name", "Signatures", source="company.legal_name"),
    f("CLIENT_LEGAL_NAME", "Client Legal Name", "Signatures", source="party.legal_name"),
] + SIGNATURE_FIELDS

ACCEPTANCE_BODY = """[[H1]]1. Milestone / Deliverable Acceptance Template
[[TABLE]]
Field || Value
Project || {{PROJECT_NAME}}
SOW || {{SOW_NUMBER}}
Milestone / Deliverable || {{MILESTONE_NAME}}
Submission Date || {{DELIVERABLE_SUBMISSION_DATE}}
Acceptance Due Date || {{ACCEPTANCE_DUE_DATE}}
Client Reviewer || {{CLIENT_REVIEWER_NAME}}
[[/TABLE]]

Acceptance statement: The Client confirms that the above milestone / deliverable has been reviewed against the agreed acceptance criteria {{ACCEPTANCE_CRITERIA}} and is: {{ACCEPTANCE_STATUS}} (Accepted / Accepted with Minor Actions / Rejected).
Comments / actions: {{ACCEPTANCE_COMMENTS}}
[[TABLE]]
SERVICE PROVIDER ||  || CLIENT || 
Legal Name || {{SERVICE_PROVIDER_LEGAL_NAME}} || Legal Name || {{CLIENT_LEGAL_NAME}}
Authorized Signatory || {{SERVICE_PROVIDER_SIGNATORY_NAME}} || Authorized Signatory || {{CLIENT_SIGNATORY_NAME}}
Title || {{SERVICE_PROVIDER_SIGNATORY_TITLE}} || Title || {{CLIENT_SIGNATORY_TITLE}}
Signature || {{SERVICE_PROVIDER_SIGNATURE_IMAGE}} || Signature || {{CLIENT_SIGNATURE_IMAGE}}
Date || {{SERVICE_PROVIDER_SIGNATURE_DATE}} || Date || {{CLIENT_SIGNATURE_DATE}}
[[/TABLE]]"""


CLOSURE_SCHEMA = [
    f("CLIENT_LEGAL_NAME", "Client Legal Name", "Project Details", source="party.legal_name"),
    f("PROJECT_NAME", "Project Name", "Project Details"),
    f("PROJECT_CODE", "Project Code", "Project Details"),
    f("SOW_NUMBER", "SOW Number", "Project Details"),
    f("PROJECT_TYPE", "Project Type", "Project Details"),
    f("ACTUAL_START_DATE", "Actual Start Date", "Project Details", "date"),
    f("ACTUAL_END_DATE", "Actual End Date", "Project Details", "date"),
    f("FINAL_COMMERCIAL_STATUS", "Final Commercial Status", "Project Details", "multiline"),
    f("STATUS", "Closure Checklist Status", "Closure Checklist"),
    f("EVIDENCE", "Closure Checklist Evidence or Comments", "Closure Checklist", "multiline"),
    f("SERVICE_PROVIDER_LEGAL_NAME", "Service Provider Legal Name", "Signatures", source="company.legal_name"),
] + SIGNATURE_FIELDS

CLOSURE_BODY = """[[H1]]1. Project / Engagement Closure Template
[[TABLE]]
Field || Value
Client || {{CLIENT_LEGAL_NAME}}
Project || {{PROJECT_NAME}}
Project Code || {{PROJECT_CODE}}
SOW || {{SOW_NUMBER}}
Project Type || {{PROJECT_TYPE}}
Actual Start Date || {{ACTUAL_START_DATE}}
Actual End Date || {{ACTUAL_END_DATE}}
Final Commercial Status || {{FINAL_COMMERCIAL_STATUS}}
[[/TABLE]]

[[H2]]1.1 Closure Checklist
[[TABLE]]
Item || Status || Evidence / Comments
All contractual deliverables submitted || {{STATUS}} || {{EVIDENCE}}
Acceptance completed || {{STATUS}} || {{EVIDENCE}}
Open change requests closed || {{STATUS}} || {{EVIDENCE}}
Final timesheets approved (if applicable) || {{STATUS}} || {{EVIDENCE}}
Final invoice issued / scheduled || {{STATUS}} || {{EVIDENCE}}
Client data / access disposition completed || {{STATUS}} || {{EVIDENCE}}
Knowledge transfer completed || {{STATUS}} || {{EVIDENCE}}
Credentials / environments decommissioned as applicable || {{STATUS}} || {{EVIDENCE}}
Lessons learned captured || {{STATUS}} || {{EVIDENCE}}
[[/TABLE]]

[[H2]]1.2 Closure Confirmation
The parties acknowledge that the project has reached closure subject to the items and surviving obligations identified in the Agreement, NDA, SOW and any approved Change Requests.
[[PAGEBREAK]]
[[TABLE]]
SERVICE PROVIDER ||  || CLIENT || 
Legal Name || {{SERVICE_PROVIDER_LEGAL_NAME}} || Legal Name || {{CLIENT_LEGAL_NAME}}
Authorized Signatory || {{SERVICE_PROVIDER_SIGNATORY_NAME}} || Authorized Signatory || {{CLIENT_SIGNATORY_NAME}}
Title || {{SERVICE_PROVIDER_SIGNATORY_TITLE}} || Title || {{CLIENT_SIGNATORY_TITLE}}
Signature || {{SERVICE_PROVIDER_SIGNATURE_IMAGE}} || Signature || {{CLIENT_SIGNATURE_IMAGE}}
Date || {{SERVICE_PROVIDER_SIGNATURE_DATE}} || Date || {{CLIENT_SIGNATURE_DATE}}
[[/TABLE]]"""


ADDITIONAL_TEMPLATES = [
    {"code": "MSA", "name": "Client Engagement Agreement", "description": "Original Client Engagement / Master Services Agreement supplied for this project.", "schema": MSA_SCHEMA, "body": MSA_BODY, "source": "01_Client_Engagement_Agreement.docx", "prefix": "MSA"},
    {"code": "SOW", "name": "Statement of Work", "description": "Original common Statement of Work template supplied for this project.", "schema": SOW_SCHEMA, "body": SOW_BODY, "source": "03_Statement_of_Work_Common.docx", "prefix": "SOW"},
    {"code": "FIXED_BID", "name": "Fixed Bid Commercial Schedule", "description": "Original fixed bid project commercial schedule supplied for this project.", "schema": FIXED_BID_SCHEMA, "body": FIXED_BID_BODY, "source": "04_Fixed_Bid_Commercial_Schedule.docx", "prefix": "FBD"},
    {"code": "TIME_MATERIAL", "name": "Time and Material Commercial Schedule", "description": "Original Time & Material project commercial schedule supplied for this project.", "schema": TM_SCHEMA, "body": TM_BODY, "source": "05_Time_and_Material_Commercial_Schedule.docx", "prefix": "TAM"},
    {"code": "MILESTONE", "name": "Milestone Based Commercial Schedule", "description": "Original milestone-based project commercial schedule supplied for this project.", "schema": MILESTONE_SCHEMA, "body": MILESTONE_BODY, "source": "06_Milestone_Based_Commercial_Schedule.docx", "prefix": "MLS"},
    {"code": "MIXED", "name": "Mixed Project Commercial Schedule", "description": "Original mixed project commercial schedule supplied for this project.", "schema": MIXED_SCHEMA, "body": MIXED_BODY, "source": "07_Mixed_Project_Commercial_Schedule.docx", "prefix": "MIX"},
    {"code": "CHANGE_REQUEST", "name": "Change Request", "description": "Original project Change Request template supplied for this project.", "schema": CHANGE_SCHEMA, "body": CHANGE_BODY, "source": "08_Change_Request.docx", "prefix": "CRQ"},
    {"code": "ACCEPTANCE", "name": "Milestone Deliverable Acceptance", "description": "Original milestone and deliverable acceptance template supplied for this project.", "schema": ACCEPTANCE_SCHEMA, "body": ACCEPTANCE_BODY, "source": "09_Milestone_Deliverable_Acceptance.docx", "prefix": "ACC"},
    {"code": "CLOSURE", "name": "Project Engagement Closure", "description": "Original project and engagement closure template supplied for this project.", "schema": CLOSURE_SCHEMA, "body": CLOSURE_BODY, "source": "10_Project_Engagement_Closure.docx", "prefix": "CLS"},
]

ADDITIONAL_TEMPLATE_MAP = {item["code"]: item for item in ADDITIONAL_TEMPLATES}
