
from pathlib import Path


def days_hours_minutes(td):
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{days}d {hours}:{minutes}:{seconds}"


def convert_bytes(total_size):
        # convert to largest unit and round to 2 decimal places and conert to string with unit
    if total_size > 1000000000:
        total_size = str(round(total_size/1000000000, 2)) + " GB"
    elif total_size > 1000000:
        total_size = str(round(total_size/1000000, 2)) + " MB"
    elif total_size > 1000:
        total_size = str(round(total_size/1000, 2)) + " KB"
    else:
        total_size = str(round(total_size, 2)) + " B"

    return total_size

def convert_string_to_bytes(total_size):
    # convert to largest unit and round to 2 decimal places and conert to string with unit
    if total_size[-2:] == "GB":
        total_size = float(total_size[:-2]) * 1000000000
    elif total_size[-2:] == "MB":
        total_size = float(total_size[:-2]) * 1000000
    elif total_size[-2:] == "KB":
        total_size = float(total_size[:-2]) * 1000
    else:
        total_size = float(total_size[:-2])

    return total_size

def get_dir_size(dir_path):
    # Check if dir_path is a Path object
    if not isinstance(dir_path, Path):
        dir_path = Path(dir_path)

    total_size = 0
    for path in dir_path.glob('**/*'):
        if path.is_file():
            total_size += path.stat().st_size

    return total_size


