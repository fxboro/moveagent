import os
import tempfile
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import pytest

_temp = tempfile.TemporaryDirectory()
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(_temp.name) / 'test.db')
os.environ['AGENT_MODE'] = 'demo'

from fastapi.testclient import TestClient
from backend.app import app
from backend.database import engine

@pytest.fixture(scope='session', autouse=True)
def dispose_test_database():
    yield
    engine.dispose()
    _temp.cleanup()

PROFILE = {'name': 'Ada Example', 'raw_cv_text': 'BSc in computer science. Three years of software development experience. Interested in postgraduate study.', 'language_level': 'B1'}

def test_complete_workflow_and_gate():
    with TestClient(app) as client:
        created = client.post('/candidates/triage', json=PROFILE)
        assert created.status_code == 202
        cid = created.json()['candidate_id']
        detail = client.get(f'/candidates/{cid}').json()
        assert detail['current_status'] == 'awaiting_approval'
        assert len(detail['matches']) == 10
        assert len({m['institution_name'] for m in detail['matches']}) == 10
        assert detail['dossiers'] == []
        assert client.get(f'/candidates/{cid}/export/pdf').status_code == 409
        ids = [m['id'] for m in detail['matches']]
        assert client.post(f'/candidates/{cid}/approve', json={'approved_ids': ids[:9]}).status_code == 422
        assert client.post(f'/candidates/{cid}/approve', json={'approved_ids': [ids[0]] * 10}).status_code == 422
        assert client.post(f'/candidates/{cid}/approve', json={'approved_ids': ids[:-1] + [999999]}).status_code == 422
        assert client.post(f'/candidates/{cid}/approve', json={'approved_ids': ids}).status_code == 202
        result = client.get(f'/candidates/{cid}').json()
        assert result['current_status'] == 'completed'
        assert len(result['dossiers']) == 3
        assert all(m['is_approved_by_human'] for m in result['matches'])
        assert client.post(f'/candidates/{cid}/approve', json={'approved_ids': ids}).status_code == 409
        assert client.post(f'/candidates/{cid}/retry').status_code == 409
        pdf = client.get(f'/candidates/{cid}/export/pdf')
        assert pdf.status_code == 200 and pdf.content.startswith(b'%PDF')
        docx = client.get(f'/candidates/{cid}/export/docx')
        assert docx.status_code == 200
        with ZipFile(BytesIO(docx.content)) as document:
            assert b'Ada Example' in document.read('word/document.xml')
        assert client.get(f'/candidates/{cid}/export/html').status_code == 422

def test_rejection_retry_and_isolation():
    with TestClient(app) as client:
        first = client.post('/candidates/triage', json=PROFILE).json()['candidate_id']
        second = client.post('/candidates/triage', json={**PROFILE, 'name': 'Second Candidate'}).json()['candidate_id']
        ids = [m['id'] for m in client.get(f'/candidates/{first}').json()['matches']]
        assert client.post(f'/candidates/{second}/approve', json={'approved_ids': ids}).status_code == 422
        assert client.post(f'/candidates/{first}/reject').status_code == 200
        assert client.get(f'/candidates/{first}').json()['dossiers'] == []
        assert client.post(f'/candidates/{first}/approve', json={'approved_ids': ids}).status_code == 409
        assert client.post(f'/candidates/{first}/retry').status_code == 202
        detail = client.get(f'/candidates/{first}').json()
        assert detail['current_status'] == 'awaiting_approval'
        assert len(detail['matches']) == 10
        assert not any(m['is_approved_by_human'] for m in detail['matches'])

def test_validation():
    with TestClient(app) as client:
        assert client.get('/candidates/999999').status_code == 404
        assert client.post('/candidates/triage', json={**PROFILE, 'language_level': 'fluent'}).status_code == 422
        assert client.post('/candidates/triage', json={**PROFILE, 'name': '  '}).status_code == 422
        assert client.post('/checks', json={'source': 'http://localhost', 'institution_name': 'Example'}).status_code == 422

def test_restart_marks_interrupted_run():
    from backend.database import SessionLocal
    from backend.models import Candidate
    with SessionLocal() as db:
        candidate = Candidate(**PROFILE, mode='demo', current_status='drafting')
        db.add(candidate)
        db.commit()
        cid = candidate.id
    with TestClient(app) as client:
        detail = client.get(f'/candidates/{cid}').json()
        assert detail['current_status'] == 'failed'
        assert 'restart' in detail['error']

