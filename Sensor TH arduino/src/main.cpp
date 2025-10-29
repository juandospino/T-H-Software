#include <Arduino.h>
#include <SPI.h>
#include <Wire.h> 
#include <RF24.h>
#include <RF24Network.h>
#include <DHT.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>

#define DHTPIN 2
#define DHTTYPE DHT22
#define Alto 32
#define Ancho 128

RF24 radio(8, 9); // CE, CSN
RF24Network network(radio);

Adafruit_SSD1306 pantalla(Ancho, Alto, &Wire, -1); // Pantalla

DHT dht(DHTPIN, DHTTYPE); // Sensor DHT22

// Estructura de datos
struct Data {
  float temperature;
  float humidity;
};

Data sensores[4];

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // Esperar conexión serial
  }

  Wire.begin();
  
  pantalla.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  pantalla.clearDisplay();
  pantalla.setTextSize(1);
  pantalla.setTextColor(SSD1306_WHITE);
  pantalla.setCursor(5, 5);
  pantalla.cp437(true);

  dht.begin();

  SPI.begin();
  
  if (radio.begin()) {
    Serial.println(F("NRF24L01 iniciado"));
    radio.setPALevel(RF24_PA_HIGH);
    radio.setDataRate(RF24_250KBPS);
    network.begin(90, 00);
  } else {
    Serial.println(F("Error NRF24L01"));
  }

  delay(1000);
  Serial.println("🚀 ARDUINO LISTO - ENVIANDO DATOS...");
}

void loop() {
  network.update();

  // Leer datos locales
  sensores[0].temperature = dht.readTemperature();
  sensores[0].humidity = dht.readHumidity();
  
  // Inicializar datos de esclavos
  for (int n = 1; n <= 3; n++) {
    sensores[n].temperature = 0;
    sensores[n].humidity = 0;
  }

  // Recibir datos de los esclavos
  while (network.available()) {
    RF24NetworkHeader header;
    Data payload;
    network.read(header, &payload, sizeof(payload));
    
    uint16_t node = header.from_node;
    if (node >= 1 && node <= 3) {
      sensores[node] = payload;
    }
  }

  // ✅ ENVIAR DATOS PARA PYTHON
  for (int i = 0; i < 4; i++) {
    if (!isnan(sensores[i].temperature) && !isnan(sensores[i].humidity)) {
      Serial.print(i);                    // ID
      Serial.print(",");
      Serial.print(sensores[i].temperature, 1);  // Temperatura
      Serial.print(",");
      Serial.print(sensores[i].humidity, 1);     // Humedad
      Serial.print(",");
      Serial.println(millis());           // Tiempo
    }
  }

  // Pantalla 
  pantalla.clearDisplay();
  pantalla.setCursor(0, 0);
  
  static int display_index = 0;
  
  if (display_index == 0) {
    pantalla.println(F("Local Data"));
  } else {
    pantalla.print(F("Sensor "));
    pantalla.println(display_index);
  }

  pantalla.print(F("Temp: "));
  pantalla.print(sensores[display_index].temperature, 1);
  pantalla.write(248);
  pantalla.println(F("C"));

  pantalla.print(F("Hum: "));
  pantalla.print(sensores[display_index].humidity, 1);
  pantalla.println(F(" %"));
  
  pantalla.display();
  
  display_index = (display_index + 1) % 4;

  delay(2000);
}