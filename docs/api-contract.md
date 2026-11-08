# API contract

The FastAPI OpenAPI contract is at http://127.0.0.1:8000/openapi.json and the interactive documentation at /docs. Next.js forwards /api/* to FastAPI /*.

| Method | Path | Result |
|---|---|---|
| GET | /health | Mode, model and liveness |
| GET | /dashboard | Persisted candidates and latest source checks |
| POST | /candidates/triage | Candidate profile → 202 with candidate_id; background workflow starts |
| GET | /candidates/{id} | Profile, score matrix, matches, dossiers and audit events |
| POST | /candidates/{id}/approve | Exactly ten distinct approved_ids belonging to this candidate → 202 |
| POST | /candidates/{id}/reject | Reject the waiting batch; no drafting |
| POST | /candidates/{id}/retry | Retry failed/rejected workflow; preserve prior approved choices |
| POST | /checks | Allowlisted source and institution_name → persisted portal check |
| GET | /candidates/{id}/export/{pdf\|docx} | Download completed dossier |

Unknown resources: 404. Invalid input: 422. Invalid state transitions: 409.

State machine: queued → triage → matching → awaiting_approval → approved → drafting → completed.
Rejection transitions to rejected; worker errors transition to failed. In-flight jobs become failed at process restart and can be explicitly retried. State claims are conditional database updates so duplicate requests cannot release a workflow twice. Use one Uvicorn worker; this local application does not use a distributed job queue.

Model tool calls are validated with Pydantic and only accepted for the expected function. Human approval is not exposed to the model. All ten candidate choices must be approved by the user; approval is permission to draft, not an admission decision. Demo scores are fixed fixtures, visibly labelled throughout the application.
