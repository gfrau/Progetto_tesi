# schemas/patient.py

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Identifier(BaseModel):
    system: Optional[str] = Field(None, example="http://fhir.example.org/identifiers")
    value: str = Field(..., example="RSSMRA85M01H501U")


class HumanName(BaseModel):
    family: str = Field(..., example="Rossi")
    given: List[str] = Field(..., example=["Mario"])


class Address(BaseModel):
    line: Optional[List[str]] = Field(None, example=["Via Roma, 1"])
    city: Optional[str] = Field(None, example="Selargius")
    district: Optional[str] = Field(None, example="CA")
    postalCode: Optional[str] = Field(None, example="09100")
    country: Optional[str] = Field(None, example="IT")


class PatientBase(BaseModel):
    identifier: List[Identifier]
    name: Optional[List[HumanName]] = None
    gender: Optional[str] = Field(None, example="male")
    birthDate: Optional[str] = Field(None, example="1985-06-15")
    address: Optional[List[Address]] = None


class PatientCreate(PatientBase):
    pass


class PatientRead(PatientBase):
    id: str
    resourceType: Literal["Patient"] = Field(default="Patient")

model_config = {"validate_by_name": True}
