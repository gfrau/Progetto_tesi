from typing import List, Dict

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.utils.anonymization import anonymize_patient
from app.services.db import get_db_session
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.observation import Observation

router = APIRouter()

@router.delete("/patients/clear")
def clear_patients(db: Session = Depends(get_db_session), user=require_role("viewer")):
    db.query(Patient).delete()
    db.commit()
    return {"status": "ok", "message": "Tutti i pazienti eliminati"}

@router.delete("/encounters/clear")
def clear_encounters(db: Session = Depends(get_db_session)):
    db.query(Encounter).delete()
    db.commit()
    return {"status": "ok", "message": "Tutti gli encounter eliminati"}

@router.delete("/observations/clear")
def clear_observations(db: Session = Depends(get_db_session)):
    db.query(Observation).delete()
    db.commit()
    return {"status": "ok", "message": "Tutte le observation eliminate"}

@router.post("/test/anonymize")
def test_anonymization(patients: List[Dict] = Body(...)):
    """
    API di test per anonimizzare una lista di risorse FHIR.Patient.
    """
    return [anonymize_patient(p) for p in patients]