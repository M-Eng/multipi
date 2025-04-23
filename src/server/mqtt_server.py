import datetime
import time
from pathlib import Path
from threading import Event, Thread

from flask import jsonify
from paho.mqtt.client import Client
from paho.mqtt.enums import CallbackAPIVersion

from common.log_utils import log
from common.mqtt_topics import (
    ACKNOWLEDGE_TOPIC_PREFIX, COMMAND_TOPIC_PREFIX, GLOBAL_COMMAND_TOPIC, 
    REGISTER_TOPIC, RESPONSE_TOPIC_PREFIX
    )
from common.utils import add_callback_when_process_terminate
from server.utils import convert_bytes, days_hours_minutes, get_dir_size
from server.video_utils import (
    extract_last_frame_from_video, read_and_save_stream, read_and_save_timestamp
    )


class MQTT_Central_Client():
    def __init__(self, mqtt_config, socketio, video_data_dir):
        global ACKNOWLEDGE_TIMEOUT

        self.socketio = socketio
        self.video_data_dir = video_data_dir

        self.last_frame_path_template = "./server/static/temp_images/{device_id}_{timestamp}.jpg"

        self.active_pis = {}
        self.event_pis = {}
        self.ffmpeg_processes = {}

        self.init_client(mqtt_config)

        ACKNOWLEDGE_TIMEOUT = float(mqtt_config["ACKNOWLEDGE_TIMEOUT"])

    def init_client(self, mqtt_config):
        """ 
        Initialize the MQTT client and connect to the broker.
        """

        log.info(f"MQTT client with the following parameters:")
        log.info(f"Broker address: {mqtt_config['BROKER_ADDRESS']}")
        log.info(f"Broker port: {mqtt_config.getint('BROKER_PORT')}")
        log.debug(f"CA certificate: {mqtt_config['CA_CERT']}")
        log.debug(f"Client certificate: {mqtt_config['CLIENT_CERT']}")
        log.debug(f"Client key: {mqtt_config['CLIENT_KEY']}")
        
        self.mqtt_client = Client(CallbackAPIVersion.VERSION2)
        
        if 'CLIENT_CERT' in mqtt_config:
            self.mqtt_client.tls_set(mqtt_config['CA_CERT'], mqtt_config['CLIENT_CERT'], mqtt_config['CLIENT_KEY'])

        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_connect = self.on_connect
        
        self.mqtt_client.connect(mqtt_config["BROKER_ADDRESS"], mqtt_config.getint("BROKER_PORT"), 60)
        self.mqtt_client.loop_start()

    
    def on_connect(self, client, userdata, flags, rc, properties):
            if rc == 0:
                log.info("Connection to MQTT broker successful")
            else:
                log.error(f"Connection to MQTT broker failed with return code: {rc}")

            self.mqtt_client.subscribe(REGISTER_TOPIC)
    

    def on_message(self, client, userdata, msg):
        topic = msg.topic

        log.debug(f"Received message on topic - {topic}")
        
        if topic == REGISTER_TOPIC:
            payload = msg.payload.decode()
            device_id, ip_address, mac_address = payload.split('|')
            self.register_device(device_id, ip_address, mac_address)
            
        
        if ACKNOWLEDGE_TOPIC_PREFIX in topic:
            payload = msg.payload.decode()
            device_id = topic.split('/')[-1]
            self.ack_received(payload, device_id)


        if RESPONSE_TOPIC_PREFIX in topic:
            device_id = topic.split('/')[-1]
            self.img_received(msg.payload, device_id)


    def register_device(self, device_id, ip_address, mac_address):
        if device_id in self.active_pis:
            # self.socketio.emit('new_device', self.active_pis[device_id])
            log.info(f"Reconnection of {device_id} with IP: {ip_address} and mac: {mac_address}")
            self.active_pis[device_id]['status'] = 'online'
            self.active_pis[device_id]['ip_address'] = ip_address

            if self.active_pis[device_id]['streaming'] and self.ffmpeg_processes[device_id] is None:
                log.warning(f"Device {device_id} was streaming but the ffmpeg process was not running. Restarting stream.")
                Thread(target=self.start_stream, args=(device_id,)).start()
            else:
                self.emit_pi_status_update(device_id, emit_event='pi_status_update')           
        
        if device_id not in self.active_pis:
            self.active_pis[device_id]  ={
                'id': device_id,
                'status': 'online',
                'ip_address': ip_address,
                'mac_address': mac_address,
                'stream_start_time': None,
                'stream_end_time': None,
                'stream_duration': None,
                'stream_file_size': None,
                'last_video_path': None,
                'hls_stream_path': None,
                'last_frame_path': None,
                'streaming': False,
                }

            self.ffmpeg_processes[device_id] = None

            self.event_pis[device_id] = {
                'waiting_for_ack': False,
                'ack_event': Event(),
                'waiting_for_ping': False,
                'ping_event': Event(),
            }

            log.info(f"Registered device: {device_id} with IP: {ip_address} and mac: {mac_address}")

            self.mqtt_client.subscribe(ACKNOWLEDGE_TOPIC_PREFIX + device_id)
            self.mqtt_client.subscribe(RESPONSE_TOPIC_PREFIX + device_id)  

            self.update_stream_info(device_id)

            self.emit_pi_status_update(device_id, emit_event='new_device')
            
            log.debug(f"Emitted new_device update on the web socket from on_message.")


    def ack_received(self, payload, device_id):
        if "STREAM_STARTED" in payload:
            log.debug(f"Received stream started acknowledgment from {device_id} with payload: {payload}")

            _, start_time = payload.split('|')
            self.active_pis[device_id]['stream_start_time'] = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').strftime('%m-%d %H:%M:%S')
            self.event_pis[device_id]['ack_event'].set()
            
        if "PING_ACK" in payload:
            log.spam(f"Received ping acknowledgment from {device_id} with payload: {payload}")
            self.event_pis[device_id]['ping_event'].set()


    def img_received(self, payload, device_id):
        timestamp = int(time.time())
        img_path = Path(self.last_frame_path_template.format(device_id=device_id, timestamp=timestamp))
        img_path.parent.mkdir(parents=True, exist_ok=True)

        if self.active_pis[device_id]['last_frame_path'] is not None:
            ("server" / Path(self.active_pis[device_id]['last_frame_path'])).unlink()
        
        self.active_pis[device_id]['last_frame_path'] = str(img_path).replace('server/', '')

        with open(img_path, 'wb') as image_file:
            image_file.write(payload)

        log.debug(f"Image received from {device_id} stored at {img_path}")

        self.emit_pi_status_update(device_id)
    

    def start_stream(self, pi_id):

        # Start tcp servers to receive video and timestamp stream
        process, video_path, hls_stream_path = read_and_save_stream(pi_id, self.video_data_dir)
        process_timestamp = read_and_save_timestamp(pi_id, video_path)

        # Wait for the tcp servers to start
        time.sleep(0.1)

        # Check status of ack_event for this device
        if self.event_pis[pi_id]['waiting_for_ack']:
            log.error(f"Already waiting for acknowledgment from Raspberry Pi, failed to start stream from {pi_id}")
            return False, "Already waiting for acknowledgment from Raspberry Pi"
        
        # Set the event and flag to wait for the acknowledgment
        self.event_pis[pi_id]['waiting_for_ack'] = True
        self.event_pis[pi_id]['ack_event'].clear()

        # Inform the Raspberry Pi to start its stream
        self.mqtt_client.publish(COMMAND_TOPIC_PREFIX + pi_id, "START_STREAM")

        # Wait for the acknowledgment to be set (with a timeout)
        ack_received = self.event_pis[pi_id]['ack_event'].wait(timeout=ACKNOWLEDGE_TIMEOUT)  # wait for up to 10 seconds

        self.event_pis[pi_id]['waiting_for_ack'] = False

        if not ack_received:
            log.error(f"No acknowledgment received from Raspberry Pi, failed to start stream from {pi_id}")
            process.terminate()
            process_timestamp.terminate()

            return False, "No acknowledgment received from Raspberry Pi"

        # Add a callback to restart the stream if it ends
        add_callback_when_process_terminate(self.end_stream_callback, process, pi_id=pi_id)

        self.active_pis[pi_id]['last_video_path'] = video_path
        self.ffmpeg_processes[pi_id] = (process, process_timestamp)
        self.active_pis[pi_id]['streaming'] = True

        Thread(target=self.wait_for_stream_file, args=(pi_id, hls_stream_path)).start()

        self.emit_pi_status_update(pi_id)

        log.info(f"Succesfully started stream from {pi_id}")
        log.debug(f"Saving video to {video_path} and hls stream to {hls_stream_path}")

        return True, "success"
    

    def stop_stream(self, pi_id):
        if self.active_pis[pi_id]['streaming']:
            log.info(f"Stopping stream from {pi_id}")
     
            self.active_pis[pi_id]['streaming'] = False
            self.active_pis[pi_id]['hls_stream_path'] = None
            self.ffmpeg_processes[pi_id][0].terminate()
            self.ffmpeg_processes[pi_id][1].terminate()
            self.ffmpeg_processes[pi_id] = None

            end_time = datetime.datetime.strptime(datetime.datetime.now().strftime('%m-%d %H:%M:%S'), '%m-%d %H:%M:%S')
            duration = end_time - datetime.datetime.strptime(self.active_pis[pi_id]['stream_start_time'], '%m-%d %H:%M:%S')
            duration = days_hours_minutes(duration)

            self.active_pis[pi_id]['stream_end_time'] = end_time.strftime('%m-%d %H:%M:%S')
            self.active_pis[pi_id]['stream_duration'] = duration

            self.emit_pi_status_update(pi_id)
            
            log.info(f"Stream from {pi_id} stopped correctly")

            return jsonify(success=True), 200        
        else:
            return jsonify(sucess=False,  error=f"No active recording found for {pi_id}"), 200
        
    def start_rec(self, pi_id):
        # Check status of ack_event for this device
        if self.event_pis[pi_id]['waiting_for_ack']:
            log.error(f"Already waiting for acknowledgment from Raspberry Pi, failed to start stream from {pi_id}")
            return False, "Already waiting for acknowledgment from Raspberry Pi"
        
               # Set the event and flag to wait for the acknowledgment
        self.event_pis[pi_id]['waiting_for_ack'] = True
        self.event_pis[pi_id]['ack_event'].clear()

        # Inform the Raspberry Pi to start its stream
        self.mqtt_client.publish(COMMAND_TOPIC_PREFIX + pi_id, "START_RECORDING")

        # Wait for the acknowledgment to be set (with a timeout)
        ack_received = self.event_pis[pi_id]['ack_event'].wait(timeout=ACKNOWLEDGE_TIMEOUT)  # wait for up to 10 seconds

        self.event_pis[pi_id]['waiting_for_ack'] = False

        if not ack_received:
            log.error(f"No acknowledgment received from Raspberry Pi, failed to start stream from {pi_id}")

            return False, "No acknowledgment received from Raspberry Pi"

        self.active_pis[pi_id]['streaming'] = True
        self.emit_pi_status_update(pi_id)

        log.info(f"Succesfully started recording on {pi_id}")

        return True, "success"
    
    def stop_rec(self, pi_id):
        if self.active_pis[pi_id]['streaming']:
            self.mqtt_client.publish(COMMAND_TOPIC_PREFIX + pi_id, "STOP_RECORDING")
            self.active_pis[pi_id]['streaming'] = False

            self.emit_pi_status_update(pi_id)
            
            log.info(f"Stoped recording on {pi_id}")

            return jsonify(success=True), 200        
        else:
            return jsonify(sucess=False,  error=f"No active recording found for {pi_id}"), 200
    
    def get_picture_from_stream(self, device_id):
        timestamp = int(time.time())
        img_path = Path(self.last_frame_path_template.format(device_id=device_id, timestamp=timestamp))
        last_frame = extract_last_frame_from_video(self.active_pis[device_id]['last_video_path'], device_id, img_path)
        
        if self.active_pis[device_id]['last_frame_path'] is not None:
            ("server" / Path(self.active_pis[device_id]['last_frame_path'])).unlink()
            
        self.active_pis[device_id]['last_frame_path'] = last_frame.replace('server/', '')
        self.update_stream_info(device_id)
        self.emit_pi_status_update(device_id)


    def get_picture(self, device_id):
        # If the Raspberry Pi is streaming, read the last frame from the file.
        # Otherwise, send a request to the Raspberry Pi for a picture.
        if self.active_pis[device_id]['streaming']:
            log.debug(f"Device {device_id} is streaming. Reading last frame from file {self.active_pis[device_id]['last_video_path']}")            
            Thread(target=self.get_picture_from_stream, args=(device_id,)).start()

            return jsonify(success=True), 200
        else:
            log.debug(f"Requesting picture from device {device_id}")
            self.mqtt_client.publish(COMMAND_TOPIC_PREFIX + device_id, "GET_PICTURE")

            return jsonify(success=True), 200
        

    def wait_for_stream_file(self, device_id, hls_stream_path):
        hls_stream_path = Path(hls_stream_path)

        count = 0

        print("waiting for stream file")
        print(hls_stream_path)
        while True:
            if count == ACKNOWLEDGE_TIMEOUT * 4:
                log.warning(f"Stream file not found for {device_id} after {ACKNOWLEDGE_TIMEOUT} seconds. Stream will not be available.")
                return 
            
            if len(list(hls_stream_path.parent.glob('*'))) > 1:
                print("found stream file", count)
                break

            count += 1
            time.sleep(1)

        self.active_pis[device_id]['hls_stream_path'] = str(hls_stream_path).replace('server/', '')
        self.update_stream_info(device_id)
        self.emit_pi_status_update(device_id)


    def is_device_alive(self, pi_id):

        if self.event_pis[pi_id]['waiting_for_ping']:
            counter = 0            
            while self.event_pis[pi_id]['waiting_for_ping']:
                log.warning(f"Waiting for previous ping to finish before sending another one. {counter}/{ACKNOWLEDGE_TIMEOUT}")
                time.sleep(1)
                counter += 1

                if counter > ACKNOWLEDGE_TIMEOUT:
                    log.error("Previous ping did not finish in time.")
                    return False
        
        self.event_pis[pi_id]['waiting_for_ping'] = True
        self.event_pis[pi_id]['ping_event'].clear()

        # Send a ping to the device
        self.mqtt_client.publish(COMMAND_TOPIC_PREFIX + pi_id, "PING")

        #wait for the response
        ack_received = self.event_pis[pi_id]['ping_event'].wait(timeout=1)  
        self.event_pis[pi_id]['waiting_for_ping'] = False
        self.active_pis[pi_id]['status'] = 'online' if ack_received else 'offline'

        self.update_stream_info(pi_id)
        self.emit_pi_status_update(pi_id)
            
        return ack_received

        
    def end_stream_callback(self, pi_id):
        log.debug(f"End stream callback called for {pi_id}")

        if not self.active_pis[pi_id]["streaming"]:
            log.debug(f"Stream from {pi_id} already stopped.")
            return 

        # Check pi status
        if self.is_device_alive(pi_id):
            log.warning(f"Device {pi_id} is alive. Restarting stream.")
            #Cleanup 
            self.active_pis[pi_id]['streaming'] = False
            self.ffmpeg_processes[pi_id] = None
            # Restart the stream
            self.start_stream(pi_id)
        else:
            log.warning(f"Device {pi_id} is not responding. Stream cannot be restarted.")
            self.active_pis[pi_id]['streaming'] = True
            self.ffmpeg_processes[pi_id] = None


    def update_stream_info(self, pi_id):
        if self.active_pis[pi_id]['streaming']:
            self.active_pis[pi_id]['stream_duration'] = days_hours_minutes(datetime.datetime.strptime(datetime.datetime.now().strftime('%m-%d %H:%M:%S'), '%m-%d %H:%M:%S') - datetime.datetime.strptime(self.active_pis[pi_id]['stream_start_time'], '%m-%d %H:%M:%S'))
            log.spam(f"Stream duration for {pi_id} updated to {self.active_pis[pi_id]['stream_duration']}")

        base_dir = Path(self.video_data_dir)
        device_dir = base_dir / pi_id.replace(':', '-')

        self.active_pis[pi_id]['stream_file_size'] = get_dir_size(device_dir)
        log.spam(f"Stream file size for {pi_id} updated to {self.active_pis[pi_id]['stream_file_size']}")


    def shutdown_device(self, pi_id):
        log.info(f"Shutting down device {pi_id}")

        self.mqtt_client.publish(COMMAND_TOPIC_PREFIX + pi_id, "SHUTDOWN")
        self.active_pis[pi_id]['status'] = 'offline'
        self.emit_pi_status_update(pi_id)


    def reboot_device(self, pi_id = None):
        if pi_id is not None:
            log.info(f"Rebooting device {pi_id}")
            self.mqtt_client.publish(COMMAND_TOPIC_PREFIX + pi_id, "REBOOT")

            self.active_pis[pi_id]['status'] = 'offline'
            self.update_stream_info(pi_id)
            self.emit_pi_status_update(pi_id)
        else:
            log.info("Rebooting all devices")
            self.mqtt_client.publish(GLOBAL_COMMAND_TOPIC, "REBOOT")

            for pi_id in self.active_pis.keys():
                self.active_pis[pi_id]['status'] = 'offline'
                self.update_stream_info(pi_id)
                self.emit_pi_status_update(pi_id)
            

    def get_active_pis_list(self):
        pi_list = list(self.active_pis.values())
        #deep copy pi_list
        pi_list = [pi.copy() for pi in pi_list]
        # convert stream file size to string
        for pi in pi_list:
            if pi['stream_file_size'] is not None:
                pi['stream_file_size'] = convert_bytes(pi['stream_file_size'])
            else:
                pi['stream_file_size'] = "0 B"

        return pi_list
    

    def emit_pi_status_update(self, pi_id, emit_event='pi_status_update'):
        pi_dict = self.active_pis[pi_id].copy()
        pi_dict['stream_file_size'] = convert_bytes(pi_dict['stream_file_size'])

        self.socketio.emit(emit_event, pi_dict)
    

    def get_total_size(self):
        total = 0
        for pi_id in self.active_pis:
            if self.active_pis[pi_id]['stream_file_size'] is not None:
                total += self.active_pis[pi_id]['stream_file_size']

        total = convert_bytes(total)
        
        return total
    
    def get_active_pis_ips(self):
        pi_addresses = dict()
        for pi in self.active_pis.values():
            pi_addresses[pi['id']] = pi['ip_address']

        return pi_addresses
        