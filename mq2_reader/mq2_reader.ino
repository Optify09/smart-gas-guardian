/*
  Citire senzor de gaz MQ-2 (modul "Flying Fish") pe ESP32
  --------------------------------------------------------


  Cum incarci codul:
  1. Deschizi Arduino IDE
  2. Tools > Board > selectezi placa ta ESP32 (ex. "ESP32 Dev Module")
  3. Tools > Port > selectezi portul USB unde e conectat ESP32
  4. Apesi butonul de Upload (sageata din stanga sus)
  5. Deschizi Serial Monitor (lupa din dreapta sus), setat la 115200 baud
*/

// "const int" = o valoare fixa, care nu se schimba niciodata in program.
// GPIO34 e un pin analog pe ESP32, bun pentru citit senzori (nu are iesire digitala, doar intrare - perfect pentru A0 de la MQ-2)

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include "secrets.h"

const int MQ2_PIN = 34;
const int DHT_PIN = 32;
DHT dht(DHT_PIN, DHT11);

// Timpul de incalzire (warm-up) al senzorului, in milisecunde.
// MQ-2 are nevoie de acest timp ca sa se stabilizeze dupa pornire (are un mic element de incalzire in interior).
// 1000UL * 60 * 2 = 1000 (o secunda in milisecunde) * 60 (secunde/minut) * 2 (minute) = 2 minute in milisecunde.
// "UL" inseamna "unsigned long" - un tip de numar intreg mare, fara semn, folosit pentru timp (millis() foloseste acelasi tip)
const unsigned long WARMUP_TIME_MS = 1000UL * 60 * 2;

// O variabila care retine "la ce moment a pornit programul", ca sa stim cat timp a trecut.
// O declaram goala acum (0), o completam in setup()
unsigned long startTime = 0;

// O variabila care tine minte daca am terminat deja warm-up-ul,
// ca sa nu tot printam mesajul de "inca ma incalzesc" la infinit dupa ce s-a terminat
bool warmupDone = false;


// setup() ruleaza O SINGURA DATA, cand placa porneste sau se reseteaza
void setup() {
  // Pornim comunicarea seriala (USB) la 115200 biti/secunda,
  // ca sa putem vedea mesaje in Serial Monitor pe calculator
  Serial.begin(115200);

  // Ne conectam la WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD); //porneste conectarea
  
  while(WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.print("Conectat! IP local: ");
  Serial.println(WiFi.localIP());

  // pinMode() spune placii cum sa foloseasca un pin.
  // INPUT = citim un semnal (nu trimitem noi curent pe acel pin)
  pinMode(MQ2_PIN, INPUT);
  dht.begin(); // similar cu pinMode, e deja inclusa in librarie prin aceasta functie initializarea pinului ca fiind pin de citire

  // Salvam momentul de pornire. millis() = cate milisecunde au trecut
  // de cand placa a pornit (se reseteaza la 0 la fiecare pornire/upload nou)
  startTime = millis();

  // Afisam un mesaj in Serial Monitor, ca sa stim ca programul a pornit
  Serial.println("Senzor MQ-2 initializat.");
  Serial.println("Incepe perioada de warm-up (2 minute)...");
}


// loop() ruleaza LA NESFARSIT, in mod repetat, atat timp cat placa e alimentata
void loop() {

  // Calculam cat timp a trecut de la pornire pana acum.
  // millis() = timpul curent; startTime = timpul de la pornire; diferenta = cat timp a trecut
  unsigned long elapsed = millis() - startTime;

  // Verificam daca suntem INCA in perioada de warm-up
  if (elapsed < WARMUP_TIME_MS) {

    // Daca nu am anuntat deja, afisam cate secunde au mai ramas pana se termina warm-up-ul.
    // "/" imparte, "1000" transforma milisecunde in secunde
    Serial.print("Warm-up in curs... secunde ramase: ");
    Serial.println((WARMUP_TIME_MS - elapsed) / 1000);

    // Asteptam 5 secunde inainte de a verifica din nou,
    // ca sa nu umplem Serial Monitor cu mesaje la fiecare fractiune de secunda
    delay(5000);

    // "return" opreste executia lui loop() aici si sare direct la urmatoarea rulare a loop().
    // Practic: cat timp suntem in warm-up, nu citim inca valori reale de gaz
    return;
  }

  // Daca ajungem aici, inseamna ca warm-up-ul s-a terminat.
  // Verificam daca am afisat deja mesajul de "warm-up terminat" (o singura data)
  if (!warmupDone) {
    Serial.println("Warm-up terminat! Incepem citirile reale.");
    warmupDone = true;  // marcam ca am afisat deja, sa nu repetam mesajul
  }

  // analogRead() citeste valoarea de pe pinul analog.
  // Pe ESP32, valoarea returnata e intre 0 si 4095 (rezolutie 12 biti),
  // spre deosebire de Arduino Uno clasic unde e 0-1023 (10 biti) - important daca urmezi tutoriale vechi
  int gasValue = analogRead(MQ2_PIN);
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  String jsonPayload = "{\"gas_value\": " + String(gasValue) + ", " + "\"temperature\": " + String(temperature) + ", " + "\"humidity\": " + String(humidity) +  "}";
  Serial.println(jsonPayload);

  // TRIMITEREA PRIN HTTP
  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  int httpResponseCode = http.POST(jsonPayload);
  if (httpResponseCode > 0)
  {
    Serial.print("Raspuns server, cod: ");
    Serial.println(httpResponseCode);
  }
  else
  {
    Serial.print("Eroare la trimitere! Cod: ");
    Serial.println(httpResponseCode);
  }
  http.end();

  // Afisam valoarea citita in Serial Monitor, cu un text explicativ
  Serial.print("Valoare gaz (raw): ");
  Serial.println(gasValue);

  // Asteptam 2 secunde inainte de urmatoarea citire.
  // Nu vrem sa citim de mii de ori pe secunda - e inutil de des pentru un senzor de gaz din mediu ambiental
  delay(2000);
}
