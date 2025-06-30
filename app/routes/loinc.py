from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.db import get_db_session
from app.models.loinc import LOINCCodes
from app.schemas.lonic import LOINCCodeOut
from typing import List

router = APIRouter()

@router.get("/loinc-codes", response_model=List[LOINCCodeOut])
def list_loinc_codes(db: Session = Depends(get_db_session)):
    return db.query(LOINCCodes).all()