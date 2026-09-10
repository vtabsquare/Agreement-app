from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import base64
import json
import os
import re
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
    NextPageTemplate, Table, TableStyle, Image as RLImage, KeepTogether
)
from reportlab.lib.utils import ImageReader

from .template_library import ADDITIONAL_TEMPLATES, ADDITIONAL_TEMPLATE_MAP

APP_NAME = "Aurelia Contract Studio"
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip('"').strip("'")
ASSET_DIR = Path(__file__).resolve().parent / "assets"
NAVY = colors.HexColor("#102f63")
TEXT = colors.HexColor("#25252b")
MUTED = colors.HexColor("#586174")

app = FastAPI(title=APP_NAME, version="1.7.0")
origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "https://agreement-studio.onrender.com"
]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url and frontend_url not in origins:
    origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def db():
    if not DATABASE_URL:
        raise HTTPException(503, "Database is not configured. Set the DATABASE_URL environment variable.")
    try:
        c = psycopg2.connect(DATABASE_URL)
        return c
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Database connection failed: %s", e)
        raise HTTPException(500, f"Database connection failed: {e}")


def ensure_column(conn, table: str, column: str, definition: str):
    cur = conn.cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name=%s AND column_name=%s",
        (table, column)
    )
    if not cur.fetchone():
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


POLICY_SCHEMA = [
    {"key":"EMPLOYEE_NAME","label":"Employee / Intern Name","type":"text","required":True,"group":"Recipient"},
    {"key":"AGREEMENT_DATE","label":"Agreement Date","type":"date","required":True,"group":"Recipient"},
    {"key":"EMPLOYEE_PHOTO","label":"Passport-size Photo","type":"image","required":False,"group":"Recipient"},

    {"key":"INTERNSHIP_MONTHS","label":"Internship Period (months)","type":"number","required":True,"default":6,"group":"Internship Period"},
    {"key":"INTERNSHIP_COMPLETION_AMOUNT","label":"Successful Completion Amount","type":"currency","required":True,"default":30000,"group":"Internship Period"},

    {"key":"TRAINING_MONTHS","label":"Training Period (months)","type":"number","required":True,"default":2,"group":"Training Period"},
    {"key":"TRAINING_STIPEND","label":"Training Stipend","type":"currency","required":True,"default":7000,"group":"Training Period"},

    {"key":"PROBATION_MONTHS","label":"Probation Period (months)","type":"number","required":True,"default":4,"group":"Probation Period"},
    {"key":"PROBATION_SALARY","label":"Probation Salary","type":"currency","required":True,"default":13500,"group":"Probation Period"},

    {"key":"POST_PROBATION_SALARY","label":"Post-Probation Salary","type":"currency","required":True,"default":15000,"group":"Post-Probation Period"},
    {"key":"POST_PROBATION_MONTHS","label":"Post-Probation Period (months)","type":"number","required":True,"default":2,"group":"Post-Probation Period"},

    {"key":"WORK_FROM_TIME","label":"Working Hours - From","type":"text","required":True,"default":"11:00","group":"Work & Leave Policy"},
    {"key":"WORK_TO_TIME","label":"Working Hours - To","type":"text","required":True,"default":"21:00","group":"Work & Leave Policy"},
    {"key":"WORK_SETUP","label":"Initial Work Setup","type":"select","required":True,"options":["work-from-home","office","hybrid"],"default":"work-from-home","group":"Work & Leave Policy"},
    {"key":"LOP_EXTENSION_DAYS","label":"Internship Extension for Leave / LOP (days)","type":"number","required":True,"default":90,"group":"Work & Leave Policy"},
    {"key":"SALARY_CREDIT_DAY","label":"Salary Credit Day of Month","type":"number","required":True,"default":15,"group":"Work & Leave Policy"},

    {"key":"EARLY_RESIGNATION_THRESHOLD_MONTHS","label":"Early Resignation Threshold (months)","type":"number","required":True,"default":11,"group":"Resignation Policy"},
    {"key":"EARLY_RESIGNATION_PENALTY_MONTHS","label":"Early Resignation Penalty (months of salary)","type":"number","required":True,"default":3,"group":"Resignation Policy"},
    {"key":"NOTICE_PERIOD_DAYS","label":"Notice Period (days)","type":"number","required":True,"default":90,"group":"Resignation Policy"},
    {"key":"NOTICE_PERIOD_MONTHS","label":"Notice Period (months shown in document)","type":"number","required":True,"default":3,"group":"Resignation Policy"},
    {"key":"FAILURE_NOTICE_PENALTY_MONTHS","label":"Failure-to-Serve Penalty (months of salary)","type":"number","required":True,"default":5,"group":"Resignation Policy"},
    {"key":"EXAMPLE_ELIGIBLE_MONTHS","label":"Eligible Resignation Example (months)","type":"number","required":True,"default":12,"group":"Resignation Policy"},
    {"key":"EXAMPLE_EARLY_MONTHS","label":"Early Resignation Example (months)","type":"number","required":True,"default":8,"group":"Resignation Policy"},

    {"key":"AUTHORIZED_SIGNATORY_NAME","label":"Authorized Signatory Name","type":"text","required":True,"default":"Vimala C.","group":"Authorization"},
    {"key":"AUTHORIZED_SIGNATORY_TITLE","label":"Authorized Signatory Designation","type":"text","required":True,"default":"Managing Director","group":"Authorization"},
    {"key":"AUTHORIZED_SIGNATORY_COMPANY","label":"Authorized Signatory Company Line","type":"text","required":True,"default":"VTAB Square Pvt Ltd (Now Part of Siroco)","group":"Authorization"},
    {"key":"AUTHORIZED_SIGNATURE_IMAGE","label":"Authorized Digital Signature (optional)","type":"signature","required":False,"group":"Authorization"},
]

