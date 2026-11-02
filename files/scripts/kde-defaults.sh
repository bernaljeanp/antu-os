#!/usr/bin/env bash
# Valores por defecto de KDE para usuarios nuevos.
# KColorScheme lee los colores de los grupos [Colors:*] de kdeglobals, no del
# archivo .colors que nombra ColorScheme, así que se añaden los grupos completos.
# Se añade al final (>>) para no borrar lo que traiga la base; en KConfig la
# última clave repetida gana.
set -euo pipefail

mkdir -p /etc/xdg
cat /usr/share/antu/kdeglobals.base \
    /usr/share/color-schemes/AntuObsidiana.colors >> /etc/xdg/kdeglobals

# Algunas apps y KDE piden los mismos íconos con otro nombre, y un nombre que falta en Antu lo responde Breeze antes de
# probar el genérico (de ahí las carpetas azules). Si una imagen original no existe, la compilación falla.
enlazar() {  # carpeta nombre original
    for imagen in /usr/share/icons/Antu/*/"$1"/"$3.png"; do
        ln -s "$3.png" "$(dirname "$imagen")/$2.png"
    done
}
enlazar places inode-directory folder
enlazar apps plasmadiscover org.kde.discover
enlazar apps system-file-manager org.kde.dolphin
enlazar apps utilities-terminal org.kde.konsole
enlazar apps accessories-calculator org.kde.kcalc
enlazar apps ark org.kde.ark
enlazar apps gwenview org.kde.gwenview
enlazar apps kate org.kde.kate
enlazar apps spectacle org.kde.spectacle
