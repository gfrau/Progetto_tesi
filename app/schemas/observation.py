# schemas/observation.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class Reference(BaseModel):
    reference: Optional[str] = Field(None, example="Patient/RSSMRA85M01H501U")
    identifier: Optional[Dict[str, Any]] = None


class Coding(BaseModel):
    system: Optional[str] = Field(None, example="http://loinc.org")
    code: str = Field(..., example="718-7")
    display: Optional[str] = Field(None, example="Hemoglobin [Mass/volume] in Blood")


class CodeableConcept(BaseModel):
    coding: List[Coding]
    text: Optional[str] = None


class Quantity(BaseModel):
    value: float = Field(..., example=13.2)
    unit: Optional[str] = Field(None, example="g/dL")
    system: Optional[str] = Field(None, example="http://unitsofmeasure.org")
    code: Optional[str] = Field(None, example="g/dL")


class ObservationBase(BaseModel):
    status: str = Field(..., example="final")
    code: CodeableConcept
    subject: Reference
    effectiveDateTime: Optional[str] = Field(None, example="2025-07-01T09:00:00Z")
    valueQuantity: Optional[Quantity] = None


class ObservationCreate(ObservationBase):
    pass


class ObservationRead(ObservationBase):
    id: str
    resourceType: str = Field("Observation", const=True)