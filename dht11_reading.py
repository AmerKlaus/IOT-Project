import time
from Freenove_DHT import DHT
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# GPIO pin for DHT11 sensor
DHT_PIN = 17  
TEMP_THRESHOLD = 24  # Temperature threshold for email notification

# Initialize DHT sensor
dht = DHT(DHT_PIN)

def read_dht11_data():
    for _ in range(15):  # Retry reading up to 15 times
        chk = dht.readDHT11()  # Perform a read operation
        if chk == 0:  # 0 indicates a successful read
            temperature = dht.getTemperature()
            humidity = dht.getHumidity()
            return temperature, humidity
        time.sleep(0.1)
    return None, None  # Return None if reading fails

def send_email(temp):
    sender_email = "micropoot@gmail.com"
    receiver_email = "amer1jawabra@gmail.com"
    password = "xxxwftitcinyrudv"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Temperature Alert"
    message["From"] = sender_email
    message["To"] = receiver_email

    text = f"The current temperature is {temp}°C. Would you like to turn on the fan?"
    message.attach(MIMEText(text, "plain"))

    try:
        # Connect to Gmail’s SMTP server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent!")
    except Exception as e:
        print("Error sending email:", e)
