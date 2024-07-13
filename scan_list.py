import xml.etree.ElementTree as ET
from gvm.connections import TLSConnection
from gvm.protocols.latest import Gmp
from gvm.errors import GvmError

# Configura la connessione e l'autenticazione
connection = TLSConnection(hostname='localhost', port=9390)
gmp = Gmp(connection=connection)
gmp.authenticate(username='admin', password='admin')

# Ottieni la lista degli scanner
try:
    scanners_response = gmp.get_scanners()
    print(f"Raw response: {scanners_response}")

    # Parsing della risposta XML
    root = ET.fromstring(scanners_response)

    # Trova tutti gli elementi 'scanner'
    scanners = root.findall('.//scanner')
    for scanner in scanners:
        scanner_id = scanner.attrib.get('id')
        scanner_name = scanner.find('name').text
        print(f"Scanner ID: {scanner_id}, Name: {scanner_name}")

except GvmError as e:
    print(f"Failed to retrieve scanners: {e}")
