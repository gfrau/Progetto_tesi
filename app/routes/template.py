from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

# Percorso ai file template CSV/JSON
TEMPLATE_DIR = os.path.join("static", "templates")

@router.get("/template/{filename}")
def get_template(filename: str):
    """
    Restituisce i file CSV o JSON di template per l'import delle risorse FHIR.
    """
    allowed_files = {"patient.csv", "encounter.csv", "observation.csv", "unified.json"}
    if filename not in allowed_files:
        raise HTTPException(status_code=404, detail="Template non disponibile")

    file_path = os.path.join(TEMPLATE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File non trovato")

    media_type = "application/json" if filename.endswith(".json") else "text/csv"
    return FileResponse(path=file_path, filename=filename, media_type=media_type)