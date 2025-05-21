#!/bin/bash

set -e

# Funktion zum Extrahieren der pip install Pakete aus dem Dockerfile
extract_pip_packages() {
    grep -E 'pip install' "$1" | \
    sed -E 's/.*pip install( --no-cache-dir| --no-index| --find-links=[^ ]+)* //;s/\\//g' | \
    tr -d '"' | tr -d "'" | tr ' ' '\n' | grep -v '^$' | grep -v '^RUN$'
}

# Gehe alle Unterverzeichnisse durch
find . -type f -name 'Dockerfile' | while read -r dockerfile; do
    dir=$(dirname "$dockerfile")
    echo "Bearbeite $dockerfile im Verzeichnis $dir"

    # Extrahiere die Pakete
    packages=$(extract_pip_packages "$dockerfile" | sort | uniq | xargs)
    if [ -z "$packages" ]; then
        echo "  Keine Python-Abhängigkeiten gefunden, überspringe."
        continue
    fi

    # Lege das Wheels-Verzeichnis an (lösche vorher, falls vorhanden)
    wheels_dir="$dir/docker_wheels"
    rm -rf "$wheels_dir"
    mkdir -p "$wheels_dir"

    echo "  Lade Wheels für: $packages"
    # Starte einen Linux-Python-Container und lade die Wheels
    docker run --rm -v "$(realpath "$wheels_dir")":/wheels python:3.9 bash -c \
      "pip install --upgrade pip && pip download -d /wheels $packages"

    echo "  Fertig: Wheels liegen in $wheels_dir"
done

echo "Alle Wheels wurden für alle Dockerfiles erzeugt."

