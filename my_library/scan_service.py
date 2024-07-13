class ScanService:
    def __init__(self, openvas_client):
        self.openvas_client = openvas_client
        self.CVE_SCANNER_ID = "6acd0832-df90-11e4-b9d5-28d24461215b"
        self.config_id = 'daba56c8-73ec-11df-a475-002264764cea'

    def perform_scan(self, scan_name, targets):
        result_details = []
        for target in targets:
            try:
                print(f"Creating target for: {target}")
                target_id = self.openvas_client.create_target(target)
                print(f"Created target with ID: {target_id}")

                print(f"Creating task with target ID: {target_id}")
                task_id = self.openvas_client.create_task(scan_name, self.config_id, target_id, scanner_id=self.CVE_SCANNER_ID)
                print(f"Created task with ID: {task_id}")

                print(f"Starting task with ID: {task_id}")
                self.openvas_client.start_task(task_id)
                print(f"Task {task_id} started successfully")

                print(f"Getting results for task ID: {task_id}")
                results = self.openvas_client.get_task_results(task_id)
                print(f"Results received: {results}")

                for result in results:
                    result_details.append({
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
            except Exception as e:
                print(f"Failed to perform scan for target {target}: {e}")
                # Optionally handle the exception or re-raise it as needed

        return result_details

    def summarize_results(self, result_details):
        summary = []

        for detail in result_details:
            summary.append({
                "endpoint": detail['endpoint'],
                "cve": detail['cve'],
                "score": detail['score'],
                "av": detail['av'],
                "ac": detail['ac'],
                "pr": detail['pr'],
                "ui": detail['ui'],
                "s": detail['s'],
                "c": detail['c'],
                "i": detail['i'],
                "a": detail['a']
            })

        return summary
