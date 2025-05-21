import streamlit as st
import os
import shutil
from config import (
    TRAINING_TRIGGER,
    ATTACK_TRIGGER,
    MODEL_PATH,
    MODEL_REF_PATH,
    CUSTOM_RULES_PATH,
    MALICIOUS_DURATION,
)
from state import add_message
from nginx_utils import (
    clear_custom_rules_file,
    reload_nginx,
    write_rules_to_file,  # NEU: Importiere die neue Funktion!
)

def mode_switch_col():
    mode = st.radio("Mode", ("Training", "Inference"), horizontal=True, key="mode_radio")
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
    return mode

def current_mode_col(mode):
    st.markdown(
        f'<div style="background-color:#2196F3;color:white;display:inline-block;padding:2px 8px;border-radius:4px;">'
        f'{"Training phase" if mode=="Training" else "Inference phase"}</div>',
        unsafe_allow_html=True
    )

def attack_button_col(mode):
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

def attack_status_col(attack_running):
    st.markdown(
        f'<div style="background-color:{"#E53935" if attack_running else "#43A047"};color:white;display:inline-block;padding:2px 8px;border-radius:4px;">'
        f'{"Malicious traffic active" if attack_running else "No malicious traffic"}</div>',
        unsafe_allow_html=True
    )

def copy_model_col():
    if st.button("Copy reference model", key="copy_model_btn"):
        try:
            if os.path.exists(MODEL_REF_PATH):
                shutil.copy(MODEL_REF_PATH, MODEL_PATH)
                add_message("Reference model copied to current model.", "info")
            else:
                add_message("Reference model not found.", "warning")
        except Exception as e:
            add_message(f"Error copying reference model: {e}", "error")

def clear_rules_col():
    if st.button("Clear custom_rules.conf", key="clear_rules_btn"):
        try:
            clear_custom_rules_file(CUSTOM_RULES_PATH)
            if reload_nginx():
                add_message("custom_rules.conf has been cleared and NGINX reloaded.", "info")
            else:
                add_message("custom_rules.conf has been cleared, but NGINX reload failed.", "warning")
        except Exception as e:
            add_message(f"Error clearing custom_rules.conf: {e}", "error")

def block_suggestions_col():
    """
    Zeigt die aktuellen Blockregel-Vorschläge an und bietet den 'Apply and Reload NGINX'-Button.
    Nach Klick werden die Vorschläge übernommen und die Liste geleert.
    """
    block_suggestions = st.session_state.get("block_suggestions", [])
    if block_suggestions:
        st.markdown("#### Blockregel-Vorschläge")
        for rule in block_suggestions:
            st.code(rule, language="nginx")
        if st.button("Apply and Reload NGINX", key="apply_block_rules_btn"):
            try:
                num_written = write_rules_to_file(block_suggestions, CUSTOM_RULES_PATH)
                if num_written > 0:
                    msg = f"{num_written} neue Regel{'n' if num_written > 1 else ''} übernommen und NGINX neu geladen."
                else:
                    msg = "Keine neuen Regeln übernommen (alle Regeln bereits vorhanden)."
                if reload_nginx():
                    add_message(msg, "info")
                else:
                    add_message(msg + " Aber: NGINX reload fehlgeschlagen.", "warning")
                st.session_state["block_suggestions"] = []  # Vorschlagsliste leeren
            except Exception as e:
                add_message(f"Fehler beim Übernehmen der Regeln: {e}", "error")

def color_row(row):
    if row.get('status', None) == 403:
        return ['background-color: #FF0000; color: white; font-weight: bold'] * len(row)
    elif row.get('anomaly', False):
        return ['background-color: #FFA500; color: black; font-weight: bold'] * len(row)
    elif row.get('status', None) == 200:
        return ['background-color: #90EE90; color: black'] * len(row)
    else:
        return [''] * len(row)

