from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.utils.audit import log_audit_event
from app.services.database import get_db_session
from app.models.fhir_resource import FhirResource
from app.schemas import ConditionCreate, ConditionRead

router = APIRouter(prefix="/condictions", tags=["Condictions"])


@router.post("/", response_model=ConditionRead, status_code=status.HTTP_201_CREATED)
def create_condition(
    condition: ConditionCreate,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    data = condition.model_dump()
    new = FhirResource(id=data["id"], resource_type="Condition", content=data)
    db.add(new)
    db.commit()
    log_audit_event(
        event_type="110110",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="C",
        entity_type="Condition",
        entity_id=new.id
    )
    return ConditionRead(**new.content)


@router.get("/", response_model=List[ConditionRead])
def list_conditions(
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    rows = db.query(FhirResource).filter(FhirResource.resource_type == "Condition").all()
    return [ConditionRead(**row.content) for row in rows]


@router.get("/{identifier}", response_model=ConditionRead)
def get_condition(
    identifier: str,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    row = db.query(FhirResource).filter(
        FhirResource.resource_type == "Condition",
        FhirResource.content["id"].astext == identifier
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Condition not found")
    return ConditionRead(**row.content)


@router.put("/{identifier}", response_model=ConditionRead)
def update_condition(
    identifier: str,
    updated: ConditionCreate,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    row = db.query(FhirResource).filter(
        FhirResource.resource_type == "Condition",
        FhirResource.content["id"].astext == identifier
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Condition not found")
    data = updated.model_dump()
    row.content = data
    db.commit()
    log_audit_event(
        event_type="110112",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="U",
        entity_type="Condition",
        entity_id=identifier
    )
    return ConditionRead(**row.content)


@router.delete("/clear", response_model=dict)
def clear_conditions(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    deleted = db.query(FhirResource).filter_by(resource_type="Condition")\
                   .delete(synchronize_session=False)
    db.commit()
    log_audit_event(
        event_type="110207",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Condition",
        entity_id="ALL"
    )
    return {"deleted_count": deleted}


@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
def delete_condition(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    row = db.query(FhirResource).filter(
        FhirResource.resource_type == "Condition",
        FhirResource.content["id"].astext == identifier
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Condition not found")
    db.delete(row)
    db.commit()
    log_audit_event(
        event_type="110111",
        username=request.session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="D",
        entity_type="Condition",
        entity_id=identifier
    )