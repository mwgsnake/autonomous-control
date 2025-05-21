#!/bin/sh
# Starte den Reload-Watcher im Hintergrund
/usr/local/bin/reload-watcher.sh &

# Starte NGINX im Vordergrund
nginx -g 'daemon off;'

