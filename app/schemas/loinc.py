# schemas/loinc.py

from pydantic import BaseModel, Field
from typing import Literal


class LOINCCodeOut(BaseModel):
    code: str = Field(..., example="718-7")
    display: str = Field(..., example="Hemoglobin [Mass/volume] in Blood")
    system: Literal["http://loinc.org"] = Field(default="http://loinc.org")