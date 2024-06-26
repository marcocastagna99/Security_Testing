# app.py
from flask import Flask, request, jsonify
from my_library.scan_service import ScanService

app = Flask(__name__)

# Configuration for OpenVAS
OPENVAS_HOST = 'localhost'
OPENVAS_PORT = 9390
OPENVAS_USERNAME = 'admin'
OPENVAS_PASSWORD = 'admin'

# Initialize the scan service
scan_service = ScanService(OPENVAS_HOST, OPENVAS_PORT, OPENVAS_USERNAME, OPENVAS_PASSWORD)

# Endpoint to trigger a new scan
@app.route('/trigger_scan', methods=['POST'])
def trigger_scan():
    data = request.json

    scan_name = data.get('scan_name')
    targets = data.get('targets')

    if not scan_name or not targets:
        return jsonify({"error": "Missing scan_name or targets in request body"}), 400

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
