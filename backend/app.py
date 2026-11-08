from contextlib import asynccontextmanager
from io import BytesIO
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from .database import Base, engine, get_db, SessionLocal
from .models import Candidate, OpportunityScore, UniversityMatch, GeneratedDossier, AuditEvent, RegulatoryCheck
from .schemas import CandidateCreate, Approval, CheckRequest
from .agents import mode, process_candidate, draft_candidate, log
from .scraper import query_anabin_on_demand
from .document_builder import compile_premium_watermarked_pdf, compile_editable_word_doc

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        interrupted = list(db.scalars(select(Candidate).where(Candidate.current_status.in_(['queued', 'triage', 'matching', 'approved', 'drafting']))))
        for candidate in interrupted:
            candidate.current_status = 'failed'
            candidate.error = 'Processing interrupted by server restart. Retry to continue.'
            log(db, candidate.id, 'System', candidate.error)
        db.commit()
    yield

app = FastAPI(title='Premium Euro-African Placement Commander', version='1.0.0', lifespan=lifespan)

def record(obj):
    return {column.name: getattr(obj, column.name) for column in obj.__table__.columns}

def require_candidate(db, cid):
    candidate = db.get(Candidate, cid)
    if candidate is None:
        raise HTTPException(404, 'Candidate not found')
    return candidate

@app.get('/health')
def health():
    return {'status': 'ok', 'mode': mode(), 'model': 'gpt-4o'}

@app.get('/dashboard')
def dashboard(db: Session = Depends(get_db)):
    return {'mode': mode(), 'candidates': [record(c) for c in db.scalars(select(Candidate).order_by(Candidate.id.desc()))],
            'checks': [record(c) for c in db.scalars(select(RegulatoryCheck).order_by(RegulatoryCheck.id.desc()).limit(12))]}

@app.post('/candidates/triage', status_code=202)
def triage_new_candidate(payload: CandidateCreate, background: BackgroundTasks, db: Session = Depends(get_db)):
    if not payload.name.strip() or not payload.raw_cv_text.strip():
        raise HTTPException(422, 'Name and CV text cannot be blank')
    candidate = Candidate(**payload.model_dump(), mode=mode())
    db.add(candidate)
    db.commit()
    log(db, candidate.id, 'Intake', 'Candidate queued for assessment.')
    db.commit()
    background.add_task(process_candidate, candidate.id)
    return {'candidate_id': candidate.id, 'status': 'queued'}

@app.get('/candidates/{cid}')
def candidate_detail(cid: int, db: Session = Depends(get_db)):
    candidate = require_candidate(db, cid)
    score = db.scalar(select(OpportunityScore).where(OpportunityScore.candidate_id == cid))
    return {**record(candidate), 'triage_matrix': record(score) if score else None,
            'matches': [record(m) for m in db.scalars(select(UniversityMatch).where(UniversityMatch.candidate_id == cid).order_by(UniversityMatch.id))],
            'dossiers': [record(d) for d in db.scalars(select(GeneratedDossier).where(GeneratedDossier.candidate_id == cid))],
            'events': [record(e) for e in db.scalars(select(AuditEvent).where(AuditEvent.candidate_id == cid).order_by(AuditEvent.id))]}

@app.post('/candidates/{cid}/approve', status_code=202)
def approve(cid: int, payload: Approval, background: BackgroundTasks, db: Session = Depends(get_db)):
    require_candidate(db, cid)
    matches = list(db.scalars(select(UniversityMatch).where(UniversityMatch.candidate_id == cid)))
    if len(set(payload.approved_ids)) != 10 or set(payload.approved_ids) != {m.id for m in matches}:
        raise HTTPException(422, 'Approve exactly the ten distinct matches belonging to this candidate')
    changed = db.execute(update(Candidate).where(Candidate.id == cid, Candidate.current_status == 'awaiting_approval').values(current_status='approved'))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Candidate is not awaiting approval')
    for match in matches:
        match.is_approved_by_human = True
    log(db, cid, 'Human reviewer', 'All ten university research choices approved for drafting.')
    db.commit()
    background.add_task(draft_candidate, cid)
    return {'status': 'approved'}

@app.post('/candidates/{cid}/reject')
def reject(cid: int, db: Session = Depends(get_db)):
    require_candidate(db, cid)
    changed = db.execute(update(Candidate).where(Candidate.id == cid, Candidate.current_status == 'awaiting_approval').values(current_status='rejected'))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Candidate is not awaiting approval')
    log(db, cid, 'Human reviewer', 'Batch rejected. Drafting remains locked.')
    db.commit()
    return {'status': 'rejected'}

@app.post('/candidates/{cid}/retry', status_code=202)
def retry(cid: int, background: BackgroundTasks, db: Session = Depends(get_db)):
    require_candidate(db, cid)
    matches = list(db.scalars(select(UniversityMatch).where(UniversityMatch.candidate_id == cid)))
    approved = len(matches) == 10 and all(m.is_approved_by_human for m in matches)
    changed = db.execute(update(Candidate).where(Candidate.id == cid, Candidate.current_status.in_(['failed', 'rejected'])).values(current_status='approved' if approved else 'queued', error=None))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, 'Only failed or rejected candidates can be retried')
    db.execute(delete(GeneratedDossier).where(GeneratedDossier.candidate_id == cid))
    if not approved:
        db.execute(delete(UniversityMatch).where(UniversityMatch.candidate_id == cid))
        db.execute(delete(OpportunityScore).where(OpportunityScore.candidate_id == cid))
    log(db, cid, 'System', 'Retry requested.')
    db.commit()
    background.add_task(draft_candidate if approved else process_candidate, cid)
    return {'status': 'queued'}

@app.post('/checks')
def live_check(payload: CheckRequest, db: Session = Depends(get_db)):
    check = RegulatoryCheck(**query_anabin_on_demand(**payload.model_dump()))
    db.add(check)
    db.commit()
    return record(check)

@app.get('/candidates/{cid}/export/{format}')
def export(cid: int, format: str, db: Session = Depends(get_db)):
    if format not in ('pdf', 'docx'):
        raise HTTPException(422, 'Choose pdf or docx')
    candidate = require_candidate(db, cid)
    if candidate.current_status != 'completed':
        raise HTTPException(409, 'Complete the approval and drafting workflow before exporting')
    dossiers = list(db.scalars(select(GeneratedDossier).where(GeneratedDossier.candidate_id == cid)))
    content = f'Execution mode: {candidate.mode.upper()}\nDrafts require human review. University approval is not an admission or recognition decision.\n\n' + '\n\n'.join(d.document_type.replace('_', ' ').upper() + '\n' + d.content for d in dossiers)
    if format == 'pdf':
        data, mime = compile_premium_watermarked_pdf(candidate.name, content), 'application/pdf'
    else:
        data, mime = compile_editable_word_doc(candidate.name, content), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    return StreamingResponse(BytesIO(data), media_type=mime, headers={'Content-Disposition': f'attachment; filename="candidate-{cid}-dossier.{format}"'})
