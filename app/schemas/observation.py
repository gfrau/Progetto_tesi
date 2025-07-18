# app/schemas/observation.py
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any

class ObservationBase(BaseModel):
    resourceType: Literal["Observation"] = "Observation"
    status: str
    code: Dict[str, Any]
    subject: Dict[str, Any]
    effectiveDateTime: Optional[str]
    valueQuantity: Optional[Dict[str, Any]]

class ObservationCreate(ObservationBase):
    id: Optional[str]

class ObservationRead(ObservationBase):
    id: str