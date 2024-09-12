# OpenVAS Automation with Python

This project provides a RESTful interface to interact with OpenVAS, allowing you to manage vulnerability scans, view results, and administer targets and scanners. It also includes a Python client to interact with OpenVAS through GVM. The project is designed to be easy to use, build, and replicate.

## Requirements

To run this project, you need to install:

- Python 3.8+
- OpenVAS with GVM (Greenbone Vulnerability Management)
- Docker (to run vulnerable containers and OpenVAS)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-repo/openvas-automation.git
   cd openvas-automation

2. Create and activate a virtual environment:

python3 -m venv venv
source venv/bin/activate


3. Install the dependencies:

pip install -r requirements.txt


4. Set up OpenVAS GVM in Docker:

To run OpenVAS with GVM using the REST API in Docker, use the following command:

docker run -d -p 443:443 -p 9390:9390 -p 80:80 --name openvas securecompliance/gvm:11.0.1-r3

Once the container is running, access the OpenVAS dashboard via your browser at https://localhost. You may need to configure OpenVAS and synchronize the feeds.


5. Start the Flask app:

python app.py

The server will be available at:

http://127.0.0.1:5000

http://172.30.56.250:5000




Usage

You can interact with the API using curl requests or tools like Postman.

1. Start a Scan

Start a new scan on one or more specified targets:

curl -X POST http://127.0.0.1:5000/trigger_scan \
-H "Content-Type: application/json" \
-d '{
  "scan_name": "DVWA Scan",
  "targets": ["172.17.0.3"]
}'

or

curl -X POST http://localhost:5000/trigger_scan \
-H "Content-Type: application/json" \
-d '{
  "scan_name": "DVWA Scan",
  "targets": ["172.17.0.3"]
}'

2. Check the Scan Status

To retrieve the scan status, replace mock_task_id with the real task ID obtained from the response of the first command:

curl -X GET "http://localhost:5000/scan_status/DVWA%20Scan?task_id=498b6fe9-6f54-41f6-ace7-2e5585f24c11"

If you are checking the status of two tasks:

curl -X GET "http://localhost:5000/scan_status/My_Scan?task_id=task_id1&task_id=task_id2"

3. View the Targets

To view all the targets in OpenVAS:

curl -X GET http://localhost:5000/openvas_targets

4. Delete Targets

To delete specific targets, use the following command:

curl -X POST http://localhost:5000/delete_targets \
-H "Content-Type: application/json" \
-d '{
  "target_ids": ["733f243c-cac4-42c5-8cdb-857c7b9e50d2", "136820aa-c2a7-47fd-ba99-33478af055b5"]
}'

5. List Available Scanners

To get the list of available scanners in OpenVAS:

curl -X GET http://localhost:5000/scanners

6. Start a Scan with Multiple Targets

To trigger a scan on multiple targets:

curl -X POST http://localhost:5000/trigger_scan \
-H "Content-Type: application/json" \
-d '{
  "scan_name": "My_Scan",
  "targets": ["172.17.0.3", "172.17.0.4"]
}'

Docker Commands for Vulnerable Containers

To run vulnerable containers for testing, you can use the following Docker commands:

DVWA (Damn Vulnerable Web Application):

docker run --rm -it -p 8080:80 vulnerables/web-dvwa

WebGoat:

docker run --rm -it -p 8081:8080 webgoat/webgoat-8.0

Metasploitable 2:

docker run --rm -it -p 22:22 -p 8090:80 -p 3307:3306 tleemcjr/metasploitable2

OWASP Juice Shop:

docker run --rm -p 3000:3000 bkimminich/juice-shop


Library Documentation

The openvas_client.py library contains all the necessary methods to interact with OpenVAS. Below is an overview of the key methods:

OpenVASClient

This class handles all interactions with OpenVAS.

ensure_authenticated(): Authenticates the client with OpenVAS if not already authenticated.

create_target(target_name): Creates a new target with the specified IP address.

target_id = client.create_target("192.168.1.10")

create_task(scan_name, config_id, target_id, scanner_id): Creates a new scan task. Requires the scan name, configuration ID (e.g., CVE, OpenVAS default), target ID, and scanner ID.

task_id = client.create_task("test_scan", "config-id", "target-id", "scanner-id")

start_task(task_id): Starts a scan for the specified task_id.

client.start_task("task-id")

get_task_status(task_id): Retrieves the current status of a scan task.

status = client.get_task_status("task-id")

get_task_progress(task_id): Returns the scan completion percentage.

progress = client.get_task_progress("task-id")

get_report_results(task_id): Returns the scan results in JSON format, including identified vulnerabilities and CVSS scores.

result, result_summary = client.get_report_results("task-id")

get_scanners_json(): Retrieves a list of available scanners from OpenVAS in JSON format.

scanners = client.get_scanners_json()

get_openvas_targets(): Retrieves a list of all configured targets in OpenVAS.

all_targets = client.get_openvas_targets()

delete_targets(target_ids): Deletes the specified targets from OpenVAS.

client.delete_targets(["target_id1", "target_id2"])


Conclusion

This project provides a simple interface to manage vulnerability scans using OpenVAS. With Docker, you can quickly run vulnerable containers to test your scanning infrastructure and ensure the system works correctly.