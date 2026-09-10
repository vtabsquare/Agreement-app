import re
import unittest

from app.template_library import ADDITIONAL_TEMPLATES


class AddedTemplateTests(unittest.TestCase):
    def test_all_supplied_templates_templates_are_registered(self):
        self.assertEqual(
            [item["code"] for item in ADDITIONAL_TEMPLATES],
            ["MSA", "SOW", "FIXED_BID", "TIME_MATERIAL", "MILESTONE", "MIXED", "CHANGE_REQUEST", "ACCEPTANCE", "CLOSURE"],
        )

    def test_field_counts_match_the_complete_source_sets(self):
        self.assertEqual(
            {item["code"]: len(item["schema"]) for item in ADDITIONAL_TEMPLATES},
            {"MSA": 33, "SOW": 33, "FIXED_BID": 8, "TIME_MATERIAL": 9, "MILESTONE": 15, "MIXED": 15, "CHANGE_REQUEST": 30, "ACCEPTANCE": 19, "CLOSURE": 19},
        )

    def test_every_source_placeholder_has_one_visible_field(self):
        for item in ADDITIONAL_TEMPLATES:
            body_keys = set(re.findall(r"\{\{\s*([A-Z][A-Z0-9_]*)\s*\}\}", item["body"]))
            field_keys = [field["key"] for field in item["schema"]]
            self.assertEqual(len(field_keys), len(set(field_keys)), item["code"])
            self.assertEqual(body_keys, set(field_keys), item["code"])
            self.assertEqual(item["body"].count("[[TABLE]]"), item["body"].count("[[/TABLE]]"), item["code"])

    def test_each_added_document_starts_its_own_numbering_at_one(self):
        for item in ADDITIONAL_TEMPLATES:
            first_heading = next(line for line in item["body"].splitlines() if line.startswith("[[H1]]"))
            self.assertRegex(first_heading, r"^\[\[H1\]\]1\. ", item["code"])
            self.assertNotRegex(item["body"], r"\[\[H[12]\]\](?:[2-9]|\d{2,})(?:\.|\s)", item["code"])

    def test_signature_templates_expose_both_reusable_signature_slots(self):
        for code in {"MSA", "SOW", "CHANGE_REQUEST", "ACCEPTANCE", "CLOSURE"}:
            item = next(template for template in ADDITIONAL_TEMPLATES if template["code"] == code)
            fields = {field["key"]: field for field in item["schema"]}
            self.assertEqual(fields["SERVICE_PROVIDER_SIGNATURE_IMAGE"]["type"], "signature")
            self.assertEqual(fields["CLIENT_SIGNATURE_IMAGE"]["type"], "signature")


if __name__ == "__main__":
    unittest.main()
