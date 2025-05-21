FROM nginx:latest

# Kopiere das Reload-Watcher-Skript ins Image
COPY reload-watcher.sh /usr/local/bin/reload-watcher.sh
RUN chmod +x /usr/local/bin/reload-watcher.sh

# Kopiere ggf. deine nginx.conf und conf.d (alternativ per Volume mounten)
# COPY nginx.conf /etc/nginx/nginx.conf
# COPY conf.d /etc/nginx/conf.d

# Entrypoint-Skript, das Watcher und nginx startet
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

