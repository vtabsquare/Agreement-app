from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from io import BytesIO
import sqlite3, json, re

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

import os

APP_NAME = "Aurelia Contract Studio"
DB_PATH = "agreement_studio.db"
app = FastAPI(title=APP_NAME, version="1.3.0")
_frontend_url = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5173")
_cors_origins = list({"http://localhost:5173", "http://127.0.0.1:5173", _frontend_url})
app.add_middleware(CORSMiddleware, allow_origins=_cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def db():
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row; return conn

def ensure_column(conn, table, column, definition):
    cols={r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    if column not in cols: conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def default_fields(kind):
    common=[
      {"key":"AGREEMENT_DATE","label":"Agreement date","type":"date","required":True,"source":"manual"},
      {"key":"PURPOSE","label":"Purpose / project context","type":"multiline","required":True,"source":"manual"},
      {"key":"GOVERNING_LAW","label":"Governing law / jurisdiction","type":"text","required":True,"default":"Tamil Nadu, India","source":"manual"},
    ]
    if kind=="NDA": return common+[
      {"key":"DISCLOSING_PERSON","label":"Disclosing representative","type":"text","required":True,"source":"manual"},
      {"key":"RECEIVING_PERSON","label":"Receiving representative","type":"text","required":True,"source":"manual"},
      {"key":"CONFIDENTIALITY_PERIOD","label":"Confidentiality period","type":"select","required":True,"options":["1 year","2 years","3 years","5 years","Perpetual"],"default":"3 years","source":"manual"}
    ]
    return common+[{"key":"PROJECT_NAME","label":"Project / engagement name","type":"text","required":True,"source":"manual"}]

def init_db():
    conn=db(); conn.executescript("""
    CREATE TABLE IF NOT EXISTS companies(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,legal_name TEXT,email TEXT,phone TEXT,address TEXT,gst TEXT,representative TEXT,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS parties(id INTEGER PRIMARY KEY AUTOINCREMENT,party_type TEXT NOT NULL,name TEXT NOT NULL,legal_name TEXT,contact_person TEXT,email TEXT,phone TEXT,address TEXT,gst TEXT,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS templates(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,agreement_type TEXT NOT NULL,description TEXT,body TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS agreements(id INTEGER PRIMARY KEY AUTOINCREMENT,agreement_number TEXT NOT NULL UNIQUE,title TEXT NOT NULL,agreement_type TEXT NOT NULL,template_id INTEGER,company_id INTEGER NOT NULL,party_id INTEGER NOT NULL,commercial_model TEXT NOT NULL,contract_value REAL NOT NULL DEFAULT 0,currency TEXT NOT NULL DEFAULT 'INR',effective_date TEXT,end_date TEXT,status TEXT NOT NULL DEFAULT 'Draft',scope TEXT,deliverables_json TEXT,commercial_json TEXT,content TEXT,version INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS audit_logs(id INTEGER PRIMARY KEY AUTOINCREMENT,agreement_id INTEGER NOT NULL,action TEXT NOT NULL,details TEXT,created_at TEXT NOT NULL);
    """)
    ensure_column(conn,"templates","fields_json","TEXT")
    ensure_column(conn,"templates","updated_at","TEXT")
    ensure_column(conn,"agreements","placeholder_values_json","TEXT")
    ensure_column(conn,"agreements","source_template_body","TEXT")
    now=datetime.utcnow().isoformat()
    if conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]==0:
        conn.execute("INSERT INTO companies(name,legal_name,email,phone,address,gst,representative,created_at) VALUES(?,?,?,?,?,?,?,?)",("VTAB Square","VTAB Square Private Limited","legal@company.com","+91 90000 00000","Coimbatore, Tamil Nadu, India","33AAAAA0000A1Z5","Authorized Signatory",now))
    if conn.execute("SELECT COUNT(*) FROM parties").fetchone()[0]==0:
        conn.executemany("INSERT INTO parties(party_type,name,legal_name,contact_person,email,phone,address,gst,created_at) VALUES(?,?,?,?,?,?,?,?,?)",[("Client","Acme Digital","Acme Digital Private Limited","Arun Kumar","arun@example.com","+91 98888 11111","Chennai, Tamil Nadu","33BBBBB0000B1Z5",now),("Vendor","Orbit Consulting","Orbit Consulting LLP","Meera S","meera@example.com","+91 97777 22222","Bengaluru, Karnataka","29CCCCC0000C1Z5",now)])
    if conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]==0:
        service="""SERVICE AGREEMENT\n\nThis Agreement dated {{AGREEMENT_DATE}} is entered into between {{OUR_COMPANY_LEGAL_NAME}} (\"Service Provider\") and {{PARTY_LEGAL_NAME}} (\"Client\") for {{PROJECT_NAME}}.\n\n1. PURPOSE\n{{PURPOSE}}\n\n2. SCOPE OF WORK\n{{SCOPE}}\n\n3. DELIVERABLES\n{{DELIVERABLES}}\n\n4. COMMERCIAL TERMS\n{{COMMERCIAL_TERMS}}\n\n5. CONFIDENTIALITY\nEach party shall protect confidential information received from the other party.\n\n6. TERMINATION\nEither party may terminate with thirty (30) days' written notice.\n\n7. GOVERNING LAW\nThis Agreement shall be governed by {{GOVERNING_LAW}}.\n\nSIGNATURES\nFor {{OUR_COMPANY_LEGAL_NAME}}\n{{OUR_REPRESENTATIVE}}\n\nFor {{PARTY_LEGAL_NAME}}\n{{PARTY_CONTACT}}\n"""
        vendor=service.replace("SERVICE AGREEMENT","VENDOR AGREEMENT").replace('(\"Client\")','(\"Vendor\")')
        nda="""MUTUAL NON-DISCLOSURE AGREEMENT\n\nThis Mutual NDA dated {{AGREEMENT_DATE}} is entered into between {{OUR_COMPANY_LEGAL_NAME}}, represented by {{DISCLOSING_PERSON}}, and {{PARTY_LEGAL_NAME}}, represented by {{RECEIVING_PERSON}}.\n\n1. PURPOSE\nThe parties wish to exchange confidential information for the following purpose:\n{{PURPOSE}}\n\n2. CONFIDENTIAL INFORMATION\nConfidential Information includes non-public business, commercial, financial, technical, operational, customer, product and project information disclosed in any form.\n\n3. OBLIGATIONS\nEach receiving party shall protect Confidential Information using reasonable safeguards and use it only for the Purpose.\n\n4. EXCLUSIONS\nInformation that is public, independently developed, lawfully received from a third party, or already known without restriction is excluded.\n\n5. TERM\nConfidentiality obligations survive for {{CONFIDENTIALITY_PERIOD}} from the date of disclosure or termination, as applicable.\n\n6. RETURN OR DESTRUCTION\nUpon request, each party shall return or destroy confidential materials subject to legal retention obligations.\n\n7. GOVERNING LAW\nThis NDA shall be governed by {{GOVERNING_LAW}}.\n\nSIGNATURES\nFor {{OUR_COMPANY_LEGAL_NAME}}\n{{DISCLOSING_PERSON}}\n\nFor {{PARTY_LEGAL_NAME}}\n{{RECEIVING_PERSON}}\n"""
        conn.executemany("INSERT INTO templates(name,agreement_type,description,body,active,fields_json,updated_at) VALUES(?,?,?,?,1,?,?)",[("Client Services Agreement","Client Agreement","Reusable service agreement for client engagements",service,json.dumps(default_fields("Client Agreement")),now),("Vendor Services Agreement","Vendor Agreement","Reusable agreement for vendors and subcontractors",vendor,json.dumps(default_fields("Vendor Agreement")),now),("Mutual NDA","NDA","Mutual confidentiality agreement with dynamic NDA-specific fields",nda,json.dumps(default_fields("NDA")),now),("Custom Agreement","Custom","Blank structured agreement for custom use",service,json.dumps(default_fields("Custom")),now)])
    else:
        # backfill metadata for older V1.x databases
        for r in conn.execute("SELECT id,agreement_type,fields_json FROM templates").fetchall():
            if not r["fields_json"]: conn.execute("UPDATE templates SET fields_json=?,updated_at=? WHERE id=?",(json.dumps(default_fields(r["agreement_type"])),now,r["id"]))
    conn.commit(); conn.close()
