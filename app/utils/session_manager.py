from itsdangerous import URLSafeSerializer
from fastapi import Request, Response

SECRET_KEY = "5ba62021e9cb8e8eb0991a29f1f4d0cfd51dcf8794f6541ab83e81dbf0a79f9c"
serializer = URLSafeSerializer(SECRET_KEY)

COOKIE_NAME = "session_token"

def create_session(response: Response, username: str, role: str = "admin"):
    session_data = {"username": username, "role": role}
    signed = serializer.dumps(session_data)
    response.set_cookie(key=COOKIE_NAME, value=signed, httponly=True)

def get_session(request: Request):
    cookie = request.cookies.get(COOKIE_NAME)
    if cookie:
        try:
            return serializer.loads(cookie)
        except Exception:
            return None
    return None

def clear_session(response: Response):
    response.delete_cookie(COOKIE_NAME)