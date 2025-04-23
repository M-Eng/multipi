import sys

print(sys.path)

import datetime
import time
import threading
import subprocess

from argparse import ArgumentParser
from gpiozero import LED, Button
from pathlib import Path
from signal import pause

from client.camera_utils import start_stream, end_stream

from common.utils import read_config
from common.network_utils import get_hostname

from common.log_utils import set_log_level, log


def get_next_file_path():
    """
    Get the next file path in the data path
    """
    current_timestamp = datetime.datetime.now()
    file_suffix = current_timestamp.strftime('%Y%m%d_%H%M%S')

    file_path = Path(DATA_PATH) / f"{DEVICE_ID}_{file_suffix}"
    return file_path

def start_task():
    global task_running

    if task_running is None:
        led.blink(on_time=1.5, off_time=3)
        task_running = "starting"
        output_file_path = get_next_file_path()
        picam2, timestamp_process = start_stream("", 0, FRAMERATE, BITRATE, file_output=output_file_path)
        task_running = (picam2, timestamp_process)

        log.info("Capture started")
        

def stop_task():
    global task_running
    if task_running:
        picam2, timestamp_process = task_running

        end_stream(picam2, timestamp_process)
        task_running = None
        led.on()  # Ensure LED is on after the task stops
        log.info("Capture stopped")
        led.on()

def shutdown_pi():
    led.off()  # Turn off the LED before shutting down
    log.info("Shutting down...")
    
    if task_running:
        stop_task()
        
    if TEST_MODE:
        exit(0)
    else:
        subprocess.call(["sudo", "shutdown", "-h", "now"])


def on_button_released():
    print("Button released")

    if task_running:
        stop_task()
    else:
        start_task()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test", default=False, action="store_true")
    parser.add_argument("-d", "--device_id", type=str, default=None)
    parser.add_argument("-c", "--config", type=str, default="../configs/config_client_manual.ini")
    parser.add_argument("-l", "--log_lvl", dest="log_lvl", default="debug", choices=["debug", "spam", "verbose", "info", "warning", "error"], help='Set level of logger to get more or less verbose output')

    args = parser.parse_args()

    config = read_config(args.config)

    DATA_PATH = config["MAIN"]["DATA_PATH"]

    TEST_MODE = args.test

    BITRATE = int(config['STREAM']['BITRATE'])
    FRAMERATE = int(config['STREAM']['FRAMERATE'])

    if args.device_id is None:
        DEVICE_ID = get_hostname()
    else:
        DEVICE_ID = args.device_id

    # if log_lvl is not set in config, use the one from the command line
    log_lvl = config["MAIN"]["LOG_LEVEL"] if "MAIN" in config and "LOG_LEVEL" in config["MAIN"] else args.log_lvl
    set_log_level(log_lvl)


    # Initialize the LED and button with the appropriate GPIO pins
    led = LED(17)  # Change 17 to the GPIO pin you've connected the LED to
    button = Button(27, hold_time=5)  # Change 27 to the GPIO pin you've connected the button to

    if button.is_pressed:
        # import main.py and run that function
        led.blink(on_time=0.2, off_time=0.1, n=6)
        # "/usr/bin/python -m client.main"
        subprocess.call(["/usr/bin/python", "-m", "client.main"])
        exit(0)

    task_running = None

    # button.when_pressed = on_button_pressed
    button.when_released = on_button_released
    button.when_held = shutdown_pi

    led.on()  # Turn on the LED when the Pi is running

    pause()  # Wait for button presses

