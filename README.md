# Aurelia Contract Studio V1.3

Premium local Contract & Agreement Management starter built for VS Code.

## One-command launch

After extracting the project and opening the `agreement-studio` folder in VS Code, run only:

```powershell
python run.py
```

`run.py` is the primary launcher. It handles the local environment automatically:

1. Checks that the project is complete.
2. Checks the current Python version (Python 3.10+ required; 3.11+ recommended).
3. Creates `backend/.venv` only when it does not already exist.
4. Checks `backend/requirements.txt` and installs Python packages only when required.
5. Checks for Node.js and npm.
6. If a suitable Node.js/npm installation is already available, it reuses it.
7. If Node.js/npm is missing or too old, it downloads an official **portable Node.js runtime** into `.runtime/` inside this project instead of modifying your system installation.
8. Checks frontend package metadata and runs `npm install` only when dependencies are missing or changed.
9. Starts FastAPI on `http://127.0.0.1:8000`.
10. Starts the React/Vite application on `http://127.0.0.1:5173`.
11. Opens the application automatically in your default browser.
12. Pressing `Ctrl+C` stops both services.

On the first run, internet access is required if Python packages, frontend packages, or the portable Node.js runtime have not already been installed. Later launches reuse the existing environment wherever possible.

> The launcher itself is a Python file, so Python must already be installed before `python run.py` can execute. If the detected Python version is unsupported, the launcher gives a clear installation instruction instead of modifying the operating system automatically.

## Environment-file safety

This package intentionally contains **no `.env` file**. It contains `.env.example` only.

`run.py`:

- never creates `.env`;
- never copies `.env.example` to `.env`;
- never overwrites `.env`;
- never deletes `.env`.

Your own local `.env` therefore remains untouched between application upgrades.

## Included

- FastAPI + SQLite backend
- React + TypeScript + Vite frontend
- Premium responsive light/dark interface
- Dashboard and agreement pipeline
- Dynamic company master
- Dynamic client/vendor master
- Client, Vendor, NDA and Custom templates
- **Working Create Template flow** with create, edit and archive actions
- **Master template editor** with placeholder-token picker
- Template-defined dynamic fields: text, multiline, date, number, currency and select
- Required/optional template-field validation and defaults
- Duplicate and undefined-placeholder checks
- **Template-aware agreement wizard**: selecting an NDA/client/vendor template automatically generates the fields that template requires
- Automatic company/party/system placeholders such as `{{OUR_COMPANY_LEGAL_NAME}}`, `{{PARTY_LEGAL_NAME}}`, `{{SCOPE}}`, `{{DELIVERABLES}}` and `{{COMMERCIAL_TERMS}}`
- Live render endpoint and unresolved-placeholder blocking before finalization
- **Final live agreement editor** after placeholder substitution; manual edits are agreement-specific
- Reset/re-render from master template + current field values
- Explicit **Save as template** action only when the user intentionally wants final agreement wording to replace the master template content
- Fixed Bid, Milestone Based, Time & Material and Hybrid commercial models
- Dynamic deliverables
- Milestone 100% validation
- Version/audit scaffolding
- Voice input through browser Speech Recognition where supported
- Local AI-assistant mock endpoint with clean provider hook point
- PDF generation from FastAPI using ReportLab
- Agreement numbering `AGR-YYYY-0001`


## V1.3 template workflow

1. Open **Templates** and choose **Create template**.
2. Define the master legal text and add placeholders such as `{{AGREEMENT_DATE}}`, `{{PURPOSE}}` or `{{CONFIDENTIALITY_PERIOD}}`.
3. Define the corresponding dynamic fields and whether each field is required.
4. While creating an agreement, select that template. The next wizard step is generated from the template field schema automatically.
5. Enter the requested values. The application substitutes them together with company, counterparty, scope, deliverables and commercial data.
6. The last wizard step shows the rendered agreement in the **Live Agreement Editor**. Edit any wording manually before creating the agreement.
7. Agreement-specific edits do not update the source/master template. Updating the master requires the explicit **Save as template** action.
8. Agreements with unresolved `{{PLACEHOLDER}}` tokens cannot be finalized.

The seeded Mutual NDA demonstrates this workflow with agreement date, purpose, representatives, confidentiality period and governing-law fields.

## Local addresses

- Application: `http://127.0.0.1:5173`
- Backend API: `http://127.0.0.1:8000`
- FastAPI Swagger: `http://127.0.0.1:8000/docs`

## Local database

`backend/agreement_studio.db` is created automatically at first backend launch and is excluded from Git.

## AI integration

The AI screen currently calls `/api/ai`, which is a local mock so the application works without secret keys. Replace the provider implementation later with OpenAI, Azure OpenAI, or another approved provider. Store credentials in your own `.env`; never commit secrets.

## Existing company agreement templates

The backend seeds placeholder-based templates including:

- `{{OUR_COMPANY_LEGAL_NAME}}`
- `{{PARTY_LEGAL_NAME}}`
- `{{SCOPE}}`
- `{{DELIVERABLES}}`
- `{{COMMERCIAL_TERMS}}`

Your existing approved company agreements can later be converted into these reusable templates without changing the agreement-creation workflow.

## Production path

The frontend and backend are separated intentionally so they can later be deployed independently. For production, replace SQLite with PostgreSQL, restrict CORS origins, add authentication/RBAC, move secrets to your deployment environment, and connect approved AI, digital-signature, email, and notification services.

## Legacy launchers

The old `.bat` launchers are retained only as fallback helpers for Windows. For normal use, use:

```powershell
python run.py
```


## Python 3.14 compatibility

V1.2 uses FastAPI/Pydantic versions with native CPython 3.14 Windows wheels. `run.py` detects an incomplete or mismatched `backend/.venv`, rebuilds it automatically, and retries backend dependency installation once. You do not need Rust or Visual Studio Build Tools for the normal setup.
