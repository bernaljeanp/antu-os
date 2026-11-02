#!/usr/bin/env bash
# Capturas de la interfaz de Antu dentro de la imagen recién compilada (contenedor desechable de CI).
# Falla si el tema de inicio de sesión tiene errores o avisos de QML: ahí un error deja al usuario sin poder entrar.
set -uo pipefail
OUT=/out

pacman -Sy --noconfirm --needed xorg-server-xvfb imagemagick >/dev/null || exit 1
useradd -m -c "Jean Bernal" jean  # cuenta ficticia, solo para ver la placa de usuario

export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1
Xvfb :99 -screen 0 2560x1600x24 -nolisten tcp &
sleep 3

# Inicio de sesión: SDDM en modo prueba con el tema Antu.
sddm-greeter-qt6 --test-mode --theme /usr/share/sddm/themes/antu > "$OUT/sddm.log" 2>&1 &
greeter=$!
sleep 12
import -window root "$OUT/sddm.png"
kill "$greeter" 2>/dev/null
if grep -E "themes/antu/|ReferenceError|TypeError|is not a type|is not installed|Cannot assign" "$OUT/sddm.log"; then
    echo "::error::El tema SDDM tiene errores o avisos de QML (ver sddm.log en el artefacto capturas)"
    exit 1
fi

# Arranque: Plymouth con su renderizador X11. Si el entorno no lo permite, solo queda el registro.
mkdir -p /run/plymouth
plymouthd --no-daemon --debug --debug-file="$OUT/plymouth.log" &
sleep 2
plymouth show-splash || echo "plymouth: show-splash falló"
sleep 3
import -window root "$OUT/plymouth-1.png" || true
sleep 6
import -window root "$OUT/plymouth-2.png" || true
plymouth quit || true

# Escritorio: Plasma en una sesión Wayland virtual con un usuario nuevo, que recibe la distribución del tema global.
# Es informativo: si el entorno de CI no lo permite, solo queda el registro.
pacman -S --noconfirm --needed spectacle >/dev/null 2>&1 || true
install -d -o jean -g jean -m 700 /run/user/1000
su jean -c 'export XDG_RUNTIME_DIR=/run/user/1000
  dbus-run-session -- bash -c "
    kwin_wayland --virtual --width 2560 --height 1600 --no-lockscreen plasmashell > /tmp/plasma.log 2>&1 &
    sleep 35
    WAYLAND_DISPLAY=wayland-0 spectacle --background --nonotify --fullscreen --output /tmp/escritorio.png >> /tmp/plasma.log 2>&1
    sleep 5"' || true
cp /tmp/escritorio.png /tmp/plasma.log "$OUT/" 2>/dev/null || true
exit 0
