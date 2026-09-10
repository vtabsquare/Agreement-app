from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main


def values_for(code):
    values = {}
    for field in main.doc_type(code)["fields"]:
        if field.get("default") not in (None, ""):
            value = field["default"]
        elif field["type"] == "date":
            value = "2026-09-09"
        elif field["type"] in {"number", "currency"}:
            value = 1
        elif field["type"] == "image":
            value = ""
        else:
            value = {
                "EMPLOYEE_NAME": "VASANTH KUMAR T",
                "SERVICE_PROVIDER_LEGAL_NAME": "VTAB Square Private Limited",
                "COMPANY_BRAND_NAME": "VTAB Square",
                "CLIENT_LEGAL_NAME": "Aurelia Client Private Limited",
                "CLIENT_NAME": "Aurelia Client",
                "NDA_PURPOSE": "a confidential technology services engagement",
            }.get(field["key"], f"Sample {field['label']}")
        values[field["key"]] = value
    return values


def make(code, output):
    values = values_for(code)
    company = {"name": "VTAB Square", "legal_name": "VTAB Square Private Limited"}
    party = {"name": "Aurelia Client", "legal_name": "Aurelia Client Private Limited"}
    content = main.doc_type(code)["body_template"]
    for key, value in values.items():
        content = content.replace("{{" + key + "}}", str(value))
    pdf = main.build_pdf(main.preview_record(code, content, values, company, party))
    output.write_bytes(pdf.getvalue())


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    main.DB_PATH = str(out / "qa.db")
    Path(main.DB_PATH).unlink(missing_ok=True)
    main.init_db()
    make("POLICY", out / "policy-v16.pdf")
    make("NDA", out / "nda-v16.pdf")
