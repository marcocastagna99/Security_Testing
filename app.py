from flask import Flask, request, jsonify
from my_library.scan_service import ScanService

app = Flask(__name__)

# Configurazione per la connessione a OpenVAS
OPENVAS_HOST = 'localhost'
OPENVAS_PORT = 9390
OPENVAS_USERNAME = 'admin'
OPENVAS_PASSWORD = 'admin'

# Inizializzazione del servizio di scansione
scan_service = ScanService(OPENVAS_HOST, OPENVAS_PORT, OPENVAS_USERNAME, OPENVAS_PASSWORD)

# Endpoint per avviare una nuova scansione
@app.route('/trigger_scan', methods=['POST'])
def trigger_scan():
    data = request.json

    scan_name = data.get('scan_name')
    targets = data.get('targets')

    result_details = scan_service.perform_scan(scan_name, targets)
    response = {
        "scan_name": scan_name,
        "targets": targets,
        "result_details": result_details,
        "result_summary": scan_service.summarize_results(result_details)
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
