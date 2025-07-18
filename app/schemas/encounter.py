from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any, List


class EncounterRead(BaseModel):
    id: str
    resourceType: Literal["Encounter"]
    status: Optional[str] = None
    class_fhir: Optional[Dict[str, Any]] = None
    subject: Optional[Dict[str, Any]] = None
    period: Optional[Dict[str, Any]] = None
    identifier: Optional[List[Dict[str, str]]] = None