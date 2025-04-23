import configparser
import datetime
import hashlib
import threading

from pathlib import Path

def read_config(config_filepath):
    config = configparser.ConfigParser()
    config.read(config_filepath)
    return config

def string_to_4_digit_int(input_string):
    # Convert the string to bytes
    input_bytes = input_string.encode()
    # Create an MD5 hash of the string
    hash_object = hashlib.md5(input_bytes)
    # Get the hex representation of the hash
    hex_hash = hash_object.hexdigest()
    four_digit_int = int(hex_hash[:4], 16) % 10000

    return four_digit_int


def add_callback_when_process_terminate(onExit, proc, **kwargs):

    def runInThread(onExit, proc, kwargs):
        proc.wait()
        onExit(**kwargs)
        return

    thread = threading.Thread(target=runInThread, args=(onExit, proc, kwargs))
    thread.start()

    return thread

def get_next_file_path(data_path, device_id):
    """
    Get the next file path in the data path
    """
    current_timestamp = datetime.datetime.now()
    file_suffix = current_timestamp.strftime('%Y%m%d_%H%M%S')

    file_path = Path(data_path) / f"{device_id}_{file_suffix}"
    return file_path