import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse

from app.services.db import get_db_session
from app.models.fhir_resource import FhirResource

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
    """
    Restituisce il conteggio di pazienti, encounter e observation.
    """
    patients = db.query(FhirResource).filter_by(resource_type="Patient").count()
    encounters = db.query(FhirResource).filter_by(resource_type="Encounter").count()
    observations = db.query(FhirResource).filter_by(resource_type="Observation").count()
    return JSONResponse(content={
        "patients": patients,
        "encounters": encounters,
        "observations": observations
    })


@router.get("/stats/aggregate/{field}")
def aggregate_stats(field: str, db: Session = Depends(get_db_session)):
    """
    Aggregate statistics by field: gender, status, code, age_group.
    """
    result = {}

    if field == "gender":
        rows = db.query(FhirResource).filter_by(resource_type="Patient").all()
        for row in rows:
            key = row.content.get("gender", "Sconosciuto")
            result[key] = result.get(key, 0) + 1

    elif field == "status":
        rows = db.query(FhirResource).filter_by(resource_type="Encounter").all()
        for row in rows:
            raw_status = row.content.get("status", "Sconosciuto")
            key = normalize_status(raw_status)
            result[key] = result.get(key, 0) + 1

    elif field == "code":
        rows = db.query(FhirResource).filter_by(resource_type="Observation").all()
        for row in rows:
            key = (row.content.get("code", {}).get("coding", [{}])[0].get("code") or "Sconosciuto")
            result[key] = result.get(key, 0) + 1

    elif field == "age_group":
        rows = db.query(FhirResource).filter_by(resource_type="Patient").all()
        for row in rows:
            birth_str = row.content.get("birthDate")
            group = get_age_group(birth_str)
            result[group] = result.get(group, 0) + 1

    else:
        raise HTTPException(status_code=400, detail="Campo non supportato")

    return JSONResponse(content=result)