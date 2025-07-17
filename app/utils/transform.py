# app/utils/transform.py

import io, csv
from fhir.resources.patient import Patient
from fhir.resources.encounter import Encounter as FhirEncounter
from fhir.resources.observation import Observation as FhirObservation
from sqlalchemy import text
from app.schemas import EncounterCreate
from app.services.database import engine



# Headers attesi per l'upload CSV
EXPECTED_HEADERS = {
    "Encounter": {"encounter_id", "codice_fiscale", "status", "class", "data_inizio", "data_fine"},
    "Patient": {"nome", "cognome", "codice_fiscale", "data_nascita", "telefono", "indirizzo", "cap", "citta", "gender"},
    "Observation": {"observation_id","codice_fiscale","codice_loinc","descrizione_test","valore","unita","data_osservazione"}
}

def validate_csv_headers(headers: list[str], resource_type: str) -> bool:
    if not headers or resource_type not in EXPECTED_HEADERS:
        return False
    headers_lower = set(h.strip().lower() for h in headers)
    expected = set(h.lower() for h in EXPECTED_HEADERS[resource_type])
    return expected.issubset(headers_lower)


def csv_to_patient(row: dict) -> dict:
    """
    Trasforma una riga CSV in un dict FHIR.Patient valido.
    """
    fhir_dict = {
        "resourceType": "Patient",
        "id": row.get("codice_fiscale"),
        "identifier": [{
            "value": row.get("codice_fiscale"),
            "system": "http://fhir.example.org"
        }],
        "name": [{
            "family": row.get("cognome"),
            "given": [row.get("nome")]
        }],
        "gender": row.get("gender"),
        "birthDate": row.get("data_nascita"),
        "telecom": [{
            "system": "phone",
            "value": row.get("telefono")
        }],
        "address": [{
            "city":       row.get("citta"),
            "district":   row.get("provincia"),
            "postalCode": row.get("cap")
        }]
    }
    patient = Patient.parse_obj(fhir_dict)
    return patient.model_dump(mode="json")


def csv_to_encounter(row: dict) -> dict:
    """
    Trasforma una riga CSV in un dict FHIR.Encounter valido.
    """
    raw = {
        "resourceType": "Encounter",
        "id":            row.get("encounter_id"),
        "status":        row.get("status"),
        "class": {
            "coding": [{
                "system":  "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code":    row.get("class"),
                "display": row.get("class")
            }]
        },
        "subject": {
            "identifier": {"value": row.get("codice_fiscale")}
        },
        "period": {
            "start": row.get("data_inizio"),
            "end":   row.get("data_fine")
        }
    }
    # se preferisci usare il tuo schema Pydantic:
    # enc_model = EncounterCreate.parse_obj(raw)
    # return enc_model.model_dump(mode="json")

    enc = FhirEncounter.parse_obj(raw)
    return enc.model_dump(mode="json")


def csv_to_observation(row: dict) -> dict:
    """
    Trasforma una riga CSV in un dict FHIR.Observation valido.
    """
    # supporto sia 'codice_lonic' che 'codice_loinc'
    loinc_code = row.get("codice_lonic") or row.get("codice_loinc") or ""
    fhir_dict = {
        "resourceType":      "Observation",
        "id":                row.get("observation_id"),
        "status":            "final",
        "code": {
            "coding": [{
                "system":  "http://loinc.org",
                "code":    loinc_code,
                "display": row.get("descrizione_test")
            }]
        },
        "subject": {
            "identifier": {"value": row.get("codice_fiscale")}
        },
        "effectiveDateTime": row.get("data_osservazione"),
        "valueQuantity": {
            "value": float(row.get("valore", 0)),
            "unit":  row.get("unita")
        }
    }


    obs = FhirObservation.parse_obj(fhir_dict)
    return obs.model_dump(mode="json")


def map_json_to_fhir_resource(entry: dict) -> tuple[str, dict]:
    """
    Determina il tipo di risorsa FHIR e la valida tramite fhir.resources.
    """
    rt = entry.get("resourceType")
    if rt == "Patient":
        model = Patient.parse_obj(entry)
    elif rt == "Encounter":
        model = FhirEncounter.parse_obj(entry)
    elif rt == "Observation":
        model = FhirObservation.parse_obj(entry)
    else:
        raise ValueError(f"Tipo di risorsa non supportato: {rt}")
    return rt, model.model_dump(mode="json")


def is_valid_loinc_code(code: str) -> bool:
    """
    Verifica se un codice LOINC esiste nella tabella loinc_codes.
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT 1 FROM loinc_codes WHERE code = :code"),
            {"code": code}
        ).first()
    return row is not None