from sqlalchemy.orm import Session
from app.models.loinc import LoincCode
from app.utils.loinc_data import loinc_data

def populate_loinc_codes(db: Session):
    existing = db.query(LoincCode).count()
    if existing == 0:
        for item in loinc_data:
            db.add(LoincCode(**item))
        db.commit()