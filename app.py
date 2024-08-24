from flask import Flask, request, jsonify
import threading
import logging
import sqlite3
from datetime import datetime
from my_library.scan_service import ScanService
from my_library.openvas_client import OpenVASClient

app = Flask(__name__)

# Configurazione per OpenVAS
OPENVAS_HOST = 'localhost'
OPENVAS_PORT = 9390
OPENVAS_USERNAME = 'admin'
OPENVAS_PASSWORD = 'admin'

# Percorso del database
DB_PATH = 'scans.db'

# Inizializzazione del client OpenVAS
openvas_client = OpenVASClient(OPENVAS_HOST, OPENVAS_PORT, OPENVAS_USERNAME, OPENVAS_PASSWORD)
openvas_client.connect()

# Inizializzazione del servizio di scansione con il client OpenVAS
scan_service = ScanService(openvas_client, DB_PATH)

# Funzione per ottenere la connessione al database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Funzione di background per eseguire la scansione
def perform_scan_background(scan_name, targets):
    try:
        logging.info(f"Starting scan: {scan_name} for targets: {targets}")
        openvas_client.ensure_authenticated()
        scan_service.perform_scan(scan_name, targets)
        logging.info(f"Scan completed: {scan_name}")
    except Exception as e:
        logging.error(f"Failed to perform scan: {e}")

# Endpoint per avviare una nuova scansione
@app.route('/trigger_scan', methods=['POST'])
def trigger_scan():
    data = request.json

    scan_name = data.get('scan_name')
    targets = data.get('targets')

    if not scan_name or not targets:
        return jsonify({"error": "Missing scan_name or targets in request body"}), 400

    scan_thread = threading.Thread(target=perform_scan_background, args=(scan_name, targets))
    scan_thread.start()

    return jsonify({"message": "Scan started"}), 202

# Endpoint per controllare lo stato della scansione
@app.route('/scan_status/<task_id>', methods=['GET'])
def scan_status(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT scan_name, targets, status, result FROM scans WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        scan_name, targets, status, result = row
        result_summary = scan_service.summarize_results(result)
        return jsonify({
            "scan_name": scan_name,
            "targets": targets.split(","),
            "result_details": result,
            "result_summary": result_summary
        })
    else:
        return jsonify({"error": "Task ID not found"}), 404

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host='0.0.0.0', port=5000)
