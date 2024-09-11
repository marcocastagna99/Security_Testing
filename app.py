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


# Funzione per ottenere la connessione al database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Modifica nel codice di perform_scan_background
def perform_scan_background(scan_name, targets, result_container):
    try:
        logging.info(f"Starting scan: {scan_name} for targets: {targets}")

        # Crea una nuova istanza di OpenVASClient per ogni thread
        local_openvas_client = OpenVASClient(OPENVAS_HOST, OPENVAS_PORT, OPENVAS_USERNAME, OPENVAS_PASSWORD)
        local_openvas_client.connect()
        
        # Crea una nuova istanza di ScanService con il client locale
        local_scan_service = ScanService(local_openvas_client, DB_PATH)
        
        local_openvas_client.ensure_authenticated()
        
        # Crea la scansione e ottieni i task_id
        task_ids = local_scan_service.perform_scan(scan_name, targets)
        
        # Memorizza i task_id nel contenitore di risultati
        result_container['task_ids'] = task_ids
        
        # Avvia il monitoraggio per ogni task_id
        for task_id in task_ids:
            monitoring_thread = threading.Thread(target=monitor_scan_with_new_connection, args=(task_id,))
            monitoring_thread.start()
        
        logging.info(f"Scan started with task IDs: {task_ids}")
    except Exception as e:
        logging.error(f"Failed to perform scan: {e}")
        result_container['task_ids'] = None

# Funzione per monitorare una scansione con una connessione OpenVAS separata
def monitor_scan_with_new_connection(task_id):
    try:
        logging.info(f"Starting monitoring for task ID: {task_id}")
        
        # Creare una nuova istanza di OpenVASClient per il monitoraggio
        local_openvas_client = OpenVASClient(OPENVAS_HOST, OPENVAS_PORT, OPENVAS_USERNAME, OPENVAS_PASSWORD)
        local_openvas_client.connect()
        local_openvas_client.ensure_authenticated()
        
        # Creare una nuova istanza di ScanService con il client locale
        local_scan_service = ScanService(local_openvas_client, DB_PATH)
        
        # Monitorare il task
        local_scan_service.monitor_scan(task_id)
        
        logging.info(f"Monitoring completed for task ID: {task_id}")
    except Exception as e:
        logging.error(f"Error monitoring task ID {task_id}: {e}")

# POST per avviare la scansione
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
@app.route('/scan_status/<scan_name>', methods=['GET'])
def scan_status(scan_name):

    data = request.args
    task_ids = data.getlist('task_id')

    if not task_ids:
        return jsonify({"error": "No task IDs provided"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    placeholders = ', '.join('?' for _ in task_ids)
    query = f"SELECT task_id, targets, status, result, result_summary FROM scans WHERE scan_name = ? AND task_id IN ({placeholders})"

    cursor.execute(query, [scan_name] + task_ids)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return jsonify({"error": "No tasks found for the specified scan name and task IDs"}), 404


    all_in_progress = all(row['result'] is None for row in rows)

    if all_in_progress:
        # Crea una lista di risultati in corso per ogni task
        in_progress_tasks = []
        for row in rows:
            task_id, targets, status, result, result_summary = row
            
            task_status = {
                "scan_name": scan_name,
                "task_id": task_id,
                "targets": targets.split(","),
                "status": status,
                "message": "Scan in progress. Results are not yet available."
            }
            in_progress_tasks.append(task_status)
        
        return jsonify({"tasks": in_progress_tasks}), 200

    # Aggregare i risultati e i riassunti
    combined_results = []
    combined_summary = []

    for row in rows:
        task_id, targets, status, result, result_summary = row
        
        # Aggiungi i dettagli del risultato e il riassunto ai risultati combinati
        if result is not None:
            combined_results.append(json.loads(result))
            combined_summary.append(json.loads(result_summary))
        else:
            # Se ci sono task ancora in corso, includili nei risultati aggregati
            in_progress_tasks = {
                "scan_name": scan_name,
                "task_id": task_id,
                "targets": targets.split(","),
                "status": status,
                "message": "Scan in progress. Results are not yet available."
            }
            combined_results.append(in_progress_tasks)
    
    # Riassumi i risultati combinati
    final_results = combine_results(combined_results)
    final_summary = combine_summaries(combined_summary)


    
    return jsonify({
        "scan_name": scan_name,
        "targets": targets.split(","), # I target sono gli stessi per tutti i task
        "status": "Completed",
        "result_details": final_results,
        "result_summary": final_summary
    })
def combine_results(results):
    combined = []
    for result in results:
        if isinstance(result, dict):
            combined.append(result)
        elif isinstance(result, list):
            combined.extend(result)
    return combined

def combine_summaries(summaries):
    combined = []
    for summary in summaries:
        if isinstance(summary, dict):
            combined.append(summary)
        elif isinstance(summary, list):
            combined.extend(summary)
    return combined



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host='0.0.0.0', port=5000)
