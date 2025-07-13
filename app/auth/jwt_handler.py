import jwt
from jose import jwt
from datetime import datetime, timedelta


# Configurazione segreta
SECRET_KEY = "superSEGRETO25"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(username: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])