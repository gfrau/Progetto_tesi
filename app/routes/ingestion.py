import csv,io, json

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from app.services.database import get_db_session, save_resource
from app.utils.anonymization import anonymize_patient, hash_identifier
from app.utils.transform import *
from app.auth.dependencies import require_role
from sqlalchemy.exc import IntegrityError


router = APIRouter(tags=["Upload CSV/JSON"])




# --- Upload CSV endpoints ---
@router.post("/upload/patient/csv")
def upload_patient_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    """
    Upload di un CSV di pazienti:
    - Parsing riga per riga con validazione tramite fhir.resources.Patient (Pydantic)
    - Anonimizzazione del codice fiscale
    - Salvataggio nella tabella FHIR unica
    Restituisce il conteggio di righe inserite, scartate e dettagli degli errori.
    """
    # Leggo tutto il contenuto del file CSV come stringa
    text = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.
                            StringIO(text))

    # Controllo gli header: se non vanno bene, lancio erroe
    if not validate_csv_headers(reader.fieldnames, "Patient"):
        raise HTTPException(
            status_code=400,
            detail="Le intestazioni del file CSV non corrispondono alla risorsa Patient."
        )

    inserted = 0   # quante righe sono state importate con successo
    skipped = 0    # quante righe sono state saltate
    errors: list[str] = []  # qui metto i messaggi d’errore riga per riga

    for row in reader:
        # 1) Provo a trasformare la riga in dict FHIR e validare con Pydantic
        try:
            fhir_data = csv_to_patient(row)
        except Exception as e:
            errors.append(f"Parsing error riga {row}: {e}")
            skipped += 1
            continue  # passo alla prossima riga

        # 2) Anonimizzazione: nascondo il codice fiscale
        try:
            fhir_data = anonymize_patient(fhir_data)
        except Exception as e:
            errors.append(f"Errore anonimizzazione riga {row}: {e}")
            skipped += 1
            continue

        # 3) Mi assicuro che ci sia sempre un campo 'id'
        if not fhir_data.get("id"):
            identifier = fhir_data.get("identifier", [{}])[0].get("value")
            fhir_data["id"] = identifier

        # 4) Provo a salvare nel DB; gestisco duplicati e altri errori
        try:
            save_resource(db, "Patient", fhir_data)
            inserted += 1
        except IntegrityError as e:
            db.rollback()
            errors.append(f"Duplicato o IntegrityError riga {row}: {e}")
            skipped += 1
        except Exception as e:
            db.rollback()
            errors.append(f"Errore salvataggio riga {row}: {e}")
            skipped += 1

    # Infine ritorno i risultati dell'operazione
    return {
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors
    }
