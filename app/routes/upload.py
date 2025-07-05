import csv
import io
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.services.db import get_db_session, save_or_deduplicate_patient
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.encounter import Encounter as FHIREncounter
from fhir.resources.observation import Observation as FHIRObservation
from pydantic import ValidationError
from app.utils.lonic import is_valid_loinc_code
from app.utils.mapping import map_csv_to_fhir_resource, csv_to_patient

router = APIRouter()


@router.post("/upload/patient/csv")
def upload_patient_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    # Leggi e decodifica il contenuto del file
    contents = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))

    rows = list(reader)
    print("Righe CSV:", rows)  # 👀 Debug: righe effettive lette dal file

    inserted, skipped = 0, 0

    for row in rows:
        try:
            fhir_data = csv_to_patient(row)
            print("Identifier hash:", fhir_data.get("identifier", [{}])[0].get("value"))
            success, _ = save_or_deduplicate_patient(db, fhir_data)
            if success:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"Errore nel processing della riga: {e}")
            skipped += 1

    return {"inserted": inserted, "skipped": skipped}


@router.post("/api/upload/encounter/csv")
def upload_encounter_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    reader = csv.DictReader(io.StringIO(file.file.read().decode("utf-8")))
    inserted, skipped = 0, 0
    for row in reader:
        try:
            fhir_data = csv_to_encounter(row)
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


@router.post("/api/upload/observation/csv")
def upload_observation_csv(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    reader = csv.DictReader(io.StringIO(file.file.read().decode("utf-8")))
    inserted, skipped, errors = 0, 0, []
    for row in reader:
        try:
            fhir_data = csv_to_observation(row)
            identifier = fhir_data.get("identifier", [{}])[0].get("value")
            code = fhir_data.get("code", {}).get("coding", [{}])[0].get("code")
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


@router.post("/api/upload/unified")
def upload_unified_data(file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    """
    Caricamento automatico da CSV o JSON contenente mix di risorse (Patient, Encounter, Observation).
    Include validazione tramite fhir.resources.
    """
    try:
        contents = file.file.read()
        decoded = contents.decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="File non leggibile")
    finally:
        file.file.close()

    inserted, skipped, errors = 0, 0, []

    try:
        data = json.loads(decoded)
        if isinstance(data, dict):
            data = [data]
    except:
        reader = csv.DictReader(io.StringIO(decoded))
        data = []
        for row in reader:
            try:
                _, res = map_csv_to_fhir_resource(row)
                data.append(res)
            except Exception as e:
                errors.append(f"Errore mappatura CSV: {str(e)}")

    for entry in data:
        rtype = entry.get("resourceType")
        identifier = entry.get("identifier", [{}])[0].get("value")

        # Validazione FHIR JSON con fhir.resources
        try:
            if rtype == "Patient":
                FHIRPatient.parse_obj(entry)
            elif rtype == "Encounter":
                FHIREncounter.parse_obj(entry)
            elif rtype == "Observation":
                FHIRObservation.parse_obj(entry)
            else:
                errors.append(f"Tipo risorsa sconosciuto: {rtype}")
                continue
        except ValidationError as ve:
            errors.append(f"Errore validazione FHIR ({rtype}): {ve.errors()}")
            skipped += 1
            continue

        if rtype == "Patient":
            success, _ = save_or_deduplicate_patient(db, entry)
            inserted += 1 if success else 0

        elif rtype == "Encounter":
            if not identifier:
                errors.append("Encounter senza identificativo")
                continue
            if db.query(Encounter).filter_by(identifier=identifier).first():
                skipped += 1
                continue
            db.add(Encounter(identifier=identifier, fhir_data=entry))
            inserted += 1

        elif rtype == "Observation":
            code = entry.get("code", {}).get("coding", [{}])[0].get("code")
            if not identifier:
                errors.append("Observation senza identificativo")
                continue
            if not is_valid_loinc_code(code):
                errors.append(f"Codice LOINC non valido: {code}")
                continue
            if db.query(Observation).filter_by(identifier=identifier).first():
                skipped += 1
                continue
            db.add(Observation(identifier=identifier, fhir_data=entry))
            inserted += 1

    db.commit()
    return {"status": "ok", "inserted": inserted, "skipped": skipped, "errors": errors}