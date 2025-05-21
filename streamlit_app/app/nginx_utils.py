# app/nginx_utils.py

import os
import subprocess
from state import add_message

RELOAD_TRIGGER = "/shared/nginx_reload.trigger"

def load_existing_rule_paths(rules_path):
    """
    Extrahiert alle Pfade, die bereits in custom_rules.conf als Blockregel existieren.
    """
    existing_paths = set()
    if os.path.exists(rules_path):
        with open(rules_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("location ="):
                    # Beispiel: location = /admin { deny all; }
                    parts = line.split()
                    if len(parts) >= 3:
                        existing_paths.add(parts[2])
    return existing_paths

def build_block_rules_from_paths(paths):
    """
    Baut für eine Liste von Pfaden NGINX-Blockregeln.
    """
    return [f"location = {path} {{ deny all; }}" for path in paths]

def write_rules_to_file(rules, rules_path):
    """
    Hängt neue Regeln an die custom_rules.conf an (ohne Doubletten).
    """
    existing_rules = set()
    if os.path.exists(rules_path):
        with open(rules_path, "r") as f:
            for line in f:
                rule = line.strip()
                if rule:
                    existing_rules.add(rule)
    new_rules = [rule for rule in rules if rule.strip() and rule not in existing_rules]
    if new_rules:
        with open(rules_path, "a") as f:
            for rule in new_rules:
                f.write(rule + "\n")
    return len(new_rules)

def clear_custom_rules_file(rules_path):
    """
    Löscht alle Blockregeln (setzt Datei auf leer).
    """
    with open(rules_path, "w") as f:
        pass

def reload_nginx():
    """
    Reloaded NGINX im Docker-Container 'nginx'.
    """
    print("CWD:", os.getcwd())
    print("shared exists:", os.path.exists("shared"))
    print("shared absolute:", os.path.abspath("shared"))
    try:
#        result = subprocess.run(
#            ["docker", "exec", "nginx", "nginx", "-s", "reload"],
#            capture_output=True, text=True, check=True
#        )
#        add_message("NGINX configuration reloaded successfully!", "info")
#        return True
#    except subprocess.CalledProcessError as e:
#        add_message(f"Failed to reload NGINX: {e.stderr} {e.stdout}", "error")
#    except Exception as e:
#        add_message(f"Unexpected error while reloading NGINX: {e}", "error")

       # Schreibe eine leere Datei oder aktualisiere den Timestamp
       with open(RELOAD_TRIGGER, "w") as f:
           f.write("reload\n")
       add_message("NGINX reload trigger file written. Waiting for external reload.", "info")
       return True
    except Exception as e:
        add_message(f"Failed to write NGINX reload trigger file: {e}", "error")
    return False

