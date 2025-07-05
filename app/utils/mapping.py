import hashlib
from app.utils.lonic import is_valid_loinc_code

def map_csv_to_fhir_resource(row: dict) -> tuple[str, dict]:
    """
    Mappa una riga CSV a una risorsa FHIR Patient, Encounter o Observation.
    Ritorna una tupla (resourceType, fhir_dict)
    """
    def hash_identifier(value: str) -> str:
        return f"anon-{hashlib.sha256(value.encode()).hexdigest()[:8]}"

    row = {k.strip().lower(): v.strip() for k, v in row.items() if v.strip()}

    # Mappatura Patient
    if "codice_fiscale" in row and "nome" in row and "cognome" in row:
        codice_fiscale = row.get("codice_fiscale")
        birth_date = row.get("data_nascita")
        gender = row.get("sesso", "").lower()

        resource = {
            "resourceType": "Patient",
            "identifier": [{"value": hash_identifier(codice_fiscale)}] if codice_fiscale else [],
            "birthDate": birth_date,
            "gender": gender if gender in ["male", "female", "other", "unknown"] else "unknown",
            "name": [{
                "family": row.get("cognome"),
                "given": [row.get("nome")]
            }]
        }
        return "Patient", resource

    # Mappatura Encounter
    if "encounter_id" in row and "codice_fiscale" in row:
        resource = {
            "resourceType": "Encounter",
            "identifier": [{"value": row.get("encounter_id")}],
            "status": row.get("status", "finished"),
            "class": {"code": row.get("class", "AMB")},
            "subject": {
                "identifier": {
                    "value": hash_identifier(row.get("codice_fiscale"))
                }
            },
            "period": {
                "start": row.get("data_inizio"),
                "end": row.get("data_fine")
            }
        }
        return "Encounter", resource

    # Mappatura Observation
    if "observation_id" in row and "codice_fiscale" in row:
        code = row.get("codice_test")
        value = row.get("valore")
        unit = row.get("unita_misura", "1")
        resource = {
            "resourceType": "Observation",
            "identifier": [{"value": row.get("observation_id")}],
            "status": row.get("status", "final"),
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": code,
                    "display": row.get("descrizione_test", "")
                }]
            },
            "subject": {
                "identifier": {
                    "value": hash_identifier(row.get("codice_fiscale"))
                }
            },
            "effectiveDateTime": row.get("data_osservazione"),
            "valueQuantity": {
                "value": float(value) if value.replace('.', '', 1).isdigit() else None,
                "unit": unit
            }
        }

        if not is_valid_loinc_code(code):
            raise ValueError(f"Codice LOINC non valido: {code}")

        return "Observation", resource

    raise ValueError("Tipo di risorsa non riconosciuto o campi insufficienti")

from app.utils.anonymization import anonymize_patient

def csv_to_patient(row: dict) -> dict:
    """
    Converte una riga CSV in una risorsa FHIR Patient anonima.
    """
    codice_fiscale = row.get("codice_fiscale", "").strip()

    if not codice_fiscale:
        raise ValueError("Codice fiscale mancante")

    # Normalizzazione del campo gender
    raw_gender = row.get("gender", "").strip().lower()
    gender_map = {
        "m": "male",
        "f": "female",
        "maschio": "male",
        "femmina": "female"
    }
    gender = gender_map.get(raw_gender, raw_gender if raw_gender in ["male", "female", "other", "unknown"] else "unknown")

    fhir_patient = {
        "resourceType": "Patient",
        "identifier": [{
            "system": "urn:oid:2.16.840.1.113883.2.9.4.3.2",  # ✅ Codice fiscale (Agenzia delle Entrate)
            "value": codice_fiscale
        }],
        "birthDate": row.get("data_nascita", "").strip(),
        "gender": gender,
        "name": [{
            "given": [row.get("nome", "").strip()],
            "family": row.get("cognome", "").strip()
        }],
        "telecom": [{
            "system": "phone",
            "value": row.get("telefono", "").strip()
        }],
        "address": [{
            "line": [row.get("indirizzo", "").strip()],
            "city": row.get("citta", "").strip(),
            "postalCode": row.get("cap", "").strip()
        }]
    }

    return anonymize_patient(fhir_patient)