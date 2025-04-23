# Raspberry Pi Client Setup

This guide details how to set up a Raspberry Pi as a remote camera client for the MultiPi system. It covers OS installation, network configuration, and the MultiPi client software setup. In the folder `raspberry-pi-setup` you can find all the files needed to setup the Raspberry Pi.

In the `raspberry-pi-setup/3d_files` directory within the repository, you can find all the 3D models for a case to hold the Raspberry Pi 4 and camera module 3 as well as a mounting bracket to mount the case easily. See the [3D Files README](../raspberry-pi-setup/3d_files/README.md) for previews and printing details.

## 1. Operating System Installation

We recommend using the official [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash your SD card.

*   **OS Choice:** Use a recent version of Raspberry Pi OS (e.g., Bookworm). Choose the "Lite" version if you don't need a graphical desktop.
*   **Imager Settings:** Use the Imager's advanced options to:
    *   Set a hostname for the Pi.
    *   Enable SSH.
    *   Set a username and password.
    *   Configure WiFi credentials (works for standard WPA2 networks).

## 2. Network Configuration

Ensure your Raspberry Pi can connect to the network where the MultiPi server and MQTT broker reside.

### Basic WiFi (WPA2)

If you didn't configure WiFi using the Imager, or need to change it, you can use the `nmtui` tool (NetworkManager Text User Interface) after connecting via SSH (see next section).

```bash
sudo nmtui
```
Navigate to "Activate a connection" to connect to available networks or "Edit a connection" to add/modify settings.

### Enterprise WiFi (WPA-EAP)

For more complex networks (like university or company WiFi):

1.  Connect the Pi temporarily using an Ethernet cable or a simpler WiFi network.
2.  SSH into the Pi (see next section).
3.  Create or edit a connection file in `/etc/NetworkManager/system-connections/`. Give it a descriptive name (e.g., `my-enterprise-wifi-name.nmconnection`).
4.  Populate the file with your network's specific settings. Below is a generic template (replace placeholders):

    ```ini
    [connection]
    id=my-enterprise-wifi-name
    uuid=924f17a3-105d-4370-ad0f-661f0d5d9915 # Generate one using `uuidgen`
    type=wifi
    autoconnect=true
    autoconnect-priority=10 # Higher number means higher priority

    [wifi]
    mode=infrastructure
    ssid=Your_Enterprise_SSID

    [wifi-security]
    key-mgmt=wpa-eap

    [802-1x]
    eap=PEAP;
    identity=your_username@your_domain.com
    password=your_password
    # Optional settings - check requirements for your network:
    # anonymous-identity=anonymous@your_domain.com
    # ca-cert=/path/to/your/ca/certificate.pem
    # phase2-auth=mschapv2
    # subject-match=CN=your_radius_server.your_domain.com

    [ipv4]
    method=auto

    [ipv6]
    addr-gen-mode=stable-privacy
    method=auto
    ```

5.  Set correct permissions:
    ```bash
    sudo chmod 600 /etc/NetworkManager/system-connections/my-enterprise-wifi.nmconnection
    ```
6.  Restart NetworkManager:
    ```bash
    sudo systemctl restart NetworkManager
    ```

### Redundant WiFi Connection

Consider adding a secondary, lower-priority connection (e.g., to a phone hotspot) to maintain access if the primary network configuration changes:

*   Create another `.nmconnection` file (e.g., `phone-hotspot.nmconnection`).
*   Set `autoconnect-priority=0` (lower than your primary connection).
*   Configure the hotspot's SSID and password.

### Debugging WiFi

```bash
sudo systemctl status NetworkManager
journalctl -u NetworkManager # View logs
nmcli device wifi list # List available networks
nmcli connection show # List configured connections
```

<!-- Foldable section for deprecated pre-Bookworm config -->
<details>
<summary>WiFi Configuration (Pre-Bookworm / wpa_supplicant - Deprecated)</summary>

For older Raspbian versions using `wpa_supplicant`, create a `wpa_supplicant.conf` file on the boot partition of the SD card before first boot.

```ini
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=CH # Set your country code

network={
    ssid="Your_Enterprise_SSID"
    key_mgmt=WPA-EAP
    eap=PEAP
    identity="your_username@your_domain.com"
    password="your_password" # Or use hash: see below
    # Optional:
    # anonymous_identity="anonymous@your_domain.com"
    # phase2="auth=MSCHAPV2"
    # ca_cert="/path/to/ca.pem"
    # subject_match="CN=your_radius_server.your_domain.com"
    priority=10
}
```

For additional security, the password can be stored as a hash. To generate the hash, you can use the `raspberry-pi-setup/hash_password.sh` script.

You can find more information about WiFi settings at this [link](https://medium.com/@bezzam/connecting-a-raspberry-pi-to-university-wpa-enterprise-wifi-532d4b203056).

</details>

## 3. Connecting via SSH

Once the Pi is booted and connected to the network, connect from your computer:

```bash
ssh your_pi_username@your_pi_hostname.local
# Or use the IP address if .local resolution fails
# ssh your_pi_username@<pi_ip_address>
```

For passwordless access (recommended for scripting/fleet management):

1.  **Generate Key Pair (on your computer):**
    ```bash
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_rpi # Choose a filename
    ```
2.  **Copy Public Key to Pi:**
    ```bash
    ssh-copy-id -i ~/.ssh/id_rsa_rpi.pub your_pi_username@your_pi_hostname.local
    ```
3.  **Connect:**
    ```bash
    ssh -i ~/.ssh/id_rsa_rpi your_pi_username@your_pi_hostname.local
    ```

## 4. System Preparation

Log in to the Pi via SSH and perform initial updates and install required system packages:

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg git
```

## 5. MultiPi Client Software Installation

Now, install the MultiPi client application.

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/M-Eng/multipi.git
    cd multipi
    ```

2.  **Create Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *Note: If using the systemd service later, ensure the service file points to the python executable inside this `venv`.* 

3.  **Install Python Dependencies:**
    ```bash
    # Ensure you are in the multipi directory and venv is active
    pip install -r src/client/requirements.txt
    ```

## 6. MultiPi Client Configuration

Configure the client to connect to your server and MQTT broker.

1.  Navigate to the configuration directory: `cd configs/`
2.  Copy the example configuration: `cp config_client.example.ini config_client.ini`
3.  Edit `config_client.ini` using a text editor (e.g., `nano config_client.ini`). Set:
    *   MQTT broker address, port, and certificate paths (if using TLS).
    *   Server address for video streaming.
    *   Any RPi-specific camera settings.
4.  Return to the project root: `cd ..`

## 7. Time Synchronization (systemd-timesyncd)

Accurate time is crucial for MultiPi. Raspberry Pi OS uses `systemd-timesyncd`. You can optionally increase polling frequency for potentially better sync:

1.  Edit the configuration:
    ```bash
    sudo nano /etc/systemd/timesyncd.conf
    ```
2.  Uncomment and adjust `PollIntervalMinSec` and `PollIntervalMaxSec` (values between 32-64s are reasonable). You can also specify custom NTP servers if needed.
    ```ini
    [Time]
    #NTP=
    #FallbackNTP= ...
    RootDistanceMaxSec=5
    PollIntervalMinSec=32
    PollIntervalMaxSec=64
    ```
3.  Restart the service:
    ```bash
    sudo systemctl restart systemd-timesyncd
    ```
4.  Check status:
    ```bash
    timedatectl status
    ```

## 8. Running the Client

The MultiPi client offers three primary modes of operation, corresponding to different main scripts in `src/client/`:

1.  **`main.py` (Standard Remote Control):**
    *   This is the standard client mode for remote control via the central server.
    *   Connects to the MQTT broker and listens for commands (start/stop recording, get picture, ping, shutdown, reboot).
    *   Requires the server and MQTT broker to be running.
    *   Uses `configs/config_client.ini` by default.

2.  **`main_auto.py` (Scheduled Recording):**
    *   Runs independently and records video locally based on time windows defined in its configuration file (`configs/config_client_auto.ini` by default).
    *   Still connects to MQTT for status reporting and remote commands like PING, GET_PICTURE, SHUTDOWN, REBOOT (but ignores START/STOP commands).
    *   **Crucially requires the Pi to have accurate time.** Ensure the clock is synchronized at boot (e.g., via NTP, requires internet access - see Section 7) or use an external Real-Time Clock (RTC) module.

3.  **`main_manual.py` (Manual Button Control):**
    *   Specifically for Raspberry Pi setups with a physical button and LED connected to GPIO pins (see script for default pins: Button=GPIO27, LED=GPIO17).
    *   Pressing the button starts/stops local recording.
    *   Holding the button triggers a shutdown.
    *   Does *not* connect to MQTT or the server.
    *   Uses `configs/config_client_manual.ini` by default.

### Running Manually

Ensure you are in the `multipi` directory and the virtual environment is activated (`source venv/bin/activate`). Choose the script corresponding to the desired mode:

*   **Standard Remote Control:**
    ```bash
    python3 src/client/main.py --config configs/config_client.ini
    ```
*   **Scheduled Recording:**
    ```bash
    # Make sure clock is synchronized!
    python3 src/client/main_auto.py --config configs/config_client_auto.ini
    ```
*   **Manual Button Control:**
    ```bash
    # Requires button/LED connected to GPIO
    python3 src/client/main_manual.py --config configs/config_client_manual.ini
    ```

### Automatically on Boot (Systemd Service)

Use the provided `systemd` service file for automatic startup. This is typically used for the **Standard Remote Control (`main.py`)** or **Scheduled Recording (`main_auto.py`)** modes.

1.  **Locate and Edit Service File:**
    The file is likely at `src/client/systemd-service/multipi-client.service` (verify this path).
    ```bash
    # Example path - VERIFY!
    SERVICE_FILE="$HOME/multipi/src/client/systemd-service/multipi-client.service"
    nano "${SERVICE_FILE}"
    ```
    **Crucially, edit the file** to set:
    *   `User`: The username the Pi runs as (e.g., `pi`).
    *   `WorkingDirectory`: The absolute path to the `multipi` directory (e.g., `/home/pi/multipi`).
    *   `ExecStart`: The absolute path to the `python3` executable **within the virtual environment** and the **correct script (`main.py` or `main_auto.py`)** with its **corresponding config file (`--config ...`)**. 
        *   Example `ExecStart` for standard mode:
            `ExecStart=/home/pi/multipi/venv/bin/python3 /home/pi/multipi/src/client/main.py --config /home/pi/multipi/configs/config_client.ini`
        *   Example `ExecStart` for auto mode:
            `ExecStart=/home/pi/multipi/venv/bin/python3 /home/pi/multipi/src/client/main_auto.py --config /home/pi/multipi/configs/config_client_auto.ini`
        *   Example `ExecStart` for manual mode:
            `ExecStart=/home/pi/multipi/venv/bin/python3 /home/pi/multipi/src/client/main_manual.py --config /home/pi/multipi/configs/config_client_manual.ini`

2.  **Copy, Enable, and Start:**
    ```bash
    sudo cp "${SERVICE_FILE}" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable multipi-client.service
    sudo systemctl start multipi-client.service
    ```

3.  **Check Status/Logs:**
    ```bash
    sudo systemctl status multipi-client.service
    sudo journalctl -f -u multipi-client.service # Follow logs
    ```

## 9. Fleet Management (Optional)

### Duplicating SD Cards

Once one Pi is fully configured, you can clone its SD card for others using `rpi-clone`. Install it following instructions from [its GitHub repository](https://github.com/framps/rpi-clone).

1.  Insert the target SD card into a USB reader connected to the configured Pi.
2.  Identify the target SD card device name:
    ```bash
    lsblk
    ```
3.  Clone and assign a new hostname:
    ```bash
    # Replace sdX with the target device (e.g., sda) and new_hostname
    sudo rpi-clone sdX -f -U # -f non interactive, -U update uuid
    # Mount the boot partition of the new SD card (e.g. /dev/sda1) 
    # Change the hostname in /etc/hostname on the new SD card 
    ```

### Keeping Pis Updated

The script `raspberry-pi-setup/update_rpi_remote.sh` can be used to update multiple Pis listed in a file.

1.  Create a file (e.g., `pi_list.txt`) with one hostname or IP per line.
2.  Ensure you have passwordless SSH configured to all target Pis.
3.  Run the script:
    ```bash
    # Assuming script is in scripts/ directory
    ./scripts/update_rpi_remote.sh pi_list.txt
    ```

