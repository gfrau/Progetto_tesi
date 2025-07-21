# app/models/DEL_loinc.py
from sqlalchemy import Column, Integer, String
from app.base import Base

class LOINCCodes(Base):
    __tablename__ = "loinc_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=False)
    unit = Column(String, nullable=False)