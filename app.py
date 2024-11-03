from flask import Flask, render_template, jsonify
from dht11_reading import read_dht11_data, send_email, check_for_yes_reply, cleanup_gpio, reset_email_flag, fanOn

app = Flask(__name__)
TEMP_THRESHOLD = 22

@app.route('/sensor_data')
def sensor_data():
    temp, humidity = read_dht11_data()
    if temp:
        if temp > TEMP_THRESHOLD:
            send_email(temp)
            # Check inbox for "yes" reply to turn on the motor and update fan status
            fan_status = check_for_yes_reply()  # Update fanOn here based on email response
        else:
            reset_email_flag()  # Reset email flag when temperature is below threshold
    # Include fanOn status in the JSON response
    return jsonify({'temperature': temp, 'humidity': humidity, 'fanOn': fan_status})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0')
    finally:
        cleanup_gpio()  # Ensure GPIO cleanup on exit
