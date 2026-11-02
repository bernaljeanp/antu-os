#!/usr/bin/env bash
# Capturas de la interfaz de Antu dentro de la imagen recién compilada (contenedor desechable de CI).
# Falla si el tema de inicio de sesión tiene errores o avisos de QML: ahí un error deja al usuario sin poder entrar.
set -uo pipefail
OUT=/out

pacman -Sy --noconfirm --needed xorg-server-xvfb imagemagick >/dev/null || exit 1
useradd -m -c "Jean Bernal" jean  # cuenta ficticia, solo para ver la placa de usuario

# Sin GLX: el GLX por software de Xvfb se cae en este contenedor. Qt dibuja por software, así que el
# desenfoque del fondo (MultiEffect) no sale en la captura; la composición sí.
export DISPLAY=:99 QT_QUICK_BACKEND=software
Xvfb :99 -screen 0 2560x1600x24 -nolisten tcp -extension GLX &
xvfb=$!
sleep 3
if ! kill -0 "$xvfb" 2>/dev/null; then
    echo "::warning::Xvfb no arrancó: sin capturas en esta compilación (problema del entorno de CI, no del tema)"
    exit 0
fi

# Inicio de sesión: SDDM en modo prueba con el tema Antu. Si el greeter se cae, el tema no carga: falla.
sddm-greeter-qt6 --test-mode --theme /usr/share/sddm/themes/antu > "$OUT/sddm.log" 2>&1 &
greeter=$!
sleep 12
if ! kill -0 "$greeter" 2>/dev/null; then
    echo "::error::sddm-greeter terminó antes de la captura: el tema de inicio de sesión no carga"
    cat "$OUT/sddm.log"
    exit 1
fi
import -window root "$OUT/sddm.png"
kill "$greeter" 2>/dev/null
if grep -E "themes/antu/|ReferenceError|TypeError|is not a type|is not installed|Cannot assign" "$OUT/sddm.log"; then
    echo "::error::El tema SDDM tiene errores o avisos de QML (ver sddm.log en el artefacto capturas)"
    exit 1
fi

# Apps de Antu en modo demo (no ejecutan nada): si no cargan o su QML tiene errores, falla.
#   capturar NOMBRE VENTANA SCRIPT     VENTANA "root" captura la pantalla entera
capturar() {
    python "$3" --demo > "$OUT/$1.log" 2>&1 &
    local app=$!
    sleep 10
    if ! kill -0 "$app" 2>/dev/null; then
        echo "::error::$1 terminó antes de la captura"
        cat "$OUT/$1.log"
        exit 1
    fi
    import -window "$2" "$OUT/$1.png"
    kill "$app" 2>/dev/null
    if grep -E "\.qml:|Traceback|ReferenceError|TypeError|is not a type|is not installed" "$OUT/$1.log"; then
        echo "::error::$1 tiene errores o avisos de QML (ver $1.log en el artefacto capturas)"
        exit 1
    fi
}
capturar inicio root /usr/lib/antu/inicio/inicio.py
# El instalador solo existe en el sistema en vivo (iso.yml).
if [ -f /usr/lib/antu/instalador/instalador.py ]; then
    QT_SCALE_FACTOR=1.5 capturar instalador "Instalar Antu" /usr/lib/antu/instalador/instalador.py
fi
QT_SCALE_FACTOR=1.5 capturar zenit "Zenit" /usr/lib/antu/zenit/app.py
QT_SCALE_FACTOR=1.5 capturar actualizaciones "Actualizaciones de Antu" /usr/lib/antu/actualizaciones/actualizaciones.py

# El arranque (Plymouth) no se captura aquí: su renderizador X11 no se activa en este contenedor; se prueba en VM.

# Escritorio: Plasma en una sesión Wayland virtual con un usuario nuevo, que recibe la distribución del tema global.
# kwin_wayland lleva capacidades de archivo que el contenedor bloquea; una copia las pierde. Es informativo.
pacman -S --noconfirm --needed spectacle >/dev/null 2>&1 || true
cp "$(command -v kwin_wayland)" /tmp/kwin_wayland
install -d -o jean -g jean -m 700 /run/user/1000
su jean -c 'export XDG_RUNTIME_DIR=/run/user/1000
  dbus-run-session -- bash -c "
    /tmp/kwin_wayland --virtual --width 2560 --height 1600 --no-lockscreen plasmashell > /tmp/plasma.log 2>&1 &
    sleep 35
    WAYLAND_DISPLAY=wayland-0 spectacle --background --nonotify --fullscreen --output /tmp/escritorio.png >> /tmp/plasma.log 2>&1
    sleep 5"' || true
cp /tmp/escritorio.png /tmp/plasma.log "$OUT/" 2>/dev/null || true
exit 0
