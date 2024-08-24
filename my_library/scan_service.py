import sqlite3
from datetime import datetime

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
            task_id = self.openvas_client.create_task(scan_name, config_id="daba56c8-73ec-11df-a475-002264764cea", target_id=target_id, scanner_id="08b69003-5fc2-4037-a479-93b440211c73")  # Default config_id and scanner_id
            self.openvas_client.start_task(task_id)

            self.openvas_client.wait_for_task_completion(task_id)
            results = self.openvas_client.get_task_results(task_id)

            result_details = results
            result_summary = self.summarize_results(results)

            cursor.execute('''
                INSERT INTO scans (task_id, scan_name, targets, status, result) VALUES (?, ?, ?, ?, ?)
            ''', (task_id, scan_name, ",".join(targets), 'Completed', result_details))
            conn.commit()

        conn.close()

    def summarize_results(self, results):
        summary = []
        for result in results:
            summary.append({
                "endpoint": result['endpoint'],
                "cve": result['cve'],
                "score": result['score'],
                "av": result['av'],
                "ac": result['ac'],
                "pr": result['pr'],
                "ui": result['ui'],
                "s": result['s'],
                "c": result['c'],
                "i": result['i'],
                "a": result['a']
            })
        return summary