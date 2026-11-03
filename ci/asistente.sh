#!/usr/bin/env bash
# Le hace preguntas de verdad al asistente, con mediciones inventadas y sin gráfica: comprueba que responde con los datos y en
# español, y deja las respuestas en el registro para leerlas. Baja el modelo (3,1 GB), por eso no corre en cada compilación.
#   bash ci/asistente.sh [imagen]
set -euo pipefail
IMAGEN="${1:-ghcr.io/bernaljeanp/antu-nvidia:testing}"
sudo podman run --rm -e HOME=/tmp/casa "$IMAGEN" \
    sh -c 'mkdir -p "$HOME" && exec python3 /usr/lib/antu/observatorio/asistente.py --real'
