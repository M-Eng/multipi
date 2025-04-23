import time
import subprocess

import paho.mqtt.client as mqtt

from argparse import ArgumentParser
from pathlib import Path

from paho.mqtt.enums import CallbackAPIVersion

from client.camera_utils import start_stream, capture_image, end_stream
from client.camera_test import start_test_stream, capture_image_test

from common.mqtt_topics import REGISTER_TOPIC, COMMAND_TOPIC_PREFIX, GLOBAL_COMMAND_TOPIC, ACKNOWLEDGE_TOPIC_PREFIX, RESPONSE_TOPIC_PREFIX
from common.utils import read_config, get_next_file_path
from common.network_utils import get_hostname, get_ip_address, get_port_from_device_id, get_mac_address

from common.log_utils import set_log_level, log


def on_connect(client, userdata, flags, rc, properties):
    log.info(f"Connected with result code {rc}")
    ip_address = get_ip_address()
    max_address = get_mac_address()
    
    client.subscribe(COMMAND_TOPIC_PREFIX + DEVICE_ID)
    client.subscribe(GLOBAL_COMMAND_TOPIC)
    client.publish(REGISTER_TOPIC, f"{DEVICE_ID}|{ip_address}|{max_address}")
    

def on_disconnect(client, userdata, rc, properties):
    """
    Original function from https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
    """

    log.error(f"Disconnected with result code: {rc}")
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        log.info(f"Reconnecting in {reconnect_delay} seconds...")
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            log.info("Reconnected successfully!")
            ip_address = get_ip_address()
            client.publish(REGISTER_TOPIC, f"{DEVICE_ID}|{ip_address}")
            return
        except Exception as err:
            log.warning(f"{err}. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1

    log.error(f"Reconnect failed after {reconnect_count} attempts. Exiting...")


def on_message(client, userdata, msg):
    command = msg.payload.decode()
    global streaming_processes

    log.debug(f"Received command: {command}")
    log.debug(f"Topic: {msg.topic}")
    log.debug(f"Payload: {msg.payload}")
    
    if command == "START_STREAM":
        port = get_port_from_device_id(DEVICE_ID)
        log.debug(f"Starting to stream on port {port}")

        if TEST_MODE:
            streaming_processes = start_test_stream(STREAMMING_ADDRESS, port)
        else:
            streaming_processes = start_stream(STREAMMING_ADDRESS, port, FRAMERATE, BITRATE)

        # Acknowledge that the stream has started
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        client.publish(ACKNOWLEDGE_TOPIC_PREFIX + DEVICE_ID, f"STREAM_STARTED|{current_time}")

    if command == "START_RECORDING":
        
        start_rec()

        # Acknowledge that the stream has started
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        client.publish(ACKNOWLEDGE_TOPIC_PREFIX + DEVICE_ID, f"STREAM_STARTED|{current_time}")

    if command == "STOP_RECORDING":
        stop_rec()
    
    if command == "GET_PICTURE":
        if TEST_MODE:
            image_path = capture_image_test(DEVICE_ID)
        else:
            image_path = capture_image(DEVICE_ID)
        
        if image_path is None:
            log.error("Error capturing image")
            return
        
        log.debug(f"Image captured stored at {image_path}")

        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
            client.publish(RESPONSE_TOPIC_PREFIX + DEVICE_ID, image_data)

        Path(image_path).unlink()

    if command == "PING":
        client.publish(ACKNOWLEDGE_TOPIC_PREFIX + DEVICE_ID, "PING_ACK")

    if command == "SHUTDOWN":
        log.info("Shutting down...")
        client.publish(ACKNOWLEDGE_TOPIC_PREFIX + DEVICE_ID, "SHUTDOWN_ACK")
        client.disconnect()
        
        if TEST_MODE:
            exit(0)
        else:
            subprocess.call(["sudo", "shutdown", "-h", "now"])

    if command == "REBOOT":
        log.info("Rebooting...")

        client.disconnect()
        
        if TEST_MODE:
            exit(0)
        else:
            subprocess.call(["sudo", "shutdown", "-r", "now"])

def start_rec():
    global task_running

    if task_running is None:
        task_running = "starting"
        output_file_path = get_next_file_path(DATA_PATH, DEVICE_ID)

        # if parent dir contains more than 20GB of data don't start recording
        if sum(f.stat().st_size for f in Path(DATA_PATH).rglob('*') if f.is_file()) > 20 * 1024 * 1024 * 1024:
            log.error("Data folder is full, can't start recording")
            task_running = None
            return False
        

        picam2, timestamp_process = start_stream("", 0, FRAMERATE, BITRATE, file_output=output_file_path)
        task_running = (picam2, timestamp_process)

        log.info("Capture started")

        return True
        

def stop_rec():
    global task_running
    if task_running:
        picam2, timestamp_process = task_running

        end_stream(picam2, timestamp_process)
        task_running = None
        log.info("Capture stopped")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test", default=False, action="store_true")
    parser.add_argument("-d", "--device_id", type=str, default=None)
    parser.add_argument("-c", "--config", type=str, default="../configs/config_client.ini")
    parser.add_argument("-l", "--log_lvl", dest="log_lvl", default="debug", choices=["debug", "spam", "verbose", "info", "warning", "error"], help='Set level of logger to get more or less verbose output')

    args = parser.parse_args()

    config = read_config(args.config)
    BROKER_ADDRESS = config['MQTT']['BROKER_ADDRESS']
    BROKER_PORT = config['MQTT'].getint('BROKER_PORT')
    STREAMMING_ADDRESS = config['STREAM']['SERVER_ADDRESS']

    FIRST_RECONNECT_DELAY = config['MQTT']['FIRST_RECONNECT_DELAY']
    RECONNECT_RATE = config['MQTT']['RECONNECT_RATE']
    MAX_RECONNECT_COUNT = config['MQTT']['MAX_RECONNECT_COUNT']
    MAX_RECONNECT_DELAY = config['MQTT']['MAX_RECONNECT_DELAY']

    BITRATE = int(config['STREAM']['BITRATE'])
    FRAMERATE = int(config['STREAM']['FRAMERATE'])

    DATA_PATH = config["MAIN"]["DATA_PATH"]

    TEST_MODE = args.test

    if args.device_id is None:
        DEVICE_ID = get_hostname()
    else:
        DEVICE_ID = args.device_id

    task_running = None

    # if log_lvl is not set in config, use the one from the command line
    log_lvl = config["MAIN"]["LOG_LEVEL"] if "MAIN" in config and "LOG_LEVEL" in config["MAIN"] else args.log_lvl
    set_log_level(log_lvl)

    log.debug("Starting client with the following parameters:")
    log.debug(f"Broker address: {BROKER_ADDRESS}")
    log.debug(f"Device ID: {DEVICE_ID}")
    log.debug(f"Test mode: {TEST_MODE}")

    log.spam(f"First reconnect delay: {FIRST_RECONNECT_DELAY}")
    log.spam(f"Reconnect rate: {RECONNECT_RATE}")
    log.spam(f"Max reconnect count: {MAX_RECONNECT_COUNT}")
    log.spam(f"Max reconnect delay: {MAX_RECONNECT_DELAY}")

    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    
    if 'CLIENT_CERT' in config['MQTT']:
        client.tls_set(config['MQTT']['CA_CERT'], config['MQTT']['CLIENT_CERT'], config['MQTT']['CLIENT_KEY'])

    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(BROKER_ADDRESS, BROKER_PORT, 60)
    client.loop_forever()


