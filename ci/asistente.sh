#!/usr/bin/env bash
# Le hace preguntas de verdad al asistente, con mediciones inventadas y sin gráfica: comprueba que responde con los datos y en
# español, y deja las respuestas en el registro para leerlas. Baja el modelo (3,1 GB), por eso no corre en cada compilación.
#   bash ci/asistente.sh [imagen]
set -euo pipefail
IMAGEN="${1:-ghcr.io/bernaljeanp/antu-nvidia:testing}"
# El Observatorio de este checkout sobre la imagen: así se prueba un cambio al asistente sin compilar todo el sistema.
sudo podman run --rm -e HOME=/tmp/casa \
    -v "$PWD/files/system/usr/lib/antu/observatorio:/usr/lib/antu/observatorio:ro" "$IMAGEN" \
    sh -c 'mkdir -p "$HOME" && exec python3 /usr/lib/antu/observatorio/asistente.py --real'
