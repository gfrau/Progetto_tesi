from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.models.fhir_resource import FhirResource
from app.services.db import get_db_session

router = APIRouter(prefix="/patients", tags=["patients"])

@router.get("/", response_model=list[dict])
def list_patients(db: Session = Depends(get_db_session)):
    rows = db.query(FhirResource).filter_by(resource_type="Patient").all()
    return [row.content for row in rows]

@router.get("/{identifier}", response_model=dict)
def get_patient(identifier: str, db: Session = Depends(get_db_session)):
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
    return row.content

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_patient(patient: dict, db: Session = Depends(get_db_session)):
    new = FhirResource(id=patient["id"], resource_type="Patient", content=patient)
    db.add(new)
    db.commit()
    return new.content

@router.put("/{identifier}", response_model=dict)
def update_patient(identifier: str, updated_patient: dict, db: Session = Depends(get_db_session)):
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
    row.content = updated_patient
    db.commit()
    return row.content

@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(identifier: str, db: Session = Depends(get_db_session)):
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
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.delete("/", response_model=dict)
def clear_patients(db: Session = Depends(get_db_session)):
    deleted = (
        db.query(FhirResource)
          .filter_by(resource_type="Patient")
          .delete(synchronize_session=False)
    )
    db.commit()
    return {"deleted_count": deleted}