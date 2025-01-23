from flask import Flask, jsonify, render_template, redirect, url_for, request, session
from flask_socketio import SocketIO
from flask_mqtt import Mqtt
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import threading
import csv
from datetime import datetime


app = Flask(__name__)
CORS(app, origins="http://localhost:5000")


app.secret_key = '83c23c1d432b76202246490b1ee6064b424292d6133560181981d2892c9595e1'

app.config['MQTT_BROKER_URL'] = '192.168.59.157' 
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 60
app.config['MQTT_TLS_ENABLED'] = False


socketio = SocketIO(app, cors_allowed_origins="*")
mqtt = Mqtt(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

users = {}  


class User(UserMixin):
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None


data = {
    "temperature": None,
    "humidity": None,
    "motion": None,
    "distance": None,
    "relay": "OFF",
    "minTemp": 25,   
    "maxTemp": 40,   
    "minHumid": 30,  
    "maxHumid": 70    
}


lock = threading.Lock()


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        mqtt.subscribe("greenhouse/#")
        print("Subscribed to all topics under 'greenhouse/#'")
    else:
        print(f"Failed to connect to MQTT Broker, return code {rc}")

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global data
    topic = message.topic
    try:
        payload = message.payload.decode()
        with lock:
           
            if topic == "greenhouse/temperature":
                data["temperature"] = float(payload)
            elif topic == "greenhouse/humidity":
                data["humidity"] = float(payload)
            elif topic == "greenhouse/motion":
                data["motion"] = payload
            elif topic == "greenhouse/distance":
                data["distance"] = float(payload)
            elif topic == "greenhouse/relay":
                data["relay"] = payload

          
            socketio.emit('update_data', data)
            print(f"Updated data from topic '{topic}': {data}")
    except ValueError as e:
        print(f"Error decoding payload '{message.payload}': {e}")


@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return redirect(url_for('register'))  

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if username in users:
            return jsonify({"message": "User already exists!"}), 400

        
        users[username] = {"password": password}
        return jsonify({"message": "Registration successful. Please log in.", "redirect": "/login"}), 200

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user)
            return jsonify({"message": "Login successful.", "redirect": url_for('index')}), 200
        else:
            return jsonify({"message": "Invalid credentials."}), 400

    return render_template('login.html')

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful."}), 200

@app.route('/api/data', methods=['GET'])
def get_data():
    global data
    with lock:
        return jsonify(data), 200


@app.route('/api/settings', methods=['POST'])
def save_settings():
    global data
    try:
     
        min_temp = request.json.get('minTemp')
        max_temp = request.json.get('maxTemp')
        min_humid = request.json.get('minHumid')
        max_humid = request.json.get('maxHumid')

   
        if min_temp is not None:
            data['minTemp'] = min_temp
        if max_temp is not None:
            data['maxTemp'] = max_temp
        if min_humid is not None:
            data['minHumid'] = min_humid
        if max_humid is not None:
            data['maxHumid'] = max_humid

       
        return jsonify({
            'message': 'Settings saved successfully',
            'settings': data
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error saving settings: {e}'}), 400


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
