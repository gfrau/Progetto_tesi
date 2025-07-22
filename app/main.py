from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from datetime import datetime
from starlette.responses import JSONResponse as StarletteJSONResponse
from sqlalchemy import text, inspect

from app.auth.dependencies import require_role
from app.utils.loinc_loader import populate_loinc_codes
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from app.base import Base
from app.services.database import engine

from app.routes import (
    patient,
    encounter,
    observation,
    condition,
    dashboard,
    DEL_loinc,
    test_db,
    auth,
    dashboard_api,
    frontend,
    template,
    test,
    ingestion,
)

app = FastAPI(
    title="Dashboard epidemiologica",
    description="Tesi LM Ingegneria Informatica - Gianluigi Frau - Matricola 001567085",
    version="1.2.0",
    docs_url=None,
    redoc_url=None
)

# Session Middleware (per login/logout)
app.add_middleware(SessionMiddleware, secret_key="F1r3Jh8!zU@7q#VpLmN5$eXwT2o&dBkR")

# Middleware CORS per sviluppo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Includo i router
app.include_router(auth.router, tags=["Auth"])

app.include_router(frontend.router, dependencies=[Depends(require_role("viewer"))])
app.include_router(dashboard.router, dependencies=[Depends(require_role("viewer"))])
app.include_router(template.router, dependencies=[Depends(require_role("viewer"))])

app.include_router(patient.router, prefix="/api")
app.include_router(encounter.router, prefix="/api")
app.include_router(observation.router, prefix="/api")
app.include_router(condition.router, prefix="/api")

app.include_router(ingestion.router, prefix="/api")
app.include_router(DEL_loinc.router, prefix="/api")
app.include_router(test_db.router, prefix="/api")
app.include_router(dashboard_api.router, prefix="/api")
app.include_router(test.router, prefix="/api/test")


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Custom OpenAPI con schema Bearer JWT
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", []).append({"BearerAuth": []})

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Swagger UI accessibile solo agli admin
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request, user=Depends(require_role("admin"))):
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="Documentazione API"
    )

# ReDoc accessibile solo agli admin
@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html(request: Request, user=Depends(require_role("admin"))):
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title="Documentazione ReDoc"
    )

# Creo tabelle e indici solo se la tabella fhir_resources non esiste, popolo LOINC se necessario
@app.on_event("startup")
def on_startup():
    inspector = inspect(engine)
    # Se la tabella fhir_resources non esiste, crea schema e indici
    if 'fhir_resources' not in inspector.get_table_names():
        Base.metadata.create_all(bind=engine)
        with engine.connect() as conn:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_fhir_resources_type ON fhir_resources(resource_type)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS gin_idx_fhir_resources_content ON fhir_resources USING GIN (content)"
            ))
    # Popola tabella LOINC (internally verifica se già popolata)
    populate_loinc_codes()