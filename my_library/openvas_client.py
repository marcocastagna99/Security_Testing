import re
from gvm.connections import TLSConnection
from gvm.protocols.latest import Gmp
from gvm.errors import GvmError
from lxml import etree
import json


class OpenVASClient:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.gmp = None
        self.connection = None

    def connect(self):
        try:
            self.connection = TLSConnection(hostname=self.host, port=self.port)
            self.gmp = Gmp(connection=self.connection)

            self.gmp.authenticate(self.username, self.password)
            print("Authentication with GMP successful")
        except GvmError as e:
            print(f"Error during GMP authentication: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error during connection: {e}")
            raise

    def ensure_authenticated(self):
        if not self.gmp:
            self.connect()
        # Check if the connection is still active, if not, try to reconnect
        try:
            self.gmp.get_version()
        except:
            self.connect()



    def create_target(self, target):
        try:
            self.ensure_authenticated()
            response = self.gmp.create_target(name=target, hosts=[target])
            
            if isinstance(response, str) and response.startswith("<create_target_response"):
                target_id = self.parse_html_response_for_id(response)
            else:
                response_json = response

            return target_id
        except GvmError as e:
            print(f"Failed to create/update target: {e}")
            raise

    def parse_html_response_for_id(self, response):
        try:
            print(f"Raw HTML response for ID: {response}")  # Stampare la risposta per debug
            target_id = response.split('id="')[1].split('"')[0]
            return target_id
        except IndexError as e:
            print(f"Failed to parse HTML response for ID: {e}")
            raise
        except Exception as e:
            print(f"Error parsing HTML response for ID: {e}")
            raise

    def create_task(self, scan_name, config_id, target_id, scanner_id):
        try:
            self.ensure_authenticated()
            response = self.gmp.create_task(name=scan_name, config_id=config_id, target_id=target_id, scanner_id=scanner_id)
            
            print(f"Response type: {type(response)}")
            if isinstance(response, str):
                print(f"Response content: {response}")
                response = self.parse_create_task_response(response)
            
            response_json = json.loads(response)
            print(f"Create task response JSON: {response_json}")
            
            task_id = response_json.get('task_id')
            if task_id:
                return task_id
            else:
                print(f"Task ID not found in response: {response_json}")
                raise GvmError("Task ID not found in response")
        except GvmError as e:
            print(f"Failed to create task: {e}")
            raise

    def parse_create_task_response(self, response):
        try:
            status = response.split('status="')[1].split('"')[0]
            status_text = response.split('status_text="')[1].split('"')[0]
            task_id = response.split('id="')[1].split('"')[0]

            json_response = {
                "status": status,
                "status_text": status_text,
                "task_id": task_id
            }

            return json_response
        except Exception as e:
            print(f"Failed to parse create_task HTML response: {e}")
            raise GvmError("Failed to parse create_task HTML response")

    def start_task(self, task_id):
        try:
            self.ensure_authenticated()
            self.gmp.start_task(task_id)
            print(f"Task {task_id} started successfully")
        except GvmError as e:
            print(f"Failed to start task {task_id}: {e}")
            raise

    def get_task_results(self, task_id):
        try:
            self.ensure_authenticated()
            response = self.gmp.get_results(task_id=task_id)
            
            print(f"Response type: {type(response)}")
            if isinstance(response, str):
                print(f"Response content: {response}")
                raise GvmError(f"Received string response instead of JSON document: {response}")
            
            response_json = json.loads(response)
            print(f"Get results response JSON: {response_json}")
            
            results = []
            for result in response_json.get('results', []):
                results.append({
                    'endpoint': result.get('host', ''),
                    'cve': result.get('nvt', {}).get('cve', ''),
                    'score': float(result.get('severity', 0)),
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
            print(f"Failed to get task results for {task_id}: {e}")
            raise
