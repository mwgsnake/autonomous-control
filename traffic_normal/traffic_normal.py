import requests
import time
import random

TARGET_URL = "http://nginx"  # Passe ggf. an, je nach Compose-Setup

NORMAL_PATHS = [
    "/",
    "/about",
    "/index.html",
    "/static/logo.png",
    "/static/style.css",
    "/contact",
    "/help",
    "/favicon.ico"
]

def send_normal_traffic():
    while True:
        path = random.choice(NORMAL_PATHS)
        url = f"{TARGET_URL}{path}"
        try:
            response = requests.get(url)
            print(f"Sent GET {path}, status: {response.status_code}")
        except Exception as e:
            print(f"Error requesting {url}: {e}")
        time.sleep(1)

if __name__ == "__main__":
    send_normal_traffic()

