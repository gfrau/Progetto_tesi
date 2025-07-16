import csv
import io
import json

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.services.database import get_db_session, save_resource
from app.utils.transform import csv_to_patient, csv_to_encounter, csv_to_observation, map_json_to_fhir_resource
from app.auth.dependencies import require_role
from app.models.fhir_resource import FhirResource

router = APIRouter(tags=["Upload CSV/JSON"])

# Headers attesi per l'upload CSV
EXPECTED_HEADERS = {
    "Encounter": {"encounter_id", "codice_fiscale", "status", "class", "data_inizio", "data_fine"},
    "Patient": {"nome", "cognome", "codice_fiscale", "data_nascita", "telefono", "indirizzo", "cap", "citta", "gender"},
    "Observation": {"observation_id","codice_fiscale","codice_lonic","descrizione_test","valore","unita","data_osservazione"}
}

def validate_csv_headers(headers: list[str], resource_type: str) -> bool:
    if not headers or resource_type not in EXPECTED_HEADERS:
        return False
    headers_lower = set(h.strip().lower() for h in headers)
    expected = set(h.lower() for h in EXPECTED_HEADERS[resource_type])
    return expected.issubset(headers_lower)

# --- Upload CSV endpoints ---
@router.post("/upload/patient/csv")
def upload_patient_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    reader = csv.DictReader(io.StringIO(file.file.read().decode("utf-8")))
    if not validate_csv_headers(reader.fieldnames, "Patient"):
        raise HTTPException(status_code=400, detail="Le intestazioni del file CSV non corrispondono alla risorsa Patient.")

    inserted, skipped = 0, 0
    for row in reader:
        try:
            fhir_data = csv_to_patient(row)
            # Assicurati che fhir_data includa 'id'
            if not fhir_data.get("id"):
                identifier = fhir_data.get("identifier", [{}])[0].get("value")
                fhir_data["id"] = identifier
            try:
                save_resource(db, "Patient", fhir_data)
                inserted += 1
            except IntegrityError:
                db.rollback()
                skipped += 1
        except Exception:
            skipped += 1
    return {"inserted": inserted, "skipped": skipped}

@router.post("/upload/encounter/csv")
def upload_encounter_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    reader = csv.DictReader(io.StringIO(file.file.read().decode("utf-8")))
    if not validate_csv_headers(reader.fieldnames, "Encounter"):
        raise HTTPException(status_code=400, detail="Le intestazioni del file CSV non corrispondono alla risorsa Encounter.")

    inserted, skipped = 0, 0
    for row in reader:
        try:
            fhir_data = csv_to_encounter(row)
            patient_id = fhir_data.get("subject", {}).get("identifier", {}).get("value", "")
            exists = db.query(FhirResource).filter_by(resource_type="Patient").filter(FhirResource.content["identifier"][0]["value"].astext == patient_id).first()
            if not exists:
                skipped += 1
                continue
            # Ensure id present
            if not fhir_data.get("id"):
                fhir_data["id"] = fhir_data.get("identifier", [{}])[0].get("value")
            try:
                save_resource(db, "Encounter", fhir_data)
                inserted += 1
            except IntegrityError:
                db.rollback()
                skipped += 1
        except Exception:
            skipped += 1
    return {"inserted": inserted, "skipped": skipped}

@router.post("/upload/observation/csv")
def upload_observation_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    reader = csv.DictReader(io.StringIO(file.file.read().decode("utf-8")))
    if not validate_csv_headers(reader.fieldnames, "Observation"):
        raise HTTPException(status_code=400, detail="Le intestazioni del file CSV non corrispondono alla risorsa Observation.")

    inserted, skipped, errors = 0, 0, []
    for row in reader:
        try:
            fhir_data = csv_to_observation(row)
            codice = fhir_data.get("subject", {}).get("identifier", {}).get("value", "")
            exists = db.query(FhirResource).filter_by(resource_type="Patient").filter(FhirResource.content["identifier"][0]["value"].astext == codice).first()
            if not exists:
                errors.append(f"Paziente non trovato: {codice}")
                skipped += 1
                continue
            if not fhir_data.get("id"):
                fhir_data["id"] = fhir_data.get("identifier", [{}])[0].get("value")
            try:
                save_resource(db, "Observation", fhir_data)
                inserted += 1
            except IntegrityError:
                db.rollback()
                errors.append(f"Duplicato: {fhir_data.get('identifier',[{}])[0].get('value')}")
                skipped += 1
        except Exception as e:
            skipped += 1
            errors.append(str(e))
    return {"inserted": inserted, "skipped": skipped, "errors": errors}

# --- Upload JSON mixed endpoint ---
@router.post("/upload/json/bulk")
def upload_json_bulk(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    try:
        file.file.seek(0)
        data = json.loads(file.file.read().decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="JSON non valido.")
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Ci si aspetta un array di oggetti FHIR.")

    inserted, skipped, errors = 0, 0, []
    for entry in data:
        try:
            resource_type, fhir_data = map_json_to_fhir_resource(entry)
            if not fhir_data.get("id") and resource_type in ("Patient", "Encounter", "Observation"):
                fhir_data["id"] = fhir_data.get("identifier", [{}])[0].get("value")
            try:
                save_resource(db, resource_type, fhir_data)
                inserted += 1
            except IntegrityError:
                db.rollback()
                skipped += 1
        except Exception as e:
            skipped += 1
            identifier = entry.get("identifier", [{}])[0].get("value", "sconosciuto")
            resource_type = entry.get("resourceType", "Unknown")
            error_msg = f"{resource_type} {identifier}: {str(e)}"
            errors.append(error_msg)
    return {"inserted": inserted, "skipped": skipped, "errors": errors}