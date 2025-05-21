# app/config.py

# Paths
LOGFILE_PATH = "/logs/access.log"
MODEL_PATH = "/model/autoencoder_model.h5"
THRESHOLD_PATH = "/model/autoencoder_threshold.json"
MODEL_REF_PATH = "/model/autoencoder_model_reference.h5"
SCALER_PATH = "/model/autoencoder_scaler.pkl"  # <--- NEU
CUSTOM_RULES_PATH = "/etc/nginx/conf.d/custom_rules.conf"
CHECK_INTERVAL = 2

# State Triggers
TRAINING_TRIGGER = "/shared/training.trigger"
ATTACK_TRIGGER = "/shared/attack.trigger"
RELOAD_TRIGGER = "/shared/nginx_reload.trigger"

# Attack Variables
MALICIOUS_DURATION = 20
MALICIOUS_RATE = 2

# Webserver
NGINX_HOST = "http://nginx:80"

# UI-Settings
N_LOG_LINES = 10
MALICIOUS_DURATION = 20  # seconds

