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



@router.post("/test/anonymize")
def test_anonymization(patients: List[Dict] = Body(...)):
    """
    API di test per anonimizzare una lista di risorse FHIR.Patient.
    """
    return [anonymize_patient(p) for p in patients]