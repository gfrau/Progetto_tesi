import logging
import hashlib
import shortuuid
from fhir.resources.observation import Observation

from fhir.resources.patient import Patient
from fhir.resources.address import Address
from fhir.resources.identifier import Identifier
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from app.utils.anonymization import hash_identifier

logger = logging.getLogger(__name__)


EXPECTED_HEADERS = {
    "Patient": {"nome", "cognome", "codice_fiscale", "data_nascita", "telefono", "indirizzo", "cap", "citta", "provincia", "gender"},
    "Encounter": {"encounter_id", "codice_fiscale", "status", "class", "data_inizio", "data_fine"},
    "Observation": {"observation_id", "codice_fiscale", "codice_lonic", "descrizione_test", "valore", "unita", "data_osservazione"},
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
            effectiveDateTime=normalize_datetime(row.get("data_osservazione", "")),            subject=Reference(identifier={"value": hashed_cf}),
            identifier=[Identifier(
                system="http://fhir.example.org",
                value=row.get("observation_id", "").strip()
            )]
        )
        return observation.model_dump(mode="json")
    except Exception as e:
        logger.error(f"Errore nella creazione Observation: {e}")
        raise