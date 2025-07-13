from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.base import Base
from app.models import Encounter
from app.services.db import get_db_session

router = APIRouter(tags=["Encounter"])

@router.get("/encounters")
def get_all_encounters(db: Session = Depends(get_db_session)):
    encounters = db.query(Encounter).all()
    return JSONResponse(content=[e.fhir_data for e in encounters])