NDA_SCHEMA = [
    {"key":"SERVICE_PROVIDER_LEGAL_NAME","label":"Legal Name","type":"text","required":True,"source":"company.legal_name","group":"Service Provider"},
    {"key":"COMPANY_BRAND_NAME","label":"Brand / Trading Name","type":"text","required":True,"source":"company.name","group":"Service Provider"},
    {"key":"SERVICE_PROVIDER_REGISTERED_ADDRESS","label":"Registered Address","type":"multiline","required":True,"source":"company.address","group":"Service Provider"},
    {"key":"SERVICE_PROVIDER_REGISTRATION_NO","label":"Registration / CIN Number","type":"text","required":True,"group":"Service Provider"},
    {"key":"SERVICE_PROVIDER_TAX_ID","label":"GST / VAT / Tax ID","type":"text","required":True,"source":"company.gst","group":"Service Provider"},
    {"key":"NOTICE_EMAIL_PROVIDER","label":"Formal Notice Email","type":"text","required":True,"source":"company.email","group":"Service Provider"},

    {"key":"CLIENT_LEGAL_NAME","label":"Legal Name","type":"text","required":True,"source":"party.legal_name","group":"Client"},
    {"key":"CLIENT_NAME","label":"Display Name","type":"text","required":True,"source":"party.name","group":"Client"},
    {"key":"CLIENT_REGISTERED_ADDRESS","label":"Registered Address","type":"multiline","required":True,"source":"party.address","group":"Client"},
    {"key":"CLIENT_REGISTRATION_NO","label":"Registration Number","type":"text","required":True,"group":"Client"},
    {"key":"CLIENT_TAX_ID","label":"GST / VAT / Tax ID","type":"text","required":True,"source":"party.gst","group":"Client"},
    {"key":"CLIENT_PRIMARY_CONTACT_NAME","label":"Primary Contact Name","type":"text","required":True,"source":"party.contact_person","group":"Client"},
    {"key":"CLIENT_PRIMARY_CONTACT_EMAIL","label":"Primary Contact Email","type":"text","required":True,"source":"party.email","group":"Client"},
    {"key":"NOTICE_EMAIL_CLIENT","label":"Formal Notice Email","type":"text","required":True,"source":"party.email","group":"Client"},

    {"key":"NDA_EFFECTIVE_DATE","label":"NDA Effective Date","type":"date","required":True,"group":"NDA Details"},
    {"key":"NDA_END_DATE","label":"NDA End Date","type":"date","required":True,"group":"NDA Details"},
    {"key":"NDA_PURPOSE","label":"Purpose of NDA / Engagement","type":"multiline","required":True,"group":"NDA Details"},
    {"key":"CONFIDENTIALITY_TERM_YEARS","label":"Confidentiality Survival Period (years)","type":"number","required":True,"default":3,"group":"NDA Details"},

    {"key":"GOVERNING_LAW","label":"Governing Law","type":"text","required":True,"default":"Tamil Nadu, India","group":"Legal Terms"},
    {"key":"DISPUTE_RESOLUTION_METHOD","label":"Dispute Resolution Method","type":"select","required":True,"options":["Courts","Arbitration","Mediation then Arbitration"],"default":"Courts","group":"Legal Terms"},
    {"key":"DISPUTE_VENUE","label":"Dispute Venue / Seat","type":"text","required":True,"default":"Coimbatore, Tamil Nadu","group":"Legal Terms"},

    {"key":"SERVICE_PROVIDER_SIGNATORY_NAME","label":"Service Provider Authorized Signatory","type":"text","required":True,"source":"company.representative","group":"Service Provider Signature"},
    {"key":"SERVICE_PROVIDER_SIGNATORY_TITLE","label":"Service Provider Signatory Title","type":"text","required":True,"default":"Managing Director","group":"Service Provider Signature"},
    {"key":"SERVICE_PROVIDER_SIGNATURE_DATE","label":"Service Provider Signature Date","type":"date","required":False,"group":"Service Provider Signature"},
    {"key":"SERVICE_PROVIDER_SIGNATURE_IMAGE","label":"Service Provider Digital Signature","type":"signature","required":False,"group":"Service Provider Signature"},

    {"key":"CLIENT_SIGNATORY_NAME","label":"Client Authorized Signatory","type":"text","required":True,"source":"party.contact_person","group":"Client Signature"},
    {"key":"CLIENT_SIGNATORY_TITLE","label":"Client Signatory Title","type":"text","required":True,"group":"Client Signature"},
    {"key":"CLIENT_SIGNATURE_DATE","label":"Client Signature Date","type":"date","required":False,"group":"Client Signature"},
    {"key":"CLIENT_SIGNATURE_IMAGE","label":"Client Digital Signature","type":"signature","required":False,"group":"Client Signature"},
]

POLICY_BODY = """POLICY AGREEMENT DOCUMENT

DEAR {{EMPLOYEE_NAME}},

Agreement Date: {{AGREEMENT_DATE}}

1. Internship Period: Upon acceptance of the offer, the initial ({{INTERNSHIP_MONTHS}}) months shall constitute a paid internship Successful completion will get {{INTERNSHIP_COMPLETION_AMOUNT}}.

2. Training Period: Upon successful completion of the internship, you will enter a ({{TRAINING_MONTHS}})-months training phase with a stipend of {{TRAINING_STIPEND}}.

3. Probation Period: After the training, you will proceed to a ({{PROBATION_MONTHS}})-months' probation period with a salary of {{PROBATION_SALARY}}.

4. Post-Probation Period: Upon successfully completing probation, your salary will increase to {{POST_PROBATION_SALARY}} for the following {{POST_PROBATION_MONTHS}} months.

5. Performance-Based Hike: After completing one year with the organization, a salary hike will be decided based on your performance.

6. Working Hours and Location: Initially, your working hours will be from {{WORK_FROM_TIME}} to {{WORK_TO_TIME}}; and it will be a {{WORK_SETUP}} setup; however, you may need to work from the office if required. Any changes will be communicated in advance.

7. Work and Leave Policy: You are required to work on all Saturdays and will not be eligible for any paid leave until confirmation of your probation period. Leaves availed will be considered as LOP and {{LOP_EXTENSION_DAYS}} days internship will get extended.

8. Salary: Salary will be credited to your preferred bank account {{SALARY_CREDIT_DAY}}th of every month.

Intern Resignation Policy

Early Resignation (before {{EARLY_RESIGNATION_THRESHOLD_MONTHS}} months):
- The intern must pay a penalty of {{EARLY_RESIGNATION_PENALTY_MONTHS}} months' last drawn salary.
- The intern must serve a {{NOTICE_PERIOD_DAYS}}-day ({{NOTICE_PERIOD_MONTHS}} months) notice period.

Intern Resignation Policy (contd.)

Failure to Serve Notice Period:
- If the intern does not serve the full {{NOTICE_PERIOD_DAYS}}-day notice period, they must instead pay a penalty of {{FAILURE_NOTICE_PENALTY_MONTHS}} months' last drawn salary.
- Immediate relieving will be granted after payment.

Example Cases
- Intern resigns after {{EXAMPLE_ELIGIBLE_MONTHS}} months: -> Eligible, no penalty, standard resignation process.
- Intern resigns after {{EXAMPLE_EARLY_MONTHS}} months, serves {{NOTICE_PERIOD_DAYS}}-day notice: -> Must pay {{EARLY_RESIGNATION_PENALTY_MONTHS}} months' salary penalty, serve {{NOTICE_PERIOD_DAYS}} days, then relieved.
- Intern resigns after {{EXAMPLE_EARLY_MONTHS}} months, refuses {{NOTICE_PERIOD_DAYS}}-day notice: -> Must pay {{FAILURE_NOTICE_PENALTY_MONTHS}} months' salary penalty, then relieved immediately.

Progression to each subsequent stage is contingent upon your performance. Please find the attachment for more details. As part of the onboarding process, please:
- Reply with your confirmation.
- Attach a recent passport-sized photograph.
- Send a copy of your ID proof and signed agreement.
- Provide your educational certificates.

Authorized Signatory
{{AUTHORIZED_SIGNATORY_NAME}}
{{AUTHORIZED_SIGNATORY_TITLE}}
{{AUTHORIZED_SIGNATORY_COMPANY}}
"""

