# app/schemas/condition.py

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class Coding(BaseModel):
    system: Optional[str] = Field(..., example="http://hl7.org/fhir/sid/icd-10")
    code: str = Field(..., example="E11")
    display: Optional[str] = Field(None, example="Diabetes mellitus type 2")


class CodeableConcept(BaseModel):
    coding: List[Coding]
    text: Optional[str] = None


class Reference(BaseModel):
    identifier: dict


class ConditionBase(BaseModel):
    subject: Reference
    code: CodeableConcept
    clinicalStatus: CodeableConcept
    verificationStatus: CodeableConcept
    recordedDate: Optional[str] = None


class ConditionCreate(ConditionBase):
    id: Optional[str] = None


class ConditionRead(ConditionBase):
    id: str
    resourceType: Literal["Condition"] = "Condition"