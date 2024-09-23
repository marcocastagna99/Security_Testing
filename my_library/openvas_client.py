from flask import json
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

    def get_report_results(self, task_id):
        try:
            report_id = self.get_report_id_by_task(task_id)
            xml_data = self.get_report(report_id)
            results = self.parse_report(xml_data)
            results_summary = self.parse_result_summary(xml_data)
            return results,results_summary
        except Exception as e:
            raise Exception(f"Failed to monitor scan with task ID {task_id}: {str(e)}")

    def get_report_id_by_task(self, task_id):
        try:
            # Ottenere i report in formato XML
            reports = self.gmp.get_reports()
          # print(f"Reports Data: {reports}")  # Debug line
            
            # Parsing dell'XML
            root = ET.fromstring(reports)
            
            # Iterare sui report per trovare il task con l'ID specificato
            for report in root.findall('.//report'):
                task = report.find('.//task')
                if task is not None and task.get('id') == task_id:
                    report_id = report.get('id')
                    #print(f"Matching report found: Report ID = {report_id} for Task ID = {task_id}")
                    return report_id
            
            raise ValueError(f"No report found for task ID {task_id}")
        
        except Exception as e:
            raise Exception(f"An error occurred while fetching report ID for task {task_id}: {str(e)}")
        
    def get_report(self, report_id):
        try:
            report = self.gmp.get_report(report_id=report_id)
            """
            # Verifica se il report è una stringa XML o un oggetto diverso
            if isinstance(report, str):
                with open(f"report_{report_id}.xml", "w") as file:
                    file.write(report)  # Scrivi il contenuto XML nel file
            else:
                raise ValueError(f"Unexpected report format: {type(report)}")"""
            
            return report
        
        except Exception as e:
            raise Exception(f"An error occurred while fetching report {report_id}: {str(e)}")

    def parse_report(self, xml_data):
        try:
            root = ET.fromstring(xml_data)
            results = []
            for result in root.findall(".//result"):
                result_id = result.get('id')
                name = result.findtext('name')
                host = result.findtext('host')
                port = result.findtext('port')
                severity = result.findtext('severity')
                description = result.findtext('description')
                cvss_base = result.findtext(".//cvss_base")
                cve = result.findtext(".//cve")

                detail = {
                    'id': result_id,
                    'name': name,
                    'host': host,
                    'port': port,
                    'severity': severity,
                    'description': description,
                    'cvss_base': cvss_base,
                    'cve': cve
                }
                results.append(detail)

            return results
        except ET.ParseError as e:
            raise Exception(f"An error occurred while parsing XML data: {str(e)}")
        
    def parse_result_summary(self, xml_content):
        root = ET.fromstring(xml_content)
        results = {}
        
        for result in root.findall(".//result"):
            # Check and get 'host'
            host_element = result.find("host")
            host = host_element.text.strip().split("<")[0].strip() if host_element is not None else "Unknown"
            
            # Check and get 'port'
            port_element = result.find("port")
            port = port_element.text.strip() if port_element is not None else "Unknown"
            endpoint = f"{host}:{port}"
            
            # Check and get 'cvss_base'
            cvss_base_element = result.find(".//cvss_base")
            cvss_base = cvss_base_element.text.strip() if cvss_base_element is not None else None
            
            # Get CVE references
            cve_refs = [ref.get("id") for ref in result.findall(".//refs/ref[@type='cve']")]

            # Check and get 'threat'
            threat_element = result.find(".//threat")
            threat = threat_element.text.strip() if threat_element is not None else "Unknown"
            
            # Check and get 'severity'
            severity_element = result.find(".//severity")
            severity = float(severity_element.text.strip()) if severity_element is not None else 0.0
            
            # Default CVSS vector components
            av = ac = pr = ui = s = c = i = a = "N"
            
            if cvss_base:
                # Check and get 'cvss_base_vector'
                cvss_base_vector_element = result.find(".//tags")
                if cvss_base_vector_element is not None:
                    cvss_base_vector = cvss_base_vector_element.text
                    # Extract CVSS vector metrics
                    if "AV:" in cvss_base_vector:
                        av = cvss_base_vector.split("AV:")[1][0]
                    if "AC:" in cvss_base_vector:
                        ac = cvss_base_vector.split("AC:")[1][0]
                    if "PR:" in cvss_base_vector:
                        pr = cvss_base_vector.split("PR:")[1][0]
                    if "UI:" in cvss_base_vector:
                        ui = cvss_base_vector.split("UI:")[1][0]
                    if "S:" in cvss_base_vector:
                        s = cvss_base_vector.split("S:")[1][0]
                    if "C:" in cvss_base_vector:
                        c = cvss_base_vector.split("C:")[1][0]
                    if "I:" in cvss_base_vector:
                        i = cvss_base_vector.split("I:")[1][0]
                    if "A:" in cvss_base_vector:
                        a = cvss_base_vector.split("A:")[1][0]
            
            if endpoint not in results:
                results[endpoint] = {
                    "endpoint": endpoint,
                    "cve": cve_refs,
                    "score": severity,
                    "av": av,
                    "ac": ac,
                    "pr": pr,
                    "ui": ui,
                    "s": s,
                    "c": c,
                    "i": i,
                    "a": a
                }
        
        return results
    

    def get_scanners_as_json(self):
        try:
            self.ensure_authenticated()
            # Ottieni la lista degli scanner
            scanners_response = self.gmp.get_scanners()
            
            # Parsing della risposta XML
            root = ET.fromstring(scanners_response)

            # Trova tutti gli elementi 'scanner'
            scanners_list = []
            scanners = root.findall('.//scanner')
            for scanner in scanners:
                scanner_id = scanner.attrib.get('id')
                scanner_name = scanner.find('name').text

                # Aggiungi ogni scanner a una lista di dizionari
                scanners_list.append({
                    'id': scanner_id,
                    'name': scanner_name
                })

            # Converti la lista di dizionari in un JSON
            return json.dumps(scanners_list, indent=4)

        except GvmError as e:
            print(f"Failed to retrieve scanners: {e}")
            return None


    def get_openvas_targets(self):
        try:
            # Ensure that authentication has been completed
            self.ensure_authenticated()

            # Get the XML of targets from OpenVAS
            targets_response = self.gmp.get_targets()
            targets_xml = ET.fromstring(targets_response)

            # Initialize the list of targets
            targets_list = []

            # Loop through all the targets in the XML
            for target in targets_xml.findall('.//target'):
                target_id = target.get('id')  # Access the 'id' attribute
                
                if target_id is not None:
                    targets_list.append({
                        "id": target_id,
                        # Uncomment the line below to include the target's name
                        # "name": target.findtext('name')
                    })

            return targets_list

        except Exception as e:
            raise Exception(f"Error retrieving targets from OpenVAS: {e}")
        
    def delete_targets(self, target_ids):
        try:
            self.ensure_authenticated()
            
            tasks_response = self.gmp.get_tasks()  
            root = ET.fromstring(tasks_response)
            
            all_tasks = []
            for task in root.findall('.//task'):
                task_id = task.get('id')
                target_id = task.find('.//target').get('id')
                all_tasks.append({'id': task_id, 'target': target_id})

            # Filtra i task da eliminare in base ai target_ids forniti
            tasks_to_delete = [task for task in all_tasks if task['target'] in target_ids]

            # Elimina i task associati ai target
            for task in tasks_to_delete:
                self.gmp.delete_task(task['id'])
                print(f"Task {task['id']} eliminated successfully.")

            # Elimina i target
            for target_id in target_ids:
                self.gmp.delete_target(target_id)
                print(f"Target {target_id} eliminated successfully.")

        except GvmError as e:
            print(f"Error while deleting targets: {e}")
            raise

    def disconnect(self):
        """Disconnect from the server and close the connection."""
        try:
            if self.gmp:
                # Verifica se la disconnessione da GMP è necessaria
                try:
                    self.gmp.logout()
                    print("Logged out from GMP.")
                except Exception as logout_error:
                    print(f"Error during GMP logout: {logout_error}")

            if self.connection:
                self.connection.disconnect()  # Chiude la connessione TLS
                print("Disconnected from the TLS connection.")
        except Exception as e:
            print(f"Error during disconnection: {e}")
        finally:
            self.gmp = None  # Pulisci la connessione GMP
            self.connection = None  # Pulisci la connessione TLS
