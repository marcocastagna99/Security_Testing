import re
from flask import json
from gvm.connections import TLSConnection
from gvm.protocols.latest import Gmp
from gvm.errors import GvmError
from xml.etree import ElementTree as ET
import xmltodict


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


    def get_task_result(self, task_id):
        # Ottiene i risultati grezzi usando l'API RESTful
        raw_results = self.get_raw_task_result(task_id)
        
        # Processa i risultati grezzi e ritorna i dettagli formattati e il sommario
        result_details, result_summary = self.parse_openvas_results(raw_results)
        
        return result_details, result_summary

    def get_raw_task_result(self, task_id):
        try:
            # Assicura che l'utente sia autenticato prima di fare la richiesta
            self.ensure_authenticated()
            
            # Effettua la richiesta all'API per ottenere i risultati del task
            response = self.gmp.get_results(task_id=task_id)
            
            # Scrivi la risposta completa su un file per il debug
            with open(f"task_{task_id}_raw_result.xml", "w") as file:
                file.write(response)
            
            # Controlla se la risposta è una stringa XML
            if isinstance(response, str):
                # Il contenuto della risposta è già in formato XML
                xml_content = response
                
                # Converti il contenuto XML in un dizionario Python (usa xmltodict)
                try:
                    result_data = xmltodict.parse(xml_content)
                except Exception as e:
                    raise Exception(f"Failed to parse XML content: {str(e)}")
                
                # Verifica la struttura dei dati risultanti
                if 'get_results_response' in result_data and 'result' in result_data['get_results_response']:
                    return xml_content  # Ritorna il contenuto XML per il parsing successivo
                else:
                    raise Exception("Unexpected structure in the XML response")
            else:
                raise Exception("Unexpected response format: expected XML string")

        except Exception as e:
            # Gestisci eventuali eccezioni
            raise Exception(f"An error occurred while fetching results for task {task_id}: {str(e)}")

    def parse_openvas_results(self, xml_data):
        root = ET.fromstring(xml_data)
        result_details = []
        result_summary = []
        seen_ids = set()  # Set per tenere traccia degli ID già visti

        for result in root.findall(".//result"):
            result_id = result.get('id')
            if result_id in seen_ids:
                continue  # Salta i risultati già processati
            seen_ids.add(result_id)

            name = result.findtext('name')
            host = result.findtext('host')
            port = result.findtext('port')
            severity = result.findtext('severity')
            description = result.findtext('description')
            cvss_base = result.findtext(".//cvss_base")
            cve = result.findtext(".//cve")

            # Parsing dettagli result_details
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
            result_details.append(detail)

            # Parsing result_summary
            if cvss_base:
                cvss_data = self.parse_cvss(cvss_base)
                if cvss_data:
                    summary = {
                        "endpoint": f"{host}:{port}",
                        "cve": cve,
                        "score": float(severity) if severity else None,
                        "av": cvss_data.get("av"),
                        "ac": cvss_data.get("ac"),
                        "pr": cvss_data.get("pr"),
                        "ui": cvss_data.get("ui"),
                        "s": cvss_data.get("s"),
                        "c": cvss_data.get("c"),
                        "i": cvss_data.get("i"),
                        "a": cvss_data.get("a")
                    }
                    result_summary.append(summary)

        # Ritorna entrambe le liste dopo il ciclo
        return result_details, result_summary

    def parse_cvss(self, cvss_string):
        # Pattern per estrarre i valori dalla stringa CVSS
        pattern = r"CVSS:(?P<version>\d\.\d)/AV:(?P<av>[NAL])/AC:(?P<ac>[LHM])/PR:(?P<pr>[NLH])/UI:(?P<ui>[NAL])/S:(?P<s>[UC])/C:(?P<c>[LHM])/I:(?P<i>[LHM])/A:(?P<a>[LHM])"
        match = re.match(pattern, cvss_string)
        if match:
            return match.groupdict()
        return None

"""
    def delete_target(self, target_id):
            
            #Elimina un target da OpenVAS e tutti i task associati.
            
            #:param target_id: ID del target da eliminare.
            
            try:
                # Assicurati di essere autenticato
                self.ensure_authenticated()

                # Recupera tutti i task e filtra quelli associati al target
                response = self.gmp.get_tasks()
                if isinstance(response, str):
                    root = ET.fromstring(response)
                else:
                    root = ET.ElementTree(response).getroot()
                
                all_tasks = []
                for task in root.findall('.//task'):
                    task_id = task.get('id')
                    task_target_id = task.find('.//target').get('id')
                    all_tasks.append({'id': task_id, 'target': task_target_id})

                # Filtra i task associati al target specificato
                tasks_to_delete = [task for task in all_tasks if task['target'] == target_id]

                # Elimina i task associati al target
                for task in tasks_to_delete:
                    self.gmp.delete_task(task['id'])
                    print(f"Task {task['id']} eliminato con successo.")

                # Elimina il target
                self.gmp.delete_target(target_id)
                print(f"Target {target_id} eliminato con successo.")

            except GvmError as e:
                print(f"Errore durante l'eliminazione del target: {e}")
                raise
            except Exception as e:
                print(f"Errore imprevisto durante l'eliminazione del target: {e}")
                raise
                """
