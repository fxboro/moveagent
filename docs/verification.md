# Verification — 8 November 2026

- `npm run build`: passed with Next.js 14.2.35, including TypeScript validation and production page generation.
- `python -m pytest backend/tests -q`: 5 passed. The installed Starlette reports a test-client deprecation warning for httpx; no test failures.
- Browser: opened the running Next.js dashboard, submitted a synthetic demo candidate, observed four scores and ten distinct matches, selected all ten, released drafting, and observed completed status with three drafts and enabled PDF/Word controls.
- Desktop (1440 px) and narrow default browser layouts inspected. Screenshot saved in `artifacts/commander-dashboard.jpg`.
- PDF signature and DOCX archive/content validated by automated tests.
- OpenAPI schema exported to `docs/openapi.json`.
- Missing live credentials tested: live mode fails visibly without producing mock scores.

Not verified: paid/live GPT-4o calls, institution-specific recognition, current migration eligibility, regulatory news, PDF OCR, public deployment, full visual pagination of long exports, and Unicode font coverage in PDF.

Postman CLI 1.73.0 is installed but signed out and does not expose the skill-documented `status` command. Connected Postman discovery was therefore skipped; local FastAPI tests and the exported OpenAPI contract provide the API evidence.

The local database contains one synthetic browser-test profile named `Demo Candidate`. No real candidate information was used.
