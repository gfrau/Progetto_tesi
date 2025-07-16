from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.utils.audit import log_audit_event
from app.services.database import get_db_session
from app.models.fhir_resource import FhirResource
from app.schemas import EncounterCreate, EncounterRead

router = APIRouter(prefix="/encounters", tags=["encounters"])

@router.get("/", response_model=list[EncounterRead])
def list_encounters(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    rows = db.query(FhirResource).filter_by(resource_type="Encounter").all()
    log_audit_event(
        event_type="110101",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Encounter"
    )
    return [EncounterRead(**row.content) for row in rows]

@router.get("/{identifier}", response_model=EncounterRead)
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
    log_audit_event(
        event_type="110101",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Encounter",
        entity_id=identifier
    )
    return EncounterRead(**row.content)

@router.post("/", response_model=EncounterRead, status_code=status.HTTP_201_CREATED)
def create_encounter(
    encounter: EncounterCreate,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    data = encounter.model_dump()
    new = FhirResource(id=data["id"], resource_type="Encounter", content=data)
    db.add(new)
    db.commit()
    log_audit_event(
        event_type="110103",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="C",
        entity_type="Encounter",
        entity_id=new.id
    )
    return EncounterRead(**new.content)

@router.put("/{identifier}", response_model=EncounterRead)
def update_encounter(
    identifier: str,
    updated: EncounterCreate,
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
    data = updated.model_dump()
    row.content = data
    db.commit()
    log_audit_event(
        event_type="110102",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="U",
        entity_type="Encounter",
        entity_id=identifier
    )
    return EncounterRead(**row.content)

@router.delete("/clear", response_model=dict)
def clear_encounters(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    deleted = db.query(FhirResource).filter_by(resource_type="Encounter")\
                   .delete(synchronize_session=False)
    db.commit()
    log_audit_event(
        event_type="110107",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Encounter",
        entity_id="ALL"
    )
    return {"deleted_count": deleted}

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
    log_audit_event(
        event_type="110107",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Encounter",
        entity_id=identifier
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)