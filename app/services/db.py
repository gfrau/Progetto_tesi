import os
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from app.models.fhir_resource import FhirResource

# Configurazione da variabili d'ambiente
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "tesi-db")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def get_db_session():
    """
    Dependency-injection di FastAPI per ottenere la sessione DB.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_database():
    """
    Cancella tutte le risorse FHIR nella tabella fhir_resources.
    """
    db = SessionLocal()
    try:
        print("Inizio reset database...")
        db.query(FhirResource).delete()
        db.commit()
        print("✅ Database resettato correttamente.")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Errore nel reset del database: {str(e)}")
        raise
    finally:
        db.close()


def load_or_deduplicate_patient(db: Session, fhir_data: dict) -> tuple[bool, dict]:
    """
    Inserisce un Patient se non esiste, altrimenti bypass.
    Ritorna (True, data) se inserito, (False, data) se già presente.
    """
    identifier = fhir_data.get("identifier", [{}])[0].get("value")
    existing = (
        db.query(FhirResource)
          .filter_by(resource_type="Patient")
          .filter(FhirResource.content["identifier"][0]["value"].astext == identifier)
          .first()
    )
    if existing:
        return False, fhir_data
    db.add(FhirResource(id=fhir_data.get("id"), resource_type="Patient", content=fhir_data))
    db.commit()
    return True, fhir_data


def save_encounter_if_valid(db: Session, fhir_data: dict) -> bool:
    """
    Verifica che il Patient di riferimento esista prima di salvare.
    Altrimenti solleva ValueError.
    """
    subject = fhir_data.get("subject", {})
    if "reference" in subject:
        patient_id = subject["reference"].replace("Patient/", "")
    elif "identifier" in subject:
        patient_id = subject["identifier"].get("value", "")
    else:
        raise ValueError("Nessun campo 'reference' o 'identifier' in subject")

    # Controllo esistenza Patient
    if not (
        db.query(FhirResource)
          .filter_by(resource_type="Patient")
          .filter(FhirResource.content["id"].astext == patient_id)
          .first()
    ):
        raise ValueError(f"Patient {patient_id} non trovato nel database")

    identifier = fhir_data.get("identifier", [{}])[0].get("value")
    if (
        db.query(FhirResource)
          .filter_by(resource_type="Encounter")
          .filter(FhirResource.content["identifier"][0]["value"].astext == identifier)
          .first()
    ):
        raise ValueError(f"Encounter {identifier} già presente nel database")

    db.add(FhirResource(id=fhir_data.get("id"), resource_type="Encounter", content=fhir_data))
    db.commit()
    return True


def save_observation_if_valid(db: Session, fhir_data: dict) -> bool:
    """
    Verifica che il Patient di riferimento esista prima di salvare.
    Ritorna False se duplicato o Patient mancante.
    """
    codice_fiscale = fhir_data.get("subject", {}).get("identifier", {}).get("value")
    # Controllo esistenza Patient
    if not (
        db.query(FhirResource)
          .filter_by(resource_type="Patient")
          .filter(FhirResource.content["identifier"][0]["value"].astext == codice_fiscale)
          .first()
    ):
        return False

    identifier = fhir_data.get("identifier", [{}])[0].get("value")
    if (
        db.query(FhirResource)
          .filter_by(resource_type="Observation")
          .filter(FhirResource.content["identifier"][0]["value"].astext == identifier)
          .first()
    ):
        return False

    db.add(FhirResource(id=fhir_data.get("id"), resource_type="Observation", content=fhir_data))
    db.commit()
    return True