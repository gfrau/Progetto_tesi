from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class PatientCreate(BaseModel):
    identifier: Optional[str] = Field(None, example="12345")
    gender: Optional[str] = Field(None, example="male")
    birth_date: Optional[date] = Field(None, example="1985-06-15")