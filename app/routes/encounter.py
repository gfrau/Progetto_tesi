from fastapi import APIRouter, Depends, Request, HTTPException, status, Response
from sqlalchemy.orm import Session, session
from starlette.responses import JSONResponse

from app.auth.dependencies import require_role
from app.models import Encounter
from app.services.db import get_db_session
from app.utils.audit import log_audit_event

router = APIRouter(tags=["Encounter"])

@router.get("/encounters")
def get_all_encounters(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    encounters = db.query(Encounter).all()
    session = request.session
    username = session.get("username", "anon")
    ip = request.client.hostq

    log_audit_event(
        event_type="110101",
        username=username,
        success=True,
        ip=ip,
        action="R",
        entity_type="Encounter"
    )
    return [e.fhir_data for e in encounters]


@router.get("/encounters/{identifier}")
def get_encounter(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db_session),
    user=Depends(require_role("viewer"))):

    enc = db.query(Encounter).filter_by(identifier=identifier).first()

    if not enc:
        raise HTTPException(404, "Encounter non trovato")
    session = request.session
    log_audit_event(event_type="110101", username=session.get("username","anon"), success=True,
                    ip=request.client.host, action="R", entity_type="Encounter", entity_id=identifier)
    return enc.fhir_data


# PUT (update) encounter
@router.put("/encounters/{identifier}")
def update_encounter(
    identifier: str,
    updated_data: dict,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    encounter = db.query(Encounter).filter_by(identifier=identifier).first()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter non trovato")

    encounter.fhir_data = updated_data
    db.commit()

    session = request.session
    log_audit_event(
        event_type="110102",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="U",
        entity_type="Encounter",
        entity_id=identifier
    )
    return encounter.fhir_data


# DELETE single encounter
@router.delete("/encounters/{identifier}")
def delete_encounter(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    encounter = db.query(Encounter).filter_by(identifier=identifier).first()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter non trovato")

    db.delete(encounter)
    db.commit()

    session = request.session
    log_audit_event(
        event_type="110107",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Encounter",
        entity_id=identifier
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# DELETE ALL encounters
@router.delete("/encounters/clear")
def delete_all_encounters(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):

    deleted_count = db.query(Encounter).delete()
    db.commit()

    session_data = request.session
    username = session_data.get("username", "anon")
    ip = request.client.host

    log_audit_event(
        event_type="110107",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Encounter",
        entity_id="ALL"
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{deleted_count} Encounter eliminati."}
    )
