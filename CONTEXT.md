# Smart Gas Guardian — CONTEXT

Document de handoff pentru proiectul de detecție a anomaliilor de gaz în bucătărie.
Citește-l primul când reiei lucrul sau când aduci pe cineva nou în echipă.

---

## 1. Ce este proiectul

Sistem de detecție a anomaliilor pentru scurgeri de gaz în bucătărie, gândit ca proiect de portofoliu.

Ideea centrală: în loc de un prag fix ("alarmă dacă valoarea trece de X"), sistemul **învață singur cum arată aerul normal** din bucătărie și semnalează abaterile. Așa se adaptează la specificul locului — gătit, aerisire, sezon — fără să fie recalibrat manual.

Lanțul complet: **senzor → ESP32 → WiFi → backend Flask → SQLite → model de anomalii → alertă.**

---

## 2. Hardware

| Componentă | Detalii |
|---|---|
| Microcontroler | ESP32 |
| Senzor | MQ-2 (modul Flying Fish) |
| Pin de citire | **GPIO34** — pin analog, input-only |

**Comportament măsurat:**

- baseline în aer curat: **~580–595**
- vârf la apropierea unei surse de gaz: **~2600+**

Diferența e mare și clară, ceea ce face detecția ușoară. Nu e nevoie de filtrare complicată a semnalului.

**De reținut despre MQ-2:**

- are nevoie de **~2 minute de warm-up** după alimentare; citirile din acest interval nu sunt valide și trebuie ignorate sau marcate distinct în interfață;
- e sensibil la LPG, propan, butan, fum — nu doar la un singur gaz;
- LPG-ul e mai greu decât aerul, deci **senzorul se montează jos**, nu în tavan ca detectoarele de fum.

---

## 3. Backend

- **Framework:** Flask
- **Bază de date:** SQLite (`readings` — conține datele de senzor colectate; ~64 MB la ultima salvare)
- **Adresă:** IP local al laptopului, port `5000`. Rețea Wi-Fi: `DIGI-32KH`. La 5 sept. 2026
  laptopul era `192.168.1.130` (subnet `192.168.1.x`; înainte de reset era `192.168.100.x`).
  **IP-ul e DHCP** — dacă ESP32 nu mai trimite date, verifică `ipconfig` vs `SERVER_URL` din
  `mq2_reader/secrets.h`. De pus rezervare DHCP pe router ca să fie fix.
- **Endpoint existent:** `POST /readings` — ESP32-ul trimite aici citirile
- **Pornire:** `.\venv\Scripts\python.exe backend_schelet.py` (PowerShell 5.1 nu are `&&`, folosește `;`).
  La prima pornire, Windows Firewall cere permisiune → Allow, altfel ESP32 nu ajunge la `:5000`.

**Fișiere principale:**

- `backend_schelet.py` — scheletul serverului Flask
- `train_model.py` — antrenarea modelului de anomalii
- `dashboard.py` — început de dashboard
- `mq2_reader/mq2_reader.ino` — sketch-ul ESP32 care citește senzorul și trimite datele
- `test_dht11/` — test separat, senzor de temperatură/umiditate

---

## 4. Modelul de anomalii

**Isolation Forest** — învățare **nesupervizată**.

De ce nesupervizat: nu ai (și nu vrei să produci) un set de date etichetat cu scurgeri reale de gaz. Modelul învață doar din date normale și marchează ca anomalie orice se abate de la tipar.

Cum funcționează, pe scurt: construiește arbori de decizie care taie datele la întâmplare. Punctele atipice se izolează după puține tăieturi, cele normale au nevoie de multe. Adâncimea medie de izolare devine scorul de anomalie.

**Atenție la reinstalare:** modelul serializat depinde de versiunea de scikit-learn. Dacă recreezi mediul cu altă versiune, s-ar putea să nu se mai încarce — vezi secțiunea 7.

---

## 5. Stadiu actual

**Făcut:**

- testarea hardware, cu rezultate bune și repetabile
- colectarea datelor de baseline în SQLite
- scheletul backend-ului Flask cu endpoint-ul de recepție
- antrenarea modelului Isolation Forest

**De făcut mai departe:**

- dashboard în **Streamlit** pentru vizualizare
- un strat de **API Claude** peste sistem
- endpoint-urile suplimentare din secțiunea 6

---

## 6. Extensie planificată — aplicație Android (PPA/POOJA)

Mini-proiect pentru opționalul PPA, anul 2 semestrul 2, ETTI. **Nu a fost începută.** Proiect de echipă — trebuie împărțit lucrul și confirmată tema cu profesorul în primele două săptămâni.

Aplicația ar fi **al doilea client** al backend-ului Flask existent; ESP32-ul rămâne producătorul de date.

### Ecrane

**Dashboard** — valoarea curentă, starea (Normal / Atenție / Alertă), grafic pe ultimele 30–60 min cu anomaliile marcate distinct, indicator de warm-up MQ-2 (~2 min) și stare senzor online/offline.

**Istoric** — lista evenimentelor-anomalii în RecyclerView, filtre 24h / săptămână, export CSV.

**Setări / Control** — prag manual, mod de alertare (prag / model / ambele), calibrare baseline, test buzzer, silențiere 10 minute, adresa serverului și intervalul de polling.

