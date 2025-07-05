import os
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, scoped_session

# from app.models import Observation, Encounter, Patient

# Configurazione da variabili d'ambiente
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "tesi-db")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Engine e sessione
engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_database():
    """
    Cancella tutto il contenuto dalle tabelle principali (patients, encounters, observations).
    """
    session = SessionLocal()
    try:
        print("Inizio reset database...")
        session.query(Observation).delete()
        session.query(Encounter).delete()
        session.query(Patient).delete()
        session.commit()
        print("✅ Database resettato correttamente.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Errore nel reset del database: {str(e)}")
        raise e
    finally:
        session.close()


def save_or_deduplicate_patient(db_session, fhir_data: dict) -> tuple:
    from app.models.patient import Patient  # ✅ spostato qui per evitare import circolare

    identifier = fhir_data.get("identifier", [{}])[0].get("value")
    existing = db_session.query(Patient).filter_by(identifier=identifier).first()
    if existing:
        return (False, fhir_data)

    new_patient = Patient(identifier=identifier, fhir_data=fhir_data)
    db_session.add(new_patient)
    db_session.commit()
    return (True, fhir_data)