FROM mikesplain/openvas:latest

# Copia i certificati SSL nel container
COPY servercert.pem /etc/openvas/servercert.pem
COPY serverkey.pem /etc/openvas/serverkey.pem

# Imposta i permessi sui certificati
RUN chmod 644 /etc/openvas/servercert.pem
RUN chmod 600 /etc/openvas/serverkey.pem

# Configura OpenVAS per utilizzare i certificati
RUN echo "ssl_cert = /etc/openvas/servercert.pem" >> /etc/openvas/openvasmd_log.conf
RUN echo "ssl_key = /etc/openvas/serverkey.pem" >> /etc/openvas/openvasmd_log.conf

# Espone le porte necessarie
EXPOSE 443 9390 9392

# Avvia il servizio OpenVAS
CMD ["/start"]
