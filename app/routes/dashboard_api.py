import datetime
from fastapi import HTTPException, Query
from sqlalchemy import cast, String
from fastapi.responses import JSONResponse
from app.models.dashboard import DailyIncidence

from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.fhir_resource import FhirResource
from app.routes.condition import require_role, get_db_session
from app.schemas.dashboard import PeriodComparison
from pydantic import BaseModel

class PeriodComparison(BaseModel):
    period: str
    value: int

router = APIRouter(
    tags=["Dashboard"],
    prefix="/dashboard"
)


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


@router.get("/stats",
            tags=["Dashboard"],
            summary="Visualizza le statistiche generali")
def get_stats_overview(db: Session = Depends(get_db_session)):
    """
    Restituisce il conteggio di pazienti, encounter e observation.
    """
    patients = db.query(FhirResource).filter_by(resource_type="Patient").count()
    encounters = db.query(FhirResource).filter_by(resource_type="Encounter").count()
    observations = db.query(FhirResource).filter_by(resource_type="Observation").count()
    conditions = db.query(FhirResource).filter_by(resource_type="Condition").count()

    return JSONResponse(content={
        "patients": patients,
        "encounters": encounters,
        "observations": observations,
        "conditions": conditions
    })


@router.get("/stats/aggregate/{field}",
tags = ["Dashboard"],
summary = "Aggregazione delle statistiche per campo: gender, status, code, age_group.")
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



# Incidenza giornaliera

@router.get(
    "/conditions/daily-incidence",
    response_model=list[DailyIncidence],
    summary="Incidenza giornaliera delle Condition (zero-fill)",
)
def conditions_daily_incidence(
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer")),
    start: date | None = Query(None, description="Data inizio (YYYY-MM-DD)"),
    end:   date | None = Query(None, description="Data fine  (YYYY-MM-DD)"),
):
    """
    Serie storica: numero di nuove Condition per recordedDate,
    include anche giorni con valore 0 (zero-fill).
    """
    # 1) Prendo min/max recordedDate
    min_max = db.query(
        func.min(FhirResource.content["recordedDate"].astext),
        func.max(FhirResource.content["recordedDate"].astext),
    ).filter(FhirResource.resource_type == "Condition").one()
    min_date_str, max_date_str = min_max

    # Se non ci sono Condition, restituisco lista vuota
    if not min_date_str or not max_date_str:
        return []

    # 2) Calcolo l'intervallo complessivo
    try:
        overall_start = date.fromisoformat(min_date_str)
        overall_end   = date.fromisoformat(max_date_str)
    except Exception as e:
        raise HTTPException(500, f"Errore parsing date in DB: {e}")

    # Sovrascrivo con start/end se forniti dall'utente
    start_date = start or overall_start
    end_date   = end   or overall_end

    if start_date > end_date:
        raise HTTPException(400, "start non può essere successiva a end")

    # 3) Costruisco lista di tutti i giorni
    days: list[date] = []
    d = start_date
    while d <= end_date:
        days.append(d)
        d += timedelta(days=1)

    # 4) Query conteggi reali
    raw_counts = db.query(
        FhirResource.content["recordedDate"].astext.label("date"),
        func.count().label("value"),
    ).filter(
        FhirResource.resource_type == "Condition",
        FhirResource.content["recordedDate"].astext.between(
            start_date.isoformat(), end_date.isoformat()
        )
    ).group_by("date").all()
    counts = {row.date: row.value for row in raw_counts}

    # 5) Zero-fill e build result
    result: list[DailyIncidence] = []
    for day in days:
        iso = day.isoformat()
        result.append(DailyIncidence(date=iso, value=counts.get(iso, 0)))

    return result


@router.get(
    "/patients/by-province",
    summary="Pazienti per provincia"
)
def patients_by_province(
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    """
    Conteggia i Patient raggruppati per address[0].district (provincia).
    """
    province_expr = (
        FhirResource.content["address"][0]["district"]
            .astext
            .label("province")
    )

    q = (
        db.query(
            province_expr,
            func.count().label("value")
        )
        .filter(FhirResource.resource_type == "Patient")
        .group_by(province_expr)
        .order_by(province_expr)
    )

    return [{"province": r.province, "value": r.value} for r in q]


@router.get("/conditions/incidence-period", response_model=list[PeriodComparison],
            tags = ["Dashboard"],
            summary = "Incidenza per periodo"
            )


@router.get(
    "/conditions/incidence-period",
    response_model=list[PeriodComparison],
    summary="Confronto incidenza tra due periodi",
)
def conditions_incidence_period(
    start1: date = Query(..., description="Inizio periodo 1"),
    end1:   date = Query(..., description="Fine periodo 1"),
    start2: date = Query(..., description="Inizio periodo 2"),
    end2:   date = Query(..., description="Fine periodo 2"),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    # Conta per il primo periodo
    count1 = (
        db.query(func.count())
          .filter(
            FhirResource.resource_type=="Condition",
            FhirResource.content["recordedDate"].astext.between(start1.isoformat(), end1.isoformat())
          )
          .scalar() or 0
    )
    # Conta per il secondo periodo
    count2 = (
        db.query(func.count())
          .filter(
            FhirResource.resource_type=="Condition",
            FhirResource.content["recordedDate"].astext.between(start2.isoformat(), end2.isoformat())
          )
          .scalar() or 0
    )
    # Restituisco sempre una lista di due entry
    return [
      PeriodComparison(period="Periodo 1", value=count1),
      PeriodComparison(period="Periodo 2", value=count2),
    ]