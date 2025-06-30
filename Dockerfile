# Dockerfile
FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file requirements
COPY requirements.txt ./

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia l'intero progetto
COPY . .

# Esponi la porta usata da Uvicorn
EXPOSE 8000

# Comando di avvio dell'app FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]