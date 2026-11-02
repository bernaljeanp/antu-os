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
