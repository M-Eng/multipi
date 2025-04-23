import socket
import subprocess
import uuid

from common.utils import string_to_4_digit_int
from common.log_utils import log


def get_mac_address(interface="wlan0"):
    try:
        # The path to the interface's MAC address information
        mac_address_path = f'/sys/class/net/{interface}/address'
        
        # Reading the MAC address for the specified interface
        mac_address = subprocess.check_output(['cat', mac_address_path]).decode().strip()
        return mac_address
    except Exception as e:
        # If an error occurs, print the error
        print(f"Error getting MAC address for {interface}: {e}")
        return None


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_address = s.getsockname()[0]
    s.close()
    return ip_address

def get_port_from_device_id(device_id, port_shift=56000):
    device_uid = string_to_4_digit_int(device_id)
    port = (device_uid % 1000) + port_shift

    log.spam(f"Generated port {port} from device_id {device_id} and device_uid {device_uid}")
    
    return port

def get_hostname():
    return socket.gethostname()


class TextTCP:
    def __init__(self, port, ip="", server=False):
        self.port = port
        self.ip = ip

        log.debug(f"Creating TextTCP object with port {port} and ip {ip}")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if server:
            self._init_server()
        else:
            self._init_client()

    def _init_server(self):
        self.socket.bind(("", self.port))
        self.socket.listen(1)
        self.conn = None

        self.wait_for_connection()

    def _init_client(self):
        self.socket.connect((self.ip, self.port))
        self.conn = self.socket

    def wait_for_connection(self):
        self.conn, self.addr = self.socket.accept()
        return True

    def send(self, data):
        if self.conn is None:
            log.error("No connection established")
            return False
        
        try:
            ret = self.conn.send(data.encode())
        except BrokenPipeError:
            log.error("Socket connection broken")
            self.socket.close()
            raise RuntimeError("Socket connection broken")

        return True
    
    
    def recv(self, buffer_size=1024):
        if self.conn is None:
            log.error("No connection established")
            return False
        
        data = self.conn.recv(buffer_size)

        if data == b'':
            raise RuntimeError("Socket connection broken")

        return data.decode()
   
    def is_open(self):
        return self.socket._closed == False
    
    def close(self):
        self.socket.close()
        return True