import logging
import hashlib
import uuid
import shortuuid

from fhir.resources.condition import Condition
from fhir.resources.observation import Observation
from fhir.resources.patient import Patient
from fhir.resources.address import Address
from fhir.resources.identifier import Identifier
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference

from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding

from sqlalchemy.orm import Session

from app.schemas import PatientCreate, ObservationCreate, ConditionCreate, EncounterCreate

from app.utils.anonymization import hash_identifier
from app.models.fhir_resource import FhirResource


logger = logging.getLogger(__name__)


EXPECTED_HEADERS = {
    "Patient": {"nome", "cognome", "codice_fiscale", "data_nascita", "telefono", "indirizzo", "cap", "citta", "provincia", "gender"},
    "Encounter": {"encounter_id", "codice_fiscale", "status", "class", "data_inizio", "data_fine"},
    "Observation": {"observation_id", "codice_fiscale", "codice_lonic", "descrizione_test", "valore", "unita", "data_osservazione"},
    "Condition": {"condition_id", "codice_fiscale", "codice_icd", "descrizione", "data_diagnosi"}
}



def hash_identifier(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def validate_csv_headers(headers: list[str], resource_type: str) -> bool:
    if not headers or resource_type not in EXPECTED_HEADERS:
        return False
    expected = EXPECTED_HEADERS[resource_type]
    headers_lower = set(h.strip().lower() for h in headers)
    return expected.issubset(headers_lower)


def generate_patient_id() -> str:
    return "pat" + shortuuid.ShortUUID().random(length=8)

def csv_to_patient(row: dict) -> dict:
    try:
        cf = row.get("codice_fiscale", "").strip()
        hashed = hash_identifier(cf)
        birth_date = row.get("data_nascita", "").strip()

        patient = Patient(
            id=generate_patient_id(),
            identifier=[Identifier(system="http://fhir.example.org", value=hashed)],
            gender=row.get("gender", "").strip(),
            birthDate=birth_date,
            address=[Address(
                city=row.get("citta", "").strip(),
                district=row.get("provincia", "").strip(),
                postalCode=row.get("cap", "").strip()
            )]
        )
        return patient.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Errore nella creazione della risorsa Patient: {e}")
        raise




def normalize_datetime(dt_str: str) -> str:
    if not dt_str:
        return None
    dt_str = dt_str.strip()
    if "Z" not in dt_str and "T" in dt_str:
        return dt_str + "Z"
    return dt_str

def generate_encounter_id() -> str:
    return "enc" + shortuuid.ShortUUID().random(length=8)



def csv_to_encounter(row: dict) -> dict:
    try:
        hashed = hash_identifier(row.get("codice_fiscale", "").strip())

        return {
            "resourceType": "Encounter",
            "id": "enc" + shortuuid.ShortUUID().random(length=8),
            "status": row.get("status", "").strip(),
            "class": {
                "coding": [{
                    "code": row.get("class", "").strip(),
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "display": row.get("class", "").strip()
                }]
            },
            "subject": {
                "identifier": {"value": hashed}
            },
            "identifier": [{
                "system": "http://fhir.example.org",
                "value": row.get("encounter_id", "").strip()
            }],
            "period": {
                "start": row.get("data_inizio", "").strip() + "Z",
                "end": row.get("data_fine", "").strip() + "Z"
            }
        }

    except Exception as e:
        logger.error(f"Errore nella creazione Encounter: {e}")
        raise


def generate_observation_id() -> str:
    return "obs" + shortuuid.ShortUUID().random(length=8)

def normalize_datetime(value: str) -> str:
    val = value.strip()
    return val if val.endswith("Z") else val + "Z"

def csv_to_observation(row: dict) -> dict:
    try:
        cf = row.get("codice_fiscale", "").strip()
        hashed_cf = hash_identifier(cf)

        observation = Observation(
            id=generate_observation_id(),
            status="final",
            code=CodeableConcept(
                coding=[Coding(
                    system="http://loinc.org",
                    code=row.get("codice_lonic", "").strip(),
                    display=row.get("descrizione_test", "").strip()
                )]
            ),
            valueQuantity=Quantity(
                value=float(row.get("valore", "0.0")),
                unit=row.get("unita", "").strip()
            ),
            effectiveDateTime=normalize_datetime(row.get("data_osservazione", "")),
            subject=Reference(identifier={"value": hashed_cf}),
            identifier=[Identifier(
                system="http://fhir.example.org",
                value=row.get("observation_id", "").strip()
            )]
        )
        return observation.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Errore nella creazione Observation: {e}")
        raise




def generate_condition_id() -> str:
        return "con" + shortuuid.ShortUUID().random(length=8)

def csv_to_condition(row: dict) -> dict:
    try:
        hashed_cf = hash_identifier(row.get("codice_fiscale", "").strip())
        condition_id = "cond" + shortuuid.ShortUUID().random(length=8)

        codice_icd = row.get("codice_icd", "").strip()
        descrizione = row.get("descrizione", "").strip()
        data_diagnosi = row.get("data_diagnosi", "").strip()

        if not codice_icd or not descrizione:
            raise ValueError("Campi 'codice_icd' o 'descrizione' mancanti o vuoti.")

        condition = Condition(
            id=condition_id,
            clinicalStatus=CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/condition-clinical",
                    code="active",
                    display="Active"
                )]
            ),
            verificationStatus = CodeableConcept.construct(
            coding=[
                Coding.construct(
                system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
                code="confirmed",
                )]
            ),
            code=CodeableConcept(
                coding=[Coding(
                    system="http://hl7.org/fhir/sid/icd-10",
                    code=codice_icd,
                    display=descrizione
                )],
                text=descrizione
            ),
            subject=Reference(identifier={"value": hashed_cf}),
            recordedDate=data_diagnosi,
        )

        return condition.model_dump(mode="json")

    except Exception as e:
        logger.error(f"Errore nella creazione della risorsa Condition: {e}")
        raise




