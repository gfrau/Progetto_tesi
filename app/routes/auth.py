from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from fastapi.templating import Jinja2Templates
from app.auth.dependencies import get_current_user
from app.utils.session_manager import create_session


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Credenziali hardcoded
VALID_USER = "gigi"
VALID_PASSWORD = "frau"
USER_ROLE = "admin"

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == VALID_USER and password == VALID_PASSWORD:
        response = RedirectResponse(url="/dashboard", status_code=HTTP_302_FOUND)
        create_session(response, username=username, role=USER_ROLE)
        return response
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "Credenziali errate"
    })

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=HTTP_302_FOUND)

@router.get("/auth/me", tags=["Auth"])
def read_current_user(user: dict = Depends(get_current_user)):
    return {"user": user}