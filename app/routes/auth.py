from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.status import HTTP_302_FOUND
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext

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
    user = users.get(username)

    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Credenziali non valide"
        })

    if not pwd_context.verify(password, user["password"]):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Credenziali non valide"
        })

    # Successo: crea sessione, salva ruolo, reindirizza
    session = request.session
    session["username"] = username
    session["role"] = user["role"]

    if user["role"] == "admin":
        return RedirectResponse(url="/home", status_code=302)
    else:
        return RedirectResponse(url="/dashboard", status_code=302)

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    response.delete_cookie("session")
    return response