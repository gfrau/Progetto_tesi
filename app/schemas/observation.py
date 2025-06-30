from pydantic import BaseModel, Field
from datetime import date

class ObservationCreate(BaseModel):
    identifier: str = Field(..., example="OBS1001")
    subject_id: int = Field(..., example=1)
    code: str = Field(..., example="29463-7")
    value: float = Field(..., example=70.5)
    unit: str = Field(..., example="kg")
    effective_date: date = Field(..., example="2023-05-01")