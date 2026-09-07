import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

conn = sqlite3.connect("readings.db")
df = pd.read_sql_query("SELECT * FROM readings WHERE timestamp >= '2026-08-10T14:56:00'", conn)
df = df[(df["temperature"]>0) & (df["humidity"]>0)]
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
df["deviation"] = (df["gas_value"] - df["rolling_mean"])/df["rolling_std"]
df["day_of_week"] = df["timestamp"].dt.dayofweek

# print(df.shape)
# print(df.head())
# print(df.tail())
# print(df[["gas_value", "rolling_mean", "rolling_std"]].tail(10))

df_clean = df.dropna(subset = ["rolling_mean", "rolling_std"])
features = ["deviation"]
X = df_clean[features]
test_size = 1700
n_ferestre = 5
rate_anomalii = []
# print(X.shape)
# print(X.head())

# Antrenarea MODELULUI

for i in range(n_ferestre):
    cutoff = len(X) - test_size * (n_ferestre - i)
    X_train_i = X.iloc[0:cutoff]
    X_test_i = X.iloc[cutoff: cutoff+test_size]
    model_i = IsolationForest(n_estimators = 100, contamination = 0.03, random_state = 42)
    model_i.fit(X_train_i)
    predictii_i = model_i.predict(X_test_i)
    rata = (predictii_i==-1).mean()
    rate_anomalii.append(rata)
    print("Fereastra", i+1, ":", round(rata*100, 2), "% anomalii")

print("Medie peste toate ferestrele: ", round(sum(rate_anomalii)/len(rate_anomalii)*100, 2), "%")

# test_bricheta = df_clean[(df_clean["timestamp"] >= "2026-07-19 17:51:50") & (df_clean["timestamp"] <= "2026-07-19 17:52:30")]
# print(test_bricheta[["timestamp", "gas_value", "rolling_std", "anomaly", "anomaly_score"]])

#test_tocanita = df_clean[(df_clean["timestamp"] >= "2026-07-20 12:55:00") & (df_clean["timestamp"] <= "2026-07-20 13:10:00")]
#print(test_tocanita[["timestamp", "gas_value", "rolling_mean", "rolling_std", "anomaly", "anomaly_score"]])

