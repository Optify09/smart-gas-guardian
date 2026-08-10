#include <DHT.h>
const int DHT_PIN = 32;
DHT dht(DHT_PIN, DHT11);
void setup() {
  Serial.begin(115250);
  dht.begin();
}

void loop() {
  float umiditate = dht.readHumidity();
  float temperatura = dht.readTemperature();
  Serial.print("Umiditate: ");
  Serial.print(umiditate);
  Serial.print("%  Temperatura: ");
  Serial.print(temperatura);
  Serial.print("*C");
  Serial.println();
  delay(2000);
}
