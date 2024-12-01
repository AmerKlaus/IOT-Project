#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <PubSubClient.h>

// Define pins for RFID
#define SS_PIN 5  // SDA Pin on RC522
#define RST_PIN 25 // RST Pin on RC522

// Set up RFID instance
MFRC522 rfid(SS_PIN, RST_PIN);

// Wi-Fi and MQTT configuration
const char* ssid = "Ghassan_EXT";
const char* password = "5146231661";
const char* mqtt_server = "10.0.0.67"; // MQTT broker IP address

WiFiClient espClient;
PubSubClient client(espClient);

// Set up Wi-Fi connection
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// Reconnect to MQTT broker if disconnected
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
      client.subscribe("light/status");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

const int photoResistorPin = 34; // Analog pin for photoresistor
const int threshold = 400;  // Light intensity threshold for action

void setup() {
  Serial.begin(115200);    // Initialize serial communication
  setup_wifi();             // Set up Wi-Fi
  client.setServer(mqtt_server, 1883);  // Set MQTT server
  SPI.begin();             // Initialize SPI bus for RFID
  rfid.PCD_Init();         // Initialize RFID reader

  Serial.println("Place your RFID card near the reader...");
}

void loop() {
  if (!client.connected()) {
    reconnect();  // Ensure MQTT client is connected
  }
  client.loop();

  // Look for new cards and read the RFID tag
  if (rfid.PICC_IsNewCardPresent()) {
    if (rfid.PICC_ReadCardSerial()) {
      String rfidTag = "";
      for (byte i = 0; i < rfid.uid.size; i++) {
        rfidTag += String(rfid.uid.uidByte[i], HEX);
      }
      Serial.print("Card UID: ");
      Serial.println(rfidTag);
      
      // Publish RFID tag to MQTT broker
      client.publish("sensor/rfidtag", rfidTag.c_str());

      // Halt the card
      rfid.PICC_HaltA();
    }
  }

  // Read light intensity from the photoresistor
  int lightIntensity = analogRead(photoResistorPin);
  Serial.print("Light Intensity: ");
  Serial.println(lightIntensity);
  
  // Publish light intensity to MQTT broker
  String lightIntensityStr = String(lightIntensity);
  client.publish("sensor/lightIntensity", lightIntensityStr.c_str());

  // If light intensity is above threshold, take action
  if (lightIntensity > threshold) {
    Serial.println("Light intensity exceeds threshold!");
    // You can add additional actions, such as turning on a light or device
  }

  delay(2000);  // Delay to avoid flooding the broker
}
