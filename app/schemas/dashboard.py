from pydantic import BaseModel

class DailyIncidence(BaseModel):
    date: str
    value: int

class PeriodComparison(BaseModel):
    period: str
    value: int