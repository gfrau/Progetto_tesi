from starlette.responses import JSONResponse
from app.models.patient import Patient
from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.services.db import get_db_session
from app.utils.audit import log_audit_event
from app.auth.dependencies import require_role


router = APIRouter(tags=["Patient"])

# GET tutti i pazienti
@router.get("/patients")
def get_all_patients(
    request: Request,
    db: Session = Depends(get_db_session),
    user = Depends(require_role("viewer"))
):


    patients = db.query(Patient).all()
    session = request.session

    log_audit_event(
        event_type="110101",  # Read
        username=session.get("username", "anon"),
        success=True,
        ip=request.client.host,
        action="R",
        entity_type="Patient"
    )
    return [p.fhir_data for p in patients]


# GET singolo paziente
@router.get("/patients/{identifier}")
def get_patient(
    identifier: str,
    request: Request,
    db: Session = Depends(get_db_session),
    user = Depends(require_role("viewer"))
):

    patient = db.query(Patient).filter_by(identifier=identifier).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    session_data = request.session
    username = session_data.get("username", "anon")
    ip = request.client.host

    log_audit_event(
        event_type="110101",
        username=username,
        success=True,
        ip=ip,
        action="R",  # Read
        entity_type="Patient",
        entity_id=identifier
    )

    return patient.fhir_data


# PUT paziente
@router.put("/patients/{identifier}")
def update_patient(identifier: str, updated_data: dict, request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):

    patient = db.query(Patient).filter(Patient.identifier == identifier).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    patient.fhir_data = updated_data
    db.commit()

    session_data = request.session
    username = session_data.get("username", "anon")
    ip = request.client.host

    log_audit_event(
        event_type="110102",
        username=username,
        success=True,
        ip=ip,
        action="U",
        entity_type="Patient",
        entity_id=identifier
    )
    return patient.fhir_data


# DELETE singolo paziente
@router.delete("/patients/{identifier}")
def delete_patient(identifier: str, request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):

    patient = db.query(Patient).filter(Patient.identifier == identifier).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Paziente non trovato")

    db.delete(patient)
    db.commit()

    session_data = request.session
    username = session_data.get("username", "anon")
    ip = request.client.host

    log_audit_event(
        event_type="110107",  # HL7 AuditEvent - Delete
        username=username,
        success=True,
        ip=ip,
        action="D",  # Delete
        entity_type="Patient",
        entity_id=identifier
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/api/patients/clear")
def delete_all_patients(
    request: Request,
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    deleted_count = db.query(Patient).delete()
    db.commit()

    session_data = request.session
    username = session_data.get("username", "anon")
    ip = request.client.host

    log_audit_event(
        event_type="110107",
        username=username,
        success=True,
        ip=ip,
        action="D",
        entity_type="Patient",
        entity_id="ALL"
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{deleted_count} pazienti eliminati."}
    )