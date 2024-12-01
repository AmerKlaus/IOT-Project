import time
from sensor_code.Freenove_DHT import DHT
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import RPi.GPIO as GPIO
from time import sleep
import threading
from threading import Thread

# GPIO setup for DHT11 and motor
DHT_PIN = 17  # GPIO pin for DHT11 sensor
TEMP_THRESHOLD = 22  # Temperature threshold for email notification
Motor1 = 22  # Motor GPIO pins
Motor2 = 27
Motor3 = 19

GPIO.setmode(GPIO.BCM)
GPIO.setup(Motor1, GPIO.OUT)
GPIO.setup(Motor2, GPIO.OUT)
GPIO.setup(Motor3, GPIO.OUT)

# Initialize DHT sensor
dht = DHT(DHT_PIN)

# Email configuration
SENDER_EMAIL = "micropoot@gmail.com"
RECEIVER_EMAIL = "amer1jawabra@gmail.com"
EMAIL_PASSWORD = "xxxwftitcinyrudv"
IMAP_SERVER = "imap.gmail.com"  # IMAP server for Gmail

# Track if an alert email has been sent
email_sent = False  # Initially set to False

# Function to read DHT11 sensor data
def read_dht11_data():
    for _ in range(15):  # Retry up to 15 times
        chk = dht.readDHT11()
        if chk == 0:  # 0 indicates a successful read
            temperature = dht.getTemperature()
            humidity = dht.getHumidity()
            return temperature, humidity
        time.sleep(0.1)
    return None, None  # Return None if reading fails

# Function to send alert email
def send_email(temp):
    global email_sent
    if email_sent:  # Only send email if no alert has been sent yet
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = "Temperature Alert"
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL

    text = f"The current temperature is {temp}°C. Would you like to turn on the fan?"
    message.attach(MIMEText(text, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        print("Email sent!")
        email_sent = True  # Set flag to True to prevent further emails
    except Exception as e:
        print("Error sending email:", e)

fanOn = False

def turn_on_motor():
    global fanOn
    print("Turning on motor...")
    fanOn = True  # Set fan status to on
    GPIO.output(Motor1, GPIO.HIGH)
    GPIO.output(Motor2, GPIO.LOW)
    GPIO.output(Motor3, GPIO.HIGH)
    
    sleep(5)  # Motor runs for 20 seconds (adjust if needed)

    # Turn off motor GPIO signals
    GPIO.output(Motor1, GPIO.LOW)
    GPIO.output(Motor2, GPIO.LOW)
    GPIO.output(Motor3, GPIO.LOW)
    
    fanOn = False  # Now set fan status to off

# Global variables to track email and reply status
email_sent = False
no_reply_received = False  # Initially set to False

def send_email(temp):
    global email_sent, no_reply_received
    # Only send email if no previous email was sent and no "no" reply has been received
    if email_sent or no_reply_received:
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = "Temperature Alert"
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL

    text = f"The current temperature is {temp}°C. Would you like to turn on the fan?"
    message.attach(MIMEText(text, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())
        print("Email sent!")
        email_sent = True  # Set flag to True to prevent further emails
    except Exception as e:
        print("Error sending email:", e)

def check_for_yes_reply():
    global fanOn, no_reply_received
    if no_reply_received:  # Skip checking if a "no" response was received
        return False

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(SENDER_EMAIL, EMAIL_PASSWORD)
        mail.select("inbox")

        # Search for unread messages with "Re: Temperature Alert" in the subject
        status, messages = mail.search(None, '(UNSEEN SUBJECT "Re: Temperature Alert")')
        if status == "OK":
            for num in messages[0].split():
                status, data = mail.fetch(num, "(RFC822)")
                if status == "OK":
                    msg = email.message_from_bytes(data[0][1])
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode().lower()
                                if "yes" in body:
                                    # Start motor control in a separate thread
                                    motor_thread = Thread(target=turn_on_motor)
                                    motor_thread.start()
                                    return True
                                elif "no" in body:
                                    no_reply_received = True  # Set flag if "no" was received
                                    print("Received 'no' reply, stopping further checks.")
                                    return False
        mail.logout()
    except Exception as e:
        print("Error checking email:", e)
    return False  # Return False if no "yes" reply

# Function to clean up GPIO on exit
def cleanup_gpio():
    GPIO.cleanup()

# Function to reset the email sent flag when temperature goes below threshold
def reset_email_flag():
    global email_sent
    email_sent = False
