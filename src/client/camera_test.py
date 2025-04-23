import time
import subprocess

from pathlib import Path

from client.camera_utils import start_timestamp_process
from common.log_utils import log
from common.utils import add_callback_when_process_terminate

def start_test_stream(ip_address, port):
    from multiprocessing import Process

    log.debug(f"Starting to stream to {ip_address}:{port}")

    timestamp_process, timestamp_queue = start_timestamp_process(ip_address, port+1)
    log.debug("Timestamp process started")
        

    def create_timestamps():
        total = 0
        while True:
            timestamp = time.time_ns()
            timestamp_queue.put((timestamp, total))
            total += timestamp / 1e9

            time.sleep(1/30)

    gen_timestamp_process = Process(target=create_timestamps)
    

    # cmd = [
    #     "ffmpeg",
    #     "-f", "lavfi",
    #     "-re",  # Read input at native frame rate
    #     "-i", "testsrc2=size=1920x1080:rate=30",  # Generate test video
    #     # "-c:v", "h264",  # Specify the H.264 video codec
    #     # "-preset", "fast",  # Optional: specify an encoding speed/quality trade-off. Others include slower, medium, fast, etc.
    #     # "-tune", "zerolatency",  # Optional: good for fast encoding and low-latency streaming
    #     "-f", "h264",  # Use FLV as the container format, which is common for H.264 streaming
    #     f"tcp://{ip_address}:{port}",  # Output location with TCP listening
    # ]

    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-re',
        '-i', 'testsrc=size=1920x1080:rate=30',
        '-c:v', 'libopenh264',
        '-g', '30',
        '-force_key_frames', 'expr:gte(t,n_forced*2)',
        '-copyts',
        '-muxdelay', '0',
        '-f', 'mpegts',
        f"tcp://{ip_address}:{port}",  # Output location with TCP listening
    ]


    process = subprocess.Popen(cmd)
    gen_timestamp_process.start()

    add_callback_when_process_terminate(end_test_stream, process, timestamp_process=timestamp_process, gen_timestamp_process=gen_timestamp_process)

    
    log.info(f"Test Video and timestamp stream started on port {port} and {port+1}")

    return process, timestamp_process, gen_timestamp_process


def end_test_stream(timestamp_process, gen_timestamp_process):
    
    log.info("Stopping stream...")
    gen_timestamp_process.terminate()
    timestamp_process.terminate()

    log.info("Stream stopped")

    return True


def capture_image_test(device_id):
    timestamp = int(time.time())
    image_folder = Path("./client/images/")
    image_folder.mkdir(parents=True, exist_ok=True)
    image_name = f"{device_id}_{timestamp}.jpg"
    image_path = image_folder / image_name

    command = ["ffmpeg",
                "-f", "lavfi",
                "-i", "testsrc=size=1920x1080:rate=1",
                "-vf", f"drawtext=fontfile=/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf:text='{timestamp}':fontsize=200:fontcolor=white:x=(w-tw)/2:y=(h-th)/2",
                "-vframes", "1",
                f"{str(image_path)}",
                ]

    capture_proc = subprocess.Popen(command)
    capture_proc.wait()

    log.info(f"Test image captured stored at {image_path}")

    return str(image_path)