import requests
import time
import random
import os
from shared_code.config import (
    ATTACK_TRIGGER,
    MALICIOUS_DURATION,
    MALICIOUS_RATE,
    NGINX_HOST,
)
 
# Feste Auswahl an "maliziösen" Methoden und URLs
MALICIOUS_METHODS = ["POST", "PUT", "DELETE"]
MALICIOUS_URLS = [
    "/admin",
    "/wp-login.php",
    "/api/secret",
    "/etc/passwd",
    "/.env",
    "/login?user=admin'--",
    "/index.php?page=../../../../etc/passwd",
    "/cgi-bin/test.cgi",
    "/config.php",
    "/hidden"
]

while True:
    if os.path.exists(ATTACK_TRIGGER):
        print("Malicious traffic started!")
        end_time = time.time() + MALICIOUS_DURATION
        while time.time() < end_time:
            method = random.choice(MALICIOUS_METHODS)
            path = random.choice(MALICIOUS_URLS)
            url = NGINX_HOST + path
            try:
                requests.request(method, url, timeout=1)
                print(f"{method} {url}")
            except Exception:
                pass
            time.sleep(1.0 / MALICIOUS_RATE)
        print("Malicious traffic stopped.")
        try:
            os.remove(ATTACK_TRIGGER)
        except Exception:
            pass
    else:
        time.sleep(0.5)

