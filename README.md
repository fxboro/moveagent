# Euro–Afro Elite Placement Commander

Single-user Next.js 14 dashboard, FastAPI service, SQLAlchemy/SQLite persistence, and direct GPT-4o function calling. Obsidian, champagne and gold interface with four-way triage, ten-match human approval, audit history, and watermarked PDF/editable Word dossiers.

## Run locally (PowerShell)

Prerequisites: Node.js 20+ and Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:3000. The database is created automatically at `backend/premium_consultancy.db`. Start the backend from the repository root. Keep a single backend worker so restart recovery does not interfere with another worker. For a frontend production build, use `npm run build` then `npm start`.

## Execution modes

Default `AGENT_MODE=demo` runs the entire workflow without credentials. It uses fixed, explicitly illustrative scores, ten university research seeds, and template drafts. It does not claim to assess the candidate.

To enable live specialists, set `AGENT_MODE=live` and `OPENAI_API_KEY` in `backend/.env`, then restart the backend. Profile text is sent to OpenAI in live mode. The requested model is exactly `gpt-4o`; three bounded specialist calls perform scoring, matching and drafting. Missing credentials fail visibly; live mode never silently falls back to fabricated results. Model results are provisional and require review.

## Workflow

1. Add a name, German level and extracted CV/transcript text (or a `.txt` file).
2. Follow the persisted four-way assessment and specialist audit history.
3. Review ten research choices. Select each checkbox, then approve all ten to release drafting. Reject all keeps drafting locked; retry starts a new research batch.
4. Review motivation letter, cover letter and enquiry email. Export as watermarked PDF or editable DOCX. Nothing is sent or submitted externally.
5. Run on-demand Anabin, ZAB or migration portal checks. These report reachability and direct you to manual review, not an automatic recognition determination.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
cd frontend
npm run typecheck
npm run build
```

Tests cover approval enforcement, cross-candidate isolation, rejection/retry, restart recovery, missing live credentials, validation and both export formats. `/docs` and `/openapi.json` expose the API contract. See `docs/api-contract.md` for state and endpoint behaviour.

### Standalone backend checks

- `python backend/test_pdf.py` (or `python -m backend.test_pdf`) uses WeasyPrint's structured HTML path to check three pages, forced section breaks, repeating diagonal watermarks, page bounds and `Page X of Y` counters. On success it writes `backend/test_premium_output.pdf`, regardless of the working directory. Inspect the PDF visually for font appearance and watermark legibility; structural assertions do not replace visual review. Native WeasyPrint libraries, including Pango/GObject, must be available on Windows. Missing libraries produce an error and a nonzero exit code, not a fallback test PDF.
- `python backend/seed_data.py` (or `python -m backend.seed_data`) creates tables in the configured SQLite database and transactionally inserts two illustrative demo profiles and their scores. Repeat runs preserve existing fixtures and unrelated candidates. No admissions, shortage-list eligibility, Anabin recognition, salary thresholds or visa outcomes are asserted as verified. No university matches or approved dossiers are inserted; reject and retry a seeded profile to run the normal matching workflow.

## Scope and deployment limits

- Parts 1–3 of the supplied specification are implemented as a local, single-user application. Bind both services to loopback. Authentication, TLS, distributed jobs and public deployment are not included; add those before exposing candidate information remotely.
- The malformed JSX and legacy OpenAI SDK calls in the supplied snippets are replaced with working components and current SDK syntax. Dependency ranges support current Python rather than the older supplied pins; the frontend lockfile records resolved versions.
- ReportLab remains the portable renderer for plain-text application exports. The explicit structured HTML test path uses WeasyPrint with an allowlist of text tags and page-break styles; external resources and other attributes are disallowed. DOCX export fixes the missing RGBColor import. Plain-text PDF content is escaped.
- CV/PDF OCR is not provided: paste extracted text or load a text file. The interface does not advertise an unsupported PDF dropzone.
- University recommendations, programme names, fees and legal eligibility are not verified by a portal homepage response. No hardcoded regulatory news or invented live alerts are shown. The Anabin portal requires human institution-specific verification.
- PDF uses standard built-in fonts; editable DOCX retains Unicode text. Add licensed Unicode fonts to the PDF engine for full multilingual glyph coverage.
- The application stores personal data in local SQLite without encryption. Protect and back up the database appropriately. API errors avoid exposing upstream secrets.

OpenAI function-calling reference: https://developers.openai.com/api/docs/guides/function-calling
