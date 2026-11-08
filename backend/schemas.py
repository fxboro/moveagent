from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class CandidateCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    raw_cv_text: str = Field(min_length=30, max_length=30000)
    language_level: Literal['None', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'] = 'None'

class Scores(StrictModel):
    direct_work_score: int = Field(ge=0, le=100)
    masters_placement_score: int = Field(ge=0, le=100)
    bachelors_placement_score: int = Field(ge=0, le=100)
    ausbildung_placement_score: int = Field(ge=0, le=100)
    strategic_monetization_flag: str = Field(min_length=1, max_length=3000)

class Match(StrictModel):
    institution_name: str
    program_name: str
    tuition_fee_structure: str
    matching_rationale: str
    source_url: str

class Matches(StrictModel):
    matches: list[Match] = Field(min_length=10, max_length=10)

class Dossier(StrictModel):
    motivation_letter: str = Field(min_length=50, max_length=12000)
    cover_letter: str = Field(min_length=50, max_length=12000)
    email_draft: str = Field(min_length=30, max_length=6000)

class Approval(StrictModel):
    approved_ids: list[int] = Field(min_length=10, max_length=10)

class CheckRequest(StrictModel):
    institution_name: str = Field(default='Not specified', min_length=1, max_length=200)
    source: Literal['anabin', 'migration', 'zab'] = 'anabin'
