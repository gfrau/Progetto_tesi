from sqlalchemy import Column, Integer, String, JSON
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.base import Base
from app.models import Patient
from app.services.db import get_db_session

router = APIRouter()

@router.get("/patients")
def get_all_patients(db: Session = Depends(get_db_session)):
    patients = db.query(Patient).all()
    return JSONResponse(content=[p.fhir_data for p in patients])