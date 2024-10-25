from flask import Flask, render_template, jsonify
from dht11_reading import read_dht11_data, send_email

app = Flask(__name__)
TEMP_THRESHOLD = 24  # Set threshold for email notification

@app.route('/sensor_data')
def sensor_data():
    temp, humidity = read_dht11_data()
    if temp and temp > TEMP_THRESHOLD:
        send_email(temp)
    return jsonify({'temperature': temp, 'humidity': humidity})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')