# app/schemas/__init__.py

from .patient import PatientCreate, PatientRead
from .condition import ConditionCreate, ConditionRead
from .observation import ObservationCreate, ObservationRead
from .encounter import EncounterCreate, EncounterRead
# … importa ed esporta tutti gli altri schemi

__all__ = [
    "PatientCreate", "PatientRead",
    "ConditionCreate", "ConditionRead",
    "ObservationCreate", "ObservationRead",
    "EncounterCreate", "EncounterRead",
    # …
]