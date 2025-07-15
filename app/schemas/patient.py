# schemas/patient.py

from pydantic import BaseModel, Field
from typing import List, Optional


class Identifier(BaseModel):
    system: Optional[str] = None
    value: str = Field(..., example="RSSMRA85M01H501U")


class HumanName(BaseModel):
    family: str = Field(..., example="Rossi")
    given: List[str] = Field(..., example=["Mario"])


class Address(BaseModel):
    line: List[str] = Field(..., example=["Via Roma, 1"])
    city: Optional[str] = Field(None, example="Milano")
    postalCode: Optional[str] = Field(None, example="20100")
    country: Optional[str] = Field(None, example="IT")


class PatientBase(BaseModel):
    identifier: List[Identifier]
    name: List[HumanName]
    gender: Optional[str] = Field(None, example="male")
    birthDate: Optional[str] = Field(None, example="1985-06-15")
    address: Optional[List[Address]] = None


class PatientCreate(PatientBase):
    pass


class PatientRead(PatientBase):
    id: str
    resourceType: str = Field("Patient", const=True)