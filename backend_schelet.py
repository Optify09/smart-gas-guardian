from flask import Flask, request
import sqlite3
from datetime import datetime
import pandas as pd 
import numpy as np
from sklearn.ensemble import IsolationForest
import threading
import time

app = Flask(__name__)
DB_NAME = "readings.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # TODO 1: scrie aici comanda SQL care creeaza tabelul "readings", daca nu exista deja
    cursor.execute(""" CREATE TABLE IF NOT EXISTS readings(
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    timestamp TEXT, 
    gas_value INTEGER) """)
    # Adaugam COLOANE pentru Temperatura si Umiditate
    try:
        cursor.execute("ALTER TABLE readings ADD COLUMN temperature REAL")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE readings ADD COLUMN humidity REAL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE readings ADD COLUMN anomaly_score REAL")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE readings ADD COLUMN is_anomaly INTEGER")
    except sqlite3.OperationalError:
        pass


    conn.commit()
    conn.close()

init_db()

def train_model():
    conn = sqlite3.connect("readings.db")
    df = pd.read_sql_query("SELECT * FROM readings WHERE timestamp >= '2026-08-10T14:56:00'", conn)
    conn.close()

    df["timestamp"] = pd.to_datetime(df["timestamp"], format = "mixed")
    df["hour"] = df["timestamp"].dt.hour
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["rolling_mean"] = df["gas_value"].rolling(window = 150).mean()
    # La fiecare citire se deschide un sub-tabel care cotine valoarea
    # curenta si cele 149 de citire de dinainte de el si se face
    # media mobila (.mean()) a acestor 150 de randuri (~ 5 minute) pentru a
    # vedea media ultimelor 5 minute a valorilor de gaz
    df["rolling_std"] = df["gas_value"].rolling(window = 150).std()
    # La fiecare citire se deschide un sub-tabel care cotine valoarea
    # curenta si cele 149 de citire de dinainte de el si se face
    # si se verifica cat de volatile au fost valorile in 
    # ultimele 5 minute prin functia .std() 
    df["deviation"] = (df["gas_value"] - df["rolling_mean"]) / df["rolling_std"]
    df["day_of_week"] = df["timestamp"].dt.dayofweek

    df_clean = df.dropna(subset = ["rolling_mean", "rolling_std"])
    features = ["deviation"]
    X = df_clean[features]

    # Antrenarea MODELULUI

    model = IsolationForest(n_estimators = 100, contamination = 0.03, random_state = 42)
    model.fit(X)

    return model

model = train_model()

def reantreneaza_periodic():
    global model # accesam variabila 'model' declarata global inainte
    while True:
        time.sleep(3600)
        print("Reantrenare model...")
        model = train_model()
        print("Model antrenat!")
thread = threading.Thread(target = reantreneaza_periodic, daemon = True)
thread.start()

@app.route("/readings", methods=["POST"])
def receive_reading():
    # TODO 2: preia gas_value din corpul cererii (JSON), 
    # salveaza-l in baza de date impreuna cu timestamp-ul curent
    data = request.get_json()
    gas_value = data["gas_value"]
    temperature = data["temperature"]
    humidity = data["humidity"]
    timestamp = datetime.now().isoformat()
    now = datetime.now()
    hour = now.hour
    hour_sin = np.sin(2 * np.pi * hour / 24)
    hour_cos = np.cos(2 * np.pi * hour / 24)
    day_of_week = now.weekday()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT gas_value FROM readings ORDER BY id DESC LIMIT 149")
    ultimele_valori = [row[0] for row in cursor.fetchall()]
    fereastra = ultimele_valori + [gas_value]
    rolling_mean = pd.Series(fereastra).mean()
    rolling_std = pd.Series(fereastra).std()
    deviation = (gas_value - rolling_mean) / rolling_std
    X = pd.DataFrame([[deviation]],columns=["deviation"])
    anomaly_score = model.decision_function(X)[0]
    is_anomaly = 1 if model.predict(X)[0] == -1 else 0
                      

    cursor.execute("INSERT INTO readings (gas_value, timestamp, temperature, humidity, anomaly_score, is_anomaly) VALUES (?, ?, ?, ?, ?,?)",
    (gas_value, timestamp, temperature, humidity, anomaly_score, is_anomaly))
    conn.commit()
    conn.close()
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)