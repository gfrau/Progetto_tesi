import json
import os
from datetime import datetime
from uuid import uuid4

# Percorso file NDJSON
AUDIT_LOG_PATH = "app/logs/audit.ndjson"
os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)

# Mappa di display leggibili per tipi di evento HL7
DISPLAY_MAP = {
    "110114": "User Login",
    "110115": "User Logout",
    "110127": "Login Failure",
    "110128": "Session Terminated",
    "110120": "Read",
    "110121": "Export",
    "110122": "Delete",
    "110123": "Update",
    "110124": "Create",
    "110129": "Import",
    "110130": "Submit Report",
    "110131": "Access Dashboard",
    "110132": "Generate Statistics",
    "110133": "Filter Epidemiological Data",
    "110140": "View Patient Record",
    "110141": "Create Encounter",
    "110142": "Create Observation",
    "110150": "System Backup",
    "110151": "System Restore",
    "110152": "Clear Database",
    "110153": "Admin Maintenance"
}

def log_audit_event(event_type: str, username: str, success: bool, ip: str = "unknown", action: str = None, entity_id: str = None, entity_type: str = None):
    event = {
        "resourceType": "AuditEvent",
        "id": str(uuid4()),
        "type": {
            "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
            "code": event_type,
            "display": DISPLAY_MAP.get(event_type, event_type)
        },
        "action": action or "E",
        "recorded": datetime.utcnow().isoformat() + "Z",
        "outcome": "0" if success else "4",
        "agent": [
            {
                "who": {
                    "identifier": {
                        "value": username
                    }
                },
                "requestor": True
            }
        ],
        "source": {
            "observer": {
                "identifier": {
                    "value": ip
                }
            }
        }
    }

    if entity_id and entity_type:
        event["entity"] = [
            {
                "what": {
                    "identifier": {
                        "value": entity_id
                    }
                },
                "type": {
                    "text": entity_type
                }
            }
        ]

    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")