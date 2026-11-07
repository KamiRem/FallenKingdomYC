#!/bin/sh
# Facultatif : uniquement si le panel autorise Python et une commande personnalisée.
# Sinon sélectionner paper.jar et Java 25 dans le panel (voir HOST_INSTALLATION.md).
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
: "${SERVER_PORT:?Définir SERVER_PORT avec le port attribué par le panel}"
exec python3 maintenance/host_ops.py start --host 0.0.0.0 --port "$SERVER_PORT" --memory "${HEAP_GB:-6}"
