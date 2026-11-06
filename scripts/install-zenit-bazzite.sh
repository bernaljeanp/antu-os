#!/usr/bin/env bash
# Instala Zenit sin rpm-ostree, pacman ni cambios a /usr.
set -euo pipefail
if (( EUID == 0 )); then echo 'Ejecuta como tu usuario habitual, sin sudo. Se pedirá permiso solo para el servicio.' >&2; exit 1; fi
mode=${1:-}
if [[ $# -gt 1 || ( -n "$mode" && "$mode" != --sin-servicio ) ]]; then
    echo 'Uso: bash scripts/install-zenit-bazzite.sh [--sin-servicio]' >&2; exit 2
fi
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
data=${XDG_DATA_HOME:-$HOME/.local/share}/zenit
config=${XDG_CONFIG_HOME:-$HOME/.config}
command -v python3 >/dev/null
if [[ -e /usr/lib/systemd/system/zenit.service ]]; then
    echo 'Ya existe un servicio Zenit de la distribución. Usa esa instalación.' >&2; exit 1
fi
if [[ -z "$mode" ]]; then
    command -v systemctl >/dev/null
    command -v sudo >/dev/null
    if [[ " $(id -nG) " != *' wheel '* ]]; then
        echo 'El servicio requiere una cuenta administradora del grupo wheel. No se modificaron grupos.' >&2; exit 1
    fi
fi
mkdir -p "$data" "$config/autostart" "${XDG_DATA_HOME:-$HOME/.local/share}/applications"
python3 -m venv "$data/venv"
"$data/venv/bin/python" -m pip install --only-binary=:all: 'PyQt6==6.10.2'
mkdir -p "$data/zenit" "$data/inicio"
cp -a "$repo/files/system/usr/lib/antu/zenit/." "$data/zenit/"
cp -a "$repo/files/system/usr/lib/antu/inicio/." "$data/inicio/"
install -m 644 "$repo/files/system/usr/share/icons/hicolor/256x256/apps/zenit.png" "$data/zenit/zenit.png"
# Generar lanzadores con rutas absolutas y escape compatible con Desktop Entry.
"$data/venv/bin/python" - "$data" "$config" <<'PY'
import os, pathlib, shlex, sys
base, config = map(pathlib.Path, sys.argv[1:])
def launcher(name, argv):
    path = base / name
    path.write_text('#!/bin/sh\nexec ' + shlex.join([str(a) for a in argv]) + ' "$@"\n')
    path.chmod(0o755)
launcher('abrir', [base/'venv/bin/python', base/'zenit/app.py'])
launcher('zenit-cli', ['/usr/bin/python3', base/'zenit/zenit.py'])
def quote(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'
entry = '[Desktop Entry]\nType=Application\nName=Zenit\nComment=Control del equipo\nExec=' + quote(base/'abrir') + '\nIcon=' + str(base/'zenit/zenit.png') + '\nCategories=System;Monitor;\nTerminal=false\n'
(base.parent/'applications/zenit.desktop').write_text(entry)
(config/'autostart/zenit.desktop').write_text(entry.replace('\nIcon=', ' --bandeja\nIcon='))
PY
python3 "$data/zenit/zenit.py" autoprueba
if [[ -z "$mode" ]]; then
    # La copia que ejecuta root pertenece a root, fuera de la carpeta del usuario.
    sudo install -d -o root -g root -m 755 /var/opt/zenit
    sudo install -o root -g root -m 644 "$repo/files/system/usr/lib/antu/zenit/zenit.py" /var/opt/zenit/zenit.py
    sudo install -o root -g root -m 644 "$repo/installer/zenit-bazzite.service" /etc/systemd/system/zenit.service
    sudo systemctl daemon-reload
    sudo systemctl enable --now zenit.service
    sudo systemctl restart zenit.service
    # systemd active no garantiza que el socket ya atienda: comprobar una petición real.
    ready=false
    for attempt in {1..20}; do
        if "$data/zenit-cli" estado; then ready=true; break; fi
        sleep 0.5
    done
    if [[ $ready != true ]]; then echo 'El servicio no respondió. Revisa: journalctl -u zenit -b' >&2; exit 1; fi
else
    echo 'Interfaz instalada sin servicio: no podrá controlar el hardware hasta instalarlo.'
fi
printf 'Instalado. Abre Zenit desde el menú o ejecuta: %q\nCLI: %q estado\n' "$data/abrir" "$data/zenit-cli"
