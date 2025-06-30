from pydantic import BaseModel

class LOINCCodeOut(BaseModel):
    code: str
    description: str
    unit: str

    class Config:
        from_attributes = True