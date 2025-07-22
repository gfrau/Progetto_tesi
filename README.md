
# 🩺 FHIR Platform – Piattaforma di gestione dati sanitari

Progetto per l'integrazione e visualizzazzione di dati sanitari a fini epidemiologici per Laure Magistrale in Ingegneria Informatica.

---

## Funzionalità principali

- Upload file in formato **CSV** e **JSON**
- Anonimizzazione del codice fiscale e altri dati sensibili
- Deduplicazione delle risorse FHIR
- CRUD completo per risorse FHIR: `Patient`, `Encounter`, `Observation`, `Condition`
- Visualizzazione interattiva dei dati clinici e test
- API REST documentate con OpenAPI (`/docs`)

---

## Tecnologie utilizzate

| Backend        | Frontend       | Altri strumenti   |
|----------------|----------------|-------------------|
| Python 3.11    | Bootstrap 5    | Docker / Compose  |
| FastAPI        | Toastify       | PostgreSQL + JSONB|
| Pydantic       |                |                   |
| FHIR.resources |                |                   |

---

## Modalità di avvio

### Opzione A – Con Docker (consigliato)

```bash
git clone https://github.com/gfrau/Progetto_tesi.git
cd Progetto_tesi
docker-compose up --build
```

> Accedi all'applicazione: [http://localhost:8000](http://localhost:8000)

---

### Opzione B – Manuale (ambiente virtuale)

```bash
git clone https://github.com/gfrau/Progetto_tesi.git
cd Progetto_tesi

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

> Accedi all'applicazione: [http://localhost:8000](http://localhost:8000)

---

## Credenziali (di default)

### Web – ruolo admin
- Username: `xxxx`
- Password: `xxxx`

### Web – ruolo viewer
- Username: `xxxx`
- Password: `xxxx`

### Database PostgreSQL
- Nome DB: `tesi-db`
- User: `postgres`
- Password: *(non richiesta)*

---

## 🗂️ Struttura del database

Il database PostgreSQL utilizza colonne `JSONB` per salvare le risorse FHIR. 
La tabella principale è fhirs_resource dove.

---

## 📎 Screenshot

| Funzionalità                | Screenshot                             |
|----------------------------|----------------------------------------|
| Login                      | ![Login](screenshots/01-login.png)     |
| Home + Template            | ![Home](screenshots/02-home.png)       |
| Upload file                | ![Upload](screenshots/03-upload.png)   |
| Dashboard risorse          | ![Dashboard](screenshots/04-dashboard.png) |
| Test grafici               | ![Test](screenshots/05-test01.png)     |
| API Docs                   | ![Docs](screenshots/docs.png)          |


---

## Documentazione API

Visita l'endpoint:

```
http://localhost:8000/docs
```

per consultare e testare le API REST generate automaticamente con FastAPI/OpenAPI.

---

## Licenza

Questo progetto è ad uso accademico per la tesi magistrale di Gianluigi Frau.  
Contiene codice open source modificabile per scopi educativi o di ricerca.

---

## Autore

**Gianluigi Frau**  
Università e-Campus – Ingegneria Informatica e dell'Automazione  
Email: gianluigi.frau@gmail.com

