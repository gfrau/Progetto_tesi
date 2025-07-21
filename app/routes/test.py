import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.services.database import get_db_session
from app.models.fhir_resource import FhirResource
from app.models.loinc import LOINCCodes
from app.schemas.loinc import LOINCCodeOut


router = APIRouter(tags=["Test"])

@router.get("/duplicates")
def test_duplicates(db: Session = Depends(get_db_session)):
    """
    Ritorna gli identifier duplicati tra i pazienti.
    """
    identifier_expr = FhirResource.content["identifier"][0]["value"].astext
    rows = (
        db.query(identifier_expr)
          .filter_by(resource_type="Patient")
          .group_by(identifier_expr)
          .having(func.count(identifier_expr) > 1)
          .all()
    )
    # rows è lista di tuple [(identifier,), ...]
    duplicates = [r[0] for r in rows]
    return {"count": len(duplicates), "duplicates": duplicates}

@router.get("/encounter-links")
def test_encounter_links(db: Session = Depends(get_db_session)):
    """
    Controlla che ogni encounter riferisca a un Patient esistente.
    """
    # Prendi tutti gli encounter
    encounter_rows = (
        db.query(FhirResource)
          .filter_by(resource_type="Encounter")
          .all()
    )
    # Prendi tutti gli identifier dei pazienti
    patient_expr = FhirResource.content["identifier"][0]["value"].astext
    patient_rows = (
        db.query(patient_expr)
          .filter_by(resource_type="Patient")
          .all()
    )
    patient_ids = {r[0] for r in patient_rows}

    broken = []
    for row in encounter_rows:
        subject = row.content.get("subject", {})
        patient_id = None
        # estraiamo il reference o usiamo stringa vuota se è None
        ref = subject.get("reference") or ""
        if ref:
            patient_id = ref.replace("Patient/", "")
        else:
            # fallback su identifier.value
            patient_id = subject.get("identifier", {}).get("value", "")

        if not patient_id or patient_id not in patient_ids:
            # identifier of the encounter
            enc_id = row.content.get("identifier", [{}])[0].get("value")
            broken.append(enc_id)

    return {"broken_count": len(broken), "broken_links": broken}

@router.get("/observation-links")
def test_observation_links(db: Session = Depends(get_db_session)):
    """
    Verifica che ogni observation abbia subject.identifier valorizzato.
    """
    obs_rows = (
        db.query(FhirResource)
          .filter_by(resource_type="Observation")
          .all()
    )
    if not obs_rows:
        return {"status": "empty", "message": "Nessuna risorsa Observation presente."}

    broken = []
    for row in obs_rows:
        if not row.content.get("subject", {}).get("identifier", {}).get("value"):
            obs_id = row.content.get("identifier", [{}])[0].get("value")
            broken.append(obs_id)

    return {"status": "ok", "broken_count": len(broken), "broken_links": broken}

@router.get("/observation-loinc")
def test_observation_loinc(db: Session = Depends(get_db_session)):
    """
    Controlla che ogni observation abbia un codice LOINC valido.
    """
    invalid = []
    obs_rows = (
        db.query(FhirResource)
          .filter_by(resource_type="Observation")
          .all()
    )
    for row in obs_rows:
        code = row.content.get("code", {}).get("coding", [{}])[0].get("code")
        if not is_valid_loinc_code(code):
            obs_id = row.content.get("identifier", [{}])[0].get("value")
            invalid.append({"id": obs_id, "code": code})
    return {"invalid_count": len(invalid), "invalid_codes": invalid}

@router.get("/loinc-codes", response_model=List[LOINCCodeOut])
def list_loinc_codes(db: Session = Depends(get_db_session)):
    return db.query(LOINCCodes).all()