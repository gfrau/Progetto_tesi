from fastapi import APIRouter, Depends, Request, HTTPException, status, Response
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.auth.dependencies import require_role
from app.services.db import get_db_session
from app.utils.audit import log_audit_event
from app.models.fhir_resource import FhirResource

router = APIRouter(prefix="/observations", tags=["Observations"])

@router.get("/", response_model=list[dict])
def list_observations(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    rows = db.query(FhirResource).filter_by(resource_type="Observation").all()
    session = request.session
    log_audit_event(
        event_type="110201",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Observation"
    )
    return [row.content for row in rows]

@router.get("/{identifier}", response_model=dict)
def get_observation(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    row = (
        db.query(FhirResource)
          .filter(
              FhirResource.resource_type == "Observation",
              FhirResource.content["id"].astext == identifier
          )
          .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Observation not found")
    session = request.session
    log_audit_event(
        event_type="110201",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Observation",
        entity_id=identifier
    )
    return row.content

@router.put("/{identifier}", response_model=dict)
def update_observation(
    identifier: str,
    updated_data: dict,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    row = (
        db.query(FhirResource)
          .filter(
              FhirResource.resource_type == "Observation",
              FhirResource.content["id"].astext == identifier
          )
          .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Observation not found")
    row.content = updated_data
    db.commit()
    session = request.session
    log_audit_event(
        event_type="110202",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="U",
        entity_type="Observation",
        entity_id=identifier
    )
    return row.content

@router.delete("/clear", response_model=dict)
def delete_all_observations(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    deleted_count = (
        db.query(FhirResource)
          .filter_by(resource_type="Observation")
          .delete(synchronize_session=False)
    )
    db.commit()
    session = request.session
    log_audit_event(
        event_type="110207",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Observation",
        entity_id="ALL"
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{deleted_count} Observation eliminati."}
    )

@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
def delete_observation(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    row = (
        db.query(FhirResource)
          .filter(
              FhirResource.resource_type == "Observation",
              FhirResource.content["id"].astext == identifier
          )
          .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Observation not found")
    db.delete(row)
    db.commit()
    session = request.session
    log_audit_event(
        event_type="110207",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Observation",
        entity_id=identifier
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)