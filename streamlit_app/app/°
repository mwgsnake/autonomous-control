import streamlit as st
import os
import json
from config import THRESHOLD_PATH

def threshold_slider_col():
    """
    Zeigt einen Slider für den Anomaly-Threshold an, lädt und speichert den Wert in THRESHOLD_PATH.
    """
    threshold = 0.0
    if os.path.exists(THRESHOLD_PATH):
        try:
            with open(THRESHOLD_PATH) as f:
                threshold = float(json.load(f).get("threshold", 0.0))
        except Exception as e:
            st.warning(f"Fehler beim Laden des Thresholds: {e}")

    st.markdown("**Anomaly threshold**")
    min_slider = 0.0
    max_slider = threshold * 10 if threshold > 0 else 1.0
    if min_slider < max_slider:
        try:
            new_threshold = st.slider(
                "Adjust threshold",
                min_value=min_slider,
                max_value=max_slider,
                value=threshold,
                step=0.01,
                format="%.2f",
                key="threshold_slider"
            )
            if new_threshold != threshold:
                try:
                    with open(THRESHOLD_PATH, "w") as f:
                        json.dump({"threshold": new_threshold}, f)
                    st.info(f"Threshold updated to {new_threshold:.2f}.")
                except Exception as e:
                    st.error(f"Failed to save new threshold: {e}")
        except Exception as e:
            st.error(f"Failed to display slider: {e}")
    else:
        st.info("Threshold range too small for slider or was not set.")
