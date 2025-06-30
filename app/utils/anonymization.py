import hashlib
import copy


def hash_identifier(value: str) -> str:
    """
    Hash SHA-256 di un identificatore (es. codice fiscale).
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def anonymize_patient(patient_data: dict) -> dict:
    """
    Anonimizza i dati sensibili del paziente mantenendo l'identifier hashato per la deduplicazione.
    """
    if not isinstance(patient_data, dict):
        raise ValueError("Il dato del paziente deve essere un dizionario.")

    data = copy.deepcopy(patient_data)

    # Identificatore originale (es. codice fiscale)
    identifier_list = data.get("identifier", [])
    if identifier_list and isinstance(identifier_list, list):
        original_value = identifier_list[0].get("value", "")
        hashed_value = hash_identifier(original_value)
        identifier_list[0]["value"] = hashed_value
        data["identifier"] = identifier_list
    else:
        raise ValueError("Il campo 'identifier' è mancante o malformato nel paziente.")

    # Rimuove altri campi potenzialmente sensibili
    data.pop("name", None)
    data.pop("telecom", None)
    data.pop("address", None)

    return data