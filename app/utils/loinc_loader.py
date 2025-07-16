from app.services.database import SessionLocal
from app.models.loinc import LOINCCodes
from app.utils.mapping_tables import loinc_data

def populate_loinc_codes():
    db = SessionLocal()
    try:
        existing = db.query(LOINCCodes).count()
        if existing == 0:
            for entry in loinc_data:
                db.add(LOINCCodes(**entry))
            db.commit()
    finally:
        db.close()