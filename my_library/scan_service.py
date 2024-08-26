import sqlite3
from datetime import datetime

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
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

        for target in targets:
            target_id = self.openvas_client.create_target(target)
            task_id = self.openvas_client.create_task(scan_name, config_id="daba56c8-73ec-11df-a475-002264764cea", target_id=target_id, scanner_id="08b69003-5fc2-4037-a479-93b440211c73")

            # Inserimento nel database con stato "In Progress"
            cursor.execute('''
                INSERT INTO scans (task_id, scan_name, targets, status) VALUES (?, ?, ?, ?)
            ''', (task_id, scan_name, target, 'In Progress'))
            conn.commit()

            # Avvia la scansione
            self.openvas_client.start_task(task_id)

            # Aggiornamento dello stato durante la scansione
            self.openvas_client.wait_for_task_completion(task_id)

            # Recupera i risultati della scansione
            results = self.openvas_client.get_task_results(task_id)
            result_details = json.dumps(results)  # Serializza i risultati in JSON
            result_summary = self.summarize_results(results)

            # Aggiorna il record con lo stato "Completed" e i risultati
            cursor.execute('''
                UPDATE scans SET status = ?, result = ? WHERE task_id = ?
            ''', ('Completed', result_details, task_id))
            conn.commit()

        conn.close()

    def summarize_results(self, results):
        summary = []
        endpoint_summary = {}

        for result in results:
            endpoint = result['endpoint']
            if endpoint not in endpoint_summary:
                endpoint_summary[endpoint] = {
                    'endpoint': endpoint,
                    'cve': result['cve'],
                    'score': result['score'],
                    'av': result['av'],
                    'ac': result['ac'],
                    'pr': result['pr'],
                    'ui': result['ui'],
                    's': result['s'],
                    'c': result['c'],
                    'i': result['i'],
                    'a': result['a']
                }
            else:
                existing = endpoint_summary[endpoint]
                if result['score'] > existing['score']:
                    existing.update({
                        'cve': result['cve'],
                        'score': result['score'],
                        'av': result['av'],
                        'ac': result['ac'],
                        'pr': result['pr'],
                        'ui': result['ui'],
                        's': result['s'],
                        'c': result['c'],
                        'i': result['i'],
                        'a': result['a']
                    })

        summary = list(endpoint_summary.values())
        return summary