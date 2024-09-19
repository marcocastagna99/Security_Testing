import sqlite3
from datetime import datetime
import time
import logging
from flask import json

class ScanService:
    def __init__(self, openvas_client, db_path):
        self.openvas_client = openvas_client
        self.db_path = db_path

    def perform_scan(self, scan_name, targets):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                task_id TEXT PRIMARY KEY,
                scan_name TEXT,
                targets TEXT,
                status TEXT,
                result TEXT,
                result_summary TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

        task_ids = []
        
        for target in targets:
            target_id = self.openvas_client.create_target(target)
            # scan list: cve: 6acd0832-df90-11e4-b9d5-28d24461215b     openvas-default: 08b69003-5fc2-4037-a479-93b440211c73
            task_id = self.openvas_client.create_task(scan_name, config_id="daba56c8-73ec-11df-a475-002264764cea", target_id=target_id, scanner_id="08b69003-5fc2-4037-a479-93b440211c73")
            targets_str = ','.join(targets)
            # Inserimento nel database con stato "In Progress"
            cursor.execute('''
                INSERT INTO scans (task_id, scan_name, targets, status) VALUES (?, ?, ?, ?)
            ''', (task_id, scan_name, targets_str, 'In Progress'))
            conn.commit()
            
            task_ids.append(task_id)

            # Avvia la scansione
            self.openvas_client.start_task(task_id)

        conn.close()
        
        # Restituisce tutti i task_id creati
        return task_ids
    
    def monitor_scan(self, task_id):
        try:
            logging.info(f"Monitoring scan with task ID: {task_id}")
            self.openvas_client.ensure_authenticated()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Aspetta che il task venga completato
            self.wait_for_task_completion(task_id, cursor, conn)
            
            # Recupera i risultati della scansione
            result, result_summary = self.openvas_client.get_report_results(task_id)
            
            # Serializza i risultati in formato JSON
            result = json.dumps(result)
            result_summary = json.dumps(result_summary, indent=4)   
        
            # Aggiorna il record con lo stato "Completed" e i risultati
            cursor.execute('''
                UPDATE scans SET status = ?, result = ?, result_summary = ? WHERE task_id = ?
            ''', ('Completed', result, result_summary, task_id))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Scan completed with task ID: {task_id}")
        except Exception as e:
            logging.error(f"Failed to monitor scan with task ID {task_id}: {e}")

    def wait_for_task_completion(self, task_id, cursor, conn, timeout=3600, interval=30):
        """Wait for the task to complete, checking the status periodically."""
        self.openvas_client.ensure_authenticated()
        end_time = time.time() + timeout
        while time.time() < end_time:
            status = self.openvas_client.get_task_status(task_id)
            if status == 'Done':
                logging.info(f"Task {task_id} completed.")
                return
            elif status == 'New':
                logging.info(f"Task {task_id} status: New. Waiting for initialization...")
            else:
                progress = self.openvas_client.get_task_progress(task_id)
                status_message = f"Task {task_id} status: {status}. Progress: {progress} %"
                logging.info(status_message)
            cursor.execute('''
                UPDATE scans 
                SET status = ? 
                WHERE task_id = ?
            ''', (f"{status}. Progress: {progress} %", task_id))
            conn.commit()

            time.sleep(interval)
        raise TimeoutError(f"Task {task_id} did not complete within the timeout period.")
