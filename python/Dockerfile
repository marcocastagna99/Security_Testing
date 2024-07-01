# Usa un'immagine di Python 3.8 basata su Alpine con OpenSSL compatibile
FROM python:3.8.13-alpine3.16

# Installa le dipendenze del sistema necessarie
RUN apk update && apk add --no-cache \
    openssl \
    openssl-dev \
    gcc \
    musl-dev \
    libffi-dev

# Imposta il working directory all'interno del container
WORKDIR /app

# Copia i file di dipendenza del tuo progetto Python
COPY requirements.txt .

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia il file app.py nella directory corrente del container
COPY ./test_connessione.py .

# Comando predefinito per avviare l'applicazione
CMD ["python", "test_connessione.py"]
