import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

LED_PIN = 18
threshold = 400
mqtt_broker = "172.20.10.5"

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

# Email configuration
SENDER_EMAIL = "micropoot@gmail.com"
EMAIL_PASSWORD = "xxxwftitcinyrudv"
RECEIVER_EMAIL = "amer1jawabra@gmail.com"

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
    try:
        light_intensity = int(msg.payload.decode())
        print("Light Intensity:", light_intensity)
        if light_intensity < threshold:
            print("Turning on LED")
            GPIO.output(LED_PIN, GPIO.HIGH)
            send_email()
        else:
            print("Turning off LED")
            GPIO.output(LED_PIN, GPIO.LOW)
    except Exception as e:
        print("Error processing message:", e)

client = mqtt.Client(client_id="", clean_session=True, protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_broker, 1883, 60)
client.loop_start()
# Keep the main script running so the background loop can continue
try:
    while True:
        pass  # or add other logic here
except KeyboardInterrupt:
    client.loop_stop()
    GPIO.cleanup()
    client.disconnect()