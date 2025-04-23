from argparse import ArgumentParser

from flask import Flask, jsonify, render_template
from flask_httpauth import HTTPBasicAuth
from flask_socketio import SocketIO
from werkzeug.security import check_password_hash, generate_password_hash

from common.log_utils import log, set_log_level
from common.utils import read_config
from server.mqtt_server import MQTT_Central_Client

app = Flask(__name__)
socketio = SocketIO(app)
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if not users:
        # If no users are defined, bypass authentication
        return True
    elif username in users and check_password_hash(users.get(username), password):
        return username
    return False 
       
@app.route('/')
@auth.login_required
def index():
    # Assuming devices is a list of device_ids you have
    return render_template('index.html', raspberry_pis=mqtt_central_client.get_active_pis_list(), total_size=mqtt_central_client.get_total_size())

@app.route('/stream_overview')
@auth.login_required
def stream_overview():
    # Assuming devices is a list of device_ids you have
    return render_template('stream_overview.html', raspberry_pis=mqtt_central_client.get_active_pis_list())

@app.route('/start_stream/<pi_id>', methods=['POST'])
@auth.login_required
def start_stream(pi_id):    
    ret = mqtt_central_client.start_stream(pi_id)

    if ret[0]:
        return jsonify(success=True), 200
    else: 
        return jsonify(success=False, error=ret[1]), 400
    
@app.route('/stop_stream/<pi_id>', methods=['POST'])
@auth.login_required
def stop_stream(pi_id):
    return mqtt_central_client.stop_stream(pi_id)

@app.route('/start_rec/<pi_id>', methods=['GET'])
@auth.login_required
def start_rec(pi_id):    
    ret = mqtt_central_client.start_rec(pi_id)

    if ret[0]:
        return jsonify(success=True), 200
    else: 
        return jsonify(success=False, error=ret[1]), 400
    
@app.route('/stop_rec/<pi_id>', methods=['GET'])
@auth.login_required
def stop_rec(pi_id):
    return mqtt_central_client.stop_rec(pi_id)


@app.route('/get_picture/<device_id>', methods=['GET'])
@auth.login_required
def get_picture(device_id):
    return mqtt_central_client.get_picture(device_id)

@app.route('/ping/<pi_id>', methods=['GET'])
@auth.login_required
def ping(pi_id):
    ret = mqtt_central_client.is_device_alive(pi_id)

    if ret:
        return jsonify(success=True), 200
    else:
        return jsonify(success=True, error="Couldn't ping device"), 200

@app.route('/shutdown/<pi_id>', methods=['GET'])
@auth.login_required
def shutdown_pi(pi_id):
    mqtt_central_client.stop_stream(pi_id)
    mqtt_central_client.shutdown_device(pi_id)

    return jsonify(success=True), 200

@app.route('/reboot/<pi_id>', methods=['GET'])
@auth.login_required
def reboot(pi_id):
    mqtt_central_client.stop_stream(pi_id)
    mqtt_central_client.reboot_device(pi_id)

    return jsonify(success=True), 200

@app.route('/reboot_all', methods=['GET'])
@auth.login_required
def reboot_all():
    mqtt_central_client.reboot_device()

    return jsonify(success=True), 200

@app.route('/get_device_ips/', methods=['GET'])
@auth.login_required
def get_devices_ip():
    device_dict = mqtt_central_client.get_active_pis_ips()
    
    return jsonify(device_dict), 200


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", type=str, default="./configs/config_server.ini")
    parser.add_argument("-l", "--log_lvl", dest="log_lvl", default="debug", choices=["debug", "spam", "verbose", "info", "warning", "error"], help='Set level of logger to get more or less verbose output')
    args = parser.parse_args()


    config = read_config(args.config)


    if "WEBSERVER" in config and "USERNAME" in config["WEBSERVER"] and "PASSWORD" in config["WEBSERVER"]:
        users = {
            config["WEBSERVER"]["USERNAME"]: generate_password_hash(config["WEBSERVER"]["PASSWORD"])
        }
    else:
        users = None

    # if log_lvl is not set in config, use the one from the command line
    log_lvl = config["MAIN"]["LOG_LEVEL"] if "MAIN" in config and "LOG_LEVEL" in config["MAIN"] else args.log_lvl
    set_log_level(log_lvl)

    log.info(f"Starting MQTT central client")

    mqtt_central_client = MQTT_Central_Client(config['MQTT'], socketio, config["MAIN"]["VIDEO_DATA_DIR"])
    socketio.run(app, host=config["WEBSERVER"]["SERVER_ADDRESS"], port=config["WEBSERVER"]["PORT"], debug=True, use_reloader=False)
    # app.run(host='0.0.0.0', port=5000, debug=True)


