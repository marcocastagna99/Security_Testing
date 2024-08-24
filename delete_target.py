from gvm.connections import TLSConnection
from gvm.protocols.latest import Gmp
from gvm.errors import GvmError

# Configurazione del client OpenVAS
OPENVAS_HOST = 'localhost'
OPENVAS_PORT = 9390
OPENVAS_USERNAME = 'admin'
OPENVAS_PASSWORD = 'admin'

def delete_openvas_target(target_id):
    try:
        # Creazione della connessione TLS e inizializzazione del client GMP
        connection = TLSConnection(hostname=OPENVAS_HOST, port=OPENVAS_PORT)
        gmp = Gmp(connection=connection)
        gmp.authenticate(OPENVAS_USERNAME, OPENVAS_PASSWORD)

        # Recupero di tutti i task e filtro locale per quelli associati al target
        tasks_response = gmp.get_tasks()
        
        # Verifica della struttura della risposta e parsing
        # Esempio: Se tasks_response è in formato XML, puoi parsarlo con ElementTree
        # Altrimenti, se è in formato JSON, usa json.loads()

        # Esempio di parsing se tasks_response è in formato XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(tasks_response)
        
        all_tasks = []
        for task in root.findall('.//task'):
            task_id = task.get('id')
            target = task.find('.//target').get('id')
            all_tasks.append({'id': task_id, 'target': target})

        # Ora puoi filtrare i task in base al target_id
        tasks_to_delete = [task for task in all_tasks if task['target'] == target_id]

        # Eliminazione dei task associati al target
        for task in tasks_to_delete:
            gmp.delete_task(task['id'])
            print(f"Task {task['id']} eliminato con successo.")

        # Eliminazione del target
        gmp.delete_target(target_id)
        print(f"Target {target_id} eliminato con successo.")
    except GvmError as e:
        print(f"Errore durante l'eliminazione del target: {e}")

# Esempio di utilizzo
if __name__ == "__main__":
    print("Inserisci l'ID del target da eliminare: ")
    target_id_to_delete = input()

    delete_openvas_target(target_id_to_delete)
