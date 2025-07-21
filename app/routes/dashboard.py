from datetime import date
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.services.database import SessionLocal, get_db_session


router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()








