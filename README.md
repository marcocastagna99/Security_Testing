
---
# OpenVAS Vulnerability Assessment Automation with Python: A RESTful Web Server for Security Scans

This project provides a RESTful interface to interact with OpenVAS, allowing you to manage vulnerability scans, view results, and administer targets and scanners. It also includes a Python client to interact with OpenVAS through GVM. The project is designed to be easy to use, build, and replicate.

## Requirements

To run this project, you need to install:

- Python 3.8+
- OpenVAS with GVM (Greenbone Vulnerability Management)
- Docker (to run vulnerable containers and OpenVAS)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/marcocastagna99/Security_Testing.git
   cd Security_Testing
   ```

2. *(Optional)* Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up OpenVAS GVM in Docker:

   To run OpenVAS with GVM using the REST API in Docker, use the following command:

   ```bash
   docker run -d -p 443:443 -p 9390:9390 -p 80:80 --name openvas securecompliance/gvm:11.0.1-r3
   ```

   Once the container is running, access the OpenVAS dashboard via your browser at [https://localhost](https://localhost). You may need to configure OpenVAS and synchronize the feeds.

5. Start the Flask app:

   ```bash
   python app.py
   ```

   The server will be available at:

   - `http://127.0.0.1:5000`
   - `http://172.30.56.250:5000`

## Configuration

If you are testing on your local machine (without Docker Compose), you should update the `app.py` configuration to use `localhost`. Specifically, you need to:

  1. **Open `app.py`** and locate the configuration section where OpenVAS connection details are specified.

  2. **Update the configuration** for local testing by using the following settings:

    ```python
    # If you are testing on a local machine, use this configuration
    OPENVAS_HOST = 'localhost'
    OPENVAS_PORT = 9390
    OPENVAS_USERNAME = 'admin'
    OPENVAS_PASSWORD = 'admin'
    ```

## Docker Build and Run Instructions   (alternative run)

This project also uses Docker and Docker Compose to create an isolated development environment that includes all necessary services for vulnerability scanning and testing. The `docker-compose.yml` file is configured to set up the application, OpenVAS, and several vulnerable containers for testing.

### Requirements

