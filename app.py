from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
from dht11_reading import read_dht11_data, send_email, check_for_yes_reply, cleanup_gpio, reset_email_flag

app = Flask(__name__)

# MQTT Setup
light_intensity = 0
led_status = "OFF"
email_sent = False

def on_connect(client, userdata, flags, rc):
    client.subscribe("sensor/lightIntensity")

def on_message(client, userdata, msg):
    global light_intensity, led_status, email_sent
    light_intensity = int(msg.payload.decode())

    if light_intensity < 400:
        led_status = "ON"
        email_sent = True
    else:
        led_status = "OFF"
        email_sent = False

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("172.20.10.5", 1883, 60)
mqtt_client.loop_start()

# DHT11 and email setup
TEMP_THRESHOLD = 22
fan_status = "OFF"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sensor_data")
def sensor_data():
    global fan_status
    temp, humidity = read_dht11_data()
    if temp:
        if temp > TEMP_THRESHOLD:
            send_email(temp)
            fan_status = check_for_yes_reply()
        else:
            reset_email_flag()

    mqtt_data = {
        "light_intensity": light_intensity,
        "led_status": led_status,
        "email_sent": "Email has been sent" if email_sent else "No email sent",
        "temperature": temp,
        "humidity": humidity,
        "fan_status": fan_status
    }
    return jsonify(mqtt_data)

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', debug=True)
    finally:
        cleanup_gpio()  # Ensure GPIO cleanup on exit
