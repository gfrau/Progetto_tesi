
import csv, io, logging
import json

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from starlette import status

from app.services.database import get_db_session, save_resource, save_encounter_if_valid
from app.auth.dependencies import require_role
from app.utils.audit import log_audit_event
from app.utils.transform import *

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
    if not validate_csv_headers(reader.fieldnames, "Patient"):
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



@router.post("/upload/observation/csv")
def upload_observation_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    raw = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw))

    if not validate_csv_headers(reader.fieldnames, "Observation"):
        raise HTTPException(status_code=400, detail="Intestazioni CSV non valide per Observation")

    inserted, skipped, errors = 0, 0, []

    for row in reader:
        try:
            fhir_data = csv_to_observation(row)

            # Controllo che il Patient esista
            patient_id = fhir_data["subject"]["identifier"]["value"]
            patient_exists = db.query(FhirResource).filter(
                FhirResource.resource_type == "Patient",
                FhirResource.content["identifier"][0]["value"].astext == patient_id
            ).first()
            if not patient_exists:
                msg = f"Observation scartata: paziente {patient_id} non trovato."
                logger.warning(msg)
                errors.append(msg)
                skipped += 1
                continue

            # Deduplicazione su identifier
            obs_id = fhir_data.get("identifier", [{}])[0].get("value")
            exists = db.query(FhirResource).filter(
                FhirResource.resource_type == "Observation",
                FhirResource.content["identifier"][0]["value"].astext == obs_id
            ).first()
            if exists:
                logger.info(f"Observation duplicata con identifier {obs_id}")
                skipped += 1
                continue

            save_resource(db, "Observation", fhir_data)
            inserted += 1

        except Exception as e:
            msg = f"Errore nella creazione Observation: {e} - Riga: {row}"
            logger.error(msg)
            errors.append(msg)
            skipped += 1

    return {"inserted": inserted, "skipped": skipped, "errors": errors}



@router.post("/upload/condition/csv")
def upload_condition_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    raw = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(raw))

    if not validate_csv_headers(reader.fieldnames, "Condition"):
        raise HTTPException(status_code=400, detail="Intestazioni CSV non valide per risorsa Condition.")

    inserted, skipped, errors = 0, 0, []

    for row in reader:
        try:
            fhir_data = csv_to_condition(row)

            # Verifica se il Patient esiste nel DB
            patient_id = fhir_data["subject"]["identifier"]["value"]
            exists = db.query(FhirResource).filter(
                FhirResource.resource_type == "Patient",
                FhirResource.content["identifier"][0]["value"].astext == patient_id
            ).first()

            if not exists:
                msg = f"Condition scartata: paziente {patient_id} non trovato."
                logger.warning(msg)
                errors.append(msg)
                skipped += 1
                continue

            # Deduplicazione: evita condizioni duplicate con stesso codice e data
            condition_code = fhir_data.get("code", {}).get("coding", [{}])[0].get("code")
            condition_date = fhir_data.get("onsetDateTime")

            duplicate = db.query(FhirResource).filter(
                FhirResource.resource_type == "Condition",
                FhirResource.content["code"]["coding"][0]["code"].astext == condition_code,
                FhirResource.content["onsetDateTime"].astext == condition_date,
                FhirResource.content["subject"]["identifier"]["value"].astext == patient_id
            ).first()

            if duplicate:
                logger.info(f"Duplicate Condition per paziente {patient_id} con codice {condition_code} e data {condition_date}")
                skipped += 1
                continue

            save_resource(db, "Condition", fhir_data)
            inserted += 1

        except Exception as e:
            msg = f"Errore nella creazione della risorsa Condition: {e} - Riga: {row}"
            logger.error(msg)
            errors.append(msg)
            skipped += 1

    return {"inserted": inserted, "skipped": skipped, "errors": errors}





@router.post(
    "/json/bulk",
    status_code=status.HTTP_200_OK,
    summary="Bulk upload JSON FHIR misto"
)
async def upload_json_bulk(
    request: Request,
    file: UploadFile = File(..., description="File .json contenente risorse FHIR"),
    db: Session = Depends(get_db_session),
    _: None = Depends(require_role("admin"))
):
    """
    Riceve un file .json (singolo oggetto o array), valida e persiste
    le risorse FHIR miste, e restituisce un report di inseriti/scartati.
    """
    raw = await file.read()
    try:
        payload = json.loads(raw)
        resources = payload if isinstance(payload, list) else [payload]
        # Debug: verifica risorse ricevute
        logger.info(f"[JSON BULK] Ricevute {len(resources)} risorse JSON")
        for r in resources:
            logger.info(f"[JSON BULK] → risorsa id={r.get('id')} type={r.get('resourceType')}")

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON non valido: {e.msg}")

    # Debug: verifica risorse ricevute
    logger.info(f"[JSON BULK] Ricevute {len(resources)} risorse JSON")
    for r in resources:
        logger.info(f"[JSON BULK] → risorsa id={r.get('id')} type={r.get('resourceType')}")

    # Processo le risorse
    report = process_json_resources(resources, db)

    # Audit batch JSON
    log_audit_event(
        event_type="120301",
        username=request.session.get("username", "anon"),
        success=(len(report["errors"]) == 0),
        ip=request.client.host,
        action="C",
        entity_type="BatchJSONIngest"
    )

    # Risposta per il front-end
    return {
        "inserted": report["processed"],
        "skipped": len(report["errors"]),
        "errors": [f"[{e['resourceType']}/{e['id']}] {e['error']}" for e in report["errors"]]
    }
