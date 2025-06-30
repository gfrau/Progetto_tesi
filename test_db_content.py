# test_db_content.py

from app.services.db import SessionLocal
from app.models import Patient, Encounter, Observation


def count_records():
    db = SessionLocal()
    try:
        patient_count = db.query(Patient).count()
        encounter_count = db.query(Encounter).count()
        observation_count = db.query(Observation).count()

        print(f"Patient: {patient_count} record")
        print(f"Encounter: {encounter_count} record")
        print(f"Observation: {observation_count} record")
    finally:
        db.close()

if __name__ == "__main__":
    count_records()