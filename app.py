from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sqlite3
import threading
import paho.mqtt.client as mqtt
import time
from dht11_sensor import read_dht11_data, fanOn, send_email, check_for_yes_reply, cleanup_gpio, reset_email_flag
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from threading import Lock, Thread
import subprocess
import re
from datetime import datetime, timedelta
from bluetooth import discover_devices

threshold_lock = Lock()

app = Flask(__name__)
CORS(app)

# Global variable to hold the latest RFID tag
latest_rfid_tag = None
light_intensity = 0
led_status = "OFF"
light_email_sent = False
temp_email_sent = False
TEMP_THRESHOLD = 26
LIGHT_THRESHOLD = 100
fan_status_lock = Lock()
email_sent_lock = Lock()
rssi_threshold = -50  # Default RSSI threshold (dBm)
scan_duration = 10
fan_status = False
TEMP_DURATION = 3
fan_on_time = None
scanning = False
scanning_lock = threading.Lock()
scanned_devices = set()
lock = threading.Lock()

# MQTT Configuration
MQTT_BROKER = "10.0.0.67"  # MQTT broker IP (adjust based on your configuration)
MQTT_PORT = 1883
MQTT_LIGHT_TOPIC = "sensor/lightIntensity"
MQTT_RFID_TOPIC = "sensor/rfidtag"  # Topic to subscribe for RFID tags

SENDER_EMAIL = "micropoot@gmail.com"
EMAIL_PASSWORD = "xxxwftitcinyrudv"
RECEIVER_EMAIL = "amer1jawabra@gmail.com"

def update_fan_status(status):
    global fan_status
    with fan_status_lock:
        fan_status = status
        print(f"Fan status updated to: {fan_status}")


def send_email_rfid(user_profile):
    now = datetime.now().strftime("%H:%M")
    user_name = user_profile.get("user_name", "User")  # Safely get the user's name
    msg = MIMEText(f"Welcome {user_name}, you have entered at {now}.")
    msg["Subject"] = "User Logged In Message"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            print("Email sent successfully.")
    except Exception as e:
        print("Failed to send email:", e)

# Function to fetch user profile from the database based on the RFID tag
def get_user_from_db(rfid_tag):
    connection = sqlite3.connect("iot_dashboard.db")  # Ensure your DB is named correctly
    cursor = connection.cursor()

    # Assuming you have a table rfid_users with these columns
    query = """
    SELECT rfid_tag_number, user_name, user_picture, temperature_threshold, light_intensity_threshold
    FROM rfid_users
    WHERE rfid_tag_number = ?
    """
    cursor.execute(query, (rfid_tag,))
    result = cursor.fetchone()
    connection.close()

    if result:
        return {
            "rfid_tag_number": result[0],
            "user_name": result[1],
            "user_picture": result[2],
            "temperature_threshold": result[3],
            "light_intensity_threshold": result[4],
        }
    return None

# Function to adjust thresholds dynamically
def update_thresholds(user_profile):
    global TEMP_THRESHOLD, LIGHT_THRESHOLD
    with threshold_lock:
        TEMP_THRESHOLD = user_profile.get("temperature_threshold", TEMP_THRESHOLD)
        LIGHT_THRESHOLD = user_profile.get("light_intensity_threshold", LIGHT_THRESHOLD)
    print(f"Updated thresholds - TEMP: {TEMP_THRESHOLD}, LIGHT: {LIGHT_THRESHOLD}")

# Function to handle light intensity messages
def on_light_intensity_message(client, userdata, msg):
    global LIGHT_THRESHOLD, light_intensity, led_status, light_email_sent
    light_intensity = int(msg.payload.decode())

    if light_intensity < LIGHT_THRESHOLD:
        led_status = "ON"
        light_email_sent = True
    else:
        led_status = "OFF"
        light_email_sent = False

# Function to handle RFID messages
def on_rfid_message(client, userdata, msg):
    global latest_rfid_tag
    latest_rfid_tag = msg.payload.decode()
    print(f"Received RFID tag: {latest_rfid_tag}")

    # Update thresholds immediately after receiving a new RFID tag
    user_profile = get_user_from_db(latest_rfid_tag)
    if user_profile:
        update_thresholds(user_profile)
        send_email_rfid(user_profile)
    else:
        print("RFID tag not recognized.")

# MQTT Setup: Handling both light intensity and RFID messages
def mqtt_setup():
    client = mqtt.Client()

    # Define a unified callback for both topics
    def on_message(client, userdata, msg):
        if msg.topic == MQTT_LIGHT_TOPIC:
            on_light_intensity_message(client, userdata, msg)  # Handle light intensity messages
        elif msg.topic == MQTT_RFID_TOPIC:
            on_rfid_message(client, userdata, msg)  # Handle RFID messages

    client.on_message = on_message  # Set the unified callback
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.subscribe(MQTT_LIGHT_TOPIC)
    client.subscribe(MQTT_RFID_TOPIC)  # Subscribe to both topics
    client.loop_forever()

@app.route('/scan', methods=['GET'])
def scan_devices():
    """Endpoint to start a Bluetooth scan and return device details."""
    scan_thread = threading.Thread(target=bluetooth_scan)
    scan_thread.start()
    scan_thread.join()  # Wait for the scan to complete before sending data

    with scanning_lock:  # Ensure thread-safe access to scanned_devices
        devices = [{'address': addr, 'name': name} for addr, name in scanned_devices]
        device_count = len(scanned_devices)

    return jsonify({'device_count': device_count, 'devices': devices}), 200