NDA_BODY = """1. MUTUAL NON-DISCLOSURE AGREEMENT

This Mutual Non-Disclosure Agreement (\"NDA\") is made effective {{NDA_EFFECTIVE_DATE}} between {{SERVICE_PROVIDER_LEGAL_NAME}} and {{CLIENT_LEGAL_NAME}} for the purpose of evaluating, discussing and/or performing {{NDA_PURPOSE}}.

PARTIES
Service Provider: {{SERVICE_PROVIDER_LEGAL_NAME}}, trading as {{COMPANY_BRAND_NAME}}, registered at {{SERVICE_PROVIDER_REGISTERED_ADDRESS}}, registration no. {{SERVICE_PROVIDER_REGISTRATION_NO}}, tax ID {{SERVICE_PROVIDER_TAX_ID}}.
Client: {{CLIENT_LEGAL_NAME}} ({{CLIENT_NAME}}), registered at {{CLIENT_REGISTERED_ADDRESS}}, registration no. {{CLIENT_REGISTRATION_NO}}, tax ID {{CLIENT_TAX_ID}}. Primary contact: {{CLIENT_PRIMARY_CONTACT_NAME}} ({{CLIENT_PRIMARY_CONTACT_EMAIL}}).

1.1 Definition of Confidential Information
\"Confidential Information\" means non-public business, commercial, financial, technical, product, security, customer, employee, source-code, architecture, pricing, roadmap, data, AI/model, strategy or other information disclosed by or on behalf of a party (\"Disclosing Party\") to the other party (\"Receiving Party\") that is marked confidential or that reasonably should be understood to be confidential given its nature and the circumstances of disclosure.

1.2 Exclusions
Confidential Information does not include information that the Receiving Party can demonstrate: (a) is or becomes public without breach; (b) was lawfully known without restriction before disclosure; (c) is received lawfully from a third party without confidentiality obligation; or (d) is independently developed without use of the Confidential Information.

1.3 Permitted Use and Protection
The Receiving Party will use Confidential Information only for {{NDA_PURPOSE}}, protect it using at least reasonable care, and disclose it only to personnel, professional advisers, affiliates or approved subcontractors who have a need to know and are bound by confidentiality obligations no less protective than those applicable here.

1.4 Compelled Disclosure
If disclosure is required by law, regulation, court order or competent authority, the Receiving Party will, where legally permitted, give prompt notice to the Disclosing Party and reasonably cooperate in seeking protective treatment.

1.5 Return or Destruction
Upon written request or termination of discussions, the Receiving Party will return or destroy Confidential Information to the extent reasonably practicable, subject to legal, regulatory, security-backup and record-retention requirements. Any retained copy remains subject to this NDA.

1.6 Ownership; No License
Confidential Information remains the property of the Disclosing Party. No intellectual-property license or other right is granted except the limited right to use Confidential Information for the stated purpose.

1.7 Term and Survival
This NDA begins on {{NDA_EFFECTIVE_DATE}} and remains in effect until {{NDA_END_DATE}} unless terminated earlier. Confidentiality obligations survive for {{CONFIDENTIALITY_TERM_YEARS}} years after disclosure or termination, except trade secrets or other information requiring longer protection under applicable law, which should be addressed by counsel.

1.8 Remedies
The parties acknowledge that unauthorized use or disclosure may cause harm for which monetary damages may be inadequate. Available equitable or injunctive remedies, if any, will be subject to applicable law and the decision of the competent court or tribunal.

1.9 Notices
Formal notices shall be delivered to the stated registered addresses and to Service Provider - {{NOTICE_EMAIL_PROVIDER}}; Client - {{NOTICE_EMAIL_CLIENT}}, or any replacement address notified in writing.

1.10 Governing Law and Disputes
This NDA is governed by {{GOVERNING_LAW}}. Disputes will be handled through {{DISPUTE_RESOLUTION_METHOD}} with venue / seat at {{DISPUTE_VENUE}}, unless otherwise agreed.

1.11 Signatures
SERVICE PROVIDER
Legal Name: {{SERVICE_PROVIDER_LEGAL_NAME}}
Authorized Signatory: {{SERVICE_PROVIDER_SIGNATORY_NAME}}
Title: {{SERVICE_PROVIDER_SIGNATORY_TITLE}}
Signature: {{SERVICE_PROVIDER_SIGNATURE_IMAGE}}
Date: {{SERVICE_PROVIDER_SIGNATURE_DATE}}

CLIENT
Legal Name: {{CLIENT_LEGAL_NAME}}
Authorized Signatory: {{CLIENT_SIGNATORY_NAME}}
Title: {{CLIENT_SIGNATORY_TITLE}}
Signature: {{CLIENT_SIGNATURE_IMAGE}}
Date: {{CLIENT_SIGNATURE_DATE}}
"""

BUILTIN_TEMPLATE_MAP = {
    "POLICY": {"code": "POLICY", "name": "Policy Agreement", "schema": POLICY_SCHEMA, "body": POLICY_BODY, "prefix": "POL"},
    "NDA": {"code": "NDA", "name": "Client Engagement NDA", "schema": NDA_SCHEMA, "body": NDA_BODY, "prefix": "NDA"},
    **ADDITIONAL_TEMPLATE_MAP,
}
ACTIVE_TEMPLATE_CODES = tuple(BUILTIN_TEMPLATE_MAP)


