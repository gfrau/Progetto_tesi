from fastapi import APIRouter, Depends, Request, HTTPException, status, Response
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.auth.dependencies import require_role
from app.services.db import get_db_session
from app.utils.audit import log_audit_event
from app.models.fhir_resource import FhirResource

router = APIRouter(prefix="/encounters", tags=["encounters"])

@router.get("/", response_model=list[dict])
def list_encounters(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    rows = db.query(FhirResource).filter_by(resource_type="Encounter").all()
    session = request.session
    log_audit_event(
        event_type="110101",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Encounter"
    )
    return [row.content for row in rows]

@router.get("/{identifier}", response_model=dict)
def get_encounter(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    row = (
        db.query(FhirResource)
          .filter(
              FhirResource.resource_type == "Encounter",
              FhirResource.content["id"].astext == identifier
          )
          .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Encounter not found")
    session = request.session
    log_audit_event(
        event_type="110101",
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Encounter",
        entity_id=identifier
    )
    return row.content

@router.put("/{identifier}", response_model=dict)
def update_encounter(
    identifier: str,
    updated_data: dict,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    row = (
        db.query(FhirResource)
          .filter(
              FhirResource.resource_type == "Encounter",
              FhirResource.content["id"].astext == identifier
          )
          .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Encounter not found")
    row.content = updated_data
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
    return row.content

@router.delete("/clear", response_model=dict)
def delete_all_encounters(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    deleted_count = (
        db.query(FhirResource)
          .filter_by(resource_type="Encounter")
          .delete(synchronize_session=False)
    )
    db.commit()
    session = request.session
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

@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
def delete_encounter(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    row = (
        db.query(FhirResource)
          .filter(
              FhirResource.resource_type == "Encounter",
              FhirResource.content["id"].astext == identifier
          )
          .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Encounter not found")
    db.delete(row)
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