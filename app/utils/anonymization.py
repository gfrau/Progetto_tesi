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

    # Identificatore codice fiscale
    identifier_list = data.get("identifier", [])
    if identifier_list and isinstance(identifier_list, list):
        original_value = identifier_list[0].get("value", "")
        hashed_value = hash_identifier(original_value)
        identifier_list[0]["value"] = hashed_value
        data["identifier"] = identifier_list
        data["id"] = hashed_value
    else:
        raise ValueError("Il campo 'identifier' è mancante o malformato nel paziente.")


    # 2) semplifico address: tengo solo città, provincia, cap per fini statistici
    if "address" in data and isinstance(data["address"], list):
        new_addresses = []
        for addr in data["address"]:
            city = addr.get("city")
            postal = addr.get("postalCode")
            # province può essere in 'district' o, se non previsto, in un custom 'province'
            province = addr.get("district") or addr.get("province")
            entry: dict = {}
            if city:
                entry["city"] = city
            if postal:
                entry["postalCode"] = postal
            if province:
                entry["district"] = province
            if entry:
                new_addresses.append(entry)
        data["address"] = new_addresses

    data.pop("name", None)

    return data