init_db()

class CompanyIn(BaseModel):
    name:str; legal_name:str=""; email:str=""; phone:str=""; address:str=""; gst:str=""; representative:str=""
class PartyIn(BaseModel):
    party_type:str; name:str; legal_name:str=""; contact_person:str=""; email:str=""; phone:str=""; address:str=""; gst:str=""
class TemplateField(BaseModel):
    key:str; label:str; type:str="text"; required:bool=True; default:Any=""; options:List[str]=Field(default_factory=list); source:str="manual"
class TemplateIn(BaseModel):
    name:str; agreement_type:str; description:str=""; body:str; fields:List[TemplateField]=Field(default_factory=list); active:bool=True
class RenderRequest(BaseModel):
    company_id:int; party_id:int; agreement_type:str=""; effective_date:str=""; end_date:str=""; scope:str=""; commercial_model:str="Fixed Bid"; contract_value:float=0; currency:str="INR"; deliverables:List[Dict[str,Any]]=Field(default_factory=list); commercial_data:Dict[str,Any]=Field(default_factory=dict); placeholder_values:Dict[str,Any]=Field(default_factory=dict)
class AgreementIn(RenderRequest):
    title:str; template_id:Optional[int]=None; content:str=""
class AgreementUpdate(BaseModel):
    status:Optional[str]=None; content:Optional[str]=None; title:Optional[str]=None
