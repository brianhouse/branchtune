#include <ESP8266WiFi.h>
#include <WiFiUDP.h>
#include <Adafruit_MMA8451.h>
#include <Adafruit_Sensor.h>

const char* ssid     = "treehouse";
const char* password = "10happysquirrels";
const char* host     = "192.168.1.6";
const int port      = 23232;
unsigned long seconds;

WiFiUDP Udp;
Adafruit_MMA8451 mma = Adafruit_MMA8451();

void setup() {
  Serial.begin(115200);
  delay(10);

  mma.begin();
  mma.setRange(MMA8451_RANGE_2_G);

  pinMode(0, OUTPUT);
  
  connectToWifi();
}

void loop() {
  seconds = millis() / 1000;
  if (seconds % 10 == 0) {
    pinMode(0, LOW);  
  } else if ((seconds + 1) % 10 == 0) {
    pinMode(0, HIGH);  
  }
  mma.read();
  sensors_event_t event; 
  mma.getEvent(&event);
  Udp.beginPacket(host, port);
  String dataString = String(event.acceleration.x, 8) + "," + String(event.acceleration.y, 8) + "," + String(event.acceleration.z, 8) + "," + String(WiFi.RSSI());
  char dataBuf[dataString.length()+1];
  dataString.toCharArray(dataBuf, dataString.length()+1);
  Udp.write(dataBuf);// + event.acceleration.y + "," + event.acceleration.z);
  Udp.endPacket();
  delay(12);
}

void connectToWifi() {
  while (WiFi.status() != WL_CONNECTED) {
    Serial.println();
    Serial.println();
    Serial.print("Attempting to connect to: ");
    Serial.println(ssid);
    WiFi.begin(ssid, password);
    int tries = 0;
    while (tries < 20 && WiFi.status() != WL_CONNECTED) {
      digitalWrite(0, HIGH);
      delay(250);
      digitalWrite(0, LOW);
      delay(250);      
      Serial.print(".");
      tries++;
    }
    if (WiFi.status() != WL_CONNECTED) {
      WiFi.disconnect();
      tries = 0;
      while (tries < 20) {
        digitalWrite(0, HIGH);
        delay(250);
        digitalWrite(0, LOW);
        delay(250);
        tries++;
      }
    }
  }
  Serial.println();
  Serial.println("Connected to wifi");
  printWifiStatus();
}

void printWifiStatus() {
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
  long rssi = WiFi.RSSI();
  Serial.print("Signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}


// blinks at 2hz if not connected
// blink once every 5 seconds if we're good

// todo: wifi status updates

