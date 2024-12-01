import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from app import LIGHT_THRESHOLD
from threading import Lock
import requests
import time

threshold_lock = Lock()

LED_PIN = 18
mqtt_broker = "10.0.0.67"

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

# Email configuration
SENDER_EMAIL = "micropoot@gmail.com"
EMAIL_PASSWORD = "xxxwftitcinyrudv"
RECEIVER_EMAIL = "amer1jawabra@gmail.com"

def fetch_updated_thresholds():
    global LIGHT_THRESHOLD
    try:
        response = requests.get("http://0.0.0.0:5000/thresholds")  # Ensure this endpoint is implemented in app.py
        if response.status_code == 200:
            data = response.json()
            with threshold_lock:
                LIGHT_THRESHOLD = data.get("light_threshold", LIGHT_THRESHOLD)
            print(f"Updated LIGHT_THRESHOLD: {LIGHT_THRESHOLD}")
    except Exception as e:
        print(f"Failed to fetch updated thresholds: {e}")

def send_email():
    now = datetime.now().strftime("%H:%M")
    msg = MIMEText(f"The Light is ON at {now}.")
    msg["Subject"] = "Light Status Notification"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            print("Email sent")
    except Exception as e:
        print("Failed to send email:", e)

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with code", rc)
    client.subscribe("sensor/lightIntensity")

def on_message(client, userdata, msg):
    global LIGHT_THRESHOLD
    with threshold_lock:
        light_intensity = int(msg.payload.decode())
        print(f"Light Intensity: {light_intensity}, Threshold: {LIGHT_THRESHOLD}")
        if light_intensity < LIGHT_THRESHOLD:
            print("Turning on LED")
            GPIO.output(LED_PIN, GPIO.HIGH)
            send_email()
        else:
            print("Turning off LED")
            GPIO.output(LED_PIN, GPIO.LOW)

client = mqtt.Client(client_id="", clean_session=True, protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_broker, 1883, 60)
client.loop_start()
# Keep the main script running so the background loop can continue
try:
    while True:
        pass  # or add other logic here
        fetch_updated_thresholds()
        time.sleep(10)
except KeyboardInterrupt:
    client.loop_stop()
    GPIO.cleanup()
    client.disconnect()