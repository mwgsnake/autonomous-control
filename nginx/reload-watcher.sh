#!/bin/sh
RELOAD_TRIGGER="/shared/nginx_reload.trigger"

while true; do
  if [ -f "$RELOAD_TRIGGER" ]; then
    echo "Reload-Trigger found, executing nginx -s reload aus"
    nginx -s reload
    rm -f "$RELOAD_TRIGGER"
  fi
  sleep 2
done

