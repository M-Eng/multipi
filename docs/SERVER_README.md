## Server Setup

This guide describes how to set up the MultiPi server application on a Linux machine.

### Prerequisites

Before installing the MultiPi server, ensure your system meets the following requirements:

1.  **Operating System:** Only tested on Linux, might work on other systems.
2.  **Python:** Python 3.x installed.
3.  **FFmpeg:** Required for video processing. Install using your system's package manager (e.g., `sudo apt-get install ffmpeg` on Debian/Ubuntu).
4.  **MQTT Broker:** A running MQTT broker is required for communication between the server and clients. If you don't have one, you can install and configure Mosquitto (see [MQTT Broker Setup](#mqtt-broker-setup-mosquitto) below).

### Server Installation

These steps assume you haven't already cloned the repository and set up a virtual environment following the main README.

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/M-Eng/multipi.git
    cd multipi
    ```

2.  **Install Python Dependencies:**
    Install the server's required Python packages.
    ```bash
    pip install -r src/server/requirements.txt
    ```

### MQTT Broker Setup (Mosquitto)

MultiPi uses MQTT for communication. If you need to set up a broker, these instructions cover installing Mosquitto and securing it with TLS certificates.

1.  **Install Mosquitto:**
    Use your system's package manager.
    ```bash
    # Example for Debian/Ubuntu
    sudo apt-get update
    sudo apt-get install mosquitto mosquitto-clients
    ```

2.  **Generate TLS Certificates (Self-Signed Example):**
    These commands generate a Certificate Authority (CA), server certificate, and client certificate. Store these securely (e.g., in a `~/certs` directory).
    ```bash
    # Choose a directory for certificates (e.g., mkdir ~/certs; cd ~/certs)

    # Create Certificate Authority (CA)
    openssl genrsa -out ca.key 2048
    openssl req -new -x509 -days 3650 -subj "/CN=MultiPiCA" -key ca.key -out ca.crt

    # Create Server Certificate
    openssl genrsa -out server.key 2048
    # IMPORTANT: Replace 'your_server_hostname_or_ip' with the actual hostname or IP address
    # clients will use to connect to the broker.
    openssl req -new -subj "/CN=your_server_hostname_or_ip" -key server.key -out server.csr
    openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650

    # Create Client Certificate (used by MultiPi server/clients to connect to broker)
    openssl genrsa -out client.key 2048
    openssl req -new -subj "/CN=MultiPiClient" -key client.key -out client.csr
    openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 3650
    ```

3.  **Configure Mosquitto for TLS:**
    Edit the Mosquitto configuration file (usually `/etc/mosquitto/mosquitto.conf` or a file in `/etc/mosquitto/conf.d/`). Add the following lines, **adjusting file paths** to where you stored your certificates:
    ```ini
    # Basic settings
    pid_file /run/mosquitto/mosquitto.pid
    persistence true
    persistence_location /var/lib/mosquitto/
    log_dest file /var/log/mosquitto/mosquitto.log

    # Allow clients without username/password if they have a valid certificate
    allow_anonymous true 
    # Use port 8883 for TLS connections
    listener 8883

    # TLS settings - ADJUST PATHS!
    cafile /path/to/your/certs/ca.crt
    certfile /path/to/your/certs/server.crt
    keyfile /path/to/your/certs/server.key
    require_certificate true # Clients must present a certificate signed by the CA
    # Optional: Specify TLS version (recommended)
    # tls_version tlsv1.2
    ```
    Ensure the Mosquitto user (often `mosquitto`) has read access to the certificate files. You might need to adjust permissions:
    ```bash
    # Example: Grant read access to the key file (adjust path)
    sudo chown mosquitto:mosquitto /path/to/your/certs/server.key
    sudo chmod 640 /path/to/your/certs/server.key 
    # Or, less secure but simpler for testing:
    # sudo chmod a+r /path/to/your/certs/server.key
    ```

4.  **Restart Mosquitto:**
    Apply the configuration changes.
    ```bash
    sudo systemctl restart mosquitto.service
    ```

5.  **Verify (Optional):**
    Check the status and logs:
    ```bash
    sudo systemctl status mosquitto.service
    sudo journalctl -u mosquitto.service
    ```
    Test publishing and subscribing using the generated certificates (adjust paths and hostname):
    ```bash
    # Terminal 1 (Subscriber)
    mosquitto_sub -h your_server_hostname_or_ip -p 8883 --cafile /path/to/your/certs/ca.crt --cert /path/to/your/certs/client.crt --key /path/to/your/certs/client.key -t test/topic

    # Terminal 2 (Publisher)
    mosquitto_pub -h your_server_hostname_or_ip -p 8883 --cafile /path/to/your/certs/ca.crt --cert /path/to/your/certs/client.crt --key /path/to/your/certs/client.key -t test/topic -m "hello secure mqtt"
    ```

### Server Configuration

Configure the MultiPi server application:

1.  Navigate to the configuration directory: `cd configs/`
2.  Copy the example configuration: `cp config_server.example.ini config_server.ini` (Adjust if the example file has a different name)
3.  Edit `config_server.ini` with your settings, paying close attention to:
    *   `[MQTT]`: Broker address, port (e.g., 8883 for TLS), and paths to the **client** certificate (`client.crt`), **client** key (`client.key`), and **CA** certificate (`ca.crt`) generated previously.
    *   `[WEBSERVER]`: Address and port for the web interface (e.g., 5000).
    *   `[MAIN]`: Path to the directory where video data should be stored (`VIDEO_DATA_DIR`). Ensure this directory exists and the server has write permissions.

Refer to the main [README's Configuration section](../README.md#configuration) and comments within the example configuration file for more details. Return to the project root after editing: `cd ..`

### Running the Server

Start the server application:
```bash
python3 src/server/start.py
```
The server should connect to the MQTT broker and start the web interface. You can access the web interface at the address specified in `config_server.ini` on port 5000 by default.

### Auto-start on Boot (Optional)

Similar to the client, you can create a `systemd` service file to run the server automatically on boot. You would need to create a `multipi-server.service` file, ensuring the `ExecStart` path points to the correct Python executable in your virtual environment and the `start.py` script, and set the correct `WorkingDirectory`. Remember to configure the server fully *before* enabling the service.

