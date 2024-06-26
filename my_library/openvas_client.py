from gvm.connections import TLSConnection
from gvm.protocols.gmp import Gmp
from gvm.errors import GvmError
import logging

class OpenVASClient:
    def __init__(self, host, port, username, password, cafile=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.cafile = cafile
        self.connection = TLSConnection(hostname=host, port=port, cafile=cafile)
        self.gmp = None

    def connect(self):
        try:
            self.connection.connect()
            self.gmp = Gmp(connection=self.connection)
            self.gmp.authenticate_with_password(self.username, self.password)
            logging.info("Authentication successful")
        except GvmError as e:
            logging.error(f"Failed to connect or authenticate: {e}")
            raise

    def create_target(self, target):
        try:
            response = self.gmp.create_target(name=target, hosts=[target])
            target_id = response.xpath('//@id')[0]
            return target_id
        except GvmError as e:
            logging.error(f"Failed to create target: {e}")
            raise

    def create_task(self, scan_name, config_id, target_id):
        try:
            response = self.gmp.create_task(name=scan_name, config_id=config_id, target_id=target_id)
            task_id = response.xpath('//@id')[0]
            return task_id
        except GvmError as e:
            logging.error(f"Failed to create task: {e}")
            raise

    def start_task(self, task_id):
        try:
            self.gmp.start_task(task_id)
            logging.info(f"Task {task_id} started successfully")
        except GvmError as e:
            logging.error(f"Failed to start task {task_id}: {e}")
            raise

    def get_task_results(self, task_id):
        try:
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
        except GvmError as e:
            logging.error(f"Failed to get task results for {task_id}: {e}")
            raise
