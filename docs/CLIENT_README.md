## Generic Linux Client Setup

This guide describes how to set up the MultiPi client on a Linux machine. For Raspberry Pi specific instructions, please refer to [`RPI_README.md`](./RPI_README.md).

### System Dependencies

The client requires Python 3 and FFmpeg.

On **Debian/Ubuntu-based systems**, you can install these using `apt-get`:
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv ffmpeg
```
*Note: Users on other Linux distributions should use their respective package managers (e.g., `yum`, `dnf`, `pacman`) to install `python3`, `python3-pip`, `python3-venv`, and `ffmpeg`.*

### Client Installation

1.  **Clone the Repository:**
    Clone the entire MultiPi repository to a location of your choice.
    ```bash
    git clone https://github.com/M-Eng/multipi.git
    cd multipi
    ```

2.  **Install Python Dependencies:**
    Install the required Python packages using pip.
    ```bash
    pip install -r src/client/requirements.txt
    ```

### Client Configuration

Before running the client, you need to configure it:

1.  Navigate to the configuration directory: `cd configs/`
2.  Copy the example configuration: `cp config_client.example.ini config_client.ini` (Assuming an example file exists, adjust if needed)
3.  Edit `config_client.ini` with your settings, especially:
    *   MQTT broker address and credentials.
    *   Server address for video streaming.
    *   Any other relevant camera or client parameters.

Refer to the main [README's Configuration section](../../README.md#configuration) for more details. After editing, return to the project root directory: `cd ..`

### Client Execution Modes

The MultiPi client offers three primary modes of operation, corresponding to different main scripts in `src/client/`:

1.  **`main.py` (Standard Remote Control):**
    *   This is the standard client mode.
    *   Connects to the MQTT broker and listens for commands from the central server (start/stop recording, get picture, ping, shutdown, reboot).
    *   Requires the server and MQTT broker to be running.
    *   Uses `configs/config_client.ini` by default.

2.  **`main_auto.py` (Scheduled Recording):**
    *   Runs independently and records video locally based on time windows defined in its configuration file (`configs/config_client_auto.ini` by default).
    *   Still connects to MQTT for status reporting and commands like PING, GET_PICTURE, SHUTDOWN, REBOOT (but ignores START/STOP commands).
    *   **Crucially requires the client machine to have accurate time.** Ensure the clock is synchronized at boot (e.g., via NTP, requires internet access) or use an external Real-Time Clock (RTC) module.

3.  **`main_manual.py` (Manual Button Control - RPi Specific):**
    *   Designed for Raspberry Pi setups with a physical button and LED connected to GPIO pins.
    *   Pressing the button starts/stops local recording.
    *   Holding the button triggers a shutdown.
    *   Does *not* connect to MQTT or the server.
    *   Uses `configs/config_client_manual.ini` by default.

### Running the Client

Choose the appropriate script based on the desired mode:

*   **Standard Remote Control:**
    ```bash
    # Ensure venv is active if used
    python3 src/client/main.py --config configs/config_client.ini
    ```
*   **Scheduled Recording:**
    ```bash
    # Ensure venv is active if used
    # Make sure clock is synchronized!
    python3 src/client/main_auto.py --config configs/config_client_auto.ini
    ```
*   **Manual Button Control (RPi Only):**
    ```bash
    # Ensure venv is active if used
    # Requires button/LED connected to GPIO
    python3 src/client/main_manual.py --config configs/config_client_manual.ini
    ```

### Auto-start on Boot (Systemd)

For systems using `systemd`, a service file is provided to run the client automatically on boot. This is typically used for the **Standard Remote Control (`main.py`)** or **Scheduled Recording (`main_auto.py`)** modes.

1.  **Locate the Service File:** The example service file is `multipi-client.service`.
    ```bash
    # Example path - VERIFY THIS!
    SERVICE_FILE_PATH="src/client/systemd-service/multipi-client.service"
    ```

2.  **Copy and Enable the Service:**
    *   You **must** edit the `multipi-client.service` file *before* copying it. Update the `WorkingDirectory`, `ExecStart` paths, and potentially the `User`.
    *   **Crucially, ensure `ExecStart` points to the correct script (`main.py` or `main_auto.py`) and its corresponding config file (`--config ...`)**. It should also use the `python3` executable within your virtual environment (e.g., `/path/to/multipi/venv/bin/python3`).
    *   Example `ExecStart` for standard mode:
        `ExecStart=/path/to/multipi/venv/bin/python3 /path/to/multipi/src/client/main.py --config /path/to/multipi/configs/config_client.ini`
    *   Example `ExecStart` for auto mode:
        `ExecStart=/path/to/multipi/venv/bin/python3 /path/to/multipi/src/client/main_auto.py --config /path/to/multipi/configs/config_client_auto.ini`
    *   Example `ExecStart` for manual mode:
        `ExecStart=/path/to/multipi/venv/bin/python3 /path/to/multipi/src/client/main_manual.py --config /path/to/multipi/configs/config_client_manual.ini`
    *   Copy the **edited** service file to the systemd directory:
        ```bash
        sudo cp ${SERVICE_FILE_PATH} /etc/systemd/system/
        ```
    *   Reload the systemd daemon and enable the service:
        ```bash
        sudo systemctl daemon-reload
        sudo systemctl enable multipi-client.service
        ```

3.  **Managing the Service:**
    *   Start: `sudo systemctl start multipi-client.service`
    *   Stop: `sudo systemctl stop multipi-client.service`
    *   Check Status: `sudo systemctl status multipi-client.service`
    *   View Logs: `sudo journalctl -u multipi-client.service`

*Remember to configure the client (`config_client.ini`) correctly before starting the service.*

### Rebooting the pi and shutting it down

To reboot the pi you can run the following command:

```bash
sudo reboot
```

To shutdown the pi you can run the following command:

```bash
sudo shutdown -h now
```