class AIRequest(BaseModel): action:str; text:str

def rows(q,p=()):
    c=db(); x=[dict(r) for r in c.execute(q,p).fetchall()]; c.close(); return x
def one(q,p=()):
    c=db(); r=c.execute(q,p).fetchone(); c.close(); return dict(r) if r else None
def template_dict(r):
    if not r:return None
    r=dict(r); r["fields"]=json.loads(r.get("fields_json") or "[]"); return r
def next_agreement_number():
    y=datetime.now().year;c=db();n=c.execute("SELECT COUNT(*) FROM agreements WHERE agreement_number LIKE ?",(f"AGR-{y}-%",)).fetchone()[0]+1;c.close();return f"AGR-{y}-{n:04d}"
def format_money(v,c):
    s={"INR":"₹","USD":"$","EUR":"€","GBP":"£"}.get(c,c+" "); return f"{s}{v:,.2f}"
def commercial_text(model,value,currency,data):
    lines=[f"Commercial Model: {model}"]
    if value:lines.append(f"Contract Value: {format_money(value,currency)}")
    if model=="Milestone Based":
        for i,m in enumerate(data.get("milestones",[]),1):lines.append(f"Milestone {i}: {m.get('name','')} - {m.get('percentage',0)}% - {m.get('amount',0)}")
    elif model=="Time & Material":
        for r in data.get("resources",[]):lines.append(f"{r.get('role','Resource')}: {r.get('rate',0)} per {r.get('unit','hour')}")
    elif model=="Hybrid (FB + T&M)":lines += [f"Fixed Bid Component: {data.get('fixed_bid',value)}",f"T&M Rate: {data.get('tm_rate',0)} per {data.get('tm_unit','hour')}"]
    elif data.get("payment_terms"): lines.append(f"Payment Terms: {data['payment_terms']}")
    return "\n".join(lines)

def base_values(company,party,a):
    deliverables="\n".join(f"{i+1}. {d.get('name','Deliverable')} — {d.get('description','')} — Target: {d.get('target_date','TBD')}" for i,d in enumerate(a.get("deliverables",[]))) or "To be mutually agreed."
    return {"OUR_COMPANY_NAME":company.get("name", ""),"OUR_COMPANY_LEGAL_NAME":company.get("legal_name") or company.get("name", ""),"OUR_COMPANY_ADDRESS":company.get("address", ""),"OUR_REPRESENTATIVE":company.get("representative", ""),"PARTY_NAME":party.get("name", ""),"PARTY_LEGAL_NAME":party.get("legal_name") or party.get("name", ""),"PARTY_ADDRESS":party.get("address", ""),"PARTY_CONTACT":party.get("contact_person", ""),"EFFECTIVE_DATE":a.get("effective_date", "") or "[Effective Date]","END_DATE":a.get("end_date", "") or "[End Date]","SCOPE":a.get("scope", "") or "[Scope of Work]","DELIVERABLES":deliverables,"COMMERCIAL_TERMS":commercial_text(a.get("commercial_model",""),a.get("contract_value",0),a.get("currency","INR"),a.get("commercial_data",{}))}
