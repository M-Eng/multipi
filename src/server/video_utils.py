import datetime
import subprocess
import time
import threading

from pathlib import Path

from common.network_utils import TextTCP
from common.network_utils import get_port_from_device_id
from common.log_utils import log

FFMPEG_LOCK = threading.Lock()

def read_and_save_stream(pi_id, video_data_dir):
    port = get_port_from_device_id(pi_id)

    log.debug(f"Starting stream on port {port} for device {pi_id} ...")

    # Create a directory for the device if it doesn't exist
    base_dir = Path(video_data_dir)
    device_dir = base_dir / pi_id.replace(':', '-')
    device_dir.mkdir(parents=True, exist_ok=True)

    current_timestamp = datetime.datetime.now()
    file_suffix = current_timestamp.strftime('%Y%m%d_%H%M%S')

    # Check for existing files and decide on a new filename
    filename = str(device_dir / f"video_{device_dir.name}_{file_suffix}.mp4")    

    stream_path = Path(f"./server/static/temp_streams/{pi_id}/live_stream_{file_suffix}.m3u8")
    stream_path.parent.mkdir(parents=True, exist_ok=True)
    # empty parent directory
    for file in stream_path.parent.glob("*"):
            file.unlink()

    stream_path = str(stream_path)

    cmd = [
        'ffmpeg',
        '-i', f'tcp://0.0.0.0:{port}?listen',
        "-c:v", "copy",
        "-f", "mp4",
        "-movflags", "frag_keyframe+empty_moov",
        "-metadata", f"creation_time={current_timestamp.strftime('%Y-%m-%dT%H:%M:%S')}",
        filename,
        '-c', 'copy',
        '-f', 'hls',
        '-hls_time', '2',
        '-hls_list_size', '10',
        '-hls_flags', 'delete_segments+append_list+program_date_time',
        stream_path
    ]

    with FFMPEG_LOCK:
        process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.debug(f"Stream started, saving video to {filename}")

    return process, filename, stream_path

def read_and_save_timestamp(pi_id, filename):
    from multiprocessing import Process

    port = get_port_from_device_id(pi_id) + 1
    timestamp_file = Path(filename.replace(".mp4", ".txt"))
    timestamp_file.touch()

    def timestamp_receiving_process():
        tcp_srv = TextTCP(port, server=True)

        with timestamp_file.open(mode="a") as f:
            while True:
                timestamp = tcp_srv.recv()

                if timestamp is None:
                    log.error("Timestamp receiving process terminated")
                    break

                f.write(timestamp)
                f.flush()

        
    process = Process(target=timestamp_receiving_process)
    process.start()

    log.debug(f"Timestamp receiving process started on port {port}, saving timestamps to {timestamp_file}")

    return process


def extract_last_frame_from_video(filepath, device_id, output_image_path=None):
    # Check if video file exists
    if not Path(filepath).exists():
        log.error("Video file does not exist")
        return None
    
    # Define the folder to store the temporary images
    image_folder = Path("./server/static/temp_images")
    image_folder.mkdir(parents=True, exist_ok=True)
    
    if output_image_path is None:
        # Generate the image filename based on the device and timestamp
        timestamp = time.strftime("%Y%m%d%H%M%S")
        output_image_path = image_folder / f"{device_id.replace(':', '-')}_{timestamp}.jpg"
    
    command = ["ffmpeg", "-sseof", "-3", "-i", str(filepath), "-update", "1", "-q:v", "1", str(output_image_path), "-movflags", "frag_keyframe+separate_moof+omit_tfhd_offset+empty_moov", "-y"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    log.debug(f"Extracting last frame from {filepath}, saving it to {output_image_path}")

    if process.returncode != 0:
        log.error(f"Failed to extract last frame, ffmpeg error: {stderr.decode('utf-8')}")
        return None

    return str(output_image_path)