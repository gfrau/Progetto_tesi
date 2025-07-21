from pydantic import BaseModel

class DailyIncidence(BaseModel):
    date: str   # formato "YYYY-MM-DD"
    value: int