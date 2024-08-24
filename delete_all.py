from gvm.connections import TLSConnection
from gvm.protocols.latest import Gmp
from gvm.errors import GvmError
from lxml import etree

# Configurazione del client OpenVAS
OPENVAS_HOST = 'localhost'
OPENVAS_PORT = 9390
OPENVAS_USERNAME = 'admin'
OPENVAS_PASSWORD = 'admin'

try:
    # Connessione al server OpenVAS tramite TLS
    connection = TLSConnection(hostname=OPENVAS_HOST, port=OPENVAS_PORT)
    gmp = Gmp(connection=connection)

    # Autenticazione
    gmp.authenticate(OPENVAS_USERNAME, OPENVAS_PASSWORD)

    # Ottenere la lista dei target
    targets_response = gmp.get_targets()

    # Debug: stampare la risposta XML originale
    print("Risposta XML originale:")
    print(targets_response)

    # Analizzare la risposta XML
    targets_xml = etree.fromstring(targets_response.encode('utf-8'))

    # Debug: stampare la risposta XML ben formattata
    print("\nRisposta XML formattata:")
    print(etree.tostring(targets_xml, pretty_print=True).decode())

    # Estrarre gli ID dei target
    target_ids = []
    for target in targets_xml.findall('.//target'):
        target_id = target.get('id')  # Qui accedi all'attributo 'id' direttamente
        if target_id:
            target_ids.append(target_id)
        else:
            print(f'Elemento target senza ID: {etree.tostring(target, pretty_print=True).decode()}')

    # Debug: stampare gli ID dei target trovati
    print(f'Target IDs trovati: {target_ids}')

    # Eliminare ogni target
    for target_id in target_ids:
        gmp.delete_target(target_id)
        print(f'Target {target_id} eliminato')

except GvmError as e:
    print(f'Errore: {e}')
except Exception as e:
    print(f'Errore generico: {e}')
