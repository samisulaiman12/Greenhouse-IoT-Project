#include <ESP8266WiFi.h>          // For ESP8266
#include <PubSubClient.h>         // MQTT library
#include <DHT.h>                  // DHT sensor library

// WiFi and MQTT broker settings
const char* ssid = "Sami";
const char* password = "123456789";
const char* mqtt_server = "192.168.59.157";   // Use your MQTT broker IP address or hostname
const int mqtt_port = 1883;

// Create a WiFi and MQTT client instance
WiFiClient espClient;
PubSubClient client(espClient);

// DHT22 settings
#define DHTPIN 2                  // DHT22 connected to GPIO2 (D4 on NodeMCU)
#define DHTTYPE DHT22             // Specify DHT sensor type
DHT dht(DHTPIN, DHTTYPE);         // Initialize DHT sensor

// Relay settings
#define RELAY_PIN 5               // Relay connected to GPIO5 (D1 on NodeMCU)

// MQTT topics
const char* relay_topic = "greenhouse/relay";         // Topic to control relay
const char* temperature_topic = "greenhouse/temperature"; // Topic to send temperature readings
const char* humidity_topic = "greenhouse/humidity";       // Topic to send humidity readings

// Variable to track relay status
bool relayStatus = false;         // false = OFF, true = ON

// Reconnect to WiFi
void setup_wifi() {
  delay(10);
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
}

// Callback function to handle received MQTT messages
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received on topic: ");
  Serial.println(topic);

  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];  // Convert payload to string
  }

  // Print received message content to Serial Monitor
  Serial.print("Message content: ");
  Serial.println(message);

  // Control relay based on received message
  if (String(topic) == relay_topic) {
    Serial.print("Message on relay topic: ");
    Serial.println(message); // Show the message received on the weather/relay topic
    
    if (message == "ON") {
      digitalWrite(RELAY_PIN, LOW);   // Activate relay (assuming LOW triggers relay)
      relayStatus = true;
    } else if (message == "OFF") {
      digitalWrite(RELAY_PIN, HIGH);  // Deactivate relay
      relayStatus = false;
    }

    // Print relay status
    Serial.print("Relay status: ");
    Serial.println(relayStatus ? "ON" : "OFF");
  }
}

// Reconnect to MQTT broker if disconnected
void reconnect() {
  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");
    if (client.connect("ESP8266Client")) {  // Provide a unique client ID
      Serial.println("MQTT connected!");

      // Subscribe to the relay control topic
      client.subscribe(relay_topic);
      Serial.println("Subscribed to relay control topic.");
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
  client.setCallback(callback);

  pinMode(RELAY_PIN, OUTPUT);      // Initialize relay pin as output
  digitalWrite(RELAY_PIN, HIGH);   // Ensure relay is off initially

  dht.begin();                     // Initialize DHT sensor
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();  // Process incoming MQTT messages

  // Read temperature and humidity from DHT22
  float temperature = dht.readTemperature();  // Read temperature in Celsius
  float humidity = dht.readHumidity();        // Read humidity

  // Check if readings are valid
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor!");
  } else {
    // Print readings to Serial Monitor
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.println(" °C");

    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");

    // Publish readings to MQTT topics
    char tempString[8];
    dtostrf(temperature, 1, 2, tempString);  // Convert float to string
    if (client.publish(temperature_topic, tempString)) {
      Serial.println("Temperature published successfully!");
    } else {
      Serial.println("Failed to publish temperature.");
    }

    char humString[8];
    dtostrf(humidity, 1, 2, humString);      // Convert float to string
    if (client.publish(humidity_topic, humString)) {
      Serial.println("Humidity published successfully!");
    } else {
      Serial.println("Failed to publish humidity.");
    }
  }

  delay(5000);  // Publish readings every 5 seconds
}