def init_db():
    conn = db()
    cur = conn.cursor()
    now = now_iso()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS digital_signatures (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            image_data TEXT NOT NULL,
            source_type TEXT NOT NULL DEFAULT 'upload',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    # Tables are pre-created in Supabase via SQL editor.
    # This function only seeds default data on first run.
    cur.execute("SELECT COUNT(*) FROM companies")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO companies(name,legal_name,email,phone,address,gst,representative,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
            ("VTAB Square","VTAB Square Private Limited","info@sirocotech.com","+91 80868 00199","Tamil Nadu, India","","Vimala C.",now)
        )
    cur.execute("SELECT COUNT(*) FROM parties")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO parties(party_type,name,legal_name,contact_person,email,phone,address,gst,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            ("Client","Sample Client","Sample Client Private Limited","Client Signatory","client@example.com","","Chennai, Tamil Nadu","",now)
        )
    docs = [
        ("POLICY","Policy Agreement","Approved policy agreement template replicated from the supplied VTAB Square Policy Agreement Letter.","policy",json.dumps(POLICY_SCHEMA),POLICY_BODY,now,"1.7.0",json.dumps({"source":"Policy Agreement PDF","shell":"VTAB Square / Siroco","page_size":"A4"})),
        ("NDA","Client Engagement NDA","Approved Mutual NDA template derived from the complete parameterized Client Engagement Agreement / NDA pack.","nda",json.dumps(NDA_SCHEMA),NDA_BODY,now,"1.7.0",json.dumps({"source":"Parameterized Client Engagement NDA pack","shell":"VTAB Square / Siroco","page_size":"A4"})),
    ]
    docs.extend(
        (
            item["code"], item["name"], item["description"], "engagement",
            json.dumps(item["schema"]), item["body"], now, "1.7.0",
            json.dumps({"source": item["source"], "shell": "VTAB Square / Siroco", "page_size": "A4", "content_policy": "source-faithful"}),
        )
        for item in ADDITIONAL_TEMPLATES
    )
    for d in docs:
        cur.execute("SELECT is_customized,builtin_version FROM document_types WHERE code=%s", (d[0],))
        existing = cur.fetchone()
        if not existing:
            cur.execute("""
                INSERT INTO document_types(code,name,description,renderer_kind,field_schema_json,body_template,active,updated_at,builtin_version,metadata_json,template_version,is_customized)
                VALUES(%s,%s,%s,%s,%s,%s,1,%s,%s,%s,1,0)""", d)
        elif not existing[0] and existing[1] != d[7]:
            cur.execute("""
                UPDATE document_types SET name=%s,description=%s,renderer_kind=%s,field_schema_json=%s,body_template=%s,
                active=1,updated_at=%s,builtin_version=%s,metadata_json=%s,template_version=template_version+1
                WHERE code=%s""",
                (d[1],d[2],d[3],d[4],d[5],d[6],d[7],d[8],d[0]))
    cur.execute("UPDATE document_types SET active=0 WHERE NOT (code = ANY(%s))", (list(ACTIVE_TEMPLATE_CODES),))
    conn.commit()
    conn.close()


if DATABASE_URL:
    try:
        init_db()
    except Exception as _init_err:
        import logging
        logging.getLogger(__name__).error("init_db() failed: %s", _init_err)
else:
    import logging
    logging.getLogger(__name__).warning(
        "DATABASE_URL is not set — skipping database initialisation. "
        "Set DATABASE_URL in the Render environment variables."
    )


class CompanyIn(BaseModel):
    name: str
    legal_name: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    gst: str = ""
    representative: str = ""


class PartyIn(BaseModel):
    party_type: str = "Client"
    name: str
    legal_name: str = ""
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    gst: str = ""


class RenderRequest(BaseModel):
    document_type_code: str
    company_id: int
    party_id: int = 0
    field_values: dict[str, Any] = Field(default_factory=dict)
    content: Optional[str] = None


class AgreementIn(RenderRequest):
    title: str
    content: str


class AgreementUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None
    title: Optional[str] = None


class TemplateUpdate(BaseModel):
    body_template: str
    fields: list[dict[str, Any]]


class SignatureIn(BaseModel):
    name: str
    image_data: str
    source_type: str = "upload"


def rows(q, p=()):
    c = db()
    cur = c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(q.replace("?", "%s"), p)
    out = [dict(r) for r in cur.fetchall()]
    c.close()
    return out


def one(q, p=()):
    c = db()
    cur = c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(q.replace("?", "%s"), p)
    r = cur.fetchone()
    c.close()
    return dict(r) if r else None


def doc_type(code: str):
    r = one("SELECT * FROM document_types WHERE code=? AND active=1", (code.upper(),))
    if not r:
        raise HTTPException(404, "Document type not found")
    r["fields"] = json.loads(r["field_schema_json"] or "[]")
    r["metadata"] = json.loads(r.get("metadata_json") or "{}")
    return r


def builtin_template(code: str):
    code=code.upper()
    item=BUILTIN_TEMPLATE_MAP.get(code)
    if item: return item["schema"], item["body"]
    raise HTTPException(404,"Built-in template not found")


def next_number(code: str):
    y = datetime.now().year
    prefix = BUILTIN_TEMPLATE_MAP.get(code, {}).get("prefix", re.sub(r"[^A-Z0-9]", "", code)[:3] or "DOC")
    c = db()
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM agreements WHERE agreement_number LIKE %s", (f"{prefix}-{y}-%",))
    n = cur.fetchone()[0] + 1
    c.close()
    return f"{prefix}-{y}-{n:04d}"


def format_value(field: dict, value: Any):
    if value is None:
        return ""
    t = field.get("type")
    if t == "currency":
        try:
            return f"Rs. {float(value):,.0f}"
        except Exception:
            return str(value)
    if t == "date" and value:
        try:
            d = datetime.strptime(str(value), "%Y-%m-%d")
            return d.strftime("%d %B %Y")
        except Exception:
            return str(value)
    return str(value)


def validate_signature_data(image_data: str) -> str:
    match = re.fullmatch(r"data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=\r\n]+)", image_data or "", re.I)
    if not match:
        raise HTTPException(400, "Signature must be a PNG, JPEG or WebP image")
    try:
        decoded = base64.b64decode(match.group(2), validate=True)
    except Exception:
        raise HTTPException(400, "Signature image data is invalid")
    if not decoded or len(decoded) > 3 * 1024 * 1024:
        raise HTTPException(400, "Signature image must be smaller than 3 MB")
    return image_data


def resolve_values(code: str, company: dict, party: Optional[dict], raw: dict[str, Any]):
    dt = doc_type(code)
    values = dict(raw or {})
    auto = {
        "SERVICE_PROVIDER_LEGAL_NAME": company.get("legal_name") or company.get("name") or "",
        "COMPANY_BRAND_NAME": company.get("name") or "",
        "SERVICE_PROVIDER_REGISTERED_ADDRESS": company.get("address") or "",
        "SERVICE_PROVIDER_TAX_ID": company.get("gst") or "",
        "NOTICE_EMAIL_PROVIDER": company.get("email") or "",
        "SERVICE_PROVIDER_SIGNATORY_NAME": values.get("SERVICE_PROVIDER_SIGNATORY_NAME") or company.get("representative") or "",
        "CLIENT_LEGAL_NAME": (party or {}).get("legal_name") or (party or {}).get("name") or "",
        "CLIENT_NAME": (party or {}).get("name") or "",
        "CLIENT_REGISTERED_ADDRESS": (party or {}).get("address") or "",
        "CLIENT_TAX_ID": (party or {}).get("gst") or "",
        "CLIENT_PRIMARY_CONTACT_NAME": (party or {}).get("contact_person") or "",
        "CLIENT_PRIMARY_CONTACT_EMAIL": (party or {}).get("email") or "",
        "NOTICE_EMAIL_CLIENT": (party or {}).get("email") or "",
        "CLIENT_SIGNATORY_NAME": values.get("CLIENT_SIGNATORY_NAME") or (party or {}).get("contact_person") or "",
    }
    values.update({k:v for k,v in auto.items() if not values.get(k)})
    # defaults and display formatting
    fields = {f["key"]: f for f in dt["fields"]}
    for f in dt["fields"]:
        if (values.get(f["key"]) is None or values.get(f["key"]) == "") and f.get("default") not in (None, ""):
            values[f["key"]] = f.get("default")
        elif f["key"] not in values:
            values[f["key"]] = ""
    display = dict(values)
    for k, f in fields.items():
        if k in display:
            display[k] = format_value(f, display[k])
    # auto values are plain text
    return dt, values, display


def render_document(code: str, company: dict, party: Optional[dict], raw: dict[str, Any]):
    dt, values, display = resolve_values(code, company, party, raw)
    body = dt["body_template"]
    replacements = dict(display)
    replacements.update({
        "SERVICE_PROVIDER_LEGAL_NAME": display.get("SERVICE_PROVIDER_LEGAL_NAME") or company.get("legal_name") or company.get("name") or "",
        "CLIENT_LEGAL_NAME": display.get("CLIENT_LEGAL_NAME") or (party or {}).get("legal_name") or (party or {}).get("name") or "",
        "SERVICE_PROVIDER_SIGNATORY_NAME": display.get("SERVICE_PROVIDER_SIGNATORY_NAME", company.get("representative") or ""),
        "CLIENT_SIGNATORY_NAME": display.get("CLIENT_SIGNATORY_NAME", (party or {}).get("contact_person") or ""),
    })
    fields = {f["key"]: f for f in dt["fields"]}
    for k, v in replacements.items():
        field_type = fields.get(k, {}).get("type")
        if field_type == "signature":
            if v:
                validate_signature_data(str(v))
            replacement = f"[[SIGNATURE:{k}]]" if v else "____________________________"
        elif field_type == "image":
            replacement = ""
        else:
            replacement = str(v or "")
        body = re.sub(r"\{\{\s*" + re.escape(k) + r"\s*\}\}", replacement, body, flags=re.I)
    missing = []
    for f in dt["fields"]:
        if f.get("required") and (values.get(f["key"]) is None or str(values.get(f["key"])).strip() == ""):
            missing.append(f["key"])
    unresolved = sorted(set(m.group(1) for m in re.finditer(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}", body)))
    return dt, values, body, sorted(set(missing + unresolved))


@app.get("/api/bootstrap")
def bootstrap():
    agreements = rows("""SELECT a.*, c.name company_name, c.legal_name company_legal_name,
                        p.name party_name, p.legal_name party_legal_name
                        FROM agreements a LEFT JOIN companies c ON c.id=a.company_id LEFT JOIN parties p ON p.id=a.party_id
                        WHERE COALESCE(a.document_type_code,'') <> '' ORDER BY a.id DESC""")
    for a in agreements:
        a["field_values"] = json.loads(a.get("field_values_json") or "{}")
    dts = rows("SELECT code,name,description,renderer_kind,field_schema_json,body_template,template_version,builtin_version,is_customized,metadata_json,updated_at FROM document_types WHERE active=1 ORDER BY CASE code WHEN 'POLICY' THEN 1 WHEN 'NDA' THEN 2 ELSE 3 END, name")
    for d in dts:
        d["fields"] = json.loads(d.pop("field_schema_json") or "[]")
        d["metadata"] = json.loads(d.pop("metadata_json") or "{}")
    return {
        "companies": rows("SELECT * FROM companies ORDER BY name"),
        "parties": rows("SELECT * FROM parties WHERE party_type='Client' ORDER BY name"),
        "signatures": rows("SELECT id,name,image_data,source_type,created_at FROM digital_signatures ORDER BY id DESC"),
        "document_types": dts,
        "agreements": agreements,
        "stats": {
            "total": len(agreements),
            "policy": sum(1 for a in agreements if a.get("document_type_code") == "POLICY"),
            "nda": sum(1 for a in agreements if a.get("document_type_code") == "NDA"),
            "signed": sum(1 for a in agreements if a.get("status") == "Signed"),
        }
    }


@app.post("/api/company")
def create_company(x: CompanyIn):
    c = db()
    cur = c.cursor()
    cur.execute(
        "INSERT INTO companies(name,legal_name,email,phone,address,gst,representative,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (x.name,x.legal_name,x.email,x.phone,x.address,x.gst,x.representative,now_iso())
    )
    i = cur.fetchone()[0]
    c.commit(); c.close()
    return {"id": i}


@app.post("/api/party")
def create_party(x: PartyIn):
    c = db()
    cur = c.cursor()
    cur.execute(
        "INSERT INTO parties(party_type,name,legal_name,contact_person,email,phone,address,gst,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (x.party_type,x.name,x.legal_name,x.contact_person,x.email,x.phone,x.address,x.gst,now_iso())
    )
    i = cur.fetchone()[0]
    c.commit(); c.close()
    return {"id": i}


@app.post("/api/signatures")
def create_signature(x: SignatureIn):
    name = x.name.strip()
    if not name:
        raise HTTPException(400, "Enter a signature name")
    source_type = x.source_type.lower().strip()
    if source_type not in {"drawn", "upload"}:
        raise HTTPException(400, "Signature source must be drawn or upload")
    image_data = validate_signature_data(x.image_data)
    c=db(); cur=c.cursor(); cur.execute(
        "INSERT INTO digital_signatures(name,image_data,source_type,created_at) VALUES(%s,%s,%s,%s) RETURNING id",
        (name,image_data,source_type,now_iso())
    )
    signature_id=cur.fetchone()[0]; c.commit(); c.close()
    return {"id":signature_id,"name":name,"source_type":source_type}


@app.delete("/api/signatures/{signature_id}")
def delete_signature(signature_id: int):
    c=db(); cur=c.cursor(); cur.execute("DELETE FROM digital_signatures WHERE id=%s RETURNING id",(signature_id,))
    deleted=cur.fetchone(); c.commit(); c.close()
    if not deleted: raise HTTPException(404,"Signature not found")
    return {"ok":True}


@app.get("/api/document-types/{code}")
def get_document_type(code: str):
    return doc_type(code)


@app.put("/api/document-types/{code}")
def update_document_type(code: str, x: TemplateUpdate):
    current=doc_type(code)
    keys=[]
    for f in x.fields:
        key=str(f.get("key","")).strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*",key): raise HTTPException(400,f"Invalid variable key: {key or '(blank)'}")
        if key in keys: raise HTTPException(400,f"Duplicate variable key: {key}")
        keys.append(key); f["key"]=key
    unresolved=sorted(set(re.findall(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}",x.body_template)))
    undeclared=[k for k in unresolved if k not in keys]
    if undeclared: raise HTTPException(400,"Declare every variable used in content: "+", ".join(undeclared))
    c=db(); cur=c.cursor(); cur.execute("UPDATE document_types SET body_template=%s,field_schema_json=%s,is_customized=1,template_version=template_version+1,updated_at=%s WHERE code=%s",
                      (x.body_template,json.dumps(x.fields),now_iso(),current["code"])); c.commit(); c.close()
    return doc_type(code)


@app.post("/api/document-types/{code}/reset")
def reset_document_type(code: str):
    fields,body=builtin_template(code); now=now_iso(); c=db(); cur=c.cursor(); cur.execute("UPDATE document_types SET body_template=%s,field_schema_json=%s,is_customized=0,template_version=template_version+1,builtin_version='1.7.0',updated_at=%s WHERE code=%s",
        (body,json.dumps(fields),now,code.upper())); c.commit(); c.close(); return doc_type(code)


@app.post("/api/documents/render")
def render(req: RenderRequest):
    company = one("SELECT * FROM companies WHERE id=?", (req.company_id,))
    if not company: raise HTTPException(400, "Select a valid company")
    party = one("SELECT * FROM parties WHERE id=?", (req.party_id,)) if req.party_id else None
    if req.document_type_code.upper() != "POLICY" and not party: raise HTTPException(400, "Select a client for this document")
    dt, values, body, missing = render_document(req.document_type_code.upper(), company, party, req.field_values)
    return {"document_type": dt["code"], "field_values": values, "content": body, "missing": missing}


@app.post("/api/agreements")
def create_agreement(req: AgreementIn):
    company = one("SELECT * FROM companies WHERE id=?", (req.company_id,))
    if not company: raise HTTPException(400, "Select a valid company")
    party = one("SELECT * FROM parties WHERE id=?", (req.party_id,)) if req.party_id else None
    if req.document_type_code.upper()!="POLICY" and not party: raise HTTPException(400, "Select a client")
    dt, values, rendered, missing = render_document(req.document_type_code.upper(), company, party, req.field_values)
    missing += [m.group(1) for m in re.finditer(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}",req.content or "")]
    missing=sorted(set(missing))
    if missing: raise HTTPException(400, "Complete required fields: " + ", ".join(missing))
    content = req.content.strip() or rendered
    number = next_number(dt["code"]); now = now_iso()
    c=db(); cur=c.cursor(); cur.execute("""
        INSERT INTO agreements(agreement_number,title,agreement_type,company_id,party_id,commercial_model,contract_value,currency,status,content,version,created_at,updated_at,document_type_code,field_values_json,source_template_body)
        VALUES(%s,%s,%s,%s,%s,'',0,'INR','Draft',%s,1,%s,%s,%s,%s,%s) RETURNING id""",
        (number,req.title,dt["name"],req.company_id,req.party_id or 0,content,now,now,dt["code"],json.dumps(values),dt["body_template"]))
    aid=cur.fetchone()[0]; cur.execute("INSERT INTO audit_logs(agreement_id,action,details,created_at) VALUES(%s,%s,%s,%s)",(aid,"Created",f"{dt['name']} created",now)); c.commit(); c.close()
    return {"id":aid,"agreement_number":number}


@app.get("/api/agreements/{aid}")
def get_agreement(aid: int):
    a = one("""SELECT a.*,c.name company_name,c.legal_name company_legal_name,c.email company_email,c.phone company_phone,c.address company_address,c.representative company_representative,
                    p.name party_name,p.legal_name party_legal_name,p.contact_person party_contact,p.address party_address
                    FROM agreements a LEFT JOIN companies c ON c.id=a.company_id LEFT JOIN parties p ON p.id=a.party_id WHERE a.id=?""", (aid,))
    if not a: raise HTTPException(404,"Agreement not found")
    a["field_values"] = json.loads(a.get("field_values_json") or "{}")
    a["audit"] = rows("SELECT * FROM audit_logs WHERE agreement_id=? ORDER BY id DESC", (aid,))
    return a


@app.patch("/api/agreements/{aid}")
def update_agreement(aid: int, x: AgreementUpdate):
    a=one("SELECT * FROM agreements WHERE id=?",(aid,))
    if not a: raise HTTPException(404,"Agreement not found")
    content=x.content if x.content is not None else a.get("content")
    status=x.status if x.status is not None else a.get("status")
    title=x.title if x.title is not None else a.get("title")
    version=(a.get("version") or 1)+1; now=now_iso(); c=db(); cur=c.cursor(); cur.execute("UPDATE agreements SET content=%s,status=%s,title=%s,version=%s,updated_at=%s WHERE id=%s",(content,status,title,version,now,aid)); cur.execute("INSERT INTO audit_logs(agreement_id,action,details,created_at) VALUES(%s,%s,%s,%s)",(aid,"Updated",f"Saved version {version}",now)); c.commit(); c.close(); return {"ok":True,"version":version}


@app.delete("/api/agreements/{aid}")
def delete_agreement(aid: int):
    a=one("SELECT id FROM agreements WHERE id=?",(aid,))
    if not a: raise HTTPException(404,"Agreement not found")
    c=db(); cur=c.cursor()
    cur.execute("DELETE FROM audit_logs WHERE agreement_id=%s",(aid,))
    cur.execute("DELETE FROM agreements WHERE id=%s",(aid,))
    c.commit(); c.close()
    return {"ok":True}


def draw_contact_block(canvas):
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica",6.3)
    canvas.drawString(34, A4[1]-48, "www.sirocotech.com")
    canvas.drawString(34, A4[1]-59, "sales@sirocollc.com")
    canvas.drawString(34, A4[1]-70, "US: (844) 708-0008")
    canvas.drawString(34, A4[1]-81, "IND: (996) 258-7975")


def draw_brand(canvas, x=425, y=718, w=120, h=100):
    p = ASSET_DIR / "brand_lockup.png"
    if p.exists():
        canvas.drawImage(str(p), x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')


def cover_page(canvas, doc):
    canvas.saveState(); W,H=A4
    canvas.setFillColor(NAVY); canvas.rect(0,116,W,H-116,fill=1,stroke=0)
    draw_contact_block(canvas); draw_brand(canvas)
    ctx=getattr(doc,"pdf_context",{})
    prepared=ctx.get("prepared_for",""); title=ctx.get("document_title","DOCUMENT")
    canvas.setFillColor(colors.white); canvas.setFont("Helvetica-Bold",10); canvas.drawCentredString(W/2,350,"PREPARED FOR")
    canvas.setFont("Helvetica-Bold",14); canvas.drawCentredString(W/2,326,prepared.upper())
    canvas.setStrokeColor(colors.HexColor("#2e4b7f")); canvas.setLineWidth(1); canvas.line(W/2-90,307,W/2+90,307)
    canvas.setFont("Helvetica",11); canvas.drawCentredString(W/2,274,title.upper())
    canvas.setFillColor(colors.white); canvas.rect(0,0,W,116,fill=1,stroke=0)
    canvas.setFillColor(NAVY); canvas.setFont("Helvetica-BoldOblique",7.2); canvas.drawCentredString(W/2,77,"Statement of Confidentiality")
    statement="This proposal has been distributed on a confidential basis for your information only. By accepting it, you agree not to disseminate it to any other person or entity and not to use the information for any purpose other than considering opportunities for a cooperative business relationship with the owner of this portfolio."
    style=ParagraphStyle('coverconf',fontName='Helvetica',fontSize=6.1,leading=8,textColor=MUTED,alignment=TA_CENTER)
    para=Paragraph(statement,style); para.wrapOn(canvas,W-70,55); para.drawOn(canvas,35,31)
    canvas.restoreState()


def standard_page(canvas, doc):
    canvas.saveState(); W,H=A4
    canvas.setFillColor(NAVY); canvas.rect(0,H-120,W,120,fill=1,stroke=0)
    draw_contact_block(canvas); draw_brand(canvas,425,H-108,105,85)
    canvas.setFillColor(NAVY); canvas.rect(0,0,W,42,fill=1,stroke=0)
    fl=ASSET_DIR/"footer_logo.png"
    if fl.exists(): canvas.drawImage(str(fl),12,8,width=68,height=26,preserveAspectRatio=True,mask='auto')
    canvas.setFillColor(colors.white); canvas.setFont("Helvetica-Bold",9); canvas.drawRightString(W-28,16,str(canvas.getPageNumber()))
    canvas.restoreState()


def contact_page(canvas, doc):
    canvas.saveState(); W,H=A4; p=ASSET_DIR/"contact_page.png"
    if p.exists(): canvas.drawImage(str(p),0,0,width=W,height=H,preserveAspectRatio=False,mask='auto')
    canvas.setFillColor(NAVY); canvas.rect(W-62,0,62,42,fill=1,stroke=0)
    canvas.setFillColor(colors.white); canvas.setFont("Helvetica-Bold",9); canvas.drawRightString(W-28,16,str(canvas.getPageNumber()))
    canvas.restoreState()


def signature_flowable(value: Any, max_width=112, max_height=34):
    if not value:
        return None
    try:
        raw = str(value).split(',', 1)[-1]
        image_bytes = base64.b64decode(raw)
        reader = ImageReader(BytesIO(image_bytes))
        width, height = reader.getSize()
        scale = min(max_width / width, max_height / height)
        return RLImage(BytesIO(image_bytes), width=width * scale, height=height * scale)
    except Exception:
        return None


def add_content_story(story, content: str, field_values: dict, code: str):
    styles=getSampleStyleSheet()
    title=ParagraphStyle('TitleX',parent=styles['Heading1'],fontName='Helvetica-Bold',fontSize=17,leading=21,textColor=TEXT,spaceAfter=18,alignment=TA_CENTER)
    h2=ParagraphStyle('H2X',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=12.5,leading=16,textColor=TEXT,spaceBefore=10,spaceAfter=7)
    compact=code not in {"POLICY"}
    body=ParagraphStyle('BodyX',parent=styles['BodyText'],fontName='Helvetica',fontSize=8.35 if compact else 9.2,leading=11.8 if compact else 14,textColor=TEXT,spaceAfter=6 if compact else 8)
    bullet=ParagraphStyle('BulletX',parent=body,leftIndent=14,firstLineIndent=-8,spaceAfter=5)
    lines=[l.rstrip() for l in content.splitlines()]
    first=True
    photo_added=False
    index=0
    while index < len(lines):
        line=lines[index]
        index += 1
        s=line.strip()
        if s=="[[TABLE]]":
            raw_rows=[]
            while index < len(lines) and lines[index].strip()!="[[/TABLE]]":
                if lines[index].strip(): raw_rows.append([cell.strip() for cell in lines[index].split("||")])
                index += 1
            if index < len(lines): index += 1
            if raw_rows:
                column_count=max(len(row) for row in raw_rows)
                for row in raw_rows: row.extend([""]*(column_count-len(row)))
                signature=column_count==4 and any("SERVICE PROVIDER" in cell.upper() for cell in raw_rows[0])
                if signature: widths=[92,143,92,143]
                elif column_count==2: widths=[165,305]
                elif column_count==3: widths=[150,150,170]
                else: widths=[470/column_count]*column_count
                cell_style=ParagraphStyle('TableCellX',parent=body,fontSize=7.35 if column_count>=5 else 7.8,leading=9.4,spaceAfter=0)
                head_style=ParagraphStyle('TableHeadX',parent=cell_style,fontName='Helvetica-Bold',textColor=colors.white)
                rendered_rows=[]
                for row_no,row in enumerate(raw_rows):
                    rendered_row=[]
                    for cell in row:
                        signature_match=re.fullmatch(r"\[\[SIGNATURE:([A-Z][A-Z0-9_]*)\]\]",cell)
                        signature=signature_flowable(field_values.get(signature_match.group(1))) if signature_match else None
                        if signature_match:
                            rendered_row.append(signature or Paragraph("____________________________",cell_style))
                        else:
                            rendered_row.append(Paragraph(cell.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('\n','<br/>'),head_style if row_no==0 else cell_style))
                    rendered_rows.append(rendered_row)
                table=Table(rendered_rows,colWidths=widths,repeatRows=1,hAlign='LEFT',splitByRow=0 if signature else 1)
                commands=[
                    ('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
                    ('GRID',(0,0),(-1,-1),0.45,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                    ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
                    ('TOPPADDING',(0,0),(-1,-1),3.5),('BOTTOMPADDING',(0,0),(-1,-1),3.5),
                ]
                for row_no in range(1,len(rendered_rows)):
                    if row_no%2==0: commands.append(('BACKGROUND',(0,row_no),(-1,row_no),colors.HexColor('#f4f6f9')))
                table.setStyle(TableStyle(commands)); story.append(KeepTogether([table]) if signature else table); story.append(Spacer(1,8))
            continue
        if s=="[[PAGEBREAK]]": story.append(PageBreak()); continue
        if not s:
            story.append(Spacer(1,5)); continue
        if s.startswith("[[H1]]"):
            heading=s[len("[[H1]]"):].strip(); esc=heading.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            story.append(Paragraph(esc,title)); first=False; continue
        if s.startswith("[[H2]]"):
            heading=s[len("[[H2]]"):].strip(); esc=heading.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            story.append(Paragraph(esc,h2)); first=False; continue
        signature_line=re.fullmatch(r"Signature:\s*\[\[SIGNATURE:([A-Z][A-Z0-9_]*)\]\]",s)
        if signature_line:
            signature=signature_flowable(field_values.get(signature_line.group(1)),112,34)
            signature_cell=signature or Paragraph("____________________________",body)
            signature_table=Table([[Paragraph("Signature:",body),signature_cell]],colWidths=[58,145],hAlign='LEFT')
            signature_table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1)]))
            story.append(signature_table)
            continue
        esc=(s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))
        if first:
            story.append(Paragraph(esc,title)); first=False
            continue
        if code=="POLICY" and s.upper().startswith("DEAR "):
            photo=None
            if field_values.get("EMPLOYEE_PHOTO"):
                try:
                    raw=str(field_values["EMPLOYEE_PHOTO"]).split(',',1)[-1]; photo=RLImage(BytesIO(base64.b64decode(raw)),width=60,height=73)
                except Exception: photo=None
            if photo is None:
                photo=Table([[Paragraph("Photo",ParagraphStyle('PhotoX',fontName='Helvetica',fontSize=7,textColor=colors.HexColor('#888888'),alignment=TA_CENTER))]],colWidths=[60],rowHeights=[73])
                photo.setStyle(TableStyle([('BOX',(0,0),(-1,-1),.5,colors.HexColor('#8a8a8a')),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
            greeting=Paragraph(esc,ParagraphStyle('GreetingX',parent=body,fontName='Helvetica-Bold',fontSize=10.5))
            t=Table([[greeting,photo]],colWidths=[410,60]); t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
            story.append(t); story.append(Spacer(1,8)); photo_added=True; continue
        numbered=re.match(r"^(\d+)\.\s+([^:]+:)(.*)$",s)
        if code=="POLICY" and numbered:
            n,label,rest=numbered.groups(); html="<b>"+label.replace('&','&amp;')+"</b>"+rest.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            t=Table([[Paragraph(n+".",ParagraphStyle('NumX',parent=body,fontName='Helvetica-Bold')),Paragraph(html,body)]],colWidths=[28,442])
            t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),7)])); story.append(t); continue
        if code=="POLICY" and s.upper()=="INTERN RESIGNATION POLICY":
            story.append(Spacer(1,3)); story.append(Table([[""]],colWidths=[470],rowHeights=[1],style=[('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#e3e6eb'))])); story.append(Spacer(1,12)); story.append(Paragraph(esc,h2)); continue
        if code=="POLICY" and s.upper()=="INTERN RESIGNATION POLICY (CONTD.)":
            story.append(Paragraph(esc,title)); continue
        if code=="POLICY" and s.upper()=="AUTHORIZED SIGNATORY":
            story.append(Spacer(1,8))
            signature=signature_flowable(field_values.get("AUTHORIZED_SIGNATURE_IMAGE"),80,32)
            if signature: story.append(signature)
            sigline=Table([[""]],colWidths=[150],rowHeights=[1],style=[('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#aeb4bf'))]); sigline.hAlign='LEFT'
            story.append(sigline); story.append(Spacer(1,6)); story.append(Paragraph(esc,body)); continue
        if re.match(r"^\d+(?:\.\d+)+\s",s) or re.match(r"^\d+\.\s",s) or s.upper() in {"INTERN RESIGNATION POLICY","FAILURE TO SERVE NOTICE PERIOD:","EXAMPLE CASES","EARLY RESIGNATION"} or s.endswith("Policy:"):
            story.append(Paragraph(esc,h2))
        elif s.startswith("-"):
            story.append(Paragraph("- "+esc.lstrip("- "),bullet))
        else:
            story.append(Paragraph(esc,body))


