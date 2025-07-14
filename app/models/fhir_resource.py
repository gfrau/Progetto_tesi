from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from app.base import Base


class FhirResource(Base):
    __tablename__ = "fhir_resources"

    id = Column(Text, primary_key=True)
    resource_type = Column(Text, nullable=False, index=True)
    content = Column(JSONB, nullable=False)
