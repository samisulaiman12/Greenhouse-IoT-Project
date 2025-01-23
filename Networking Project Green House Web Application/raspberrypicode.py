import time
import ssl
import paho.mqtt.client as mqtt
import serial
from threading import Thread

# Local MQTT Configuration
mqtt_broker_local = "192.168.59.157"
mqtt_port_local = 1883

# Cloud MQTT Configuration
mqtt_broker_cloud = "6ca2e75a05bf44d194bd2cf18389f7e8.s1.eu.hivemq.cloud"
mqtt_port_cloud = 8883
cloud_username = "Maryhannoush"
cloud_password = "Mary1234"

# Initialize global variables
current_temperature = None
current_humidity = None
temp_state = None
humid_state = None
motion_state = None
distance_state = None
previous_relay_state = None

# MQTT Topics
temperature_topic = "greenhouse/temperature"
humidity_topic = "greenhouse/humidity"
motion_topic = "greenhouse/motion"
distance_topic = "greenhouse/distance"
arduino_topic = "arduino/messages"
relay_topic = "greenhouse/relay"

# Thresholds
mintemp = 25
maxtemp = 40
minhumid = 30
maxhumid = 70

# Initialize serial communication with Arduino
ser = serial.Serial('/dev/ttyAMA0', 9600)
time.sleep(2)

# Callback for local broker connection
def on_connect_local(client, userdata, flags, rc):
    print(f"Connected to local MQTT broker with result code {rc}")
    client.subscribe("greenhouse/#")

# Callback for receiving messages from local broker
def on_message_local(client, userdata, message):
    global current_temperature, current_humidity, motion_state, distance_state, temp_state, humid_state, previous_relay_state

    topic = message.topic
    payload = message.payload.decode()
    print(f"Local message received: Topic={topic}, Payload={payload}")

    # Relay message to the cloud broker
    client_cloud.publish(topic, payload)

    # Process specific topics
    if topic == temperature_topic:
        try:
            current_temperature = float(payload)
            print(f"Current temperature: {current_temperature}")
            if mintemp < current_temperature < maxtemp:
                temp_state = "normal"
            elif current_temperature < mintemp:
                temp_state = "low"
            else:
                temp_state = "high"
        except ValueError:
            print(f"Invalid temperature value received: {payload}")

    elif topic == humidity_topic:
        try:
            current_humidity = float(payload)
            print(f"Current humidity: {current_humidity}")
            if minhumid < current_humidity < maxhumid:
                humid_state = "normal"
            elif current_humidity < minhumid:
                humid_state = "low"
            else:
                humid_state = "high"
        except ValueError:
            print(f"Invalid humidity value received: {payload}")

    elif topic == motion_topic:
        motion_state = payload.lower()  # Normalize to lowercase for consistency
        print(f"Motion state: {motion_state}")

    elif topic == distance_topic:
        try:
            distance_state = float(payload)
            print(f"Distance state: {distance_state}")
        except ValueError:
            print(f"Invalid distance value received: {payload}")

    # Determine relay state based on conditions
    relay_state = "OFF"
    reason = "Conditions do not match any ON state."
    if temp_state == "normal" and motion_state == "detected":
        relay_state = "ON"
        reason = "Temperature normal and motion detected."
    elif temp_state == "low" or humid_state == "low":
        relay_state = "ON"
        reason = "Temperature or humidity is low."
    elif temp_state == "high" or humid_state == "high" or motion_state == "not detected":
        relay_state = "OFF"
        reason = "Temperature/humidity too high or no motion detected."
    elif distance_state is not None and distance_state < 10:
        relay_state = "ON"
        reason = "Object detected within 10 units of distance."

    # Only publish relay state if it changes
    if relay_state != previous_relay_state:
        client.publish(relay_topic, relay_state)
        previous_relay_state = relay_state
        print(f"Relay is {relay_state}: {reason}")

# Callback for cloud broker connection
def on_connect_cloud(client, userdata, flags, rc, properties=None):
    print(f"Connected to cloud MQTT broker with result code {rc}")

# MQTT Clients
client_local = mqtt.Client()
client_local.on_connect = on_connect_local
client_local.on_message = on_message_local

client_cloud = mqtt.Client(protocol=mqtt.MQTTv5)
client_cloud.on_connect = on_connect_cloud

# Secure connection for cloud broker
client_cloud.tls_set(tls_version=ssl.PROTOCOL_TLS)
client_cloud.username_pw_set(cloud_username, cloud_password)
client_cloud.connect(mqtt_broker_cloud, mqtt_port_cloud)

# Connect to the local broker
client_local.connect(mqtt_broker_local, mqtt_port_local)

# Serial communication with Arduino
def serial_communication():
    while True:
        if ser.in_waiting > 0:
            raw_message = ser.readline()
            print(f"Raw message from Arduino: {raw_message}")
            try:
                message = raw_message.decode('utf-8', errors='replace').strip()
                print(f"Decoded message: {message}")

                client_cloud.publish(arduino_topic, message)

                ser.write(b"ok\n")
            except Exception as e:
                print(f"Error processing message: {e}")
        time.sleep(0.1)

# Start MQTT clients
def start_mqtt_clients():
    Thread(target=client_local.loop_forever, daemon=True).start()
    Thread(target=client_cloud.loop_forever, daemon=True).start()

if __name__ == "__main__":
    print("Starting system...")
    start_mqtt_clients()
    serial_communication()
