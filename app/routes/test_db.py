from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.auth.dependencies import require_role
from app.services.db import get_db_session

router = APIRouter(prefix="/api")

@router.get("/ping-db", summary="Verifica connessione al DB")
def ping_db(db: Session = Depends(get_db_session), user=(require_role("viewer"))):
    try:
        db.execute(text("SELECT 1"))
        return {"message": "Connessione al database OK"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}