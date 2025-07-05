
def is_valid_loinc_code(code: str) -> bool:
    """
    Valida un codice LOINC nel formato '1234-5'.
    Ritorna True se il codice è plausibile.
    """
    if not isinstance(code, str):
        return False
    parts = code.split("-")
    return len(parts) == 2 and all(part.isdigit() for part in parts)