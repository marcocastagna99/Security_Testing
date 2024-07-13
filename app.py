from flask import Flask, request, jsonify
import threading
import logging
from my_library.scan_service import ScanService
from my_library.openvas_client import OpenVASClient

app = Flask(__name__)

# Configuration for OpenVAS
OPENVAS_HOST = 'localhost'
OPENVAS_PORT = 9390
OPENVAS_USERNAME = 'admin'
OPENVAS_PASSWORD = 'admin'

# Initialize the OpenVAS client
openvas_client = OpenVASClient(OPENVAS_HOST, OPENVAS_PORT, OPENVAS_USERNAME, OPENVAS_PASSWORD)
openvas_client.connect()  # Assicura che il client sia connesso e autenticato

# Initialize the scan service with OpenVAS client
scan_service = ScanService(openvas_client)

# Background thread to perform the scan and emit progress updates
def perform_scan_background(scan_name, targets):
    try:
        openvas_client.ensure_authenticated()  # Assicura che la sessione sia valida prima di eseguire la scansione
        result_details = scan_service.perform_scan(scan_name, targets)
        result_summary = scan_service.summarize_results(result_details)
        # Store or log the result_summary as needed
        print(result_summary)  # For debugging purposes
    except Exception as e:
        print(f"Failed to perform scan: {e}")

# Endpoint to trigger a new scan
@app.route('/trigger_scan', methods=['POST'])
def trigger_scan():
    data = request.json

    scan_name = data.get('scan_name')
    targets = data.get('targets')

    if not scan_name or not targets:
        return jsonify({"error": "Missing scan_name or targets in request body"}), 400

    # Start scan in a background thread
    scan_thread = threading.Thread(target=perform_scan_background, args=(scan_name, targets))
    scan_thread.start()

    return jsonify({"message": "Scan started"}), 202  # Return immediate response

# Endpoint to check scan status (example implementation)
@app.route('/scan_status', methods=['GET'])
def scan_status():
    # Implement logic to retrieve the current scan status
    # Return the current scan status
    return jsonify({"status": "in progress"})  # Example status

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
