
# schemas/encounter.py

from pydantic import BaseModel, Field
from typing import Optional, Literal


class EncounterRead(BaseModel):
    id: str
    status: str
    class_code: Optional[str]
    patient_id: Optional[str]
    start: Optional[str]
    end: Optional[str]
    resourceType: Literal["Encounter"] = "Encounter"
