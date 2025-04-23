import time
import subprocess

from pathlib import Path
from picamera2 import Picamera2, MappedArray
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput, FileOutput
from libcamera import controls

from common.log_utils import log
from common.network_utils import TextTCP
from common.utils import add_callback_when_process_terminate

picam2 = Picamera2()

def start_timestamp_process(ip_address, port, file_output=None):
    from multiprocessing import Process, Queue

    timestamp_queue = Queue()

    def timestamp_sending_process(port, timestamp_queue):
        if file_output:
            file_output.parent.mkdir(parents=True, exist_ok=True)
            log.debug(f"Starting timestamp process towards {file_output}")
        else:
            log.debug(f"Starting timestamp process towards {ip_address}:{port}")
            tcp_conn = TextTCP(port, ip_address)

        while True: # and tcp_conn.is_open():

            timestamp_tuple = timestamp_queue.get()
            # local_timestamp in nanoseconds (ns)
            local_timestamp = timestamp_tuple[0]
            # pseudo_kernel_timestamp converted to miliseconds (ms)
            pseudo_kernel_timestamp = timestamp_tuple[1] / 1000

            msg = f"{local_timestamp}, {pseudo_kernel_timestamp} \n"

            if file_output:
                with open(str(file_output) + ".txt", "a") as file:
                    file.write(msg)
            else:
                try:
                    tcp_conn.send(msg)
                except:
                    log.error("Error with tcp connection, terminating timestamp process")
                    break

    process = Process(target=timestamp_sending_process, args=(port, timestamp_queue))
    process.start()

    return process, timestamp_queue


def start_stream(ip_address, port, framerate=30, bitrate=10000000, file_output=None):

    timestamp_process, timestamp_queue = start_timestamp_process(ip_address, port+1, file_output)
    log.debug("Timestamp process started")
        
    # picam2 = Picamera2()
    
    config = picam2.create_video_configuration(
        main={"size": (1920, 1080)}, 
        controls={
            "AfMode": controls.AfModeEnum.Manual, 
            "LensPosition": 0.0, 
            "FrameRate": framerate,
            # "ExposureTime": int(1000000 / framerate - 1000),
            #"FrameDurationLimits": (int(33333/2), int(33333/2))
            }
        )
    
    log.debug(f"Camera configuration: {config}")
    picam2.configure(config)                                       
   
    encoder = H264Encoder(bitrate=bitrate, repeat=True, iperiod=15)

    if file_output:
        file_output.parent.mkdir(parents=True, exist_ok=True)
        file_output = str(file_output) + ".h264"
        output = FileOutput(file_output)
        log.debug(f"Write output: {file_output}")
    else:
        output = FfmpegOutput(f"-f mpegts tcp://{ip_address}:{port}")
        log.debug(f"Stream output: ffmpeg -f mpegts tcp://{ip_address}:{port}")

    def apply_timestamp(request):
        timestamp = time.time_ns()

        if encoder.firsttimestamp is None:
            timestamp_queue.put((timestamp, -1000))
        else:
            timestamp_queue.put((timestamp, request.get_metadata()['SensorTimestamp'] / 1000 - encoder.firsttimestamp))

    picam2.pre_callback = apply_timestamp


    picam2.start_encoder(encoder, output)

    if not file_output:
        add_callback_when_process_terminate(end_stream, output.ffmpeg, camera=picam2, timestamp_process=timestamp_process)

    picam2.start()
    log.info(f"Video and timestamp stream started on port {port} and {port+1}")

    return picam2, timestamp_process


def end_stream(camera, timestamp_process):
    
    log.info("Stopping stream...")
    camera.stop()
    camera.stop_encoder()
    # camera.close()

    time.sleep(0.5)

    timestamp_process.terminate()

    log.info("Stream stopped")

    return True

# def capture_image(device_id):
#     timestamp = int(time.time())
#     image_folder = Path("./client/images/")
#     image_folder.mkdir(parents=True, exist_ok=True)
#     image_name = f"{device_id}_{timestamp}.jpg"
#     image_path = image_folder / image_name

#     # Capture the image using libcamera-still
#     command = ["libcamera-still",
#                "-o", f"{str(image_path)}",
#                "--tuning-file", "/usr/share/libcamera/ipa/rpi/vc4/imx708_wide.json",
#                "--width", "1920",
#                "--height", "1080",
#                "--autofocus-mode", "manual",
#                "--lens-position", "0",
#                ]
    
#     capture_proc = subprocess.Popen(command)
#     capture_proc.wait()

#     log.info(f"Image captured stored at {image_path}")

#     return str(image_path)


def capture_image(device_id):
    # Initialize Picamera2
    # try:        
        # Generate and apply camera configuration
        camera_config = picam2.create_still_configuration(
            main={"size": (1920, 1080)},
            controls={"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.0}
        )
        
        picam2.configure(camera_config)
        
        # Start camera
        picam2.start()

        # Define image storage path
        timestamp = int(time.time())
        image_folder = Path("./client/images/")
        image_folder.mkdir(parents=True, exist_ok=True)
        image_name = f"{device_id}_{timestamp}.jpg"
        image_path = image_folder / image_name

        # Capture and save the image
        picam2.capture_file(str(image_path))
        picam2.stop()  # Stop the camera after capturing
        # picam2.close()  # Close the camera after stopping
        
        print(f"Image captured stored at {image_path}")

        return str(image_path)
    
    # except RuntimeError as e:
    #     print(f"Failed to initialize camera: {e}")
    # finally:
    #     picam2.stop() if 'picam2' in locals() else None

    # return None
