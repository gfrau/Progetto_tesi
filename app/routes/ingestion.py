
import csv, io, logging
import json

from anyio.streams import file
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.database import get_db_session, save_resource, save_encounter_if_valid
from app.models.fhir_resource import FhirResource
from app.auth.dependencies import require_role
from app.utils.transform import csv_to_patient, validate_csv_headers, csv_to_encounter, EXPECTED_HEADERS

router = APIRouter(tags=["Upload CSV/JSON"])
logger = logging.getLogger(__name__)



@router.post("/upload/patient/csv")
def upload_patient_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    raw = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw))
    if not validate_csv_headers(reader.fieldnames, EXPECTED_HEADERS["Patient"]):
        raise HTTPException(status_code=400, detail="Intestazioni CSV non valide per risorsa Patient.")

    inserted, skipped, errors = 0, 0, []
    for row in reader:
        try:
            fhir_data = csv_to_patient(row)
            resource_id = fhir_data.get("id")
            exists = db.query(FhirResource).filter(FhirResource.resource_type == "Patient", FhirResource.id == resource_id).first()
            if exists:
                logger.info(f"Duplicate Patient con id {resource_id}")
                skipped += 1
                continue
            save_resource(db, "Patient", fhir_data)
            inserted += 1
        except Exception as e:
            skipped += 1
            logger.error(f"Errore: {e} - Riga: {row}")
            errors.append(f"Errore: {e} - Riga: {row}")

    return {"inserted": inserted, "skipped": skipped, "errors": errors}


@router.post("/upload/encounter/csv")
def upload_encounter_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    raw = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw))

    if not validate_csv_headers(reader.fieldnames, "Encounter"):
        raise HTTPException(status_code=400, detail="Intestazioni CSV non valide per risorsa Encounter.")

    inserted, skipped, errors = 0, 0, []

    for row in reader:
        try:
            fhir_data = csv_to_encounter(row)

            # Controllo esistenza Patient (identifier hashato)
            patient_id = fhir_data.get("subject", {}).get("identifier", {}).get("value")
            if not patient_id:
                raise ValueError("CF hashato mancante nel campo subject.identifier")

            patient_exists = db.query(FhirResource).filter(
                FhirResource.resource_type == "Patient",
                FhirResource.content["identifier"][0]["value"].astext == patient_id
            ).first()

            if not patient_exists:
                msg = f"Encounter scartato: paziente {patient_id} non trovato."
                logger.warning(msg)
                errors.append(msg)
                skipped += 1
                continue

            # Deduplicazione basata su identifier Encounter
            encounter_id = fhir_data.get("identifier", [{}])[0].get("value")
            if not encounter_id:
                raise ValueError("Encounter identifier mancante")

            exists = db.query(FhirResource).filter(
                FhirResource.resource_type == "Encounter",
                FhirResource.content["identifier"][0]["value"].astext == encounter_id
            ).first()

            if exists:
                logger.info(f"Duplicate Encounter con identifier {encounter_id}")
                skipped += 1
                continue

            # Salvataggio
            save_resource(db, "Encounter", fhir_data)
            inserted += 1

        except Exception as e:
            msg = f"Errore: {e} - Riga: {row}"
            logger.error(msg)
            errors.append(msg)
            skipped += 1

    return {
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors
    }