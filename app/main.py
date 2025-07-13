from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from datetime import datetime
from fhir.resources.observation import Observation
from starlette.responses import JSONResponse
from app.auth.dependencies import require_role
from app.utils.loinc_loader import populate_loinc_codes
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from app.base import Base
from app.services.db import engine

from app.routes import (
    patient,
    encounter,
    observation,
    dashboard,
    loinc,
    maintenance,
    test_db,
    auth,
    stats,
    frontend,
    template,
    upload,
    test,
    test_data
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
app.include_router(patient.router, prefix="/api")
app.include_router(encounter.router, prefix="/api")
app.include_router(observation.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(loinc.router, prefix="/api")
app.include_router(maintenance.router, prefix="/api")
app.include_router(test_db.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(test.router, prefix="/api/test")
app.include_router(test_data.router, prefix="/test/data")


app.include_router(frontend.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(template.router)



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

# @app.get("/openapi.json", include_in_schema=False)
# async def get_openapi(request: Request, user=Depends(require_role("admin"))):
#    return JSONResponse(app.openapi())


# Creo tabelle e popolo con codici LOINC se assenti
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    populate_loinc_codes()

# Utility: mapping CSV → Observation FHIR
def map_csv_row_to_fhir_observation(row: dict) -> Observation:
    return Observation.construct(
        resourceType="Observation",
        status=row.get("status", "final"),
        code={
            "coding": [{
                "system": "http://loinc.org",
                "code": row.get("code", "unknown"),
                "display": row.get("display", "unknown")
            }]
        },
        subject={
            "reference": f"Patient/{row.get('patient_id', 'unknown')}"
        },
        effectiveDateTime=row.get("effectiveDateTime", datetime.utcnow().isoformat()),
        valueQuantity={
            "value": float(row.get("value", 0)),
            "unit": row.get("unit", "unit"),
            "system": "http://unitsofmeasure.org",
            "code": row.get("unit_code", "1")
        }
    )
