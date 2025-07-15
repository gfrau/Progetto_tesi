# app/routes/observation.py

from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.utils.audit import log_audit_event
from app.services.db import get_db_session
from app.models.fhir_resource import FhirResource
from app.schemas import ObservationCreate, ObservationRead

router = APIRouter(prefix="/observations", tags=["observations"])

@router.get("/", response_model=list[ObservationRead])
def list_observations(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    rows = db.query(FhirResource).filter_by(resource_type="Observation").all()
    log_audit_event(
        event_type="110201",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Observation"
    )
    return [ObservationRead(**row.content) for row in rows]

@router.get("/{identifier}", response_model=ObservationRead)
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
    log_audit_event(
        event_type="110201",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Observation",
        entity_id=identifier
    )
    return ObservationRead(**row.content)

@router.post("/", response_model=ObservationRead, status_code=status.HTTP_201_CREATED)
def create_observation(
    observation: ObservationCreate,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    data = observation.model_dump()
    new = FhirResource(id=data["id"], resource_type="Observation", content=data)
    db.add(new)
    db.commit()
    log_audit_event(
        event_type="110203",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="C",
        entity_type="Observation",
        entity_id=new.id
    )
    return ObservationRead(**new.content)

@router.put("/{identifier}", response_model=ObservationRead)
def update_observation(
    identifier: str,
    updated: ObservationCreate,
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
    data = updated.model_dump()
    row.content = data
    db.commit()
    log_audit_event(
        event_type="110202",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="U",
        entity_type="Observation",
        entity_id=identifier
    )
    return ObservationRead(**row.content)

@router.delete("/clear", response_model=dict)
def clear_observations(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    deleted = db.query(FhirResource).filter_by(resource_type="Observation")\
                   .delete(synchronize_session=False)
    db.commit()
    log_audit_event(
        event_type="110207",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Observation",
        entity_id="ALL"
    )
    return {"deleted_count": deleted}

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
    log_audit_event(
        event_type="110207",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Observation",
        entity_id=identifier
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)