def build_pdf(a: dict):
    buf=BytesIO(); W,H=A4
    doc=BaseDocTemplate(buf,pagesize=A4,leftMargin=42,rightMargin=42,topMargin=138,bottomMargin=58)
    code=a.get("document_type_code") or ""
    item=BUILTIN_TEMPLATE_MAP.get(code,{})
    doc.pdf_context={
        "prepared_for": a.get("field_values",{}).get("EMPLOYEE_NAME") if a.get("document_type_code")=="POLICY" else (a.get("party_legal_name") or a.get("party_name") or "CLIENT"),
        "document_title": "Policy Agreement Document" if code=="POLICY" else ("Client Engagement Agreement NDA Document" if code=="NDA" else item.get("name",a.get("agreement_type") or "Document")),
    }
    cover_frame=Frame(0,0,W,H,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,id='coverframe')
    content_frame=Frame(42,58,W-84,H-196,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,id='contentframe')
    contact_frame=Frame(0,0,W,H,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,id='contactframe')
    doc.addPageTemplates([
        PageTemplate(id='cover',frames=[cover_frame],onPage=cover_page),
        PageTemplate(id='content',frames=[content_frame],onPage=standard_page,autoNextPageTemplate='content'),
        PageTemplate(id='contact',frames=[contact_frame],onPage=contact_page),
    ])
    story=[Spacer(1,H-30),NextPageTemplate('content'),PageBreak()]
    add_content_story(story,a.get("content") or "",a.get("field_values") or {},a.get("document_type_code") or "")
    story += [NextPageTemplate('contact'),PageBreak(),Spacer(1,H-20)]
    doc.build(story)
    buf.seek(0); return buf


