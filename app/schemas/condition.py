from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from typing import Union
from pydantic import field_validator

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
    clinicalStatus: CodeableConcept
    verificationStatus: Optional[CodeableConcept]
    code: CodeableConcept
    subject: Reference
    recordedDate: Optional[str] = None


class ConditionCreate(ConditionBase):
    id: Optional[str] = None


CLIN_SYS = "http://terminology.hl7.org/CodeSystem/condition-clinical"
VER_SYS  = "http://terminology.hl7.org/CodeSystem/condition-ver-status"

class ConditionRead(BaseModel):
    clinicalStatus: Union[CodeableConcept, str]
    verificationStatus: Union[CodeableConcept, str]
    resourceType: Literal["Condition"] = "Condition"
    id: str
    subject: Reference
    recordedDate: Optional[str]
    clinicalStatus: CodeableConcept
    verificationStatus: CodeableConcept
    code: CodeableConcept

    @field_validator("clinicalStatus", "verificationStatus", mode="before")
    def _str_to_codeable(cls, v, info):
        if isinstance(v, str):
            system = CLIN_SYS if info.field_name == "clinicalStatus" else VER_SYS
            return {
                "coding": [{
                    "system": system,
                    "code": v,
                    "display": v.capitalize()
                }],
                "text": v
            }
        return v