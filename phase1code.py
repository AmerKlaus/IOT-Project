from flask import Flask, render_template, redirect, url_for, request
import RPi.GPIO as GPIO

app = Flask(__name__)

# Set up GPIO
LED_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

@app.route('/')
def index():
    led_status = GPIO.input(LED_PIN)
    # 'True' if GPIO.HIGH else 'False' to correctly align with your HTML checkbox and image logic
    return render_template('index.html', led_status=(led_status == GPIO.HIGH))

@app.route('/toggle', methods=['POST'])
def toggle_led():
    current_status = GPIO.input(LED_PIN)
    new_status = GPIO.LOW if current_status == GPIO.HIGH else GPIO.HIGH
    GPIO.output(LED_PIN, new_status)
    return {"led_status": new_status == GPIO.HIGH}

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)