def preview_record(code: str, content: str, values: dict, company: dict, party: Optional[dict]):
    return {
        "document_type_code":code,
        "content":content,
        "field_values":values,
        "company_name":company.get("name","") if company else "",
        "company_legal_name":company.get("legal_name","") if company else "",
        "party_name":(party or {}).get("name",""),
        "party_legal_name":(party or {}).get("legal_name",""),
    }


@app.post("/api/documents/preview.pdf")
def document_preview_pdf(req: RenderRequest):
    company=one("SELECT * FROM companies WHERE id=?",(req.company_id,))
    if not company: raise HTTPException(400,"Select a valid company")
    party=one("SELECT * FROM parties WHERE id=?",(req.party_id,)) if req.party_id else None
    if req.document_type_code.upper()!="POLICY" and not party: raise HTTPException(400,"Select a client for this document")
    dt,values,rendered,missing=render_document(req.document_type_code,company,party,req.field_values)
    content=req.content if req.content is not None else rendered
    unresolved=sorted(set(re.findall(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}",content)))
    missing=sorted(set(missing+unresolved))
    buf=build_pdf(preview_record(dt["code"],content,values,company,party))
    return StreamingResponse(buf,media_type="application/pdf",headers={"X-Missing-Fields":",".join(missing),"Content-Disposition":"inline; filename=preview.pdf"})


@app.get("/api/document-types/{code}/preview.pdf")
def template_preview_pdf(code: str):
    dt=doc_type(code); fields=dt["fields"]
    sample={f["key"]:("____________________________" if f.get("type") in {"signature","image"} else (f.get("default") if f.get("default") not in (None,"") else f"[{f.get('label',f['key'])}]")) for f in fields}
    company={"name":"VTAB Square","legal_name":"VTAB Square Private Limited"}
    party={"name":"Client Name","legal_name":"Client Legal Name"}
    content=dt["body_template"]
    for k,v in sample.items(): content=re.sub(r"\{\{\s*"+re.escape(k)+r"\s*\}\}",str(v),content,flags=re.I)
    buf=build_pdf(preview_record(dt["code"],content,sample,company,party))
    return StreamingResponse(buf,media_type="application/pdf",headers={"Content-Disposition":f"inline; filename={code.lower()}-template-preview.pdf"})


@app.get("/api/agreements/{aid}/pdf")
def agreement_pdf(aid: int):
    a=get_agreement(aid)
    buf=build_pdf(a)
    filename=re.sub(r"[^A-Za-z0-9_.-]+","_",f"{a['agreement_number']}_{a['title']}.pdf")
    return StreamingResponse(buf,media_type="application/pdf",headers={"Content-Disposition":f'inline; filename="{filename}"'})


@app.get("/api/health")
def health(): return {"ok":True,"version":"1.7.0"}