def bluetooth_scan():
    """Scan for Bluetooth devices and update the global set."""
    global scanned_devices
    with scanning_lock:
        scanned_devices.clear()  # Clear previous scan results

    print("Starting Bluetooth scan...")
    try:
        nearby_devices = discover_devices(duration=10, lookup_names=True)
        with scanning_lock:
            for addr, name in nearby_devices:
                scanned_devices.add((addr, name))  # Add device as a tuple
                print(f"Device found: {addr} - {name}")
    except Exception as e:
        print(f"Error during Bluetooth scan: {e}")
    print("Bluetooth scan completed.")

# Route to fetch the latest user profile based on RFID tag
@app.route('/user_profile', methods=['GET'])
def get_user_profile():
    global latest_rfid_tag
    if not latest_rfid_tag:
        return jsonify({'success': False, 'message': 'No RFID tag detected'}), 404

    user_profile = get_user_from_db(latest_rfid_tag)
    if user_profile:
        return jsonify({'success': True, 'profile': user_profile}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid RFID tag'}), 400

# Route for frontend to fetch RFID tag data
@app.route('/sensor_data/rfid', methods=['GET'])
def sensor_data_rfid():
    global latest_rfid_tag
    if latest_rfid_tag:
        return jsonify({'success': True, 'rfid_tag': latest_rfid_tag}), 200
    else:
        return jsonify({'success': False, 'message': 'No RFID tag available'}), 400

# Route for fetching sensor data (light intensity, fan status, etc.)
@app.route("/sensor_data", methods=['GET'])
def sensor_data():
    global fan_status, fan_on_time, light_email_sent, temp_email_sent, last_temp, last_humidity

    # Read temperature and humidity
    temperature, humidity = read_dht11_data()
    if temperature:
        print(f"Info: Current Temperature={temperature}, Humidity={humidity}")
        # Handle high-temperature scenario
        if temperature and temperature > TEMP_THRESHOLD:
            if not temp_email_sent:
                print(f"Alert: Temperature exceeded threshold ({TEMP_THRESHOLD}°C). Sending email.")
                send_email(temperature)  # Trigger email alert
                temp_email_sent = True
            if fan_status == False:
                fan_status = check_for_yes_reply()
                fan_on_time = datetime.now()
        else:
            # Reset email logic if temperature normalizes
            print(f"Info: Temperature ({temperature}°C) is below threshold ({TEMP_THRESHOLD}°C). No email sent.")
            reset_email_flag()
            temp_email_sent = False
    else:
        print("Warning: Failed to get valid temperature reading. Using last cached values.")

    if fan_on_time and (datetime.now() - fan_on_time) < timedelta(seconds=TEMP_DURATION):
        with fan_status_lock:
            print(f"Fan Status: {fan_status} (Fan on for {TEMP_DURATION} seconds)")
    else:
        # After TEMP_DURATION seconds, turn off the fan
        with fan_status_lock:
            fan_status = False
        print(f"Fan turned off after {TEMP_DURATION} seconds.")

    # Construct MQTT data to send to the frontend
    mqtt_data = {
        "light_intensity": light_intensity,
        "led_status": led_status,
        "email_sent": "Email sent" if light_email_sent else "No email sent",
        "temperature": temperature,
        "humidity": humidity,
        "fanOn": fan_status  # Use the thread-safe fan status
    }
    print(f"Debug: MQTT Data={mqtt_data}")
    return jsonify(mqtt_data)

@app.route('/thresholds', methods=['GET'])
def get_thresholds():
    global TEMP_THRESHOLD, LIGHT_THRESHOLD
    return jsonify({
        "temp_threshold": TEMP_THRESHOLD,
        "light_threshold": LIGHT_THRESHOLD
    }), 200

# @app.route('/scan', methods=['GET'])
# def scan_devices():
#     try:
#         # Perform the scan and fetch device list
#         global scanned_devices
#         with scanning_lock:
#             if scanning:
#                 return jsonify({"message": "Scan in progress. Please wait."}), 202

#         start_bluetooth_scan()
#         num_devices = len(scanned_devices)
#         return jsonify({"number_of_devices": num_devices, "devices": scanned_devices})
#     except Exception as e:
#         print(f"Error during scan: {e}")
#         return {"error": str(e)}, 500

@app.route("/set_threshold", methods=["POST"])
def set_threshold():
    """
    Updates the RSSI threshold for filtering devices.
    """
    global rssi_threshold
    data = request.json
    if "threshold" in data:
        rssi_threshold = int(data["threshold"])
        return jsonify({"message": "Threshold updated", "rssi_threshold": rssi_threshold})
    return jsonify({"message": "Invalid input"}), 400

def clean_processed_uids():
    global REPLY_UIDS_PROCESSED
    while True:
        time.sleep(300)  # Cleanup every 5 minutes
        REPLY_UIDS_PROCESSED.clear()
        print("Processed UIDs cleaned up.")

# Start the cleanup thread
cleanup_thread = threading.Thread(target=clean_processed_uids, daemon=True)
cleanup_thread.start()

# Root route to render the index.html
@app.route("/")
def index():
    return render_template("index.html")

# Start the app and MQTT listener in a separate thread
if __name__ == '__main__':
    try:   
        mqtt_thread = threading.Thread(target=mqtt_setup)  # Start MQTT listener in a separate thread
        mqtt_thread.daemon = True  # Ensures the thread exits when the main program exits
        mqtt_thread.start()
        app.run(debug=True, host="0.0.0.0", port=5000)
    finally:
        cleanup_gpio()