@router.post("/upload/encounter/csv")
def upload_encounter_csv(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    """
    Upload di un CSV di Encounter:
    - parsing riga per riga con validazione tramite fhir.resources.Encounter (Pydantic)
    - salvataggio nella tabella FHIR unica
    Restituisce il conteggio di righe inserite, scartate e dettagli degli errori.
    """
    text = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    if not validate_csv_headers(reader.fieldnames, "Encounter"):
        raise HTTPException(
            status_code=400,
            detail="Le intestazioni del file CSV non corrispondono alla risorsa Encounter."
        )

    inserted = 0
    skipped = 0
    errors: list[str] = []

    for row in reader:
        # 1) parsing + validazione Pydantic/FHIR
        try:
            fhir_data = csv_to_encounter(row)
        except Exception as e:
            errors.append(f"Parsing error riga {row}: {e}")
            skipped += 1
            continue

        # 2) anonimizzazione: hash del CF del paziente in subject.identifier
        try:
            # recupero il dict che contiene il CF
            identifier_obj = fhir_data["subject"]["identifier"]
            if isinstance(identifier_obj, dict):
                original_cf = identifier_obj.get("value", "")
                # uso la funzione hash_identifier già presente in anonymization.py
                hashed_cf = hash_identifier(original_cf)
                # riscrivo il valore col suo hash
                fhir_data["subject"]["identifier"]["value"] = hashed_cf
        except Exception:
            # in caso di qualunque problema, proseguo comunque
            pass

        # 3) assicuro che l'Encounter abbia sempre un 'id'
        if not fhir_data.get("id"):
            fhir_data["id"] = row.get("encounter_id")

        # 4) provo a salvare nel DB
        try:
            save_resource(db, "Encounter", fhir_data)
            inserted += 1
        except IntegrityError as e:
            db.rollback()
            errors.append(f"Duplicato o IntegrityError riga {row}: {e}")
            skipped += 1
        except Exception as e:
            db.rollback()
            errors.append(f"Errore salvataggio riga {row}: {e}")
            skipped += 1

    return {
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors
    }


@router.post("/upload/observation/csv")
def upload_observation_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    """
    Upload di un CSV di Observation:
    - parsing riga per riga con validazione tramite csv_to_observation (Pydantic)
    - anonimizzazione del codice fiscale in subject.identifier
    - verifica che il paziente esista (hashato) in fhir_resources
    - salvataggio nella tabella FHIR unica
    Restituisce il conteggio di righe inserite, scartate e i dettagli degli errori.
    """
    import io, csv
    from sqlalchemy.exc import IntegrityError
    from app.services.database import save_resource
    from app.utils.transform import csv_to_observation, validate_csv_headers
    from app.utils.anonymization import hash_identifier
    from app.models.fhir_resource import FhirResource

    # 1) Leggo e decodifico il CSV (UTF-8 o Latin-1)
    raw = file.file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    reader = csv.DictReader(io.StringIO(text))

    # 2) Controllo intestazioni
    if not validate_csv_headers(reader.fieldnames, "Observation"):
        raise HTTPException(
            status_code=400,
            detail="Le intestazioni del file CSV non corrispondono alla risorsa Observation."
        )

    inserted = 0
    skipped  = 0
    errors: list[str] = []

    # 3) Giro ogni riga del CSV
    for row in reader:
        # 3.1) Validazione Pydantic/FHIR
        try:
            fhir_data = csv_to_observation(row)
        except Exception as e:
            errors.append(f"Parsing error riga {row}: {e}")
            skipped += 1
            continue

        # 3.2) Anonimizzazione CF in subject.identifier
        try:
            subj = fhir_data["subject"]["identifier"]
            if isinstance(subj, dict):
                original = subj.get("value", "")
                hashed   = hash_identifier(original)
                fhir_data["subject"]["identifier"]["value"] = hashed
        except Exception:
            pass

        # 3.3) Garantisco sempre un ID
        if not fhir_data.get("id"):
            fhir_data["id"] = row.get("observation_id")

        # 3.4) Verifica che il paziente (hashato) esista
        patient_exists = db.query(FhirResource).filter(
            FhirResource.resource_type == "Patient",
            FhirResource.id == fhir_data["subject"]["identifier"]["value"]
        ).first()
        if not patient_exists:
            errors.append(f"Observation scartata: paziente {fhir_data['subject']['identifier']['value']} non trovato.")
            skipped += 1
            continue

        # 3.5) Salvataggio su fhir_resources
        try:
            save_resource(db, "Observation", fhir_data)
            inserted += 1
        except IntegrityError as e:
            db.rollback()
            errors.append(f"Duplicato riga {row}: {e}")
            skipped += 1
        except Exception as e:
            db.rollback()
            errors.append(f"Errore salvataggio riga {row}: {e}")
            skipped += 1

    return {"inserted": inserted, "skipped": skipped, "errors": errors}


# --- Upload JSON mixed endpoint ---
@router.post("/upload/json/bulk")
def upload_json_bulk(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    """
    Upload bulk JSON (array di oggetti FHIR):
    - validazione con fhir.resources (Pydantic)
    - anonimizzazione CF per Patient e Observation
    - verifica che Observation/Encounter abbiano un Patient esistente
    - salvataggio in unica tabella fhir_resources
    """
    import json
    from sqlalchemy.exc import IntegrityError
    from app.services.database import save_resource
    from app.utils.transform import map_json_to_fhir_resource
    from app.utils.anonymization import anonymize_patient, hash_identifier
    from app.models.fhir_resource import FhirResource
    from fastapi import HTTPException

    # 1) Leggo e parsifico il JSON
    try:
        raw = file.file.read().decode("utf-8")
        payload = json.loads(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="File JSON non valido.")
    if not isinstance(payload, list):
        raise HTTPException(status_code=400, detail="Ci si aspetta un array di oggetti FHIR.")

    inserted = 0
    skipped  = 0
    errors: list[str] = []

    # 2) Ciclo ogni risorsa
    for entry in payload:
        try:
            # 2.1) Validazione e conversione base
            resource_type, fhir_data = map_json_to_fhir_resource(entry)

            # 2.2) Assicuro un ID
            if not fhir_data.get("id"):
                fhir_data["id"] = fhir_data.get("identifier", [{}])[0].get("value")

            # 2.3) Anonimizzazione CF per Patient
            if resource_type == "Patient":
                fhir_data = anonymize_patient(fhir_data)

            # 2.4) Anonimizzazione CF per Observation
            if resource_type == "Observation":
                subj = fhir_data.get("subject", {}).get("identifier", {})
                if isinstance(subj, dict):
                    hashed = hash_identifier(subj.get("value", ""))
                    fhir_data["subject"]["identifier"]["value"] = hashed

            # 2.5) Verifica referenza Patient per Observation/Encounter
            if resource_type in ("Observation", "Encounter"):
                subj = fhir_data.get("subject", {})
                # estraggo l’ID del patient (hash o reference)
                pid = None
                if "reference" in subj:
                    pid = subj["reference"].split("/", 1)[-1]
                elif "identifier" in subj:
                    pid = subj["identifier"].get("value")
                exists = db.query(FhirResource).filter(
                    FhirResource.resource_type == "Patient",
                    FhirResource.id == pid
                ).first()
                if not exists:
                    raise ValueError(f"{resource_type} {fhir_data['id']}: paziente non trovato (hash={pid})")

            # 2.6) Salvataggio
            try:
                save_resource(db, resource_type, fhir_data)
                inserted += 1
            except IntegrityError:
                db.rollback()
                skipped += 1

        except Exception as e:
            skipped += 1
            rid = entry.get("id") or entry.get("identifier", [{}])[0].get("value", "sconosciuto")
            errors.append(f"{resource_type} {rid}: {e}")

    return {"inserted": inserted, "skipped": skipped, "errors": errors}