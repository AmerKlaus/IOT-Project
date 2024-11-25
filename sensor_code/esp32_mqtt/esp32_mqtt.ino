#include <WiFi.h>
#include <PubSubClient.h>

const char* ssid = "JAB";
const char* password = "myownwifi";
const char* mqtt_server = "10.0.0.67";

WiFiClient espClient;
PubSubClient client(espClient);

const int photoResistorPin = 34; // Analog pin for photoresistor
const int threshold = 400;

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

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

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

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  int lightIntensity = analogRead(photoResistorPin);
  Serial.print("Light Intensity: ");
  Serial.println(lightIntensity);
  
  String lightIntensityStr = String(lightIntensity);
  client.publish("sensor/lightIntensity", lightIntensityStr.c_str());

  delay(2000);
}
