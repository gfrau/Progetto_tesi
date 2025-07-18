
import logging
import hashlib
import shortuuid
from fhir.resources.patient import Patient
from fhir.resources.address import Address
from fhir.resources.identifier import Identifier

logger = logging.getLogger(__name__)

def hash_identifier(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def validate_csv_headers(headers: list[str], expected: set[str]) -> bool:
    if not headers:
        return False
    return expected.issubset(set(h.strip().lower() for h in headers))


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
