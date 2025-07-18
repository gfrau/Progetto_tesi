from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class Coding(BaseModel):
    system: Optional[str] = Field(default="http://loinc.org")
    code: str
    display: Optional[str] = None


class CodeableConcept(BaseModel):
    coding: List[Coding]
    text: Optional[str] = None


class Quantity(BaseModel):
    value: float
    unit: Optional[str] = None


class Reference(BaseModel):
    identifier: dict  # {"value": hashed_cf}


class ObservationBase(BaseModel):
    status: str = Field(..., example="final")
    code: CodeableConcept
    subject: Reference
    valueQuantity: Quantity
    effectiveDateTime: str


class ObservationCreate(ObservationBase):
    pass


class ObservationRead(ObservationBase):
    id: str
    resourceType: Literal["Observation"] = Field(default="Observation")