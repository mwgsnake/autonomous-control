# app/state.py
import streamlit as st
import time

# --- Status-Message-Queue mit Timeout ---
def init_session_state():
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

def show_messages():
    now = time.time()
    messages_to_keep = []
    for m in st.session_state["messages"]:
        if now - m["timestamp"] < m["duration"]:
            if m["type"] == "info":
                st.info(m["msg"])
            elif m["type"] == "warning":
                st.warning(m["msg"])
            elif m["type"] == "error":
                st.error(m["msg"])
            else:
                st.write(m["msg"])
            messages_to_keep.append(m)
    st.session_state["messages"] = messages_to_keep

