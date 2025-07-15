# schemas/encounter.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


class Reference(BaseModel):
    reference: Optional[str] = Field(None, example="Patient/RSSMRA85M01H501U")
    identifier: Optional[Dict[str, Any]] = None


class Coding(BaseModel):
    system: Optional[str] = Field(None, example="http://terminology.hl7.org/CodeSystem/v3-ActCode")
    code: str = Field(..., example="AMB")
    display: Optional[str] = Field(None, example="ambulatory")


class CodeableConcept(BaseModel):
    coding: List[Coding]
    text: Optional[str] = None


class Period(BaseModel):
    start: Optional[str] = Field(None, example="2025-07-01T09:00:00Z")
    end: Optional[str] = Field(None, example="2025-07-01T10:00:00Z")


class EncounterBase(BaseModel):
    status: str = Field(..., example="planned")
    class_: CodeableConcept = Field(..., alias="class")
    subject: Reference
    period: Optional[Period] = None


class EncounterCreate(EncounterBase):
    pass


class EncounterRead(EncounterBase):
    id: str
    resourceType: Literal["Encounter"] = Field(default="Encounter")

model_config = {"validate_by_name": True}