import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app.services.db import get_db_session
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.observation import Observation

router = APIRouter()


def get_age_group(birth_str: str) -> str:
    try:
        birth = datetime.datetime.strptime(birth_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        age = (today - birth).days // 365
    except Exception:
        return "Sconosciuta"

    if age < 18:
        return "0-17"
    elif age < 40:
        return "18-39"
    elif age < 65:
        return "40-64"
    else:
        return "65+"


def normalize_status(status: str) -> str:
    mapping = {
        "planned": "Pianificato",
        "arrived": "Arrivato",
        "in-progress": "In corso",
        "onleave": "In pausa",
        "finished": "Concluso",
        "cancelled": "Cancellato"
    }
    return mapping.get(status.lower(), "Sconosciuto")


@router.get("/stats")
def get_stats_overview(db: Session = Depends(get_db_session)):
    return JSONResponse(content={
        "patients": db.query(Patient).count(),
        "encounters": db.query(Encounter).count(),
        "observations": db.query(Observation).count()
    })


@router.get("/stats/aggregate/{field}")
def aggregate_stats(field: str, db: Session = Depends(get_db_session)):
    result = {}

    if field == "gender":
        for p in db.query(Patient.fhir_data).all():
            key = p.fhir_data.get("gender", "Sconosciuto")
            result[key] = result.get(key, 0) + 1

    elif field == "status":
        for e in db.query(Encounter.fhir_data).all():
            raw_status = e.fhir_data.get("status", "Sconosciuto")
            key = normalize_status(raw_status)
            result[key] = result.get(key, 0) + 1

    elif field == "code":
        for o in db.query(Observation.fhir_data).all():
            key = o.fhir_data.get("code", {}).get("coding", [{}])[0].get("code", "Sconosciuto")
            result[key] = result.get(key, 0) + 1

    elif field == "age_group":
        for p in db.query(Patient.fhir_data).all():
            birth_str = p.fhir_data.get("birthDate")
            group = get_age_group(birth_str)
            result[group] = result.get(group, 0) + 1

    else:
        return JSONResponse(content={"error": "Campo non supportato"}, status_code=400)

    return JSONResponse(content=result)