def test_missing_live_key_fails_honestly(monkeypatch):
    monkeypatch.setenv('AGENT_MODE', 'live')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with TestClient(app) as client:
        cid = client.post('/candidates/triage', json=PROFILE).json()['candidate_id']
        result = client.get(f'/candidates/{cid}').json()
        assert result['current_status'] == 'failed'
        assert 'OPENAI_API_KEY' in result['error']
        assert result['triage_matrix'] is None


def test_seed_profiles_are_idempotent_and_transactional(monkeypatch):
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from backend import seed_data
    from backend.models import Candidate, OpportunityScore

    isolated_engine = create_engine('sqlite:///:memory:')
    sessions = sessionmaker(bind=isolated_engine)
    monkeypatch.setattr(seed_data, 'engine', isolated_engine)
    monkeypatch.setattr(seed_data, 'SessionLocal', sessions)
    seed_data.Base.metadata.create_all(isolated_engine)
    try:
        with sessions() as db:
            db.add(Candidate(**PROFILE, mode='demo', current_status='completed'))
            db.commit()
        assert seed_data.seed_system_database() == 2
        assert seed_data.seed_system_database() == 0
        with sessions() as db:
            assert db.query(Candidate).count() == 3
            scores = db.query(OpportunityScore).all()
            assert len(scores) == 2
            assert {score.direct_work for score in scores} == {95, 10}
            assert {score.ausbildung_score for score in scores} == {15, 92}
            for profile in seed_data.PROFILES:
                candidate = db.query(Candidate).filter_by(name=profile['name']).one()
                assert candidate.mode == 'demo'
                assert candidate.current_status == 'awaiting_approval'
                assert db.query(OpportunityScore).filter_by(candidate_id=candidate.id).count() == 1
            db.query(OpportunityScore).delete()
            db.query(Candidate).filter(Candidate.name != PROFILE['name']).delete()
            db.commit()

        def fail_score_insert(mapper, connection, target):
            raise RuntimeError('simulated score failure')

        event.listen(OpportunityScore, 'before_insert', fail_score_insert)
        try:
            with pytest.raises(RuntimeError, match='simulated score failure'):
                seed_data.seed_system_database()
        finally:
            event.remove(OpportunityScore, 'before_insert', fail_score_insert)
        with sessions() as db:
            assert db.query(Candidate).count() == 1
            assert db.query(OpportunityScore).count() == 0
    finally:
        isolated_engine.dispose()


def test_structured_pdf_markup_is_safe_and_explicit(monkeypatch):
    import sys
    from types import SimpleNamespace
    from unittest.mock import Mock
    from backend.document_builder import compile_premium_watermarked_pdf, render_premium_document
    from backend.test_pdf import MOCK_LARGE_CONTENT

    rendered = Mock()
    rendered.write_pdf.return_value = b'%PDF-test'
    renderer = Mock(return_value=SimpleNamespace(render=Mock(return_value=rendered)))
    stylesheet = Mock()
    monkeypatch.setitem(sys.modules, 'weasyprint', SimpleNamespace(HTML=renderer, CSS=stylesheet))

    assert compile_premium_watermarked_pdf('<Candidate>', MOCK_LARGE_CONTENT, content_is_html=True) == b'%PDF-test'
    markup = renderer.call_args.kwargs['string']
    assert '&lt;Candidate&gt;' in markup
    assert markup.count('break-before: page;') == 2
    assert '<h2>' in markup
    assert 'counter(pages)' in stylesheet.call_args.kwargs['string']
    assert 'position: fixed' in stylesheet.call_args.kwargs['string']
    assert 'rotate(-38deg)' in stylesheet.call_args.kwargs['string']
    render_premium_document('Candidate', '<p style="background: url(file:///secret)">Safe</p>', content_is_html=True)
    assert 'file:///secret' not in renderer.call_args.kwargs['string']
    for unsafe in ('<img src="file:///secret">', '<script>alert(1)</script>', '<style>@import "https://example.com";</style>'):
        with pytest.raises(ValueError, match='Unsupported dossier HTML tag'):
            render_premium_document('Candidate', unsafe, content_is_html=True)
    render_premium_document('Candidate', '<script>literal text</script>')
    assert '&lt;script&gt;literal text&lt;/script&gt;' in renderer.call_args.kwargs['string']
