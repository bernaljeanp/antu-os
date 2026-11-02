"""Dibuja los fondos de Antu: un fragmento de red de metro con las cuatro líneas del sistema.

Uso: python scripts/make_wallpapers.py   (requiere Pillow)
Escribe images/ (Andén, día) e images_dark/ (Túnel, noche) del paquete de fondo «Antu».
"""
import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).parent.parent
PKG = ROOT / "files/system/usr/share/wallpapers/Antu/contents"
W, H = 3840, 2160
SS = 2  # supermuestreo para bordes suaves

LINES = {  # colores de línea del sistema (ver DESIGN de la superficie)
    "jugar": "#C8281E", "trabajar": "#E9A800", "familia": "#138A4B", "sistema": "#1450A0",
}
GROUNDS = {"images": ("#F7F6F2", "#1C1C1B"), "images_dark": ("#141517", "#F2F1EC")}

# Geometría en píxeles de 3840x2160: solo tramos horizontales, verticales y a 45 grados exactos (plano de metro).
# Las cuatro líneas corren en paralelo desde la combinación Antu hacia la derecha y se separan en ramales sin cruzarse.
STROKE, GAP = 30, 44          # grosor de línea y distancia entre carriles paralelos
CX, CY = 2480, 1200           # combinación
LANE = {"sistema": -1.5, "familia": -0.5, "trabajar": 0.5, "jugar": 1.5}


def lane_y(name):
    return CY + LANE[name] * GAP


def diag(x, y, dy, direction=-1):
    """Punto tras un tramo a 45 grados que avanza dy en vertical (hacia la izquierda por defecto)."""
    return (x + direction * abs(dy), y + dy)


ys, yf, yt, yj = (lane_y(n) for n in ("sistema", "familia", "trabajar", "jugar"))
ROUTES = {
    # arriba: sube a 45 grados y sale por el borde superior
    "sistema": [(W + 60, ys), (2380, ys), diag(2380, ys, -500), (diag(2380, ys, -500)[0], -60)],
    # sigue recto hacia la izquierda
    "familia": [(W + 60, yf), (-60, yf)],
    # baja más lejos y sale por la izquierda
    "trabajar": [(W + 60, yt), (1900, yt), diag(1900, yt, 278), (-60, yt + 278)],
    # baja primero y sale por el borde inferior
    "jugar": [(W + 60, yj), (2340, yj), diag(2340, yj, 434), (diag(2340, yj, 434)[0], H + 60)],
}
STATIONS = {  # estaciones en coordenadas de píxel, sobre cada línea
    "sistema": [(ROUTES["sistema"][2][0], 320)],
    "familia": [(560, yf), (1240, yf), (3300, yf)],
    "trabajar": [(820, yt + 278)],
    "jugar": [(ROUTES["jugar"][2][0], 1960)],
}


def draw(folder, ground, ink):
    s = SS
    img = Image.new("RGB", (W * s, H * s), ground)
    d = ImageDraw.Draw(img)
    for name, route in ROUTES.items():
        d.line([(x * s, y * s) for x, y in route], fill=LINES[name], width=STROKE * s, joint="curve")
    tick = 24 * s
    for name, points in STATIONS.items():
        for x, y in points:
            x, y = x * s, y * s
            d.ellipse([x - tick, y - tick, x + tick, y + tick], fill=ground, outline=LINES[name], width=9 * s)
    # Combinación: una placa vertical que abarca los cuatro carriles.
    half_w, top, bottom = 54 * s, (ys - 46) * s, (yj + 46) * s
    d.rounded_rectangle([CX * s - half_w, top, CX * s + half_w, bottom], radius=half_w, fill=ground, outline=ink, width=12 * s)
    out = img.resize((W, H), Image.LANCZOS)
    path = PKG / folder / f"{W}x{H}.png"
    out.save(path, optimize=True)
    return path


if __name__ == "__main__":
    for folder, (ground, ink) in GROUNDS.items():
        print("escrito", draw(folder, ground, ink).relative_to(ROOT))
