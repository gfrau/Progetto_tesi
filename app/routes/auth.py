from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.status import HTTP_302_FOUND
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext

from app.auth.dependencies import get_session
from app.utils.audit import log_audit_event

router = APIRouter()
templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users = {
    "gigi": {
        "username": "gigi",
        "password": "$2b$12$cqdg3hyq2ChHhEM2hG2twuykk..YpLXc1Dl8FOMCvQc7f7kvIkexC",  # hash di "frau"
        "role": "admin"
    },
    "viewer": {
        "username": "viewer",
        "password": "$2b$12$affCRDI.Hcql6bLRE9fsWOzADnwTyO70koyqy67wDhR9EKMBKaBw6",  # hash di "viewer"
        "role": "viewer"
    }
}

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    ip_address = request.client.host
    user = users.get(username)

    if not user or not pwd_context.verify(password, user["password"]):
        log_audit_event(
            event_type="110127",  # Login Failure
            username=username,
            success=False,
            ip=ip_address,
            action="E"
        )
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Credenziali non valide"
        })

    # Login successo
    session = request.session
    session["username"] = username
    session["role"] = user["role"]

    log_audit_event(
        event_type="110114",  # Login Success
        username=username,
        success=True,
        ip=ip_address,
        action="E"
    )

    redirect_url = "/home" if user["role"] == "admin" else "/dashboard"
    return RedirectResponse(url=redirect_url, status_code=HTTP_302_FOUND)


@router.get("/logout")
def logout(request: Request):
    session = request.session
    username = session.get("username", "anon")
    ip_address = request.client.host

    log_audit_event(
        event_type="110115",  # Logout
        username=username,
        success=True,
        ip=ip_address,
        action="E"
    )

    response = RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    response.delete_cookie("session")
    return response