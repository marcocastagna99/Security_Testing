from flask import Flask, json, request, jsonify
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

def perform_scan_background(scan_name, targets, result_container):
    try:
        logging.info(f"Starting scan: {scan_name} for targets: {targets}")
        scan_service.openvas_client.ensure_authenticated()
        
        # Crea la scansione e ottieni i task_id
        task_ids = scan_service.perform_scan(scan_name, targets)
        
        # Memorizza i task_id nel contenitore di risultati
        result_container['task_ids'] = task_ids
        
        # Avvia il monitoraggio per ogni task_id
        for task_id in task_ids:
            monitoring_thread = threading.Thread(target=scan_service.monitor_scan, args=(task_id,))
            monitoring_thread.start()
        
        logging.info(f"Scan started with task IDs: {task_ids}")
    except Exception as e:
        logging.error(f"Failed to perform scan: {e}")
        result_container['task_ids'] = None

#post to trigger the scan
@app.route('/trigger_scan', methods=['POST'])
def trigger_scan():
    data = request.json

    scan_name = data.get('scan_name')
    targets = data.get('targets')

    if not scan_name or not targets:
        return jsonify({"error": "Missing scan_name or targets in request body"}), 400

    # Usando un threading.Event per sincronizzare il risultato dei task_id
    task_id_event = threading.Event()
    task_id_container = {'task_ids': None}
    
    def perform_scan_with_event(scan_name, targets):
        perform_scan_background(scan_name, targets, task_id_container)
        task_id_event.set()  # Segnala che i task_id sono pronti

    scan_thread = threading.Thread(target=perform_scan_with_event, args=(scan_name, targets))
    scan_thread.start()
    
    # Attendere che i task_id siano disponibili
    task_id_event.wait()
    
    return jsonify({"message": "Scan started", "task_ids": task_id_container['task_ids']}), 202

#get to obtain information about the scan status
@app.route('/scan_status/<task_id>', methods=['GET'])
def scan_status(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT scan_name, targets, status, result, result_summary FROM scans WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        scan_name, targets, status, result, result_summary = row
        
        # Se il risultato è None, significa che la scansione non è ancora completata
        if result is None:
            return jsonify({
                "scan_name": scan_name,
                "targets": targets.split(","),
                "status": status,
                "message": "Scan in progress. Results are not yet available."
            })

        # Se il risultato è disponibile, lo riassumiamo
        result_details = json.loads(result)  # Deserializza il risultato dal JSON
        result_summary = json.loads(result_summary)
        #result_summary = scan_service.summarize_results(result_details)
        return jsonify({
            "scan_name": scan_name,
            "targets": targets.split(","),
            "status": status,
            "result_details": result_details,
            "result_summary": result_summary
        })
    else:
        return jsonify({"error": "Task ID not found"}), 404

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host='0.0.0.0', port=5000)
