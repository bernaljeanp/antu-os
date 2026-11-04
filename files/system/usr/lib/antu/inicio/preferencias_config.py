"""Lectura de preferencias KDE sin dependencias gráficas."""
import configparser
import pathlib
import math


def factor_animacion(rutas=None):
    if rutas is None:
        rutas = [pathlib.Path("/etc/xdg/kdeglobals"), pathlib.Path.home() / ".config/kdeglobals"]
    valor = 1.0
    for ruta in rutas:
        cp = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            cp.read(ruta, encoding="utf-8")
            if cp.has_option("KDE", "AnimationDurationFactor"):
                candidato = float(cp["KDE"]["AnimationDurationFactor"])
                if math.isfinite(candidato):
                    valor = candidato
        except (OSError, ValueError, configparser.Error):
            continue
    return max(0.0, min(4.0, valor))
