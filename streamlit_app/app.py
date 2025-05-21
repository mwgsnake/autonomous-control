import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import numpy as np
import re
import tensorflow as tf
import os
import shutil
import subprocess
from datetime import datetime
import json
import time
import joblib  # <--- NEU

st.set_page_config(page_title="NGINX Traffic Demo", layout="wide")
st.header("NGINX Traffic: Training vs. Inference Mode Demo")
st_autorefresh(interval=2000, key="log_autorefresh")

# --- Compact global CSS for smaller font and less padding ---
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

TRAINING_TRIGGER = "/shared/training_mode"
ATTACK_TRIGGER = "/shared/trigger_attack"
MODEL_PATH = "/model/autoencoder_model.h5"
MODEL_REF_PATH = "/model/autoencoder_model_reference.h5"
THRESHOLD_PATH = "/model/autoencoder_threshold.json"
SCALER_PATH = "/model/autoencoder_scaler.pkl"  # <--- NEU
LOGFILE_PATH = "/logs/access.log"
N_LOG_LINES = 10
MALICIOUS_DURATION = 20  # seconds
CUSTOM_RULES_PATH = "/etc/nginx/conf.d/custom_rules.conf"

if not os.path.exists(CUSTOM_RULES_PATH):
    with open(CUSTOM_RULES_PATH, "w") as f:
        pass  # Ensure the file exists, even if empty

# --- Status-Message-Queue mit Timeout ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "measures_state" not in st.session_state:
    st.session_state["measures_state"] = {}
if "persisted_measures" not in st.session_state:
    st.session_state["persisted_measures"] = []

def add_message(msg, type="info", duration=10):
    st.session_state["messages"].append({
        "msg": msg,
        "type": type,
        "timestamp": time.time(),
        "duration": duration
    })

def extract_features_with_line_numbers(logfile_path, last_n=N_LOG_LINES):
    pattern = re.compile(
        r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) \S+" (?P<status>\d+) (?P<size>\d+)'
    )
    data = []
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
            all_lines = f.readlines()
            total_lines = len(all_lines)
            lines = all_lines[-last_n:]
            start_line_number = total_lines - len(lines) + 1
            for i, line in enumerate(lines):
                m = pattern.match(line)
                if m:
                    entry = m.groupdict()
                    entry['Line'] = start_line_number + i
                    entry['method_num'] = 0 if entry['method'] == 'GET' else 1
                    entry['url_num'] = url_map.get(entry['url'], 99)
                    entry['status'] = int(entry['status'])
                    entry['size'] = int(entry['size'])
                    data.append(entry)
    except Exception as e:
        add_message(f"Error reading logfile: {e}", "warning")
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if not df.empty:
        cols = ['Line'] + [c for c in df.columns if c != 'Line']
        df = df[cols]
    return df

def update_custom_rules_file(new_rules, rules_path):
    existing_rules = set()
    if os.path.exists(rules_path):
        with open(rules_path, "r") as f:
            for line in f:
                rule = line.strip()
                if rule:
                    existing_rules.add(rule)
    for rule in new_rules:
        rule = rule.strip()
        if rule and rule not in existing_rules:
            existing_rules.add(rule)
    with open(rules_path, "w") as f:
        for rule in sorted(existing_rules):
            f.write(rule + "\n")

def load_existing_rules(rules_path):
    existing_rules = set()
    if os.path.exists(rules_path):
        with open(rules_path, "r") as f:
            for line in f:
                rule = line.strip()
                if rule:
                    existing_rules.add(rule)
    return existing_rules

def clear_custom_rules_file(rules_path):
    with open(rules_path, "w") as f:
        pass

def reload_nginx():
    try:
        result = subprocess.run(
            ["docker", "exec", "nginx", "nginx", "-s", "reload"],
            capture_output=True, text=True, check=True
        )
        add_message("NGINX configuration reloaded successfully!", "info")
        return True
    except subprocess.CalledProcessError as e:
        add_message(f"Failed to reload NGINX: {e.stderr} {e.stdout}", "error")
    except Exception as e:
        add_message(f"Unexpected error while reloading NGINX: {e}", "error")
    return False

