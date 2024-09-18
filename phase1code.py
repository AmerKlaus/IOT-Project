from flask import Flask, render_template, request
import RPi.GPIO as GPIO

app = Flask(__name__)

# Set up GPIO
LED_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

@app.route('/')
def index():
    led_status = GPIO.input(LED_PIN)
    return render_template('index.html', led_status=led_status)

@app.route('/toggle', methods=['POST'])
def toggle_led():
    led_status = GPIO.input(LED_PIN)
    if led_status == GPIO.LOW:
        GPIO.output(LED_PIN, GPIO.HIGH)  # Turn on LED
    else:
        GPIO.output(LED_PIN, GPIO.LOW)  # Turn off LED
    return "LED Toggled"

if __name__ == "__main__":
    app.run(host='0.0.0.0')