from fastapi import APIRouter, Depends
from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.base import Base
from app.models import Observation
from app.services.db import get_db_session

router = APIRouter()

@router.get("/observations")
def get_all_observations(db: Session = Depends(get_db_session)):
    observations = db.query(Observation).all()
    return JSONResponse(content=[o.fhir_data for o in observations])