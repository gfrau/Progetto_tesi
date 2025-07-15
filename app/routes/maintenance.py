from typing import List, Dict

from fastapi import APIRouter, Depends, Body
from app.auth.dependencies import require_role
from app.utils.anonymization import anonymize_patient

router = APIRouter()

@router.post("/test/anonymize", dependencies=[Depends(require_role("admin"))], response_model=List[Dict])
def test_anonymization(patients: List[Dict] = Body(...)):
    """
    API di test per anonimizzare una lista di risorse FHIR.Patient.
    """
    return [anonymize_patient(p) for p in patients]