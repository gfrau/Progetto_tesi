from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.services.db import get_db_session
from app.models import Patient, Encounter, Observation
from app.utils.mapping import is_valid_loinc_code

router = APIRouter(tags=["test"])

@router.get("/duplicates")
def test_duplicates(db: Session = Depends(get_db_session)):
    result = (
        db.query(Patient.identifier)
        .group_by(Patient.identifier)
        .having(func.count(Patient.identifier) > 1)
        .all()
    )
    return {"count": len(result), "duplicates": result}


@router.get("/encounter-links")
def test_encounter_links(db: Session = Depends(get_db_session)):
    from app.models.patient import Patient

    encounters = db.query(Encounter).all()
    patients = db.query(Patient.identifier).all()
    patient_ids = {p.identifier for p in patients}

    broken = []

    for e in encounters:
        subject = e.fhir_data.get("subject", {})
        patient_id = None

        if "reference" in subject:
            patient_id = subject["reference"].replace("Patient/", "")
        elif "identifier" in subject:
            patient_id = subject["identifier"].get("value")

        if not patient_id or patient_id not in patient_ids:
            broken.append(e.identifier)

    return {"broken_count": len(broken), "broken_links": broken}


@router.get("/observation-links")
def test_observation_links(db: Session = Depends(get_db_session)):
    observations = db.query(Observation).all()

    if not observations:
        return {"status": "empty", "message": "Nessuna risorsa Observation presente."}

    broken = [
        obs.identifier for obs in observations
        if not obs.fhir_data.get("subject", {}).get("identifier", {}).get("value")
    ]
    return {"status": "ok", "broken_count": len(broken), "broken_links": broken}


@router.get("/observation-loinc")
def test_observation_loinc(db: Session = Depends(get_db_session)):
    invalid = []
    for obs in db.query(Observation).all():
        code = obs.fhir_data.get("code", {}).get("coding", [{}])[0].get("code")
        if not is_valid_loinc_code(code):
            invalid.append({"id": obs.identifier, "code": code})
    return {"invalid_count": len(invalid), "invalid_codes": invalid}