### Notificări

Canal separat cu categoria **ALARM**, ca să sune chiar dacă telefonul e pe notificări silențioase. Acțiuni „Silențiază" și „Deschide" direct în notificare. Implementare cu WorkManager sau ForegroundService.

### Endpoint-uri de adăugat în Flask

```
GET  /latest
GET  /readings?since=
GET  /events?limit=
GET  /health
POST /config      # prag, calibrare, silențiere — citite de ESP32 la următorul ciclu
```

### Plan tehnic

- polling la 3–5 s pentru prototipul minimal, apoi FCM sau MQTT ca upgrade
- **Room** pentru cache local și funcționare offline
- **MPAndroidChart** pentru grafic

### Problemă de rezolvat înainte de demo

Backend-ul e pe IP local (`192.168.100.12:5000`), deci nu e accesibil din afara rețelei. Soluții: tunel (Cloudflare Tunnel sau ngrok), sau hotspot propriu la prezentare.

### Momentul-cheie de prezentare

Alertă live pe telefon în ~2 secunde de la apropierea unei brichete de senzor. Ăsta e demo-ul care vinde proiectul — restul e context.

---

## 7. Reconstruirea mediului după reinstalarea sistemului

Folderul `venv` **nu este portabil** — conține căi absolute către instalarea veche de Python. Se recreează:

```powershell
# 1. Instalează Python 3.14 (nu vine cu `py`/`python` în PATH; doar stub-ul WindowsApps)
winget install --id Python.Python.3.14 --scope user
# ajunge la: C:\Users\elect\AppData\Local\Programs\Python\Python314\python.exe

# 2. Recreează venv folosind calea completă către python
& "C:\Users\elect\AppData\Local\Programs\Python\Python314\python.exe" -m venv venv
.\venv\Scripts\Activate.ps1
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Dacă `requirements.txt` lipsește, pachetele necesare sunt, în principiu: `flask`, `scikit-learn`, `pandas`, `numpy`, iar pentru dashboard `streamlit`.

**Note din reconstruirea din 5 sept. 2026 (după reset total de laptop):**

- Proiectul s-a mutat din `...\OneDrive\Documents\Proiecte Esp32 - Acasa\Smart-Gas-Guardian` în `C:\Users\elect\Projects\esp32\Smart-Gas-Guardian`. `venv/pyvenv.cfg` mai conține calea veche pe linia `command` — pur cosmetic.
- `requirements.txt` era salvat în **UTF-16 LE**, ceea ce spărgea `pip install -r`. A fost convertit în UTF-8. Dacă îl regenerezi cu `pip freeze > requirements.txt` din PowerShell, forțează UTF-8: `pip freeze | Out-File -Encoding utf8 requirements.txt`.
- Niciun model nu se serializează pe disc: `backend_schelet.py` antrenează în memorie la pornire (și reantrenează orar), iar `train_model.py` e doar script de **evaluare** walk-forward. Deci nu există fișier `.pkl` de reîncărcat — grija despre versiunea de scikit-learn contează doar dacă rezultatele diferă, nu pentru încărcare.

### 7.1 Unelte (reinstalate 5 sept. 2026)

```powershell
winget install --id Git.Git --scope user                    # deja era prezent (2.55.0)
winget install --id Microsoft.VisualStudioCode --scope user
winget install --id ArduinoSA.IDE.stable                     # Arduino IDE 2.3.x
winget install --id ArduinoSA.CLI                            # arduino-cli, pt. setup headless
```

- **VS Code:** extensia `ms-python.python` instalată (aduce Pylance + debugpy). `code` e la
  `C:\Users\elect\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd` (poate să nu fie în PATH până la un logout).
- **arduino-cli** (`C:\Program Files\Arduino CLI\arduino-cli.exe`) configurat cu:
  - URL board manager: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
  - core `esp32:esp32@3.3.11` instalat
  - librării: `DHT sensor library@1.4.7` + `Adafruit Unified Sensor@1.1.15`
- **Test compilare OK:** `arduino-cli compile --fqbn esp32:esp32:esp32 mq2_reader` → 78% flash, fără erori.
  (FQBN `esp32:esp32:esp32` = placa „ESP32 Dev Module".)
- **Driver USB-serial:** la conectarea ESP32, dacă nu apare niciun port COM, instalează driverul
  CP210x (Silicon Labs) sau CH340, în funcție de cip. Necunoscut până se conectează placa.

---

## 8. De reținut

- Baza de date `readings.db` (~64 MB) este cea mai valoroasă piesă a proiectului. Reprezintă ore de colectare și e fundamentul modelului. Ține-o mereu în două locuri. Backup curent: `C:\Users\elect\OneDrive\Backups\Smart-Gas-Guardian\readings-<data>.db`.
- Sketch-ul ESP32 conține SSID-ul și parola de WiFi. **Scoate-le într-un fișier separat, trecut în `.gitignore`, înainte de primul commit pe GitHub.**
- Warm-up-ul de 2 minute al senzorului trebuie tratat explicit în UI, altfel primele citiri par anomalii.

## 9. Python Version

`3.14.7` (recreat 5 sept. 2026; inițial `3.14.0`). Instalat cu `winget install --id Python.Python.3.14 --scope user`.
