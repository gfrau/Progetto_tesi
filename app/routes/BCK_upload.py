
import csv
import io
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.services.db import get_db_session, save_or_deduplicate_patient
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.observation import Observation
from app.utils.loinc import is_valid_loinc_code
from app.utils.mapping import csv_to_patient, csv_to_encounter, csv_to_observation, map_csv_to_fhir_resource

router = APIRouter()

EXPECTED_HEADERS = {
    "Encounter": {"encounter_id", "codice_fiscale", "status", "class", "data_inizio", "data_fine"},
    "Patient": {"nome", "cognome", "codice_fiscale", "data_nascita", "telefono", "indirizzo", "cap", "citta", "gender"},
    "Observation": {"observation_id", "codice_fiscale", "codice", "valore", "unita", "data_osservazione", "descrizione_test"}
}

def validate_csv_headers(headers: list[str], resource_type: str) -> bool:
    """
    Verifica che le intestazioni del CSV siano compatibili con il tipo di risorsa.
    """
    if not headers or resource_type not in EXPECTED_HEADERS:
        return False
    headers_lower = set(h.strip().lower() for h in headers)
    expected = set(h.lower() for h in EXPECTED_HEADERS[resource_type])
    return expected.issubset(headers_lower)


@router.post("/upload/patient/csv")
def upload_patient_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    try:
        contents = file.file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Errore nella lettura del file CSV: {str(e)}")

    inserted, skipped, errors = 0, 0, []

    for idx, row in enumerate(reader, start=2):  # Start=2 per saltare header
        try:
            fhir_data = csv_to_patient(row)
            success, _ = save_or_deduplicate_patient(db, fhir_data)
            if success:
                inserted += 1
            else:
                skipped += 1
                errors.append(f"Riga {idx}: duplicato")
        except Exception as e:
            skipped += 1
            errors.append(f"Riga {idx}: {str(e)}")

    return {"inserted": inserted, "skipped": skipped, "errors": errors}


from app.utils.mapping import csv_to_encounter
from app.models import Patient, Encounter

@router.post("/upload/encounter/csv")
def upload_encounter_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    contents = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))

    # Validazione intestazioni
    if not validate_csv_headers(reader.fieldnames, "Encounter"):
        raise HTTPException(status_code=400, detail="Le intestazioni del file CSV non corrispondono alla risorsa Encounter.")

    inserted, skipped = 0, 0
    errors = []

    for row in reader:
        try:
            fhir_data = csv_to_encounter(row)
            reference = fhir_data.get("subject", {}).get("reference", "")
            patient_identifier = reference.replace("Patient/", "").strip() if reference.startswith("Patient/") else None

            # Verifica che il paziente esista già nel DB
            if not db.query(Patient).filter(Patient.identifier == patient_identifier).first():
                skipped += 1
                errors.append(f"Encounter scartato: paziente {patient_identifier} non trovato.")
                continue

            identifier = fhir_data.get("identifier", [{}])[0].get("value")
            if db.query(Encounter).filter_by(identifier=identifier).first():
                skipped += 1
                errors.append(f"Encounter duplicato con ID {identifier}")
                continue

            db.add(Encounter(identifier=identifier, fhir_data=fhir_data))
            inserted += 1
        except Exception as e:
            skipped += 1
            errors.append(f"Errore nella riga: {str(e)}")

    db.commit()
    return {"inserted": inserted, "skipped": skipped, "errors": errors}


@router.post("/upload/observation/csv")
def upload_observation_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    contents = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))

    if not validate_headers(reader.fieldnames, EXPECTED_HEADERS["observation"]):
        raise HTTPException(status_code=400, detail="Le intestazioni del file CSV non corrispondono alla risorsa Observation.")

    inserted, skipped, errors = 0, 0, []
    for row in reader:
        try:
            fhir_data = csv_to_observation(row)
            code = fhir_data.get("code", {}).get("coding", [{}])[0].get("code")
            identifier = fhir_data.get("identifier", [{}])[0].get("value")
            if not is_valid_loinc_code(code):
                errors.append(f"Codice LOINC non valido: {code}")
                continue
            if db.query(Observation).filter_by(identifier=identifier).first():
                skipped += 1
                continue
            db.add(Observation(identifier=identifier, fhir_data=fhir_data))
            inserted += 1
        except Exception as e:
            errors.append(str(e))
    db.commit()
    return {"inserted": inserted, "skipped": skipped, "errors": errors}
