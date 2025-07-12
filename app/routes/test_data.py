from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.db import get_db_session
from app.models import Patient, Encounter, Observation

router = APIRouter(tags=["Data View"])

@router.get("/patients")
def get_all_patients(db: Session = Depends(get_db_session)):
    return [p.fhir_data for p in db.query(Patient).all()]

@router.get("/encounters")
def get_all_encounters(db: Session = Depends(get_db_session)):
    return [e.fhir_data for e in db.query(Encounter).all()]

@router.get("/observations")
def get_all_observations(db: Session = Depends(get_db_session)):
    return [o.fhir_data for o in db.query(Observation).all()]