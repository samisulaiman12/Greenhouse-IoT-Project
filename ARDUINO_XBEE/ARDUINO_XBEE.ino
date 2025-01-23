// Define the pin for the MH Flame sensor
const int flameSensorPin = A0; // Analog pin connected to the flame sensor (AO pin)

void setup() {
  Serial.begin(9600);  // Initialize serial communication for XBee or USB serial
  pinMode(flameSensorPin, INPUT);   // Set analog pin as input

  delay(2000);  // Allow initialization time
  Serial.println("Arduino initialized");  // Notify Raspberry Pi
} 

void loop() {
  // Read the analog value from the flame sensor (IR light intensity)
  int irLightValue = analogRead(flameSensorPin);

  // Send the infrared light intensity value to the Raspberry Pi
  Serial.print("IR Light Intensity: ");
  Serial.println(irLightValue); // Send the raw analog value (0-1023)

  // Optionally, listen for any response from the Raspberry Pi
  if (Serial.available() > 0) {
    String response = Serial.readStringUntil('\n');  // Read until newline
    response.trim(); // Remove any extra spaces or newline characters

    Serial.print("Received from Pi: "); // Debugging line to print the incoming data
    Serial.println(response); // Print the raw response
    // Check if the response is "OK" from Raspberry Pi
    if (response == "ok") {
        Serial.println("Received 'OK' from Raspberry Pi.");  // Print OK when received
    } else {
        Serial.print("Received response: ");
        Serial.println(response);  // Print any other response
    }
  }


  delay(1000);  // Wait before the next iteration (adjustable for speed)
}
