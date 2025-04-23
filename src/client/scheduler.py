import configparser
from datetime import time as dt_time

# Read and parse time windows from config
def read_time_windows(config, section="TIME_WINDOWS"):
    time_windows = []
    for key, value in config.items(section):
        start_str, end_str = value.split('-')
        start = dt_time.fromisoformat(start_str)
        end = dt_time.fromisoformat(end_str)
        time_windows.append((start, end))
    return time_windows