JSON_SCHEMA_MAP: dict[str, type] = {
    "Patient": PatientCreate,
    "Condition": ConditionCreate,
    "Observation": ObservationCreate,
    "Encounter": EncounterCreate,
}

def process_json_resources(resources: list[dict], db: Session) -> dict:
    """
    Valida e persiste in batch un array di risorse FHIR di tipi diversi.
    Ritorna un report { total, processed, errors }.
    """
    summary = {
        "total": len(resources),
        "processed": 0,
        "errors": []
    }

    for raw in resources:
        if not raw.get("resourceType"):
            raw["resourceType"] = "Patient"

        r_type = raw["resourceType"]
        if not raw.get("id"):
            if r_type == "Patient":
                raw["id"] = generate_patient_id()
            else:
                raw["id"] = uuid.uuid4().hex
        r_id = raw["id"]

        # Anonimizzazione: hash su tutti i subject.identifier.value (Patient e gli altri)
        if r_type == "Patient" and raw.get("identifier"):
            # Patient può avere più identifier
            for ident in raw["identifier"]:
                if ident.get("value"):
                    ident["value"] = hash_identifier(ident["value"])

        elif r_type in ("Encounter", "Observation", "Condition"):
            # Tutti gli altri hanno subject.identifier come dict
            subj = raw.get("subject", {})
            ident = subj.get("identifier")
            if isinstance(ident, dict) and ident.get("value"):
                ident["value"] = hash_identifier(ident["value"])

        if r_type == "Condition":
            # clinicalStatus
            cs = raw.get("clinicalStatus")
            if isinstance(cs, str):
                raw["clinicalStatus"] = {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": cs, "display": cs.capitalize()}],
                    "text": cs.capitalize()
                }
            # verificationStatus
            vs = raw.get("verificationStatus")
            if isinstance(vs, str):
                raw["verificationStatus"] = {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                                "code": vs, "display": vs.capitalize()}],
                    "text": vs.capitalize()
                }


        logger.info(f"[PROCESS] Inizio {r_type} (id={r_id})")

        schema = JSON_SCHEMA_MAP.get(r_type)

        if not schema:
            msg = f"Tipo non supportato: {r_type}"
            logger.warning(f"[PROCESS] {msg} (id={r_id})")
            summary["errors"].append({
                "id": r_id,
                "resourceType": r_type,
                "error": msg
            })
            continue

        if db.query(FhirResource).filter(FhirResource.id == r_id).first():
            warn = f"Risorsa duplicata saltata: {r_type} (id={r_id})"
            logger.warning(warn)
            summary["errors"].append({
                "id": r_id,
                "resourceType": r_type,
                "error": warn
            })
            continue

        try:
            schema(**raw)
            logger.info(f"[PROCESS] Validazione OK: {r_type} (id={r_id})")
            db.add(FhirResource(id=r_id, resource_type=r_type, content=raw))
            logger.info(f"[PROCESS] Aggiunto al DB: {r_type} (id={r_id})")
            summary["processed"] += 1
        except Exception as e:
            logger.error(f"[PROCESS] Errore validazione/persistenza {r_type} (id={r_id}): {e}")
            summary["errors"].append({
                "id": r_id,
                "resourceType": r_type,
                "error": str(e)
            })

    # commit finale di tutte le risorse valide
    db.commit()
    return summary