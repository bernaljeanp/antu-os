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
    import -window "$2" "$OUT/$1.png" || { echo "::error::no se pudo capturar $1"; exit 1; }
    kill "$app" 2>/dev/null
    if grep -E "\.qml:|Traceback|ReferenceError|TypeError|is not a type|is not installed" "$OUT/$1.log"; then
        echo "::error::$1 tiene errores o avisos de QML (ver $1.log en el artefacto capturas)"
        exit 1
    fi
}
capturar inicio root /usr/lib/antu/inicio/inicio.py
# El instalador solo existe en el sistema en vivo (iso.yml).
if [ -f /usr/lib/antu/instalador/instalador.py ]; then
    QT_SCALE_FACTOR=1.5 capturar bienvenida "Antu en vivo" /usr/lib/antu/bienvenida/bienvenida.py
    QT_SCALE_FACTOR=1.5 capturar instalador "Instalar Antu" /usr/lib/antu/instalador/instalador.py
    QT_SCALE_FACTOR=1.5 capturar informe "Informe del equipo" /usr/lib/antu/informe/informe.py
    python /usr/lib/antu/informe-helper --autoprueba || { echo "::error::El informe no limpia los datos personales"; exit 1; }
fi
# Zenit por pantalla completa: por su nombre, import no encuentra una ventana legible (la foto salía vacía sin avisar).
QT_SCALE_FACTOR=1.5 capturar zenit root /usr/lib/antu/zenit/app.py
QT_SCALE_FACTOR=1.5 capturar centro "Centro de Antu" /usr/lib/antu/centro/centro.py
QT_SCALE_FACTOR=1.5 capturar actualizaciones "Actualizaciones de Antu" /usr/lib/antu/actualizaciones/actualizaciones.py
QT_SCALE_FACTOR=1.5 capturar biblioteca root /usr/lib/antu/biblioteca/biblioteca.py
python /usr/lib/antu/biblioteca/biblioteca.py --autoprueba || { echo "::error::La Biblioteca da veredictos equivocados"; exit 1; }
QT_SCALE_FACTOR=1.5 capturar observatorio root /usr/lib/antu/observatorio/observatorio.py
QT_SCALE_FACTOR=1.5 capturar aviso root /usr/lib/antu/aviso/aviso.py
python /usr/lib/antu/observatorio/observatorio.py --autoprueba || { echo "::error::El Observatorio compara mal"; exit 1; }
python /usr/lib/antu/observatorio/asistente.py --autoprueba || { echo "::error::El asistente recibe mal las mediciones"; exit 1; }
capturar_con() {  # capturar_con NOMBRE OPCIÓN: el Observatorio con otra pantalla de demostración
    QT_SCALE_FACTOR=1.5 python /usr/lib/antu/observatorio/observatorio.py "$2" > "$OUT/$1.log" 2>&1 &
    local app=$!
    sleep 10
    kill -0 "$app" 2>/dev/null || { echo "::error::$1 terminó antes de la captura"; cat "$OUT/$1.log"; exit 1; }
    import -window root "$OUT/$1.png" || { echo "::error::no se pudo capturar $1"; exit 1; }
    kill "$app" 2>/dev/null
    if grep -E "\.qml:|Traceback|ReferenceError|TypeError|is not a type|is not installed" "$OUT/$1.log"; then
        echo "::error::$1 tiene errores o avisos de QML"
        exit 1
    fi
}
capturar_con observatorio-detalle --demo-detalle
capturar_con observatorio-charla --demo-pregunta
capturar_con observatorio-activar --demo-activar
python /usr/lib/antu/observatorio/observador.py --autoprueba || { echo "::error::El Observador lee mal los datos"; exit 1; }

# El arranque y el escritorio de verdad no se capturan aquí, sino en la VM de iso.yml (galería de ci/iso-test.sh).
exit 0
