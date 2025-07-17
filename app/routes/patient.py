from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.utils.audit import log_audit_event
from app.services.database import get_db_session
from app.models.fhir_resource import FhirResource
from app.schemas import PatientCreate, PatientRead

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("/", response_model=list[PatientRead])
def list_patients(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    rows = db.query(FhirResource).filter_by(resource_type="Patient").all()
    log_audit_event(
        event_type="110001",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Patient"
    )
    return [PatientRead(**row.content) for row in rows]

@router.get("/{identifier}", response_model=PatientRead)
def get_patient(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("viewer"))
):
    row = (
        db.query(FhirResource)
          .filter(
              FhirResource.resource_type == "Patient",
              FhirResource.content["identifier"][0]["value"].astext == identifier
          )
          .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    log_audit_event(
        event_type="110001",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Patient",
        entity_id=identifier
    )
    return PatientRead(**row.content)

@router.post("/", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(
    patient: PatientCreate,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    data = patient.model_dump()
    new = FhirResource(id=data["identifier"][0]["value"], resource_type="Patient", content=data)
    db.add(new)
    db.commit()
    log_audit_event(
        event_type="110003",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="C",
        entity_type="Patient",
        entity_id=new.id
    )
    return PatientRead(**new.content)

@router.put("/{identifier}", response_model=PatientRead)
def update_patient(
    identifier: str,
    updated_patient: PatientCreate,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    row = (
        db.query(FhirResource)
          .filter(
              FhirResource.resource_type == "Patient",
              FhirResource.content["identifier"][0]["value"].astext == identifier
          )
          .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    data = updated_patient.model_dump()
    row.content = data
    db.commit()
    log_audit_event(
        event_type="110002",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="U",
        entity_type="Patient",
        entity_id=identifier
    )
    return PatientRead(**row.content)

@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    row = (
        db.query(FhirResource)
          .filter(
              FhirResource.resource_type == "Patient",
              FhirResource.content["identifier"][0]["value"].astext == identifier
          )
          .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(row)
    db.commit()
    log_audit_event(
        event_type="110007",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Patient",
        entity_id=identifier
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.delete("/", response_model=dict)
def clear_patients(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    deleted = (
        db.query(FhirResource)
          .filter_by(resource_type="Patient")
          .delete(synchronize_session=False)
    )
    db.commit()
    log_audit_event(
        event_type="110007",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Patient",
        entity_id="ALL"
    )
    return {"deleted_count": deleted}