import logging, json
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from app.auth.jwt_handler import decode_jwt

security = HTTPBearer()

def get_session(request: Request):
    return request.cookies.get("session")

def set_session(response, data: dict):
    import json
    response.set_cookie("session", json.dumps(data), httponly=True)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_jwt(token)
    if payload is None:
        raise HTTPException(status_code=403, detail="Token non valido o scaduto")
    return payload




def require_role(required_role: str):
    def role_checker(request: Request):
        session_data = request.session

        if not isinstance(session_data, dict):
            raise HTTPException(status_code=401, detail="Sessione non valida")

        username = session_data.get("username")
        role = session_data.get("role")

        if not username or not role:
            raise HTTPException(status_code=401, detail="Utente non autenticato")

        # L'admin ha accesso a tutto
        if role == "admin":
            return {"username": username, "role": role}

        # Se non è admin, controlla se ha il ruolo richiesto
        if role != required_role:
            raise HTTPException(status_code=403, detail="Accesso negato per il ruolo corrente")

        # Blocca i metodi non GET per ruolo = viewer
        if role == "viewer" and request.method not in ["GET", "HEAD", "OPTIONS"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operazione non consentita")

        return {"username": username, "role": role}
    return role_checker