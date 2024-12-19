#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <Adafruit_BMP085.h>

#define TCAADDR 0x70

// Dont use wifi that has 5G only use the 2.4GHz
const char* ssid = "spikatech";      
const char* password = "51343651"; 

Adafruit_BMP085 bmp1;
Adafruit_BMP085 bmp2;
Adafruit_BMP085 bmp3;  
Adafruit_BMP085 bmp4;

WiFiServer server(80);  // Create an HTTP server on port 80

void tcaselect(uint8_t i) {
  if (i > 7) return;

  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission();
  delay(10);  // Delay to allow sensor to settle
}

void setup(void) {
  Serial.begin(9600);
  Wire.begin(21, 22);  // Initialize I2C with ESP32's default SDA (GPIO21) and SCL (GPIO22)
  
  // Connect to WiFi
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  
  // Start the HTTP server
  server.begin();

  Serial.println("Initializing sensors...");

  /* Initialize sensors */
  tcaselect(7);
  if (!bmp1.begin()) {
    Serial.println("Ooops, no BMP1 detected ... Check your wiring!!!");
    while (1);
  }
  tcaselect(4);
  if (!bmp2.begin()) {
    Serial.println("Ooops, no BMP2 detected ... Check your wiring!");
    while (1);
  }
  tcaselect(2);
  if (!bmp3.begin()) {
    Serial.println("Ooops, no BMP3 detected ... Check your wiring!");
    while (1);
  }
  tcaselect(1);
  if (!bmp4.begin()) {
    Serial.println("Ooops, no BMP4 detected ... Check your wiring!");
    while (1);
  }

  Serial.println("Sensors initialized successfully.");
}

void loop() {
  // Wait for a client to connect
  WiFiClient client = server.available();
  if (!client) {
    return;
  }

  Serial.println("Client connected!");
  while (client.connected()) {
    if (client.available()) {
      String request = client.readStringUntil('\r');  // Read the request
      Serial.println(request);
      client.flush();

      // Start HTTP response header
      String response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n";

      // Collect data for 4 sensors and send them in one line
      String line = "";
      for (int i = 0; i < 4; i++) {
        if (i == 0) tcaselect(7);
        else if (i == 1) tcaselect(4);
        else if (i == 2) tcaselect(2);
        else tcaselect(1);
        
        // Read and format the pressure value
        unsigned long pressure = 0;
        if (i == 0) pressure = bmp1.readPressure();
        else if (i == 1) pressure = bmp2.readPressure();
        else if (i == 2) pressure = bmp3.readPressure();
        else pressure = bmp4.readPressure();
        
        unsigned long roundedPressure = (pressure + 50) / 10;  // Round to nearest value with 3 digits
        line += String(roundedPressure);
        if (i < 3) line += " ";  // Add space between values
      }

      // Send the response
      client.print(response + line + "\n"); // Add newline after each row

      // Also print the same data to the Serial Monitor
      Serial.println(line);
      
      break;  // Exit after responding
    }
  }
  client.stop();
  Serial.println("Client disconnected.");
}