# --- NEU: Feature scaling wie im Training ---
def scale_features(df):
    feature_cols = ['method_num', 'url_num', 'status', 'size']
    if not os.path.exists(SCALER_PATH):
        add_message("Scaler file not found! Model inference will be incorrect.", "error")
        return np.zeros((len(df), len(feature_cols)))
    scaler = joblib.load(SCALER_PATH)
    X = df[feature_cols].astype(float).to_numpy()
    X_scaled = scaler.transform(X)
    return X_scaled

# --- Compact control bar: all in one line ---
steer_cols = st.columns([1.2, 1.1, 1.3, 1.1, 1.3, 1.3, 1.3, 1.7])
with steer_cols[0]:
    mode = st.radio("Mode", ("Training", "Inference"), horizontal=True, key="mode_radio")
    # Triggerdatei entsprechend Modus anlegen/löschen
    training_mode = os.path.exists(TRAINING_TRIGGER)
    if mode == "Training" and not training_mode:
        try:
            open(TRAINING_TRIGGER, "w").close()
        except Exception as e:
            add_message(f"Could not activate training mode: {e}", "warning")
    elif mode == "Inference" and training_mode:
        try:
            os.remove(TRAINING_TRIGGER)
        except Exception as e:
            add_message(f"Could not deactivate training mode: {e}", "warning")
with steer_cols[1]:
    st.markdown(
        f'<div style="background-color:#2196F3;color:white;display:inline-block;padding:2px 8px;border-radius:4px;">'
        f'{"Training phase" if mode=="Training" else "Inference phase"}</div>',
        unsafe_allow_html=True
    )
with steer_cols[2]:
    attack_running = os.path.exists(ATTACK_TRIGGER)
    malicious_btn_label = f"Malicious traffic ({MALICIOUS_DURATION}s)"
    malicious_btn_disabled = attack_running or (mode == "Training")
    if st.button(malicious_btn_label, key="malicious_btn", disabled=malicious_btn_disabled):
        if os.path.exists(TRAINING_TRIGGER):
            try:
                os.remove(TRAINING_TRIGGER)
                st.session_state["mode_radio"] = "Inference"
                add_message("Automatically switched to inference mode to avoid training the model with attack data.", "info")
            except Exception as e:
                add_message(f"Could not deactivate training mode: {e}", "warning")
        with open(ATTACK_TRIGGER, "w") as f:
            f.write("go")
        add_message("Malicious traffic is being generated! Watch the log entries.", "info")
    if mode == "Training":
        st.info("In training mode, generating attacks is disabled.")
with steer_cols[3]:
    st.markdown(
        f'<div style="background-color:{"#E53935" if attack_running else "#43A047"};color:white;display:inline-block;padding:2px 8px;border-radius:4px;">'
        f'{"Malicious traffic active" if attack_running else "No malicious traffic"}</div>',
        unsafe_allow_html=True
    )
with steer_cols[4]:
    if st.button("Copy reference model", key="copy_model_btn"):
        try:
            if os.path.exists(MODEL_REF_PATH):
                shutil.copy(MODEL_REF_PATH, MODEL_PATH)
                add_message("Reference model copied to current model.", "info")
            else:
                add_message("Reference model not found.", "warning")
        except Exception as e:
            add_message(f"Error copying reference model: {e}", "error")
with steer_cols[5]:
    if st.button("Clear custom_rules.conf", key="clear_rules_btn"):
        try:
            clear_custom_rules_file(CUSTOM_RULES_PATH)
            # Automatically reload NGINX after clearing
            if reload_nginx():
                add_message("custom_rules.conf has been cleared and NGINX reloaded.", "info")
            else:
                add_message("custom_rules.conf has been cleared, but NGINX reload failed.", "warning")
        except Exception as e:
            add_message(f"Error clearing custom_rules.conf: {e}", "error")
with steer_cols[6]:
    pass

# --- Model status and threshold side by side ---
model_col, threshold_col = st.columns([2, 2])

