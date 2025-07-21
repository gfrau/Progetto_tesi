from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.auth.dependencies import require_role
from app.services.database import get_db_session, reset_database
from app.models.fhir_resource import FhirResource

router = APIRouter(prefix="/test-db", tags=["Test-db"])




@router.get("/ping", response_model=dict)
def ping_db(db: Session = Depends(get_db_session)):
    """
    Endpoint di test: verifica connessione al database.
    """
    try:
        # Esegue una query leggera per testare la connessione
        db.execute("SELECT 1")
        return {"ping": "pong"}
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database connection failed")

@router.delete(
    "/reset",
    response_model=dict,
    dependencies=[Depends(require_role("admin"))]
)
def reset_db(db: Session = Depends(get_db_session)):
    """
    Endpoint di test: reset della tabella fhir_resources.
    Ritorna il numero di record eliminati.
    """
    # Conta quante risorse esistono prima del reset
    count_before = db.query(FhirResource).count()
    # Esegui il reset (svuota fhir_resources)
    reset_database()
    return {"deleted_count": count_before}