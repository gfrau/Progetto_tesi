
import csv, io, logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.services.database import get_db_session, save_resource
from app.models.fhir_resource import FhirResource
from app.auth.dependencies import require_role
from app.utils.transform import csv_to_patient, validate_csv_headers

router = APIRouter(tags=["Upload CSV/JSON"])
logger = logging.getLogger(__name__)

EXPECTED_HEADERS = {
    "Patient": {"nome", "cognome", "codice_fiscale", "data_nascita", "telefono", "indirizzo", "cap", "citta", "provincia", "gender"}
}

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