with model_col:
    st.markdown("**Model status**")
    model_info = {}
    if os.path.exists(MODEL_PATH):
        mod_time = os.path.getmtime(MODEL_PATH)
        model_info['Available'] = "✅"
        model_info['Last written'] = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
        if os.path.exists(THRESHOLD_PATH):
            try:
                with open(THRESHOLD_PATH) as f:
                    threshold_data = json.load(f)
                threshold = threshold_data.get("threshold", None)
                model_info['Threshold'] = f"{threshold:.2f}" if threshold is not None else "-"
            except Exception as e:
                threshold = None
                model_info['Threshold'] = f"Error: {e}"
        else:
            threshold = None
            model_info['Threshold'] = "-"
        if os.path.exists(LOGFILE_PATH):
            with open(LOGFILE_PATH) as f:
                lines = f.readlines()
            model_info['Log lines'] = len(lines)
            df = extract_features_with_line_numbers(LOGFILE_PATH, last_n=N_LOG_LINES)
            if not df.empty:
                try:
                    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
                    X_scaled = scale_features(df)  # <--- NEU
                    X_pred = model.predict(X_scaled)
                    mse = np.mean(np.power(X_scaled - X_pred, 2), axis=1)
                    model_info[f'Avg. MSE ({N_LOG_LINES})'] = f"{np.mean(mse):.2f}"
                except Exception as e:
                    model_info[f'Avg. MSE ({N_LOG_LINES})'] = f"Err: {e}"
            else:
                model_info[f'Avg. MSE ({N_LOG_LINES})'] = "-"
        else:
            model_info['Log lines'] = "-"
            model_info[f'Avg. MSE ({N_LOG_LINES})'] = "-"
    else:
        threshold = None
        model_info['Available'] = "❌"
        model_info['Last written'] = "-"
        model_info['Threshold'] = "-"
        model_info['Log lines'] = "-"
        model_info[f'Avg. MSE ({N_LOG_LINES})'] = "-"
    st.table(pd.DataFrame([model_info]))

with threshold_col:
    st.markdown("**Anomaly threshold**")
    
    # Initialisiere Threshold und Max-Wert in session_state, falls nicht vorhanden
    if 'threshold_max' not in st.session_state:
        st.session_state.threshold_max = 1.0  # Default, falls noch kein Training
    
    if os.path.exists(THRESHOLD_PATH):
        try:
            with open(THRESHOLD_PATH) as f:
                threshold_data = json.load(f)
            threshold = threshold_data.get("threshold", 0.0)
            
            # Berechne Max-Wert nur einmal beim Wechsel in den Inference-Modus
            if mode == "Inference" and 'initial_threshold_set' not in st.session_state:
                # Beispiel: Max = 10 * aktueller Threshold (kann an deine Daten angepasst werden)
                st.session_state.threshold_max = max(1.0, threshold * 10)
                st.session_state.initial_threshold_set = True  # Flag, damit nicht neu berechnet wird
        except Exception as e:
            threshold = 0.0
            st.error(f"Threshold-File has error: {e}")
    else:
        threshold = 0.0
    
    if threshold > 0 and st.session_state.threshold_max > threshold:
        new_threshold = st.slider(
            "Adjust threshold",
            min_value=0.0,
            max_value=float(st.session_state.threshold_max),
            value=float(threshold),
            step=0.01,
            format="%.2f",
            key="threshold_slider"
        )
        if new_threshold != threshold:
            try:
                with open(THRESHOLD_PATH, "w") as f:
                    json.dump({"threshold": new_threshold}, f)
                add_message(f"Threshold updated to {new_threshold:.2f}.", "info")
                threshold = new_threshold
            except Exception as e:
                add_message(f"Failed to save new threshold: {e}", "error")
    else:
        st.warning("Threshold not set or non vlid range. Train the model first.")


# --- Logfile and anomaly detection ---
st.markdown("**Latest log entries**")
df = extract_features_with_line_numbers(LOGFILE_PATH)