def render_template(body,company,party,a):
    vals=base_values(company,party,a); vals.update({str(k).upper():v for k,v in (a.get("placeholder_values") or {}).items()})
    return re.sub(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}",lambda m:str(vals.get(m.group(1).upper(),m.group(0))),body)
def extract_tokens(body): return sorted(set(x.upper() for x in re.findall(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}",body)))
def unresolved(body): return extract_tokens(body)

@app.get("/api/health")
def health():return {"ok":True,"app":APP_NAME,"version":"1.3.0"}
@app.get("/api/bootstrap")
def bootstrap():
    ag=rows("SELECT a.*,c.name company_name,p.name party_name FROM agreements a LEFT JOIN companies c ON c.id=a.company_id LEFT JOIN parties p ON p.id=a.party_id ORDER BY a.id DESC")
    ts=[template_dict(x) for x in rows("SELECT * FROM templates WHERE active=1 ORDER BY id")]
    return {"companies":rows("SELECT * FROM companies ORDER BY id DESC"),"parties":rows("SELECT * FROM parties ORDER BY id DESC"),"templates":ts,"agreements":ag,"stats":{"total":len(ag),"draft":sum(x['status']=='Draft' for x in ag),"active":sum(x['status']=='Active' for x in ag),"signed":sum(x['status']=='Signed' for x in ag)}}
@app.post("/api/companies")
def create_company(item:CompanyIn):
    c=db();cur=c.execute("INSERT INTO companies(name,legal_name,email,phone,address,gst,representative,created_at) VALUES(?,?,?,?,?,?,?,?)",(*item.model_dump().values(),datetime.utcnow().isoformat()));c.commit();i=cur.lastrowid;c.close();return one("SELECT * FROM companies WHERE id=?",(i,))
@app.post("/api/parties")
def create_party(item:PartyIn):
    c=db();cur=c.execute("INSERT INTO parties(party_type,name,legal_name,contact_person,email,phone,address,gst,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(*item.model_dump().values(),datetime.utcnow().isoformat()));c.commit();i=cur.lastrowid;c.close();return one("SELECT * FROM parties WHERE id=?",(i,))

@app.post("/api/templates")
def create_template(item:TemplateIn):
    keys=[f.key.upper().strip() for f in item.fields]
    if len(keys)!=len(set(keys)): raise HTTPException(400,"Placeholder field keys must be unique")
    c=db();cur=c.execute("INSERT INTO templates(name,agreement_type,description,body,active,fields_json,updated_at) VALUES(?,?,?,?,?,?,?)",(item.name,item.agreement_type,item.description,item.body,1 if item.active else 0,json.dumps([f.model_dump()|{'key':f.key.upper().strip()} for f in item.fields]),datetime.utcnow().isoformat()));c.commit();i=cur.lastrowid;c.close();return template_dict(one("SELECT * FROM templates WHERE id=?",(i,)))
@app.put("/api/templates/{template_id}")
def update_template(template_id:int,item:TemplateIn):
    if not one("SELECT id FROM templates WHERE id=?",(template_id,)):raise HTTPException(404,"Template not found")
    keys=[f.key.upper().strip() for f in item.fields]
    if len(keys)!=len(set(keys)): raise HTTPException(400,"Placeholder field keys must be unique")
    c=db();c.execute("UPDATE templates SET name=?,agreement_type=?,description=?,body=?,active=?,fields_json=?,updated_at=? WHERE id=?",(item.name,item.agreement_type,item.description,item.body,1 if item.active else 0,json.dumps([f.model_dump()|{'key':f.key.upper().strip()} for f in item.fields]),datetime.utcnow().isoformat(),template_id));c.commit();c.close();return template_dict(one("SELECT * FROM templates WHERE id=?",(template_id,)))
@app.delete("/api/templates/{template_id}")
def delete_template(template_id:int):
    c=db();c.execute("UPDATE templates SET active=0,updated_at=? WHERE id=?",(datetime.utcnow().isoformat(),template_id));c.commit();c.close();return {"ok":True}
@app.get("/api/templates/{template_id}")
def get_template(template_id:int):
    t=template_dict(one("SELECT * FROM templates WHERE id=?",(template_id,))); 
    if not t:raise HTTPException(404,"Template not found")
    t["tokens"]=extract_tokens(t["body"]);return t
@app.post("/api/templates/{template_id}/render")
def render_preview(template_id:int,item:RenderRequest):
    t=template_dict(one("SELECT * FROM templates WHERE id=?",(template_id,)));company=one("SELECT * FROM companies WHERE id=?",(item.company_id,));party=one("SELECT * FROM parties WHERE id=?",(item.party_id,))
    if not t or not company or not party:raise HTTPException(400,"Template, company or party not found")
    content=render_template(t["body"],company,party,item.model_dump());return {"content":content,"unresolved":unresolved(content),"tokens":extract_tokens(t["body"])}

@app.post("/api/agreements")
def create_agreement(item:AgreementIn):
    company=one("SELECT * FROM companies WHERE id=?",(item.company_id,));party=one("SELECT * FROM parties WHERE id=?",(item.party_id,));template=template_dict(one("SELECT * FROM templates WHERE id=?",(item.template_id,))) if item.template_id else None
    if not company or not party:raise HTTPException(400,"Company or party not found")
    if not template:raise HTTPException(400,"Template not found")
    payload=item.model_dump()
    if item.commercial_model=="Milestone Based":
        ms=payload["commercial_data"].get("milestones",[]);total=sum(float(m.get("percentage",0) or 0) for m in ms)
        if ms and abs(total-100)>0.01:raise HTTPException(400,f"Milestone percentages must total 100%. Current total: {total}%")
    rendered=render_template(template["body"],company,party,payload);content=item.content.strip() or rendered
    missing=unresolved(content)
    if missing:raise HTTPException(400,"Unresolved placeholders: "+", ".join(missing))
    number=next_agreement_number();now=datetime.utcnow().isoformat();c=db();cur=c.execute("INSERT INTO agreements(agreement_number,title,agreement_type,template_id,company_id,party_id,commercial_model,contract_value,currency,effective_date,end_date,status,scope,deliverables_json,commercial_json,content,version,created_at,updated_at,placeholder_values_json,source_template_body) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(number,item.title,item.agreement_type,item.template_id,item.company_id,item.party_id,item.commercial_model,item.contract_value,item.currency,item.effective_date,item.end_date,"Draft",item.scope,json.dumps(item.deliverables),json.dumps(item.commercial_data),content,1,now,now,json.dumps(item.placeholder_values),template["body"]));aid=cur.lastrowid;c.execute("INSERT INTO audit_logs(agreement_id,action,details,created_at) VALUES(?,?,?,?)",(aid,"Agreement Created",number,now));c.commit();c.close();return {"id":aid,"agreement_number":number,"content":content}
@app.get("/api/agreements/{agreement_id}")
def get_agreement(agreement_id:int):
    a=one("SELECT a.*,c.name company_name,c.legal_name company_legal_name,p.name party_name,p.legal_name party_legal_name FROM agreements a LEFT JOIN companies c ON c.id=a.company_id LEFT JOIN parties p ON p.id=a.party_id WHERE a.id=?",(agreement_id,))
    if not a:raise HTTPException(404,"Agreement not found")
    a["deliverables"]=json.loads(a.get("deliverables_json") or "[]");a["commercial_data"]=json.loads(a.get("commercial_json") or "{}");a["placeholder_values"]=json.loads(a.get("placeholder_values_json") or "{}");a["audit"]=rows("SELECT * FROM audit_logs WHERE agreement_id=? ORDER BY id DESC",(agreement_id,));return a
@app.patch("/api/agreements/{agreement_id}")
def update_agreement(agreement_id:int,item:AgreementUpdate):
    current=one("SELECT * FROM agreements WHERE id=?",(agreement_id,));
    if not current:raise HTTPException(404,"Agreement not found")
    up=[];vals=[]
    for k,v in item.model_dump(exclude_none=True).items():up.append(f"{k}=?");vals.append(v)
    if not up:return current
    nv=current["version"]+(1 if item.content is not None else 0);up += ["version=?","updated_at=?"];vals += [nv,datetime.utcnow().isoformat(),agreement_id];c=db();c.execute(f"UPDATE agreements SET {', '.join(up)} WHERE id=?",vals);c.execute("INSERT INTO audit_logs(agreement_id,action,details,created_at) VALUES(?,?,?,?)",(agreement_id,"Agreement Content Updated" if item.content is not None else "Agreement Updated",f"Version {nv}",datetime.utcnow().isoformat()));c.commit();c.close();return get_agreement(agreement_id)
@app.post("/api/agreements/{agreement_id}/save-as-template")
def save_agreement_as_template(agreement_id:int):
    a=get_agreement(agreement_id);tid=a.get("template_id")
    if not tid:raise HTTPException(400,"Agreement has no source template")
    c=db();c.execute("UPDATE templates SET body=?,updated_at=? WHERE id=?",(a["content"],datetime.utcnow().isoformat(),tid));c.execute("INSERT INTO audit_logs(agreement_id,action,details,created_at) VALUES(?,?,?,?)",(agreement_id,"Master Template Updated",f"Template {tid}",datetime.utcnow().isoformat()));c.commit();c.close();return {"ok":True}
@app.post("/api/ai")
def ai_assist(item:AIRequest):
    text=item.text.strip()
    if not text:return {"result":""}
    if item.action=="professional":result="The Parties agree that "+text[0].lower()+text[1:] if len(text)>1 else text
    elif item.action=="scope":result="The Service Provider shall perform the following services in accordance with the agreed timelines, requirements and acceptance criteria:\n\n"+text
    elif item.action=="payment":result="The Client shall pay all undisputed invoices within thirty (30) calendar days from the invoice date, subject to the commercial schedule set out in this Agreement."
    elif item.action=="termination":result="Either Party may terminate this Agreement by giving thirty (30) days' prior written notice. A material breach may permit earlier termination if the breach remains uncured after written notice."
    elif item.action=="review":
        warnings=[];low=text.lower()
        for w,l in [("termination","Termination clause"),("payment","Payment terms"),("confidential","Confidentiality clause"),("governing","Governing law")]:
            if w not in low:warnings.append(f"Missing or unclear: {l}")
        result="Review complete. "+("No obvious structural omissions detected." if not warnings else " | ".join(warnings))
    else:result=text
    return {"result":result,"mode":"local-mock","note":"Replace this endpoint with your approved AI provider later; no secret keys are bundled."}
@app.get("/api/agreements/{agreement_id}/pdf")
def agreement_pdf(agreement_id:int):
    a=get_agreement(agreement_id);buffer=BytesIO();doc=SimpleDocTemplate(buffer,pagesize=A4,rightMargin=48,leftMargin=48,topMargin=52,bottomMargin=52,title=a["title"]);styles=getSampleStyleSheet();title=ParagraphStyle("ContractTitle",parent=styles["Title"],fontName="Helvetica-Bold",fontSize=20,leading=24,alignment=TA_CENTER,textColor=colors.HexColor("#28243D"),spaceAfter=18);body=ParagraphStyle("ContractBody",parent=styles["BodyText"],fontSize=10,leading=15,textColor=colors.HexColor("#262636"),spaceAfter=8);story=[Paragraph(a["title"],title)];meta=[["Agreement No.",a["agreement_number"],"Status",a["status"]],["Company",a.get("company_name",""),"Counterparty",a.get("party_name","")],["Effective",a.get("effective_date") or "—","End",a.get("end_date") or "—"]];t=Table(meta,colWidths=[72,150,60,150]);t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F4F3FA")),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#D8D6E3")),("FONTSIZE",(0,0),(-1,-1),8),("VALIGN",(0,0),(-1,-1),"TOP")]));story += [t,Spacer(1,20)]
    for raw in (a.get("content") or "").splitlines():
        line=raw.strip()
        if not line:story.append(Spacer(1,7));continue
        safe=line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        story.append(Paragraph(safe,styles["Heading2"] if line.isupper() and len(line)<80 else body))
    doc.build(story);buffer.seek(0);fn=f"{a['agreement_number']}_{a['title'].replace(' ','_')}.pdf";return StreamingResponse(buffer,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="{fn}"'})
