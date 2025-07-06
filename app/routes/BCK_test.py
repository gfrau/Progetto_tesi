from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from app.services.db import get_db_session
from app.models import Encounter, Observation, Patient

router = APIRouter()
templates = Jinja2Templates(directory="templates")




@router.get("/encounter-links")
def test_encounter_links(db: Session = Depends(get_db_session)):
    encounters = db.query(Encounter).all()
    broken = [e.identifier for e in encounters if not e.fhir_data.get("subject", {}).get("reference")]
    return {"broken_count": len(broken), "broken_links": broken}

@router.get("/observation-links")
def check_observation_links(db: Session = Depends(get_db_session)):
    observations = db.query(Observation).all()
    if not observations:
        return {
            "broken_count": 0,
            "message": "Nessuna Observation presente nel database.",
            "broken_links": []
        }

    broken = []
    for obs in observations:
        subject = obs.fhir_data.get("subject", {})
        patient_id = subject.get("identifier", {}).get("value") or \
                     subject.get("reference", "").replace("Patient/", "")
        if not patient_id or not db.query(Patient).filter(Patient.identifier == patient_id).first():
            broken.append(obs.identifier)

    return {
        "broken_count": len(broken),
        "broken_links": broken,
        "message": f"{len(broken)} Observation scollegate." if broken else "Tutte le Observation sono collegate."
    }

@router.get("/duplicates")
def test_duplicates(db: Session = Depends(get_db_session)):
    from sqlalchemy import func
    dupes = (
        db.query(Patient.identifier)
        .group_by(Patient.identifier)
        .having(func.count() > 1)
        .all()
    )
    return {"count": len(dupes), "duplicates": [d[0] for d in dupes]}