def color_row(row):
    if row['status'] == 403:
        return ['background-color: #FF0000; color: white; font-weight: bold'] * len(row)
    elif row.get('anomaly', False):
        return ['background-color: #FFA500; color: black; font-weight: bold'] * len(row)
    elif row['status'] == 200:
        return ['background-color: #90EE90; color: black'] * len(row)
    else:
        return [''] * len(row)

malicious_ips = set()
malicious_urls = set()
measures = []

if mode == "Inference" and not df.empty:
    feature_cols = ['method_num', 'url_num', 'status', 'size']
    X_scaled = scale_features(df)  # <--- NEU
    if os.path.exists(MODEL_PATH):
        try:
            model = tf.keras.models.load_model(MODEL_PATH, compile=False)
            X_pred = model.predict(X_scaled)
            mse = np.mean(np.power(X_scaled - X_pred, 2), axis=1)
            if 'threshold' not in locals() or threshold is None:
                threshold = 50
            anomalies = mse > threshold
            df['anomaly'] = anomalies
            df['mse'] = mse.round(2)

            st.write("**Legend:** 🟩 OK &nbsp;&nbsp; 🟧 Anomaly detected &nbsp;&nbsp; 🟥 Blocked (403)")
            st.dataframe(df.style.apply(color_row, axis=1))

            st.write(f"Detected anomalies: {anomalies.sum()} / {len(df)}")

            # --- Collect suggestions, filter out existing rules ---
            for _, row in df[df['anomaly']].iterrows():
                malicious_ips.add(row['ip'])
                malicious_urls.add(row['url'])
            existing_rules = load_existing_rules(CUSTOM_RULES_PATH)
            measures = []
            for ip in malicious_ips:
                rule = f"deny {ip};"
                if rule not in existing_rules:
                    measures.append({'type': 'IP block', 'rule': rule, 'selected': st.session_state["measures_state"].get(rule, True)})
            for url in malicious_urls:
                rule = f"location = {url} {{ deny all; }}"
                if rule not in existing_rules:
                    measures.append({'type': 'URL block', 'rule': rule, 'selected': st.session_state["measures_state"].get(rule, True)})

            # --- Persist suggestions while attack is running ---
            if attack_running:
                st.session_state["persisted_measures"] = measures
            elif not attack_running:
                st.session_state["persisted_measures"] = []

            # --- Show suggestions only if attack is running and there are measures ---
            if attack_running and st.session_state["persisted_measures"]:
                st.markdown("### Suggested measures (NGINX rules)")
                for m in st.session_state["persisted_measures"]:
                    m['selected'] = st.checkbox(f"{m['type']}: {m['rule']}", value=m['selected'], key=f"measure_{m['rule']}")
                    st.session_state["measures_state"][m['rule']] = m['selected']

                if st.button("Apply measures and write file"):
                    try:
                        selected_rules = [m['rule'] for m in st.session_state["persisted_measures"] if m['selected']]
                        if selected_rules:
                            update_custom_rules_file(selected_rules, CUSTOM_RULES_PATH)
                            if reload_nginx():
                                add_message("Selected measures applied and NGINX reloaded.", "info")
                            else:
                                add_message("Selected measures applied, but NGINX reload failed.", "warning")
                        else:
                            add_message("No measures selected.", "warning")
                    except Exception as e:
                        add_message(f"Error applying measures: {e}", "error")
            elif attack_running:
                st.info("No new measures suggested.")

        except Exception as e:
            add_message(f"Error loading or applying the model: {e}", "error")
    else:
        add_message("No model found! Please train first.", "error")

elif mode == "Training" and not df.empty:
    st.dataframe(df)
    st.info("Training mode: Only normal log entries are shown here. No anomaly detection, no evaluation!")

elif not df.empty:
    st.dataframe(df)

else:
    st.info("No log entries found.")
# --- Status message display ---
now = time.time()
st.markdown("---")
for m in st.session_state["messages"]:
    if now - m["timestamp"] < m["duration"]:
        st.info(m["msg"]) if m["type"] == "info" else st.warning(m["msg"]) if m["type"] == "warning" else st.error(m["msg"])
