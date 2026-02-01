#include <Arduino.h>
#include <SPI.h>
#include <RF24.h>
#include <RF24Network.h>
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT22

RF24 radio(8, 9); // CE, CSN
RF24Network network(radio);

DHT dht(DHTPIN, DHTTYPE);

// Estructura de datos
struct Data {
  float temperature;
  float humidity;
};

Data sensores[4];

void setup() {
  Serial.begin(9600);
  while (!Serial) {;}

  dht.begin();
  SPI.begin();

  if (radio.begin()) {
    Serial.println(F("NRF24L01 iniciado"));
    radio.setPALevel(RF24_PA_HIGH);
    radio.setDataRate(RF24_250KBPS);
    network.begin(90, 00); // nodo maestro
  } else {
    Serial.println(F("Error NRF24L01"));
  }

  delay(1000);
  Serial.println("ARDUINO LISTO - ENVIANDO DATOS");
}

void loop() {
  network.update();

  // Sensor local
  sensores[0].temperature = dht.readTemperature();
  sensores[0].humidity = dht.readHumidity();

  // Inicializar sensores remotos
  for (int n = 1; n <= 3; n++) {
    sensores[n].temperature = NAN;
    sensores[n].humidity = NAN;
  }

  // Recibir datos
  while (network.available()) {
    RF24NetworkHeader header;
    Data payload;
    network.read(header, &payload, sizeof(payload));

    uint16_t node = header.from_node;
    if (node >= 1 && node <= 3) {
      sensores[node] = payload;
    }
  }

  // 📤 ENVÍO PARA PYTHON (CSV)
  for (int i = 0; i < 4; i++) {
    if (!isnan(sensores[i].temperature) && !isnan(sensores[i].humidity)) {
      Serial.print(i);                       // ID
      Serial.print(",");
      Serial.print(sensores[i].temperature, 1);
      Serial.print(",");
      Serial.print(sensores[i].humidity, 1);
      Serial.print(",");
      Serial.println(millis());              // timestamp
    }
  }

  delay(2000);
}
