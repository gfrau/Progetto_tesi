from sqlalchemy import Column, String, Text
from app.base import Base

class IcdCode(Base):
    __tablename__ = "icd_codes"

    code        = Column(String(10), primary_key=True, index=True)
    display     = Column(Text, nullable=False)
    chapter     = Column(String(50), nullable=True)
    parent      = Column(String(10), nullable=True)