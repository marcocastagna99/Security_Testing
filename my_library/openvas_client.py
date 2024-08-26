import time
from gvm.connections import TLSConnection
from gvm.protocols.latest import Gmp
from gvm.errors import GvmError
from xml.etree import ElementTree as ET

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
                response_dict = self.parse_create_task_response(response)
            else:
                response_dict = response  # Se response non è una stringa, presumibilmente è già un dizionario

            task_id = response_dict.get('task_id')

            if task_id:
                print(f"Task ID found: {task_id}")
                return task_id

            else:
                print(f"Task ID not found in response: {response_dict}")
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

    def wait_for_task_completion(self, task_id, timeout=3600, interval=30):
        """Wait for the task to complete, checking the status periodically."""
        self.ensure_authenticated()
        end_time = time.time() + timeout
        while time.time() < end_time:
            status = self.get_task_status(task_id)
            if status == 'Done':
                print(f"Task {task_id} completed.")
                return
            elif status == 'New':
                print(f"Task {task_id} status: New. Waiting for initialization...")
            else:
                progress = self.get_task_progress(task_id)
                print(f"Task {task_id} status: {status}. Progress: {progress}")
            time.sleep(interval)
        raise TimeoutError(f"Task {task_id} did not complete within the timeout period.")

    def get_task_status(self, task_id):
        """Retrieve the current status of the task."""
        try:
            self.ensure_authenticated()
            response = self.gmp.get_task(task_id=task_id)
            root = ET.fromstring(response)
            status = root.find('.//status').text
            return status
        except Exception as e:
            print(f"Error retrieving task status for {task_id}: {e}")
            raise

    def get_task_progress(self, task_id):
        """Retrieve the progress information of the task."""
        try:
            self.ensure_authenticated()
            response = self.gmp.get_task(task_id=task_id)
            root = ET.fromstring(response)
            progress = root.find('.//progress').text
            return progress
        except Exception as e:
            print(f"Error retrieving task progress for {task_id}: {e}")
            raise


    def get_task_results(self, task_id):
        try:
            self.ensure_authenticated()
            response = self.gmp.get_results(task_id=task_id)

            # Print for verifying the type and content of the response
            # print(f"Response type: {type(response)}")
            # print(f"Response content: {response}")

            # Parse XML response
            root = ET.fromstring(response)
            
            results = []
            for result in root.findall('.//result'):
                host = result.find('.//host')
                nvt = result.find('.//nvt')
                severity = result.find('.//severity')
                cvss_vector = result.find('.//cvss')
                
                # Extract endpoint and CVE information
                endpoint = host.text if host is not None else 'Unknown'
                cve = nvt.find('.//cve').text if nvt is not None and nvt.find('.//cve') is not None else ''
                score = float(severity.text) if severity is not None else 0.0

                # Extract CVSS vector information
                av = 'N'
                ac = 'L'
                pr = 'N'
                ui = 'N'
                s = 'U'
                c = 'H'
                i = 'H'
                a = 'N'
                
                if cvss_vector is not None and cvss_vector.text:
                    cvss_parts = cvss_vector.text.split('/')
                    vector_parts = {part.split(':')[0]: part.split(':')[1] for part in cvss_parts[1:]}
                    av = vector_parts.get('AV', av)
                    ac = vector_parts.get('AC', ac)
                    pr = vector_parts.get('PR', pr)
                    ui = vector_parts.get('UI', ui)
                    s = vector_parts.get('S', s)
                    c = vector_parts.get('C', c)
                    i = vector_parts.get('I', i)
                    a = vector_parts.get('A', a)
                
                results.append({
                    'endpoint': endpoint,
                    'cve': cve,
                    'score': score,
                    'av': av,
                    'ac': ac,
                    'pr': pr,
                    'ui': ui,
                    's': s,
                    'c': c,
                    'i': i,
                    'a': a
                })
            return results
        except GvmError as e:
            print(f"Failed to get task results for {task_id}: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error while parsing task results: {e}")
            raise GvmError(f"Failed to parse task results for {task_id}")