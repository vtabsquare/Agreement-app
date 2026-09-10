# Aurelia Contract Studio V1.7

A local-first agreement generator built around the approved Policy, NDA and engagement templates supplied for this project.

## Approved Templates

1. **Policy Agreement** - based on the supplied VTAB Square Policy Agreement PDF.
2. **Client Engagement NDA** - based on the full parameterized Client Engagement Agreement and NDA pack, with the non-variable document used as a wording check.
3. **Client Engagement Agreement** - the original Client Engagement / Master Services Agreement content.
4. **Statement of Work** - the original common SOW content and signature table.
5. **Fixed Bid Commercial Schedule** - the original fixed bid content and commercial table.
6. **Time and Material Commercial Schedule** - the original T&M content and commercial table.
7. **Milestone Based Commercial Schedule** - the original milestone content and milestone table.
8. **Mixed Project Commercial Schedule** - the original mixed-project content and workstream table.
9. **Change Request** - the original request, impact-assessment and approval content.
10. **Milestone Deliverable Acceptance** - the original acceptance content and signature table.
11. **Project Engagement Closure** - the original closure checklist, confirmation and signature content.

Each template owns its complete field schema. Selecting a template shows only the variables present in that source document. Company and Client Master values are prefilled where possible, but every field remains visible and editable.

The nine engagement additions preserve the supplied paragraph wording, heading order, lists, table rows, table cells, signatures and every unique `{{VARIABLE}}` occurrence. The application adds the existing VTAB/Siroco cover and Contact Us page around that source content.

Every approved document now has independent clause numbering. A document begins at **1.**, and its subsections continue as **1.1, 1.2, 1.3...** instead of inheriting section numbers from the original multi-document pack.

## Digital signatures

The **Signatures** section provides two reusable capture methods:

- Draw a signature in the application and save it with a recognizable name.
- Upload a PNG, JPEG or WebP signature image and save it to the library.

Saved signatures appear in dropdowns for every template signature slot. Users may instead upload a one-time signature image directly in a document field. The selected image is embedded in the WYSIWYG preview and the exported PDF. Removing a saved library item does not alter documents that already contain that image.

## Policy Agreement fields

The Policy template exposes recipient name, agreement date, optional photo, internship/training/probation/post-probation periods and amounts, work hours and setup, leave and LOP terms, salary-credit day, resignation thresholds, notice and penalties, example values, signatory details and an optional reusable digital signature.

The static body follows the supplied reference wording and is laid out across the same cover, two content pages and final contact page as the supplied PDF.

## Complete NDA fields

V1.7 exposes the complete NDA inputs in usable groups:

- Service Provider legal name, brand name, registered address, registration/CIN number, tax ID and notice email.
- Client legal and display names, registered address, registration number, tax ID, primary contact name/email and notice email.
- NDA effective/end dates, purpose and confidentiality term.
- Governing law, dispute-resolution method and dispute venue/seat.
- Both authorized signatory names, titles, signature dates and reusable digital-signature selections.

The variables are derived from the parameterized source pack rather than a reduced manual subset.

## Template actions and versioning

Each stored template has visible **View**, **Edit** and **Use** actions. View opens a page-by-page PDF preview of the stored shell. Edit changes content and variable definitions while the VTAB/Siroco branded shell remains locked. **Reset to built-in** restores the V1.7 source definition.

Template records store their revision, built-in version, update time, source metadata and customized/original status. All eleven approved built-in templates remain active.

## WYSIWYG PDF workflow

```text
Approved template
      -> complete template-specific fields
      -> unresolved-field check
      -> branded page-by-page final preview
      -> optional Edit Final Content
      -> save/version
      -> export the same branded PDF
```

The final on-screen preview is produced by the same ReportLab renderer as PDF export. It is not a generic rich-text card. Every approved template uses the Policy reference framework:

- A4 navy cover with contact details, VTAB Square and Siroco lockup, PREPARED FOR, document title and white confidentiality strip.
- White content pages with the same navy header band, contact block, lockup, navy footer, Siroco mark and page number.
- Final Contact Us page with USA red, INDIA orange and MENA green sections plus navy footer.

Missing required values are listed by field name and block document creation/export until resolved.

## Run locally

From the project root:

```powershell
python run.py
```

The launcher supports Python 3.14, checks dependencies, starts FastAPI and Vite, and opens the application. Press **Ctrl+C** once to stop both services.

## Existing V1.x database

Uncustomized built-ins are upgraded to V1.7 automatically. User-customized templates remain intact and can be restored explicitly with **Reset to built-in**. Existing agreement history, generated content, versions, status, audit records and PDF export remain available.

## Environment safety

- `.env` is never created, copied, replaced or overwritten.
- No `.env` file is included in the release.
- `.venv`, `.runtime`, `.launcher`, `node_modules`, local databases, generated PDFs and other runtime content are excluded from the release ZIP.
