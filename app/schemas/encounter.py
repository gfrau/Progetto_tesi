
from pydantic import BaseModel
from typing import Optional
from datetime import date

class EncounterCreate(BaseModel):
    identifier: str
    status: str
    subject_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
