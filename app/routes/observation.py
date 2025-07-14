from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from app.models.observation import Observation
from app.services.db import get_db_session
from app.utils.audit import log_audit_event
from app.auth.dependencies import require_role

router = APIRouter(tags=["Observation"])

# GET all observations
@router.get("/observations")
def get_all_observations(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    observations = db.query(Observation).all()

    session = request.session

    log_audit_event(
        event_type="110101",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Observation"
    )
    return [o.fhir_data for o in observations]

# GET single observation
@router.get("/observations/{identifier}")
def get_observation(identifier: str, request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    observation = db.query(Observation).filter(Observation.identifier == identifier).first()

    if not observation:
        raise HTTPException(status_code=404, detail="Observation non trovata")

    session = request.session

    log_audit_event(
        event_type="110101",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Observation",
        entity_id=identifier
    )
    return observation.fhir_data

# PUT observation
@router.put("/observations/{identifier}")
def update_observation(identifier: str, updated_data: dict, request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    observation = db.query(Observation).filter(Observation.identifier == identifier).first()

    if not observation:
        raise HTTPException(status_code=404, detail="Observation non trovata")

    observation.fhir_data = updated_data
    db.commit()

    session = request.session

    log_audit_event(
        event_type="110102",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="U",
        entity_type="Observation",
        entity_id=identifier
    )
    return observation.fhir_data


# DELETE all observations
@router.delete("/observations/clear")
def delete_all_observations(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    deleted_count = db.query(Observation).delete()
    db.commit()

    session_data = request.session

    log_audit_event(
        event_type="110107",
        username=session_data.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Observation",
        entity_id="ALL"
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{deleted_count} osservazioni eliminate."}
    )



# DELETE single observation
@router.delete("/observations/{identifier}")
def delete_observation(identifier: str, request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    observation = db.query(Observation).filter(Observation.identifier == identifier).first()
    if not observation:
        raise HTTPException(status_code=404, detail="Observation non trovata")

    db.delete(observation)
    db.commit()

    session = request.session

    log_audit_event(
        event_type="110107",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Observation",
        entity_id=identifier
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

