#!/usr/bin/env python3
"""Valida el escritorio empaquetado y emite su manifiesto. Sin red ni cambios de configuración.

--root ensaya una raíz aislada; --runtime verifica Qt solo dentro de la imagen real.
"""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET


def verificar(root, live=False, runtime=False):
    root = Path(root).resolve()
    if runtime and root != Path("/"):
        raise ValueError("--runtime debe ejecutarse dentro de la imagen, con raíz /")
    files = {}

    def asset(name):
        path = root / name.lstrip("/")
        if not path.is_file():
            raise ValueError("Falta en la imagen: /" + name.lstrip("/"))
        data = path.read_bytes()
        files[name.lstrip("/")] = hashlib.sha256(data).hexdigest()
        return data

    def text(name):
        data = asset(name)
        if b"\r" in data:
            raise ValueError("Se requieren finales LF: " + name)
        return data.decode("utf-8")

    def ini(name):
        cp = configparser.ConfigParser(interpolation=None, strict=False)
        cp.read_string(text(name))
        return cp

    def require(value, message):
        if not value:
            raise ValueError(message)

    config = ini("etc/xdg/kdeglobals")
    require(config.get("Icons", "Theme") == "Antu", "El tema de iconos empaquetado no es Antu")
    require(config.get("KDE", "widgetStyle") == "kvantum", "El estilo Qt empaquetado no es Kvantum")
    require("theme=AntuObsidiana" in text("etc/xdg/Kvantum/kvantum.kvconfig"), "Falta el estilo inicial de Antu")
    for theme in ("AntuObsidiana", "AntuSalar"):
        text(f"usr/share/Kvantum/{theme}/{theme}.kvconfig")
        text(f"usr/share/Kvantum/{theme}/{theme}.svg")
    for name in ("org.antuos.desktop", "org.antuos.mac"):
        base = f"usr/share/plasma/look-and-feel/{name}/contents/"
        require("Theme=Antu" in text(base + "defaults"), "Un layout conserva iconos ajenos al tema")
        layout = text(base + "layouts/org.kde.plasma.desktop-layout.js")
        require('"applications:zenit.desktop"' not in layout, "Zenit sigue fijado en un layout inicial")
        require('writeConfig("iconSpacing", 2)' in layout, "Falta el espaciado de tareas")
    text("usr/share/plasma/shells/org.kde.plasma.desktop/contents/updates/antu-2026-11-zenit-tray.js")
    for path in (root / "usr/share/plasma/desktoptheme/antu").rglob("*.svg"):
        source = text(path.relative_to(root).as_posix())
        ids = {node.attrib["id"] for node in ET.fromstring(source).iter() if "id" in node.attrib}
        for reference in re.findall(r"url\(#([^\)]+)\)", source):
            require(reference in ids, "Referencia SVG sin definición: " + reference)
    tasks = text("usr/share/plasma/desktoptheme/antu/widgets/tasks.svg")
    for state in ("normal", "minimized", "focus", "normal-hover", "focus-hover", "attention", "progress"):
        require(f'id="south-{state}-bottom"' in tasks, "Falta un estado nativo: " + state)
    theme_path = "usr/share/icons/Antu/"
    index = ini(theme_path + "index.theme")
    require(index["Icon Theme"]["Inherits"] == "breeze-dark,hicolor", "Herencia de iconos incorrecta")
    directories = index["Icon Theme"]["Directories"].split(",")
    require(len(directories) == 32, "Faltan directorios de tamaños del tema")
    pngs = 0
    for directory in directories:
        size = int(index[directory]["Size"])
        require(index[directory]["Type"] == "Fixed", "Directorio de iconos no fijo")
        for path in (root / theme_path / directory).glob("*.png"):
            data = asset(path.relative_to(root).as_posix())
            require(data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) > 32, "PNG inválido: " + str(path))
            require(struct.unpack(">II", data[16:24]) == (size, size) and data[25] == 6, "Tamaño o transparencia incorrectos: " + str(path))
            pngs += 1
    require(pngs >= 464, "El tema está incompleto")
    for size in (16, 22, 24, 32, 48, 64, 128, 256):
        for name in ("folder", "folder-games", "user-home"):
            asset(f"{theme_path}{size}x{size}/places/{name}.png")
    qml = "usr/lib/antu/inicio/"
    for line in text(qml + "qmldir").splitlines():
        if line.strip() and not line.startswith("#"):
            text(qml + line.split()[-1])
    for name in ("preferencias.py", "preferencias_config.py", "estilo.py"):
        compile(text(qml + name), qml + name, "exec")
    for directory, name in (("biblioteca", "Biblioteca"), ("observatorio", "Observatorio"), ("zenit", "Zenit"),
                             ("actualizaciones", "Actualizaciones"), ("aviso", "VentanaAviso")):
        text(f"usr/lib/antu/{directory}/{name}.qml")
    text("etc/xdg/autostart/antu-estilo.desktop")
    for name in ("centro.py", "catalogo.py", "respaldo.py", "rendimiento.py"):
        compile(text("usr/lib/antu/centro/" + name), name, "exec")
    compile(text("usr/lib/antu/preparar-helper"), "preparar-helper", "exec")
    text("usr/share/applications/antu-centro.desktop")
    text("usr/share/doc/antu/recuperacion.html")
    text("usr/share/plymouth/themes/antu/antu.script")
    asset("usr/share/plymouth/themes/antu/titulo-estatico-2x.png")
    asset("usr/share/wallpapers/Paranal/contents/images_dark/3840x2160.jpg")
    base_id = None
    if live:
        original = json.loads(asset("usr/share/antu/escritorio.json"))
        require(original["phase"] == "system", "El manifiesto base no corresponde al sistema instalado")
        for name, digest in original["files"].items():
            require(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, "El live difiere del escritorio que se instala: " + name)
        base_id = original["content_id"]
        for directory, name in (("bienvenida", "Bienvenida"), ("informe", "Informe"), ("instalador", "Instalador")):
            text(f"usr/lib/antu/{directory}/{name}.qml")
        for name in ("bienvenida/bienvenida.py", "informe/registro.py"):
            compile(text("usr/lib/antu/" + name), name, "exec")
        compile(text("usr/lib/antu/instalador/almacenamiento.py"), "almacenamiento.py", "exec")
        text("usr/lib/antu/instalador/instalar-entero.sh")
        require("bienvenida/bienvenida.py" in text("etc/xdg/autostart/antu-instalador.desktop"), "El USB no abre la bienvenida")
        text("usr/share/applications/antu-bienvenida.desktop")
        text("usr/lib/systemd/system/antu-registro-live.service")
    qt_style = "not_checked_in_staging"
    if runtime:
        from PyQt6.QtWidgets import QStyleFactory
        import gi
        gi.require_version("Flatpak", "1.0")
        from gi.repository import Flatpak
        require(hasattr(Flatpak.TransactionProgress, "get_bytes_transferred"), "Falta la API de progreso de Flatpak")
        require("kvantum" in (key.lower() for key in QStyleFactory.keys()), "El motor Qt Kvantum no carga en la imagen")
        qt_style = "kvantum_available"
    fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"phase": "live" if live else "system", "content_id": fingerprint, "base_content_id": base_id,
            "theme": "Antu", "style": qt_style, "png_files_including_aliases": pngs, "files": files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/"))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--runtime", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(verificar(args.root, args.live, args.runtime), sort_keys=True, indent=2))
    except (ValueError, OSError, configparser.Error, KeyError, ET.ParseError, ImportError) as error:
        print("Escritorio de Antu incompleto: " + str(error), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
