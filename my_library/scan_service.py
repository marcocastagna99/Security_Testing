from .openvas_client import OpenVASClient

class ScanService:
    def __init__(self, host, port, username, password, cafile=None):
        self.openvas_client = OpenVASClient(host, port, username, password, cafile)
        self.openvas_client.connect()

    def perform_scan(self, scan_name, targets):
        result_details = []

        for target in targets:
            config_id = 'daba56c8-73ec-11df-a475-002264764cea'
            target_id = self.openvas_client.create_target(target)
            task_id = self.openvas_client.create_task(scan_name, config_id, target_id)
            self.openvas_client.start_task(task_id)
            results = self.openvas_client.get_task_results(task_id)

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
