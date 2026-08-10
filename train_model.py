import sqlite3
import pandas as pd
from sklearn.ensemble import IsolationForest

conn = sqlite3.connect("readings.db")
df = pd.read_sql_query("SELECT * FROM readings", conn)
conn.close()

df["timestamp"] = pd.to_datetime(df["timestamp"], format = "mixed")
df["hour"] = df["timestamp"].dt.hour
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
df["day_of_week"] = df["timestamp"].dt.dayofweek

# print(df.shape)
# print(df.head())
# print(df.tail())
# print(df[["gas_value", "rolling_mean", "rolling_std"]].tail(10))

df_clean = df.dropna(subset = ["rolling_mean", "rolling_std"])
features = ["gas_value", "hour", "day_of_week", "rolling_mean", "rolling_std"]
X = df_clean[features]

# print(X.shape)
# print(X.head())

# Antrenarea MODELULUI

model = IsolationForest(n_estimators = 100, contamination = 0.03, random_state = 42)
model.fit(X)
print("Model antrenat!")

df_clean["anomaly"] = model.predict(X)
df_clean["anomaly_score"] = model.decision_function(X)

print(df_clean["anomaly"].value_counts())

# test_bricheta = df_clean[(df_clean["timestamp"] >= "2026-07-19 17:51:50") & (df_clean["timestamp"] <= "2026-07-19 17:52:30")]
# print(test_bricheta[["timestamp", "gas_value", "rolling_std", "anomaly", "anomaly_score"]])

test_tocanita = df_clean[(df_clean["timestamp"] >= "2026-07-20 12:55:00") & (df_clean["timestamp"] <= "2026-07-20 13:10:00")]
print(test_tocanita[["timestamp", "gas_value", "rolling_mean", "rolling_std", "anomaly", "anomaly_score"]])

