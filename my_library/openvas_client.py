import gvm
from gvm.connections import TLSConnection
from gvm.protocols.gmp import Gmp

class OpenVASClient:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = TLSConnection(hostname=host, port=port)
        self.gmp = None

    def connect(self):
        self.gmp = Gmp(connection=self.connection)
        self.gmp.authenticate(self.username, self.password)

    def create_target(self, target):
        response = self.gmp.create_target(
            name=target,
            hosts=[target]
        )
        return response.xpath('//@id')[0]

    def create_task(self, scan_name, config_id, target_id):
        response = self.gmp.create_task(
            name=scan_name,
            config_id=config_id,
            target_id=target_id
        )
        return response.xpath('//@id')[0]

    def start_task(self, task_id):
        self.gmp.start_task(task_id)

    def get_task_results(self, task_id):
        response = self.gmp.get_results(task_id=task_id)
        results = []
        for result in response.xpath('//result'):
            results.append({
                'endpoint': result.xpath('host/text()')[0],
                'cve': result.xpath('nvt/cve/text()')[0],
                'score': float(result.xpath('severity/text()')[0]),
                'av': 'N',  # Placeholder, update with actual data
                'ac': 'L',  # Placeholder, update with actual data
                'pr': 'N',  # Placeholder, update with actual data
                'ui': 'N',  # Placeholder, update with actual data
                's': 'U',  # Placeholder, update with actual data
                'c': 'H',  # Placeholder, update with actual data
                'i': 'H',  # Placeholder, update with actual data
                'a': 'N'   # Placeholder, update with actual data
            })
        return results
