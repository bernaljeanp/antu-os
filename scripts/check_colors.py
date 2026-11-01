"""Comprueba el contraste WCAG de los esquemas de color de Antu.

Uso: python scripts/check_colors.py   (sale con 1 si algún par baja de 4.5:1)
"""
import configparser
import pathlib
import sys

SCHEMES = pathlib.Path(__file__).parent.parent / "files/system/usr/share/color-schemes"
GROUPS = ["Window", "View", "Button", "Tooltip", "Header", "Selection", "Complementary"]
# Inactive cubre texto secundario legible; Active es acento de foco, no texto de lectura.
FOREGROUNDS = ["Normal", "Inactive", "Link", "Visited", "Negative", "Neutral", "Positive"]
MINIMUM = 4.5


def luminance(rgb):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(int(v)) for v in rgb.split(","))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def failures(path):
    ini = configparser.ConfigParser(interpolation=None)
    ini.optionxform = str
    ini.read(path, encoding="utf-8")
    for group in GROUPS:
        section = ini[f"Colors:{group}"]
        for bg in ("BackgroundNormal", "BackgroundAlternate"):
            for fg in FOREGROUNDS:
                ratio = contrast(section[f"Foreground{fg}"], section[bg])
                if ratio < MINIMUM:
                    yield f"{path.name} {group}: Foreground{fg} sobre {bg} = {ratio:.2f}"


if __name__ == "__main__":
    bad = [f for scheme in sorted(SCHEMES.glob("*.colors")) for f in failures(scheme)]
    print("\n".join(bad) or "Contraste OK en todos los esquemas (>= 4.5:1).")
    sys.exit(1 if bad else 0)
