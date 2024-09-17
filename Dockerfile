# Usa un'immagine base di Python slim
FROM python:3.9-slim

# Aggiorna l'elenco dei pacchetti e installa le dipendenze necessarie
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Scarica e installa OpenSSL 1.1.1k
RUN curl -O https://www.openssl.org/source/openssl-1.1.1k.tar.gz && \
    tar -xzf openssl-1.1.1k.tar.gz && \
    cd openssl-1.1.1k && \
    ./config --prefix=/usr/local/openssl-1.1.1k --openssldir=/usr/local/openssl-1.1.1k/openssl && \
    make && \
    make install && \
    cd .. && \
    rm -rf openssl-1.1.1k openssl-1.1.1k.tar.gz

# Configura le variabili d'ambiente per utilizzare OpenSSL 1.1.1k
ENV LD_LIBRARY_PATH=/usr/local/openssl-1.1.1k/lib
ENV PATH="/usr/local/openssl-1.1.1k/bin:${PATH}"

# Installa le dipendenze Python definite in requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copia l'applicazione nella directory di lavoro
COPY . /app
WORKDIR /app

# Comando per avviare l'applicazione
CMD ["python", "app.py"]
