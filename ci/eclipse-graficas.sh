#!/usr/bin/env bash
# Prueba de antu-eclipse: qué gráfica elige en cada tipo de equipo, con gráficas de mentira. No usa nada del sistema:
# corre en CI y en cualquier PC.   bash ci/eclipse-graficas.sh
set -euo pipefail
ECLIPSE="$(dirname "$0")/../files/system/usr/bin/antu-eclipse"
INTEL=0x8086 AMD=0x1002 NVIDIA=0x10de
OFFLOAD="__NV_PRIME_RENDER_OFFLOAD=1"

#   probar NOMBRE ESPERA SOBRA GRÁFICA...     cada GRÁFICA es tarjeta:fabricante:conector:estado
probar() {
    local nombre="$1" espera="$2" sobra="$3" drm orden g
    shift 3
    drm="$(mktemp -d)"
    for g in "$@"; do
        IFS=: read -r tarjeta fabricante conector estado <<< "$g"
        mkdir -p "$drm/$tarjeta/device" "$drm/$tarjeta-$conector"
        echo "$fabricante" > "$drm/$tarjeta/device/vendor"
        echo 0x1234 > "$drm/$tarjeta/device/device"
        echo "$estado" > "$drm/$tarjeta-$conector/status"
    done
    orden="$(ANTU_DRM="$drm" bash "$ECLIPSE" --mostrar)"
    rm -rf "$drm"
    echo "$orden" | grep -qF -- "$espera" || { echo "FALLO, $nombre: falta «$espera» en: $orden"; exit 1; }
    if [ -n "$sobra" ] && echo "$orden" | grep -qF -- "$sobra"; then
        echo "FALLO, $nombre: sobra «$sobra» en: $orden"
        exit 1
    fi
    echo "bien: $nombre"
}

probar "híbrido, pantalla en la integrada: compone Intel, el juego va en NVIDIA" "--prefer-vk-device 8086:1234" "" \
    "card0:$INTEL:eDP-1:connected" "card1:$NVIDIA:HDMI-A-1:disconnected"
probar "híbrido, el juego lleva lo necesario para ir en NVIDIA" "$OFFLOAD" "" \
    "card0:$INTEL:eDP-1:connected" "card1:$NVIDIA:HDMI-A-1:disconnected"
probar "híbrido con pantalla externa en NVIDIA: gana NVIDIA, sin copias" "--prefer-vk-device 10de:1234" "$OFFLOAD" \
    "card0:$INTEL:eDP-1:connected" "card1:$NVIDIA:HDMI-A-1:connected"
probar "modo solo dedicada (MUX): compone NVIDIA" "--prefer-vk-device 10de:1234" "$OFFLOAD" \
    "card0:$NVIDIA:eDP-1:connected"
probar "solo AMD: compone AMD, sin nada de NVIDIA" "--prefer-vk-device 1002:1234" "$OFFLOAD" \
    "card0:$AMD:eDP-1:connected"
probar "solo Intel: compone Intel, sin nada de NVIDIA" "--prefer-vk-device 8086:1234" "$OFFLOAD" \
    "card0:$INTEL:eDP-1:connected"
probar "AMD integrada y NVIDIA: compone AMD, el juego va en NVIDIA" "$OFFLOAD" "" \
    "card0:$AMD:eDP-1:connected" "card1:$NVIDIA:DP-1:disconnected"
probar "sin pantalla detectada: Gamescope decide" "gamescope --steam" "--prefer-vk-device" \
    "card0:$NVIDIA:DP-1:disconnected"
