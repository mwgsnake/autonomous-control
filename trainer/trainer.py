import pandas as pd
import numpy as np
import tensorflow as tf
import os
import time
import re
import json
from sklearn.preprocessing import MinMaxScaler

LOGFILE = "/logs/access.log"
MODEL_PATH = "/model/autoencoder_model.h5"
THRESHOLD_PATH = "/model/autoencoder_threshold.json"
TRAINING_TRIGGER = "/shared/training_mode"
SCALER_PATH = "/model/autoencoder_scaler.pkl"

def extract_features(logfile_path):
    pattern = re.compile(
        r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) \S+" (?P<status>\d+) (?P<size>\d+)'
    )
    data = []
    # Mapping nach deinen echten Logdaten!
    url_map = {
        '/': 0,
        '/index.html': 1,
        '/about': 2,
        '/contact': 3,
        '/help': 4,
        '/favicon.ico': 5,
        '/static/logo.png': 6,
        '/static/style.css': 7
    }
    try:
        with open(logfile_path) as f:
            lines = f.readlines()
            for line in lines:
                m = pattern.search(line)
                if m:
                    entry = m.groupdict()
                    entry['method_num'] = 0 if entry['method'] == 'GET' else 1
                    entry['url_num'] = url_map.get(entry['url'], 99)
                    entry['status'] = int(entry['status'])
                    entry['size'] = int(entry['size'])
                    data.append(entry)
    except Exception as e:
        print(f"Fehler beim Lesen des Logfiles: {e}")
        return pd.DataFrame()
    df = pd.DataFrame(data)
    return df

def safe_model_save(model, path, retries=5, delay=2):
    for i in range(retries):
        try:
            model.save(path)
            return
        except BlockingIOError:
            print(f"Speichern blockiert, versuche erneut ({i+1}/{retries}) ...")
            time.sleep(delay)
    raise RuntimeError("Konnte Modell nach mehreren Versuchen nicht speichern!")

def train_and_save_model():
    print("Starte Training ...")
    df = extract_features(LOGFILE)
    if df.empty:
        print("Keine Trainingsdaten gefunden. Training übersprungen.")
        return False
    feature_cols = ['method_num', 'url_num', 'status', 'size']
    X_train = df[feature_cols].astype(float).to_numpy()

    # Normalisierung mit MinMaxScaler
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # Debug-Prints einfügen
    print("Min/Max nach Skalierung:", X_train_scaled.min(), X_train_scaled.max())
    print("Beispielwerte nach Skalierung:", X_train_scaled[:5])

    # Optional: Scaler speichern, falls du ihn für spätere Inferenz brauchst
    import joblib
    joblib.dump(scaler, SCALER_PATH)

    print(f"Trainingsdaten: {X_train_scaled.shape[0]} Zeilen (normalisiert)")

    # Einfacher Autoencoder
    inputs = tf.keras.Input(shape=(4,))
    encoded = tf.keras.layers.Dense(2, activation="relu")(inputs)
    decoded = tf.keras.layers.Dense(4, activation="linear")(encoded)
    autoencoder = tf.keras.Model(inputs, decoded)

    autoencoder.compile(optimizer="adam", loss=tf.keras.losses.MeanSquaredError())
    autoencoder.fit(X_train_scaled, X_train_scaled, epochs=10, batch_size=32, verbose=0)
    safe_model_save(autoencoder, MODEL_PATH)
    print(f"Modell gespeichert ({MODEL_PATH})")

    reconstructions = autoencoder.predict(X_train_scaled)
    mse = np.mean(np.power(X_train_scaled - reconstructions, 2), axis=1)
    # Threshold-Berechnung und Fallback
    if len(mse) == 0:
        threshold = 0.1  # Fallback, falls keine Daten
    else:
        threshold = float(np.mean(mse) + 3 * np.std(mse))
    print(f"Threshold (MSE): {threshold:.4f}")

    # Threshold speichern
    with open(THRESHOLD_PATH, "w") as f:
        json.dump({"threshold": threshold}, f)

def is_training_mode():
    return os.path.exists(TRAINING_TRIGGER)

def wait_for_logfile():
    while not os.path.exists(LOGFILE) or os.path.getsize(LOGFILE) == 0:
        print("Warte auf Logdaten ...")
        time.sleep(2)

def main():
    print("Trainer gestartet.")
    wait_for_logfile()
    last_mod_time = 0
    while True:
        if is_training_mode():
            log_mod_time = os.path.getmtime(LOGFILE)
            model_exists = os.path.exists(MODEL_PATH)
            if (not model_exists) or (log_mod_time > last_mod_time):
                trained = train_and_save_model()
                if trained:
                    last_mod_time = log_mod_time
            else:
                print("Modell aktuell. Warte auf neue Logdaten oder Datei-Löschung ...")
        else:
            print("Nicht in Trainingsphase. Warte ...")
        time.sleep(10)

if __name__ == "__main__":
    main()

