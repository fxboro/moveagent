"""Insert illustrative candidate fixtures, not verified regulatory assessments."""

import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import Base, SessionLocal, engine
from backend.models import Candidate, OpportunityScore


PROFILES = (
    {
        'name': 'Kofi Mensah',
        'language_level': 'A2',
        'raw_cv_text': '''DEMO PROFILE: All credentials require human verification.
EXPERIENCE: 6 years senior full-stack engineering at Lagos tech hubs.
SKILLS: AWS cloud architecture, Python, Go, distributed systems.
EDUCATION: B.Sc. Computer Science, University of Lagos; Anabin status not verified.
TARGET: Research German EU Blue Card and Austrian shortage-occupation routes.''',
        'scores': {
            'direct_work': 95, 'masters_score': 40,
            'bachelors_score': 0, 'ausbildung_score': 15,
            'monetization_strategy': 'Illustrative demo score, not an eligibility decision. Research the German EU Blue Card route and Blue Card Core Deployment Framework consulting package. Verify recognition, a qualifying job offer, current salary thresholds and applicable official rules before advice.',
        },
    },
    {
        'name': 'Amara Diallo',
        'language_level': 'B1',
        'raw_cv_text': '''DEMO PROFILE: All credentials require human verification.
AGE: 22 years old.
EDUCATION: WASSCE, 6 credits.
EXPERIENCE: 1 year volunteer clinical assistance at a community hospital.
LANGUAGE: Training towards a Goethe B2 certificate.
TARGET: Research German nursing Ausbildung; no placement is confirmed.''',
        'scores': {
            'direct_work': 10, 'masters_score': 0,
            'bachelors_score': 45, 'ausbildung_score': 92,
            'monetization_strategy': 'Illustrative demo score, not an eligibility decision. Research nursing Ausbildung providers in Bavaria. Verify provider-specific language and school-recognition requirements, B2 certification and current visa rules. Assess Studienkolleg requirements individually; no partner clinic placement is guaranteed.',
        },
    },
)


def seed_system_database():
    print('Creating database tables and inserting illustrative demo profiles...')
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        try:
            inserted = 0
            for profile in PROFILES:
                existing = db.query(Candidate).filter_by(
                    name=profile['name'], raw_cv_text=profile['raw_cv_text'], mode='demo'
                ).first()
                if existing is not None:
                    continue
                candidate = Candidate(
                    name=profile['name'], raw_cv_text=profile['raw_cv_text'],
                    language_level=profile['language_level'], mode='demo',
                    current_status='awaiting_approval',
                )
                db.add(candidate)
                db.flush()
                db.add(OpportunityScore(candidate_id=candidate.id, **profile['scores']))
                inserted += 1
            db.commit()
            print(f'Seeding complete: {inserted} profiles inserted; existing fixtures preserved.')
            print('Scores are illustrative. No university matches or approved dossiers are seeded.')
            print('Reject and retry a seeded profile to run the normal matching workflow.')
            return inserted
        except Exception:
            db.rollback()
            raise


if __name__ == '__main__':
    try:
        seed_system_database()
    except Exception as error:
        print(f'Seeding failed: {error}', file=sys.stderr)
        sys.exit(1)