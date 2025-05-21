import streamlit as st
from streamlit_autorefresh import st_autorefresh
import os
import json
import numpy as np

from config import (
    LOGFILE_PATH, N_LOG_LINES, MODEL_PATH, SCALER_PATH, THRESHOLD_PATH, CUSTOM_RULES_PATH
)
from state import init_session_state, add_message, show_messages
from log_utils import extract_features_with_line_numbers
from model_utils import scale_features, load_model
from nginx_utils import (
    reload_nginx,
    load_existing_rule_paths,
    build_block_rules_from_paths,
)
from ui_components import (
    color_row,
    mode_switch_col,
    current_mode_col,
    attack_button_col,
    attack_status_col,
    copy_model_col,
    clear_rules_col,
    block_suggestions_col,  # NEU: Vorschlagsanzeige importieren!
)
from slider_component import threshold_slider_col

def main():
    st.set_page_config(page_title="NGINX Traffic Demo", layout="wide")
    st.header("NGINX Traffic: Training vs. Inference Mode Demo")
    st_autorefresh(interval=2000, key="log_autorefresh")

    # CSS
    st.markdown("""
        <style>
            html, body, [class*="css"]  { font-size:12px !important; }
            .block-container { padding-top: 2.5rem !important; }
            .stButton>button { padding:2px 8px !important; font-size:12px !important; }
            .stRadio>div { flex-direction: row !important; gap: 10px !important; }
            h1, h2, h3, h4 { margin-top: 2.5rem !important; margin-bottom: 0.5rem !important; }
            .stSlider { padding-top: 0.2rem !important; padding-bottom: 0.2rem !important; }
            .stDataFrame, .stTable { font-size: 11px !important; }
            .stMarkdown { margin-bottom: 0.2rem !important; }
            .stAlert { margin-bottom: 4px !important; }
        </style>
    """, unsafe_allow_html=True)

    # Session State initialisieren
    init_session_state()

    # --- Steuerspalten erzeugen (4 Spalten) ---
    steer_cols = st.columns([1.2, 1.1, 1.3, 1.7])

    # --- Spalten befüllen ---
    with steer_cols[0]:
        mode = mode_switch_col()

    with steer_cols[1]:
        current_mode_col(mode)

    with steer_cols[2]:
        attack_button_col(mode)
        copy_model_col()
        clear_rules_col()

    with steer_cols[3]:
        threshold_slider_col()

    # --- Logdaten laden und ML-Inferenz anwenden ---
    st.markdown("### Latest Logentries")
    # Legend for color codes
    st.markdown("""
    <div style="margin-bottom: 0.5rem;">
        <b>Legend:</b>
        <span style="background-color:#90EE90;color:black;padding:2px 8px;border-radius:4px;margin-left:8px;">GRN = OK (200)</span>
        <span style="background-color:#FFA500;color:black;padding:2px 8px;border-radius:4px;margin-left:8px;">ORG = Anomaly</span>
        <span style="background-color:#FF0000;color:white;padding:2px 8px;border-radius:4px;margin-left:8px;">RED = Blocked (403)</span>
    </div>
    """, unsafe_allow_html=True)
    try:
        df = extract_features_with_line_numbers(LOGFILE_PATH, N_LOG_LINES)
        if not df.empty and mode == "Inference":
            model = load_model(MODEL_PATH)
            X_scaled = scale_features(df, SCALER_PATH)
            reconstructions = model.predict(X_scaled)
            mse = np.mean(np.power(X_scaled - reconstructions, 2), axis=1)
            df["mse"] = mse
            if os.path.exists(THRESHOLD_PATH):
                with open(THRESHOLD_PATH) as f:
                    threshold = json.load(f)["threshold"]
            else:
                threshold = 0.1  # Fallback
            df["anomaly"] = mse > threshold

            # --- Blockregel-Vorschlagslogik ---
            anomalous_df = df[df["anomaly"]]
            if not anomalous_df.empty:
                existing_paths = load_existing_rule_paths(CUSTOM_RULES_PATH)
                # Passe den Spaltennamen ggf. an (url)
                suggested_paths = set(anomalous_df["url"].unique()) - existing_paths
                block_suggestions = build_block_rules_from_paths(suggested_paths)
                # Nur aktualisieren, wenn die Liste leer ist (stabil bis Button-Klick)
                if "block_suggestions" not in st.session_state or not st.session_state["block_suggestions"]:
                    st.session_state["block_suggestions"] = block_suggestions

        if not df.empty:
            st.write(df.style.apply(color_row, axis=1))
        else:
            st.info("Keine Logeinträge gefunden.")
    except Exception as e:
        add_message(f"Fehler beim Laden/Anzeigen der Logdaten: {e}", "error")

    # --- Blockregel-Vorschläge anzeigen & anwenden ---
    block_suggestions_col()

    # --- Statusmeldungen anzeigen ---
    show_messages()

if __name__ == "__main__":
    main()
