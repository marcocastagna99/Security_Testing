import ssl
import socket
import os



hostname = 'localhost'
port = 9390


""""
hostname = os.getenv('OPENVAS_HOST', 'openvas')  # Docker service name as default
port = int(os.getenv('OPENVAS_PORT', 9390))"""



# Creazione di un contesto SSL
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE  # Disabilita la verifica del certificato (solo per test)

try:
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            print("TLS version:", ssock.version())
            # Esegui altre operazioni con la connessione ssock se necessario
except ssl.SSLError as e:
    print("SSL Error:", e)
except socket.error as e:
    print("Socket Error:", e)
except Exception as e:
    print("An unexpected error occurred:", e)
