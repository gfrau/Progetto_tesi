import hashlib
from app.utils.loinc import is_valid_loinc_code



def is_valid_loinc_code(code: str) -> bool:
    """
    Valida un codice LOINC nel formato '1234-5'.
    - Deve contenere un trattino.
    - Entrambe le parti devono essere numeriche.
    """
    if not isinstance(code, str):
        return False
    code = code.strip()
    if "-" not in code:
        return False
    parts = code.split("-")
    return (
        len(parts) == 2 and
        all(part.isdigit() for part in parts) and
        len(parts[1]) > 0  # la seconda parte non deve essere vuota
    )


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


def csv_to_encounter(row: dict) -> dict:
    """
    Converte una riga CSV in una risorsa FHIR Encounter.
    Richiede: encounter_id, codice_fiscale, status, class, data_inizio, data_fine
    """
    codice_fiscale = row.get("codice_fiscale", "").strip()
    encounter_id = row.get("encounter_id", "").strip()
    status = row.get("status", "finished").strip().lower()
    encounter_class = row.get("class", "AMB").strip().upper()
    start_date = row.get("data_inizio", "").strip()
    end_date = row.get("data_fine", "").strip()

    if not codice_fiscale:
        raise ValueError("Codice fiscale mancante nella riga Encounter")
    if not encounter_id:
        raise ValueError("ID encounter mancante")

    # Calcolo dell’hash del codice fiscale per collegare al Patient
    patient_identifier_hash = hashlib.sha256(codice_fiscale.encode("utf-8")).hexdigest()
    print(f"[DEBUG] Codice fiscale: {codice_fiscale} -> Hash: {patient_identifier_hash}")

    fhir_encounter = {
        "resourceType": "Encounter",
        "identifier": [{
            "value": encounter_id
        }],
        "status": status,
        "class": {
            "code": encounter_class
        },
        "period": {
            "start": start_date,
            "end": end_date
        },
        "subject": {
            "identifier": {
                "value": patient_identifier_hash
            }
        }
    }

    return fhir_encounter



def csv_to_observation(row: dict) -> dict:
    """
    Converte una riga CSV in una risorsa FHIR Observation.
    Richiede: observation_id, codice_fiscale, codice_lonic, descrizione_test, valore, unita, data_osservazione
    """
    codice = row.get("codice_lonic", "").strip()
    valore = row.get("valore", "").strip()
    unita = row.get("unita", "").strip()
    codice_fiscale = row.get("codice_fiscale", "").strip()
    descrizione = row.get("descrizione_test", "").strip()
    data = row.get("data_osservazione", "").strip()
    observation_id = row.get("observation_id", "").strip()

    if not observation_id or not codice_fiscale or not codice or not valore:
        raise ValueError("Dati insufficienti: observation_id, codice_fiscale, codice_lonic e valore sono obbligatori")

    if not is_valid_loinc_code(codice):
        print(f"[ERRORE] Codice LOINC non valido → '{codice}'")
        raise ValueError(f"Codice LOINC non valido: {codice}")

    try:
        valore_float = float(valore)
    except ValueError:
        raise ValueError(f"Valore non numerico: '{valore}'")

    codice_fiscale = hashlib.sha256(codice_fiscale.encode("utf-8")).hexdigest()
    return {
        "resourceType": "Observation",
        "identifier": [{"value": observation_id}],
        "status": "final",
        "subject": {"identifier": {"value": codice_fiscale}},
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": codice,
                "display": descrizione
            }],
            "text": descrizione
        },
        "effectiveDateTime": data,
        "valueQuantity": {
            "value": valore_float,
            "unit": unita
        }
    }


def validate_csv_headers(headers: list[str], resource_type: str) -> bool:
    """
    Verifica se le intestazioni CSV corrispondono a quelle attese per il tipo di risorsa.
    """
    expected_headers = {
        "Patient": {"nome", "cognome", "codice_fiscale", "data_nascita", "telefono", "indirizzo", "cap", "citta","gender"},
        "Encounter": {"encounter_id", "codice_fiscale", "status", "class", "data_inizio", "data_fine"},
        "Observation": {"observation_id", "codice_fiscale", "codice_lonic", "descrizione_test", "valore", "unita","data_osservazione"}
    }

    normalized_headers = {h.strip().lower() for h in headers}
    expected = expected_headers.get(resource_type)

    if not expected:
        return False  # Tipo non supportato

    return expected.issubset(normalized_headers)


def map_json_to_fhir_resource(data: dict) -> tuple[str, dict]:
    resource_type = data.get("resourceType")
    if resource_type not in {"Patient", "Encounter", "Observation"}:
        raise ValueError("Tipo di risorsa non supportato")
    return resource_type, data