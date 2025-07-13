from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import require_role

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/home", response_class=HTMLResponse)
def home(request: Request, user=Depends(require_role("admin"))):
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(require_role("viewer"))):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@router.get("/upload", response_class=HTMLResponse)
async def show_upload(request: Request, user=Depends(require_role("admin"))):
    return templates.TemplateResponse("upload.html", {"request": request, "user": user})

@router.get("/test", response_class=HTMLResponse)
def get_test_page(request: Request, user=Depends(require_role("viewer"))):
    return templates.TemplateResponse("test.html", {"request": request, "user": user})