#include <Arduino.h>
#include <SPI.h>
#include <RF24.h>
#include <RF24Network.h>
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT22

#define NODE_ID 02
#define MASTER_NODE 00

RF24 radio(8, 9);   
RF24Network network(radio);

DHT dht(DHTPIN, DHTTYPE);


struct Data {
  float temperature;
  float humidity;
};

void setup() {
  Serial.begin(9600);
  while (!Serial) {}

  dht.begin();
  SPI.begin();

  if (radio.begin()) {
    Serial.println(F("NRF24L01 iniciado"));
    radio.setPALevel(RF24_PA_HIGH);
    radio.setDataRate(RF24_250KBPS);
    network.begin(90, NODE_ID);
  } else {
    Serial.println(F("Error NRF24L01"));
  }

  delay(1000);
  Serial.print("NODO SENSOR ");
  Serial.print(NODE_ID);
  Serial.println(" LISTO");
}

void loop() {
  network.update();

  Data payload;
  payload.temperature = dht.readTemperature();
  payload.humidity    = dht.readHumidity();

  if (isnan(payload.temperature) || isnan(payload.humidity)) {
    Serial.println("Error leyendo DHT");
    delay(2000);
    return;
  }

  RF24NetworkHeader header(MASTER_NODE);
  bool ok = network.write(header, &payload, sizeof(payload));

  if (ok) {
    Serial.print("Enviado → T: ");
    Serial.print(payload.temperature, 1);
    Serial.print(" °C  H: ");
    Serial.print(payload.humidity, 1);
    Serial.println(" %");
  } else {
    Serial.println("❌ Fallo envío");
  }

  delay(2000);
}