- **Docker**: Ensure you have Docker installed on your machine. You can download it from [Docker's official website](https://www.docker.com/products/docker-desktop).
- **Docker Compose**: Docker Compose is required to manage multi-container Docker applications. It usually comes with Docker Desktop. If not, you can install it from [Docker Compose's installation page](https://docs.docker.com/compose/install/).

### Building and Running the Environment

1. **Clone the Repository**

   First, clone the repository if you haven't already:

   ```bash
   git clone https://github.com/marcocastagna99/Security_Testing.git
   cd Security_Testing
   ```

2. **Build and Start Containers**

   Use Docker Compose to build and start the containers. This command will build the application container and start all defined services:

   ```bash
   docker-compose up --build
   ```

   The `--build` flag ensures that Docker Compose builds the latest version of your application before starting the services.

3. **Check the Services**

   Once the containers are up and running, the following services will be available:

   - **Flask Application**: Accessible at `http://127.0.0.1:5000`
   - **OpenVAS**: Accessible at `http://localhost` (Ensure that OpenVAS is configured and feeds are synchronized)
   - **DVWA (Damn Vulnerable Web Application)**: Accessible at `http://localhost:8080`
   - **WebGoat**: Accessible at `http://localhost:8081`

4. **Stop and Remove Containers**

   To stop and remove all running containers, use:

   ```bash
   docker-compose down
   ```

   This command will stop all containers and remove them, along with any networks created by `docker-compose up`.

### Customizing and Testing

You can modify the `docker-compose.yml` file to add or remove services as needed. To run additional vulnerable containers for testing, you can include their respective Docker images in the `docker-compose.yml` file.

For example, to add more containers or change configurations, edit the `docker-compose.yml` file and restart the environment using the `docker-compose up --build` command.

### Troubleshooting

If you encounter any issues, check the logs for individual services using:

```bash
docker-compose logs <service_name>
```

Replace `<service_name>` with the name of the service you want to check (e.g., `app`, `openvas`, `web-dvwa`, etc.).



Feel free to adjust the instructions based on your specific needs or any additional configurations you might have.

## Usage

You can interact with the API using curl requests or tools like Postman.

N.B
It's important knew the ip of the target before start the test

1. **Start a Scan**

   Start a new scan on one or more specified targets:
  

   ```bash
   curl -X POST http://127.0.0.1:5000/trigger_scan \
   -H "Content-Type: application/json" \
   -d '{
     "scan_name": "DVWA Scan",
     "targets": ["172.20.0.2"]
   }'
   ```

   or

   ```bash
   curl -X POST http://localhost:5000/trigger_scan \
   -H "Content-Type: application/json" \
   -d '{
     "scan_name": "DVWA Scan",
     "targets": ["172.20.0.2"]
   }'
   ```
   
 **Important:** Once the scan is initiated, make sure to keep track of the task IDs associated with the targets. These IDs will be returned in the response, like so:

   ```json
   {
     "message": "Scan started",
     "task_ids": [
       "07f47596-f5e4-4b92-8d1f-a25f31661772",
       "b0db9d3c-1d17-41c7-b466-e60fa327c6fc"
     ]
   }
   ```



2. **Check the Scan Status**

   To retrieve the scan results or status, replace DVWA%20Scan with the real scan name and add the real task ID obtained from the response of the first command as a parameter of the request:
   ```bash
   curl -X GET "http://localhost:5000/scan_status/DVWA%20Scan?task_id=498b6fe9-6f54-41f6-ace7-2e5585f24c11"
   ```

   If you are checking the status of two tasks:

   ```bash
   curl -X GET "http://localhost:5000/scan_status/My_Scan?task_id=task_id1&task_id=task_id2"
   ```

3. **View the Targets**

   To view all the targets in OpenVAS:

   ```bash
   curl -X GET http://localhost:5000/openvas_targets
   ```

4. **Delete Targets**

   To delete specific targets, use the following command:

   ```bash
   curl -X POST http://localhost:5000/delete_targets \
   -H "Content-Type: application/json" \
   -d '{
     "target_ids": ["733f243c-cac4-42c5-8cdb-857c7b9e50d2", "136820aa-c2a7-47fd-ba99-33478af055b5"]
   }'
   ```

5. **List Available Scanners**

   To get the list of available scanners in OpenVAS:

   ```bash
   curl -X GET http://localhost:5000/scanners
   ```

6. **Start a Scan with Multiple Targets**

   To trigger a scan on multiple targets:

   ```bash
   curl -X POST http://localhost:5000/trigger_scan \
   -H "Content-Type: application/json" \
   -d '{
     "scan_name": "My_Scan",
     "targets": ["172.20.0.2", "172.20.0.3"]
   }'
   ```

## Docker Commands for Vulnerable Containers

To run vulnerable containers for testing, you can use the following Docker commands:

- **DVWA (Damn Vulnerable Web Application):**

  ```bash
  docker run --rm -it -p 8080:80 vulnerables/web-dvwa
  ```

- **WebGoat:**

  ```bash
  docker run --rm -it -p 8081:8080 webgoat/webgoat-8.0
  ```

- **Metasploitable 2:**

  ```bash
  docker run --rm -it -p 22:22 -p 8090:80 -p 3307:3306 tleemcjr/metasploitable2
  ```

- **OWASP Juice Shop:**

  ```bash
  docker run --rm -p 3000:3000 bkimminich/juice-shop
  ```

## Library Documentation

The `openvas_client.py` library contains all the necessary methods to interact with OpenVAS. Below is an overview of the key methods:

### `OpenVASClient`

This class handles all interactions with OpenVAS.

- `ensure_authenticated()`: Authenticates the client with OpenVAS if not already authenticated.
  
- `create_target(target_name)`: Creates a new target with the specified IP address.

  ```python
  target_id = client.create_target("192.168.1.10")
  ```

- `create_task(scan_name, config_id, target_id, scanner_id)`: Creates a new scan task. Requires the scan name, configuration ID (e.g., CVE, OpenVAS default), target ID, and scanner ID.

  ```python
  task_id = client.create_task("test_scan", "config-id", "target-id", "scanner-id")
  ```

- `start_task(task_id)`: Starts a scan for the specified task_id.

  ```python
  client.start_task("task-id")
  ```

- `get_task_status(task_id)`: Retrieves the current status of a scan task.

  ```python
  status = client.get_task_status("task-id")
  ```

- `get_task_progress(task_id)`: Returns the scan completion percentage.

  ```python
  progress = client.get_task_progress("task-id")
  ```

- `get_report_results(task_id)`: Returns the scan results in JSON format, including identified vulnerabilities and CVSS scores.

  ```python
  result, result_summary = client.get_report_results("task-id")
  ```

- `get_scanners_json()`: Retrieves a list of available scanners from OpenVAS in JSON format.

  ```python
  scanners = client.get_scanners_json()
  ```

- `get_openvas_targets()`: Retrieves a list of all configured targets in OpenVAS.

  ```python
  all_targets = client.get_openvas_targets()
  ```

- `delete_targets(target_ids)`: Deletes the specified targets from OpenVAS.

  ```python
  client.delete_targets(target_ids)
  ```
  Here’s how you can update your README with a "Common Errors" section in English:



## Common Errors

### Error: `{"message": "Scan started", "task_ids": null}`

**Issue:**
When you trigger a scan with the `curl` command and receive the response `{"message": "Scan started", "task_ids": null}`, it indicates that the scan was initiated, but the task IDs could not be retrieved. This typically happens if the target already exists in OpenVAS. Additionally, it may occur if OpenVAS is not yet fully configured or ready to accept connections.

**Solution:**
1. **Check if the target already exists:**
   - Use the following command to retrieve a list of all targets:
     ```bash
     curl -X GET http://localhost:5000/openvas_targets
     ```

2. **Find the target ID from the response.**

3. **Delete the existing target:**
   - Use the target ID obtained from the previous step to delete the target with the following command:
     ```bash
     curl -X POST http://localhost:5000/delete_targets \
     -H "Content-Type: application/json" \
     -d '{
       "target_ids": ["<target_id>"]
     }'
     ```
   - Replace `<target_id>` with the actual ID of the target you want to delete.

4. **Retry the scan request:**
   - Once the target is deleted, trigger the scan again using the `curl` command:
     ```bash
     curl -X POST http://127.0.0.1:5000/trigger_scan \
     -H "Content-Type: application/json" \
     -d '{
       "scan_name": "DVWA Scan",
       "targets": ["172.24.0.2"]
     }'
     ```

### Error: `Error when retrieving targets from OpenVAS: SSL Error: TLS/SSL connection has been closed (EOF) (_ssl.c:1131)`

**Issue:**
This error indicates that the Flask application is unable to connect to the OpenVAS service. This usually happens when OpenVAS is still starting up or has not yet finished configuring.

**Solution:**
1. **Ensure OpenVAS is fully started:**
   - Check the logs of the OpenVAS container to confirm it has finished starting up. You can view the logs using:
     ```bash
     docker logs openvas
     ```

2. **Wait for OpenVAS to be ready:**
   - It may take a few minutes for OpenVAS to become fully operational. Wait a bit longer and retry the request.

3. **Verify OpenVAS configuration:**
   - Make sure that OpenVAS is properly configured and that the ports are correctly mapped and accessible.

4. **Check network configuration:**
   - Ensure that there are no network issues preventing communication between your Flask app and the OpenVAS container.


## Conclusion

This project provides a simple interface to manage vulnerability scans using OpenVAS. With Docker, you can quickly run vulnerable containers to test your scanning infrastructure and ensure the system works correctly.

---
