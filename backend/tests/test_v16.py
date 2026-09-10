import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from app import main


class V16TemplateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        main.DB_PATH = str(Path(self.tmp.name) / "test.db")
        main.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def values_for(self, code):
        dt = main.doc_type(code)
        values = {}
        for field in dt["fields"]:
            if field.get("default") not in (None, ""):
                value = field["default"]
            elif field["type"] == "date":
                value = "2026-09-09"
            elif field["type"] in {"number", "currency"}:
                value = 1
            elif field["type"] == "image":
                value = ""
            else:
                value = f"Test {field['label']}"
            values[field["key"]] = value
        return values

    def test_exactly_two_builtins_and_complete_counts(self):
        docs = main.rows("SELECT code FROM document_types WHERE active=1 ORDER BY code")
        self.assertEqual([d["code"] for d in docs], ["NDA", "POLICY"])
        self.assertEqual(len(main.doc_type("POLICY")["fields"]), 27)
        nda = main.doc_type("NDA")["fields"]
        self.assertEqual(len(nda), 27)
        keys = {f["key"] for f in nda}
        required = {
            "SERVICE_PROVIDER_REGISTERED_ADDRESS", "SERVICE_PROVIDER_REGISTRATION_NO",
            "SERVICE_PROVIDER_TAX_ID", "COMPANY_BRAND_NAME", "CLIENT_NAME",
            "CLIENT_REGISTERED_ADDRESS", "CLIENT_REGISTRATION_NO", "CLIENT_TAX_ID",
            "CLIENT_PRIMARY_CONTACT_NAME", "CLIENT_PRIMARY_CONTACT_EMAIL",
            "NOTICE_EMAIL_PROVIDER", "NOTICE_EMAIL_CLIENT", "NDA_EFFECTIVE_DATE",
            "NDA_END_DATE", "NDA_PURPOSE", "CONFIDENTIALITY_TERM_YEARS",
            "GOVERNING_LAW", "DISPUTE_RESOLUTION_METHOD", "DISPUTE_VENUE",
            "SERVICE_PROVIDER_SIGNATORY_NAME", "CLIENT_SIGNATORY_NAME",
        }
        self.assertTrue(required.issubset(keys))

    def test_unresolved_required_fields_block_generation(self):
        company = {"name": "", "legal_name": "", "address": "", "gst": "", "email": "", "representative": ""}
        party = {"name": "", "legal_name": "", "address": "", "gst": "", "email": "", "contact_person": ""}
        _, _, _, missing = main.render_document("NDA", company, party, {})
        self.assertIn("NDA_PURPOSE", missing)
        self.assertIn("CLIENT_REGISTRATION_NO", missing)
        self.assertGreater(len(missing), 10)

    def test_template_update_and_reset(self):
        policy = main.doc_type("POLICY")
        changed = policy["body_template"] + "\n\nCustom clause."
        updated = main.update_document_type("POLICY", main.TemplateUpdate(body_template=changed, fields=policy["fields"]))
        self.assertEqual(updated["is_customized"], 1)
        self.assertIn("Custom clause", updated["body_template"])
        reset = main.reset_document_type("POLICY")
        self.assertEqual(reset["is_customized"], 0)
        self.assertNotIn("Custom clause", reset["body_template"])

    def test_policy_and_nda_pdf_render(self):
        for code in ("POLICY", "NDA"):
            values = self.values_for(code)
            company = {"name": "VTAB Square", "legal_name": "VTAB Square Private Limited"}
            party = {"name": "Client", "legal_name": "Client Private Limited"}
            dt = main.doc_type(code)
            content = dt["body_template"]
            for key, value in values.items():
                content = content.replace("{{" + key + "}}", str(value))
            pdf = main.build_pdf(main.preview_record(code, content, values, company, party))
            reader = PdfReader(pdf)
            self.assertGreaterEqual(len(reader.pages), 4)
            self.assertAlmostEqual(float(reader.pages[0].mediabox.width), 595.2756, places=2)
            self.assertNotIn("{{", "".join((p.extract_text() or "") for p in reader.pages))


if __name__ == "__main__":
    unittest.main()
