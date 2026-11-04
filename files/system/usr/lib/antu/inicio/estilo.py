"""Sincroniza solo los dos estilos propios; conserva cualquier elección ajena a Antu.

Kvantum lee esta selección al abrir una app. Las ventanas existentes pueden necesitar
cerrarse y abrirse al cambiar entre Obsidiana y Salar. Sin Qt ni procesos gráficos extra.
"""
import configparser
import os
import re
from pathlib import Path
import time

THEMES = {"AntuObsidiana", "AntuSalar"}


def selection(kde, current):
    if kde.get("KDE", "widgetStyle", fallback="kvantum").lower() != "kvantum":
        return None
    scheme = kde.get("General", "ColorScheme", fallback="AntuObsidiana")
    return scheme if scheme in THEMES and current in THEMES else None


def synchronize(config):
    kde = configparser.ConfigParser(interpolation=None, strict=False)
    kde.optionxform = str
    kde.read(["/etc/xdg/kdeglobals", str(config / "kdeglobals")], encoding="utf-8")
    path = config / "Kvantum/kvantum.kvconfig"
    original = path.read_text(encoding="utf-8") if path.exists() else "theme=AntuObsidiana\n"
    # Kvantum guarda 'theme' antes del primer grupo INI, no en [General].
    lines = original.splitlines()
    index = next((i for i, s in enumerate(lines) if re.match(r"^\s*theme\s*=", s)), None)
    current = lines[index].split("=", 1)[1].strip() if index is not None else "AntuObsidiana"
    wanted = selection(kde, current)
    if wanted is None or (wanted == current and path.exists()):
        return
    if index is None:
        lines.insert(0, "theme=" + wanted)
    else:
        lines[index] = "theme=" + wanted
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def main():
    config = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    previous = None
    while True:
        paths = [config / "kdeglobals", config / "Kvantum/kvantum.kvconfig"]
        stamp = tuple((p.stat().st_mtime_ns, p.stat().st_size) if p.exists() else None for p in paths)
        if stamp != previous:
            try:
                synchronize(config)
            except (OSError, configparser.Error, UnicodeError):
                pass  # Una preferencia dañada no debe interrumpir el escritorio.
            previous = stamp
        time.sleep(3)


if __name__ == "__main__":
    main()
