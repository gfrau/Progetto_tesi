
import csv, json, io
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.services.db import get_db_session, save_or_deduplicate_patient
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.observation import Observation
from app.utils.loinc import is_valid_loinc_code
from app.utils.mapping import csv_to_patient, csv_to_encounter, csv_to_observation, map_json_to_fhir_resource

router = APIRouter()


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
def upload_patient_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    reader = csv.DictReader(io.StringIO(file.file.read().decode("utf-8")))
    if not validate_csv_headers(reader.fieldnames, "Patient"):
        raise HTTPException(status_code=400, detail="Le intestazioni del file CSV non corrispondono alla risorsa Patient.")

    inserted, skipped = 0, 0
    for row in reader:
        try:
            fhir_data = csv_to_patient(row)
            success, _ = save_or_deduplicate_patient(db, fhir_data)
            if success:
                inserted += 1
            else:
                skipped += 1
        except Exception:
            skipped += 1
    return {"inserted": inserted, "skipped": skipped}

@router.post("/upload/encounter/csv")
def upload_encounter_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    contents = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))

    if not validate_csv_headers(reader.fieldnames, "Encounter"):
        raise HTTPException(status_code=400, detail="Le intestazioni del file CSV non corrispondono alla risorsa Encounter.")

    inserted, skipped = 0, 0
    for row in reader:
        try:
            fhir_data = csv_to_encounter(row)
            patient_identifier = fhir_data.get("subject", {}).get("reference", "").replace("Patient/", "")
            if not db.query(Patient).filter(Patient.identifier == patient_identifier).first():
                skipped += 1
                continue
            identifier = fhir_data.get("identifier", [{}])[0].get("value")
            if db.query(Encounter).filter_by(identifier=identifier).first():
                skipped += 1
                continue
            db.add(Encounter(identifier=identifier, fhir_data=fhir_data))
            inserted += 1
        except Exception:
            skipped += 1
    db.commit()
    return {"inserted": inserted, "skipped": skipped}

@router.post("/upload/observation/csv")
def upload_observation_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    contents = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))

    if not validate_csv_headers(reader.fieldnames, "Observation"):
        raise HTTPException(status_code=400, detail="Le intestazioni del file CSV non corrispondono alla risorsa Observation.")

    inserted, skipped, errors = 0, 0, []

    for row in reader:
        try:
            fhir_data = csv_to_observation(row)

            # Verifico se esiste il paziente nel DB
            codice_fiscale = fhir_data.get("subject", {}).get("identifier", {}).get("value")
            paziente = db.query(Patient).filter(Patient.identifier == codice_fiscale).first()
            if not paziente:
                errors.append(f"Observation scartata: paziente {codice_fiscale} non trovato.")
                skipped += 1
                continue

            # Verifico duplicato
            identifier = fhir_data.get("identifier", [{}])[0].get("value")
            if db.query(Observation).filter_by(identifier=identifier).first():
                errors.append(f"Observation duplicata: {identifier}")
                skipped += 1
                continue

            db.add(Observation(identifier=identifier, fhir_data=fhir_data))
            inserted += 1
        except Exception as e:
            skipped += 1
            errors.append(f"Errore riga: {str(e)}")

    db.commit()
    return {"inserted": inserted, "skipped": skipped, "errors": errors}


# --- Upload JSON mixed endpoint ---

def _save_encounter(db: Session, fhir_data: dict) -> bool:
    patient_ref = fhir_data.get("subject", {}).get("reference", "")
    patient_id = patient_ref.replace("Patient/", "")
    if not db.query(Patient).filter(Patient.identifier == patient_id).first():
        return False

    identifier = fhir_data.get("identifier", [{}])[0].get("value")
    if db.query(Encounter).filter_by(identifier=identifier).first():
        return False

    db.add(Encounter(identifier=identifier, fhir_data=fhir_data))
    db.commit()
    return True

def _save_observation(db: Session, fhir_data: dict) -> bool:
    codice_fiscale = fhir_data.get("subject", {}).get("identifier", {}).get("value")
    if not db.query(Patient).filter(Patient.identifier == codice_fiscale).first():
        return False

    identifier = fhir_data.get("identifier", [{}])[0].get("value")
    if db.query(Observation).filter_by(identifier=identifier).first():
        return False

    db.add(Observation(identifier=identifier, fhir_data=fhir_data))
    db.commit()
    return True


@router.post("/upload/json/bulk")
def upload_json_bulk(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    try:
        file.file.seek(0)
        contents = file.file.read().decode("utf-8")
        print("[DEBUG] Contenuto JSON ricevuto:")
        print(contents)
        data = json.loads(contents)
    except Exception as e:
        print(f"[ERRORE] durante il parsing JSON: {str(e)}")
        raise HTTPException(status_code=400, detail="Il file JSON non è valido.")

    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="JSON non valido: ci si aspetta un array di oggetti.")

    inserted, skipped, errors = 0, 0, []

    for entry in data:
        try:
            resource_type, fhir_data = map_json_to_fhir_resource(entry)

            print(f"[DEBUG] Resource type: {resource_type}")
            print(f"[DEBUG] FHIR data: {fhir_data}")

            if resource_type == "Patient":
                success, _ = save_or_deduplicate_patient(db, fhir_data)
            elif resource_type == "Encounter":
                success = _save_encounter(db, fhir_data)
            elif resource_type == "Observation":
                success = _save_observation(db, fhir_data)
            else:
                raise ValueError("Tipo di risorsa non supportato.")

            if success:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"[ERRORE] durante il parsing di una risorsa: {str(e)}")
            skipped += 1
            errors.append(str(e))

    return {"inserted": inserted, "skipped": skipped, "errors": errors}