from gvm.connections import TLSConnection
from gvm.protocols.latest import Gmp
from gvm.errors import GvmError

# Configurazione del client OpenVAS
OPENVAS_HOST = 'localhost'
OPENVAS_PORT = 9390
OPENVAS_USERNAME = 'admin'
OPENVAS_PASSWORD = 'admin'

def delete_openvas_target(target_id):
    try:
        # Creazione della connessione TLS e inizializzazione del client GMP
        connection = TLSConnection(hostname=OPENVAS_HOST, port=OPENVAS_PORT)
        gmp = Gmp(connection=connection)
        gmp.authenticate(OPENVAS_USERNAME, OPENVAS_PASSWORD)

        # Eliminazione del target
        gmp.delete_target(target_id)

        print(f"Target {target_id} eliminato con successo.")
    except GvmError as e:
        print(f"Errore durante l'eliminazione del target: {e}")

# Esempio di utilizzo
if __name__ == "__main__":
    target_id_to_delete = "31ebff6a-8466-4558-b101-f469b8ee7858"
    delete_openvas_target(target_id_to_delete)
