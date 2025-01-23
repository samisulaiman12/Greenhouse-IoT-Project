#include <ESP8266WiFi.h>          // For ESP8266
#include <PubSubClient.h>         // MQTT library

// WiFi and MQTT broker settings
const char* ssid = "Sami";
const char* password = "123456789";
const char* mqtt_server = "192.168.59.157";   // Use your MQTT broker IP address or hostname
const int mqtt_port = 1883;

// Create a WiFi and MQTT client instance
WiFiClient espClient;
PubSubClient client(espClient);

// PIR motion sensor settings
#define PIR_PIN 5                 // PIR sensor connected to GPIO5 (D1 on NodeMCU)
int pirState = LOW; // Initial state: no motion detected

// HC-SR04 sensor settings
#define TRIG_PIN 12               // HC-SR04 Trigger connected to GPIO12 (D6 on NodeMCU)
#define ECHO_PIN 14               // HC-SR04 Echo connected to GPIO14 (D5 on NodeMCU)

// MQTT topics
const char* motion_topic = "greenhouse/motion";        // Topic to send motion detection status
const char* distance_topic = "greenhouse/distance";    // Topic to send distance readings

void setup_wifi() {
  delay(10);
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("ESP IP Address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");
    if (client.connect("ESP8266Client")) {  // Provide a unique client ID
      Serial.println("MQTT connected!");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);

  pinMode(PIR_PIN, INPUT);        // Initialize PIR pin as input
  pinMode(TRIG_PIN, OUTPUT);      // Initialize HC-SR04 Trigger as output
  pinMode(ECHO_PIN, INPUT);       // Initialize HC-SR04 Echo as input

  Serial.println("PIR Sensor and HC-SR04 Initialized.");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();  // Process incoming MQTT messages (if any)

  // PIR motion detection
  int pirState = digitalRead(PIR_PIN);  // Read the PIR sensor state
  if (pirState == HIGH) {
    if (client.publish(motion_topic, "Motion Detected")) {
      Serial.println("Motion Detected published successfully!");
    } else {
      Serial.println("Failed to publish motion detection status.");
    }
  } else {
    if (client.publish(motion_topic, "No Motion")) {
      Serial.println("No Motion published successfully!");
    } else {
      Serial.println("Failed to publish motion detection status.");
    }
  }

  // HC-SR04 distance measurement
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH);  // Measure the pulse duration
  float distance = (duration * 0.034) / 2; // Convert to distance in cm

  // Publish distance reading to MQTT
  char distanceString[8];
  dtostrf(distance, 1, 2, distanceString);  // Convert float to string
  if (client.publish(distance_topic, distanceString)) {
    Serial.print("Distance published successfully: ");
    Serial.println(distanceString);
  } else {
    Serial.println("Failed to publish distance.");
  }

  delay(2000);  // Delay to control the frequency of readings
}
