from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from .database import Base

def now():
    return datetime.now(timezone.utc).isoformat()

class Candidate(Base):
    __tablename__ = 'candidates'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    raw_cv_text = Column(Text, nullable=False)
    language_level = Column(String, nullable=False)
    current_status = Column(String, default='queued', nullable=False)
    mode = Column(String, nullable=False)
    error = Column(Text)
    created_at = Column(String, default=now)

class OpportunityScore(Base):
    __tablename__ = 'opportunity_scores'
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), unique=True)
    direct_work = Column(Integer)
    masters_score = Column(Integer)
    bachelors_score = Column(Integer)
    ausbildung_score = Column(Integer)
    monetization_strategy = Column(Text)

class UniversityMatch(Base):
    __tablename__ = 'university_matches'
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    institution_name = Column(String)
    program_name = Column(String)
    tuition_fee_structure = Column(String)
    matching_rationale = Column(Text)
    source_url = Column(String)
    is_approved_by_human = Column(Boolean, default=False)

class GeneratedDossier(Base):
    __tablename__ = 'generated_dossiers'
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    document_type = Column(String)
    content = Column(Text)
    is_approved_by_human = Column(Boolean, default=False)

class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    agent = Column(String)
    message = Column(Text)
    created_at = Column(String, default=now)

class RegulatoryCheck(Base):
    __tablename__ = 'regulatory_checks'
    id = Column(Integer, primary_key=True)
    institution_name = Column(String)
    source = Column(String)
    source_url = Column(String)
    status = Column(String)
    note = Column(Text)
    verified = Column(Boolean, default=False)
    checked_at = Column(String, default=now)
