import os
from flask import Flask, json, request, jsonify
import threading
import logging
import sqlite3
from datetime import datetime
from my_library.scan_service import ScanService
from my_library.openvas_client import OpenVASClient


app = Flask(__name__)


# Configuration for OpenVAS using environment variables
"""S
#if you are using docker-compose, use this OpenVAS configuration 
OPENVAS_HOST = os.getenv('OPENVAS_HOST', 'openvas')  # Docker service name as default
OPENVAS_PORT = int(os.getenv('OPENVAS_PORT', 9390))
OPENVAS_USERNAME = os.getenv('OPENVAS_USERNAME', 'admin')
OPENVAS_PASSWORD = os.getenv('OPENVAS_PASSWORD', 'admin')

"""
 #If you test in local machine, use this configuration
OPENVAS_HOST = 'localhost'
OPENVAS_PORT = 9390
OPENVAS_USERNAME = 'admin'
OPENVAS_PASSWORD = 'admin'


# Database path
DB_PATH = 'scans.db'


# Function to get a connection to the database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_openvas_connection():
    openvas_client = OpenVASClient(OPENVAS_HOST, OPENVAS_PORT, OPENVAS_USERNAME, OPENVAS_PASSWORD)
    openvas_client.connect()
    openvas_client.ensure_authenticated()
    return openvas_client

# Modification in the perform_scan_background code
def perform_scan_background(scan_name, targets, result_container):
    try:
        logging.info(f"Starting scan: {scan_name} for targets: {targets}")

        # Create a new instance of OpenVASClient for each thread
        local_openvas_client=get_openvas_connection()
        # Create a new instance of ScanService with the local client
        local_scan_service = ScanService(local_openvas_client, DB_PATH)
        
        # Create the scan and get the task IDs
        task_ids = local_scan_service.perform_scan(scan_name, targets)
        
        # Store the task IDs in the result container
        result_container['task_ids'] = task_ids
        
        # Start monitoring for each task ID
        for task_id in task_ids:
            monitoring_thread = threading.Thread(target=monitor_scan_with_new_connection, args=(task_id,))
            monitoring_thread.start()
        
        logging.info(f"Scan started with task IDs: {task_ids}")
    except Exception as e:
        logging.error(f"Failed to perform scan: {e}")
        result_container['task_ids'] = None
    finally:
        local_openvas_client.disconnect() 

# Function to monitor a scan with a separate OpenVAS connection
def monitor_scan_with_new_connection(task_id):
    try:
        logging.info(f"Starting monitoring for task ID: {task_id}")
        
        # Create a new instance of OpenVASClient for monitoring
        local_openvas_client = get_openvas_connection()
        
        # Create a new instance of ScanService with the local client
        local_scan_service = ScanService(local_openvas_client, DB_PATH)
        
        # Monitor the task
        local_scan_service.monitor_scan(task_id)
        
        logging.info(f"Monitoring completed for task ID: {task_id}")
    except Exception as e:
        logging.error(f"Error monitoring task ID {task_id}: {e}")
        
# POST to trigger the scan
@app.route('/trigger_scan', methods=['POST'])
def trigger_scan():
    data = request.json

    scan_name = data.get('scan_name')
    targets = data.get('targets')

    if not scan_name or not targets:
        return jsonify({"error": "Missing scan_name or targets in request body"}), 400

    # Using a threading.Event to synchronize the result of task IDs
    task_id_event = threading.Event()
    task_id_container = {'task_ids': None}
    
    def perform_scan_with_event(scan_name, targets):
        perform_scan_background(scan_name, targets, task_id_container)
        task_id_event.set()  # Signal that the task IDs are ready

    scan_thread = threading.Thread(target=perform_scan_with_event, args=(scan_name, targets))
    scan_thread.start()
    
    # Wait for the task IDs to become available
    task_id_event.wait()
    
    return jsonify({"message": "Scan started", "task_ids": task_id_container['task_ids']}), 202

# GET to obtain information about the scan status
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
        # Create a list of in-progress results for each task
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

    # Aggregate the results and summaries
    combined_results = []
    combined_summary = []

    for row in rows:
        task_id, targets, status, result, result_summary = row
        
        # Add the result details and summary to the combined results
        if result is not None:
            combined_results.append(json.loads(result))
            combined_summary.append(json.loads(result_summary))
        else:
            # If there are still tasks in progress, include them in the aggregated results
            in_progress_tasks = {
                "scan_name": scan_name,
                "task_id": task_id,
                "targets": targets.split(","),
                "status": status,
                "message": "Scan in progress. Results are not yet available."
            }
            combined_results.append(in_progress_tasks)
    
    # Summarize the combined results
    final_results = combine_results(combined_results)
    final_summary = combine_summaries(combined_summary)


    
    return jsonify({
        "scan_name": scan_name,
        "targets": targets.split(","),  # The targets are the same for all tasks
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


@app.route('/openvas_targets', methods=['GET'])
def openvas_targets():
    try:
        openvas_client = get_openvas_connection()
        targets = openvas_client.get_openvas_targets()
        
        if not targets:
            return jsonify({"message": "No targets found in OpenVAS"}), 404

        return jsonify({"targets": targets}), 200

    except Exception as e:
        logging.error(f"Error when retrieving targets from OpenVAS: {e}")
        return jsonify({"error": "Failed to retrieve targets from OpenVAS"}), 500
    finally:
        openvas_client.disconnect()
    

@app.route('/delete_targets', methods=['POST'])
def delete_targets():
    openvas_client = get_openvas_connection()
    data = request.get_json()
    target_ids = data.get('target_ids', [])

    if not isinstance(target_ids, list):
        return jsonify({"error": "Invalid input format. 'target_ids' should be a list."}), 400

    try:
        openvas_client.delete_targets(target_ids)
        return jsonify({"message": "Targets deleted successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        openvas_client.disconnect()


@app.route('/scanners', methods=['GET'])
def get_scanners():
    try:
        openvas_client = get_openvas_connection()
        # Richiama la funzione per ottenere la lista degli scanner in formato JSON
        scanners_json = openvas_client.get_scanners_as_json()
        
        if scanners_json:
            return scanners_json, 200
        else:
            return jsonify({"error": "Failed to retrieve scanners"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        openvas_client.disconnect()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host='0.0.0.0', port=5000)