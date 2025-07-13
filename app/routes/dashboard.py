from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.auth.dependencies import require_role
from app.services.db import SessionLocal, get_db_session
from app.models import Patient, Encounter, Observation
from app.utils.session_manager import get_session


router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=require_role("viewer")):
    session_data = get_session(request)
    if not session_data:
        return RedirectResponse(url="/login", status_code=302)
    else:
        return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": user["sub"],
        "role": user["role"]
    })


@router.get("/upload/csv", response_class=HTMLResponse)
def upload_csv(request: Request):
    return templates.TemplateResponse("upload_csv.html", {"request": request})


@router.get("/upload/json", response_class=HTMLResponse)
def upload_json(request: Request):
    return templates.TemplateResponse("upload_json.html", {"request": request})


@router.get("/docs/api", response_class=HTMLResponse)
def api_docs(request: Request):
    return templates.TemplateResponse("api_docs.html", {"request": request})

@router.get("/dashboard/data/patient-gender", response_class=JSONResponse)
def get_patient_gender_data():
    db: Session = next(get_db())
    results = db.query(Patient.gender, func.count(Patient.id)).group_by(Patient.gender).all()
    labels = [r[0] if r[0] else "unknown" for r in results]
    values = [r[1] for r in results]
    return {"labels": labels, "values": values}


@router.get("/dashboard/data/encounter-monthly")
def get_encounter_monthly_data(db: Session = Depends(get_db_session)):
    results = (
        db.query(
            func.to_char(Encounter.start_date, 'YYYY-MM').label("month"),
            func.count().label("count")
        )
        .group_by("month")
        .order_by("month")
        .all()
    )

    labels = [r.month for r in results]
    values = [r.count for r in results]

    return JSONResponse(content={"labels": labels, "values": values})


@router.get("/dashboard/data/observation-by-code")
def get_observation_by_code(db: Session = Depends(get_db_session)):
    from sqlalchemy import func
    query = db.query(
        Observation.code,
        func.count(Observation.id)
    ).group_by(Observation.code).all()

    labels = [row[0] for row in query]
    values = [row[1] for row in query]
    return {"labels": labels, "values": values}
