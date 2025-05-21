# app/model_utils.py

import os
import joblib
import numpy as np
import tensorflow as tf
from state import add_message
import pandas as pd

def scale_features(df: pd.DataFrame, scaler_path: str) -> np.ndarray:
    """
    Skaliert die Features im DataFrame df mit dem Scaler aus scaler_path.
    Gibt ein 2D-numpy-Array zurück.
    """
    feature_cols = ['method_num', 'url_num', 'status', 'size']
    if not os.path.exists(scaler_path):
        add_message("Scaler file not found! Model inference will be incorrect.", "error")
        return np.zeros((len(df), len(feature_cols)))
    try:
        scaler = joblib.load(scaler_path)
        X = df[feature_cols].astype(float).to_numpy()
        X_scaled = scaler.transform(X)
        return X_scaled
    except Exception as e:
        add_message(f"Failed to scale features: {e}", "error")
        return np.zeros((len(df), len(feature_cols)))

def load_model(model_path: str):
    """
    Lädt ein ML-Modell (Keras oder scikit-learn) vom angegebenen Pfad.
    Gibt das Modell zurück oder None, wenn kein Modell gefunden/geladen werden konnte.
    """
    if not os.path.exists(model_path):
        add_message(f"Model file not found at {model_path}!", "error")
        return None

    # Versuche zuerst, ein Keras-Modell zu laden
    try:
        model = tf.keras.models.load_model(model_path, compile=False)
        return model
    except Exception:
        pass  # Kein Keras-Modell

    # Versuche, ein scikit-learn-Modell zu laden
    try:
        model = joblib.load(model_path)
        if hasattr(model, "predict"):
            return model
        else:
            add_message("Loaded object is not a valid ML model (no 'predict' method)!", "error")
            return None
    except Exception as e:
        add_message(f"Failed to load model with joblib: {e}", "error")
        return None

