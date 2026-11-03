"""Estilo de Plasma «Antu»: vidrio de obsidiana con esquinas amplias para la barra, los menús, los avisos, las
descripciones emergentes y el resalte de las apps en la barra.

Uso: python scripts/make_plasma_theme.py   (requiere Pillow)
Escribe files/system/usr/share/plasma/desktoptheme/antu/. Cada superficie es un marco de 9 piezas en SVG con la
estructura de Breeze (piezas, máscaras para el desenfoque, sombras y marcas de margen), pintado con los colores del
esquema activo: sirve igual para Obsidiana y para Salar. La sombra se calcula con Pillow, se recorta por fuera del
vidrio (así no oscurece los bordes translúcidos) y va incrustada como PNG. Lo que este estilo no dibuja (botones,
barras de desplazamiento, campos de texto) lo toma Plasma de Breeze.
"""
import base64
import io
import json
import pathlib

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "files/system/usr/share/plasma/desktoptheme/antu"
C = 32  # lado de las piezas centrales: se estiran
SS = 4  # supermuestreo de la sombra


def png(img):
    datos = io.BytesIO()
    img.save(datos, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(datos.getvalue()).decode()


def marco(r, opacidad, sombra, margen):
    """SVG de un marco de radio r. sombra = (alcance, desplazamiento hacia abajo, desenfoque) o None."""
    L = 2 * r + C
    piezas = []

    def g(ident, *formas):
        piezas.append(f'<g id="{ident}">{"".join(formas)}</g>')

    fondo = f'class="ColorScheme-Background" style="fill:currentColor;fill-opacity:{opacidad}"'

    def borde(o):
        return f'class="ColorScheme-Text" style="fill:currentColor;fill-opacity:{o}"'

    luz, linea = 0.26, 0.09  # el borde de arriba recibe la luz
    brillo = 'style="fill:url(#brillo)"'  # y el vidrio la deja caer hacia abajo
    i = r - 1  # radio interior
    # Esquinas: un cuarto de disco de vidrio y el anillo del borde, sin superponerse (el vidrio es translúcido).
    g("topleft",
      f'<path {fondo} d="M1,{r} A{i},{i} 0 0 1 {r},1 L{r},{r} Z"/>',
      f'<path {brillo} d="M1,{r} A{i},{i} 0 0 1 {r},1 L{r},{r} Z"/>',
      f'<path {borde(luz)} d="M0,{r} A{r},{r} 0 0 1 {r},0 L{r},1 A{i},{i} 0 0 0 1,{r} Z"/>')
    g("top", f'<rect {fondo} x="{r}" y="1" width="{C}" height="{r - 1}"/>',
      f'<rect {brillo} x="{r}" y="1" width="{C}" height="{r - 1}"/>',
      f'<rect {borde(luz)} x="{r}" y="0" width="{C}" height="1"/>')
    g("topright",
      f'<path {fondo} d="M{r + C},1 A{i},{i} 0 0 1 {L - 1},{r} L{r + C},{r} Z"/>',
      f'<path {brillo} d="M{r + C},1 A{i},{i} 0 0 1 {L - 1},{r} L{r + C},{r} Z"/>',
      f'<path {borde(luz)} d="M{r + C},0 A{r},{r} 0 0 1 {L},{r} L{L - 1},{r} A{i},{i} 0 0 0 {r + C},1 Z"/>')
    g("left", f'<rect {fondo} x="1" y="{r}" width="{r - 1}" height="{C}"/>',
      f'<rect {borde(linea)} x="0" y="{r}" width="1" height="{C}"/>')
    g("center", f'<rect {fondo} x="{r}" y="{r}" width="{C}" height="{C}"/>')
    g("right", f'<rect {fondo} x="{r + C}" y="{r}" width="{r - 1}" height="{C}"/>',
      f'<rect {borde(linea)} x="{L - 1}" y="{r}" width="1" height="{C}"/>')
    g("bottomleft",
      f'<path {fondo} d="M{r},{L - 1} A{i},{i} 0 0 1 1,{r + C} L{r},{r + C} Z"/>',
      f'<path {borde(linea)} d="M{r},{L} A{r},{r} 0 0 1 0,{r + C} L1,{r + C} A{i},{i} 0 0 0 {r},{L - 1} Z"/>')
    g("bottom", f'<rect {fondo} x="{r}" y="{r + C}" width="{C}" height="{r - 1}"/>',
      f'<rect {borde(linea)} x="{r}" y="{L - 1}" width="{C}" height="1"/>')
    g("bottomright",
      f'<path {fondo} d="M{L - 1},{r + C} A{i},{i} 0 0 1 {r + C},{L - 1} L{r + C},{r + C} Z"/>',
      f'<path {borde(linea)} d="M{L},{r + C} A{r},{r} 0 0 1 {r + C},{L} L{r + C},{L - 1} A{i},{i} 0 0 0 {L - 1},{r + C} Z"/>')

    # Márgenes del contenido: lejos de las esquinas redondas.
    oculto = 'style="fill:none"'
    for lado, (x, y, w, h) in {"top": (r, 0, 4, margen), "bottom": (r, L - margen, 4, margen),
                               "left": (0, r, margen, 4), "right": (L - margen, r, margen, 4)}.items():
        piezas.append(f'<rect id="hint-{lado}-margin" {oculto} x="{x}" y="{y}" width="{w}" height="{h}"/>')
    piezas.append(f'<rect id="hint-stretch-borders" {oculto} x="{r}" y="{r}" width="2" height="2"/>')

    # Máscara: la forma del vidrio, para el desenfoque detrás.
    mx = L + 16
    negro = 'style="fill:#000000"'
    mascara = {
        "topleft": f'M{mx},{r} A{r},{r} 0 0 1 {mx + r},0 L{mx + r},{r} Z',
        "topright": f'M{mx + r + C},0 A{r},{r} 0 0 1 {mx + L},{r} L{mx + r + C},{r} Z',
        "bottomleft": f'M{mx + r},{L} A{r},{r} 0 0 1 {mx},{r + C} L{mx + r},{r + C} Z',
        "bottomright": f'M{mx + L},{r + C} A{r},{r} 0 0 1 {mx + r + C},{L} L{mx + r + C},{r + C} Z',
    }
    for ident, d in mascara.items():
        piezas.append(f'<path id="mask-{ident}" {negro} d="{d}"/>')
    for ident, (x, y, w, h) in {"top": (r, 0, C, r), "bottom": (r, r + C, C, r), "left": (0, r, r, C),
                                "right": (r + C, r, r, C), "center": (r, r, C, C)}.items():
        piezas.append(f'<rect id="mask-{ident}" {negro} x="{mx + x}" y="{y}" width="{w}" height="{h}"/>')

    ancho, alto = 2 * mx, L
    if sombra:
        alcance, abajo, desenfoque = sombra
        arriba, lados, bajo = alcance - abajo, alcance, alcance + abajo
        W, H = lados + L + lados, arriba + L + bajo
        capa = Image.new("L", (W * SS, H * SS))
        ImageDraw.Draw(capa).rounded_rectangle(
            (lados * SS, (arriba + abajo) * SS, (lados + L) * SS, (arriba + abajo + L) * SS), radius=r * SS, fill=150)
        capa = capa.filter(ImageFilter.GaussianBlur(desenfoque * SS))
        vidrio = Image.new("L", (W * SS, H * SS))
        ImageDraw.Draw(vidrio).rounded_rectangle(
            (lados * SS, arriba * SS, (lados + L) * SS, (arriba + L) * SS), radius=r * SS, fill=255)
        capa = ImageChops.subtract(capa, vidrio)  # nada de sombra bajo el vidrio
        capa = capa.resize((W, H), Image.Resampling.LANCZOS)
        sombra_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sombra_img.putalpha(capa)
        sy = alto + 16
        xs = [0, lados + r, lados + r + C, W]
        ys = [0, arriba + r, arriba + r + C, H]
        nombres = [["topleft", "top", "topright"], ["left", "center", "right"], ["bottomleft", "bottom", "bottomright"]]
        for fila in range(3):
            for col in range(3):
                x0, x1, y0, y1 = xs[col], xs[col + 1], ys[fila], ys[fila + 1]
                trozo = sombra_img.crop((x0, y0, x1, y1))
                piezas.append(f'<image id="shadow-{nombres[fila][col]}" x="{x0}" y="{sy + y0}" width="{x1 - x0}" '
                              f'height="{y1 - y0}" xlink:href="{png(trozo)}"/>')
        hx = W + 16
        for lado, (w, h) in {"top": (2, arriba), "bottom": (2, bajo), "left": (lados, 2), "right": (lados, 2)}.items():
            piezas.append(f'<rect id="shadow-hint-{lado}-margin" {oculto} x="{hx}" y="{sy}" width="{w}" height="{h}"/>')
        ancho, alto = max(ancho, hx + alcance + 4), sy + H

    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}">\n'
            '<defs><style id="current-color-scheme" type="text/css">'
            '.ColorScheme-Background{color:#141418}.ColorScheme-Text{color:#f5f5f7}</style></defs>\n'
            + "\n".join(piezas) + "\n</svg>\n")


def tareas():
    """SVG de widgets/tasks.svg: resaltes de vidrio de las apps en la barra, redondeados y separados de sus bordes."""
    a, r, C2 = 3, 6, 16  # separación del borde, radio y lado de las piezas centrales
    b = a + r  # lado de las piezas de borde
    L = 2 * b + C2
    P, R = b + C2, L - a  # inicio de la columna derecha y borde exterior del vidrio
    i = r - 1
    invisible = 'style="fill:#000000;fill-opacity:0.002"'  # da a cada pieza su tamaño completo, con la separación
    # Prefijo: (color del esquema, opacidad del vidrio, opacidad del borde)
    estados = {
        "normal": ("Text", 0.05, 0.10),
        "minimized": ("Text", 0.02, 0.06),
        "hover": ("Text", 0.10, 0.18),
        "focus": ("Highlight", 0.26, 0.60),
        "attention": ("Highlight", 0.45, 0.85),
        "progress": ("Highlight", 0.35, 0.0),
    }
    piezas = []
    for fila, (prefijo, (color, vidrio, linea)) in enumerate(estados.items()):
        y0 = fila * (L + 4)

        def Y(v):
            return y0 + v

        def g(nombre, x, y, w, h, *formas):
            piezas.append(f'<g id="{prefijo}-{nombre}"><rect {invisible} x="{x}" y="{Y(y)}" width="{w}" height="{h}"/>'
                          f'{"".join(formas)}</g>')

        fondo = f'class="ColorScheme-{color}" style="fill:currentColor;fill-opacity:{vidrio}"'
        borde = f'class="ColorScheme-{color}" style="fill:currentColor;fill-opacity:{linea}"'
        g("topleft", 0, 0, b, b,
          f'<path {fondo} d="M{a + 1},{Y(b)} A{i},{i} 0 0 1 {b},{Y(a + 1)} L{b},{Y(b)} Z"/>',
          f'<path {borde} d="M{a},{Y(b)} A{r},{r} 0 0 1 {b},{Y(a)} L{b},{Y(a + 1)} A{i},{i} 0 0 0 {a + 1},{Y(b)} Z"/>')
        g("top", b, 0, C2, b, f'<rect {fondo} x="{b}" y="{Y(a + 1)}" width="{C2}" height="{r - 1}"/>',
          f'<rect {borde} x="{b}" y="{Y(a)}" width="{C2}" height="1"/>')
        g("topright", P, 0, b, b,
          f'<path {fondo} d="M{P},{Y(a + 1)} A{i},{i} 0 0 1 {R - 1},{Y(b)} L{P},{Y(b)} Z"/>',
          f'<path {borde} d="M{P},{Y(a)} A{r},{r} 0 0 1 {R},{Y(b)} L{R - 1},{Y(b)} A{i},{i} 0 0 0 {P},{Y(a + 1)} Z"/>')
        g("left", 0, b, b, C2, f'<rect {fondo} x="{a + 1}" y="{Y(b)}" width="{r - 1}" height="{C2}"/>',
          f'<rect {borde} x="{a}" y="{Y(b)}" width="1" height="{C2}"/>')
        g("center", b, b, C2, C2, f'<rect {fondo} x="{b}" y="{Y(b)}" width="{C2}" height="{C2}"/>')
        g("right", P, b, b, C2, f'<rect {fondo} x="{P}" y="{Y(b)}" width="{r - 1}" height="{C2}"/>',
          f'<rect {borde} x="{R - 1}" y="{Y(b)}" width="1" height="{C2}"/>')
        g("bottomleft", 0, P, b, b,
          f'<path {fondo} d="M{b},{Y(R - 1)} A{i},{i} 0 0 1 {a + 1},{Y(P)} L{b},{Y(P)} Z"/>',
          f'<path {borde} d="M{b},{Y(R)} A{r},{r} 0 0 1 {a},{Y(P)} L{a + 1},{Y(P)} A{i},{i} 0 0 0 {b},{Y(R - 1)} Z"/>')
        g("bottom", b, P, C2, b, f'<rect {fondo} x="{b}" y="{Y(P)}" width="{C2}" height="{r - 1}"/>',
          f'<rect {borde} x="{b}" y="{Y(R - 1)}" width="{C2}" height="1"/>')
        g("bottomright", P, P, b, b,
          f'<path {fondo} d="M{R - 1},{Y(P)} A{i},{i} 0 0 1 {P},{Y(R - 1)} L{P},{Y(P)} Z"/>',
          f'<path {borde} d="M{R},{Y(P)} A{r},{r} 0 0 1 {P},{Y(R)} L{P},{Y(R - 1)} A{i},{i} 0 0 0 {R - 1},{Y(P)} Z"/>')
        # El ícono se mide con estos márgenes, no con el tamaño de las piezas: así no se achica.
        for lado, (x, y, w, h) in {"top": (b, 0, 4, 5), "bottom": (b, L - 5, 4, 5),
                                   "left": (0, b, 5, 4), "right": (L - 5, b, 5, 4)}.items():
            piezas.append(f'<rect id="{prefijo}-hint-{lado}-margin" style="fill:none" x="{x}" y="{Y(y)}" '
                          f'width="{w}" height="{h}"/>')
    alto = len(estados) * (L + 4)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{L}" height="{alto}" viewBox="0 0 {L} {alto}">\n'
            '<defs><style id="current-color-scheme" type="text/css">'
            '.ColorScheme-Text{color:#f5f5f7}.ColorScheme-Highlight{color:#ff5a1f}</style>'
            f'<linearGradient id="brillo" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{r}">'
            '<stop offset="0" stop-color="#ffffff" stop-opacity="0.11"/>'
            '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient></defs>\n'
            + "\n".join(piezas) + "\n</svg>\n")


# Superficie: (archivo, radio, margen del contenido, sombra)
SUPERFICIES = [
    ("dialogs/background.svg", 14, 7, (30, 10, 13)),   # menú, bandeja, avisos, ventanas emergentes
    ("widgets/panel-background.svg", 14, 4, (22, 6, 9)),  # barra flotante
    ("widgets/tooltip.svg", 10, 6, (16, 5, 7)),       # descripciones emergentes
]


def main():
    for archivo, r, margen, sombra in SUPERFICIES:
        # Sin desenfoque disponible: casi opaco. Con desenfoque (translucent/): vidrio de verdad.
        for carpeta, opacidad in (("", 0.96), ("translucent/", 0.74)):
            destino = DEST / carpeta / archivo
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(marco(r, opacidad, sombra, margen), encoding="utf-8", newline="\n")
    (DEST / "widgets/tasks.svg").write_text(tareas(), encoding="utf-8", newline="\n")
    (DEST / "metadata.json").write_text(json.dumps({
        "KPackageStructure": "Plasma/Theme",
        "KPlugin": {
            "Authors": [{"Name": "Antu OS"}],
            "Description": "Vidrio de obsidiana con esquinas amplias y acentos de lava.",
            "Id": "antu",
            "License": "GPL-3.0-or-later",
            "Name": "Antu",
            "Version": "1.0",
            "Website": "https://github.com/bernaljeanp/antu-os",
        },
        "X-Plasma-API-Minimum-Version": "6.0",
    }, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")
    (DEST / "plasmarc").write_text(
        "[ContrastEffect]\nenabled=true\ncontrast=0.45\nintensity=0.9\nsaturation=1.4\n\n"
        "[BlurBehindEffect]\nenabled=true\n\n[AdaptiveTransparency]\nenabled=true\n",
        encoding="utf-8", newline="\n")
    print("Estilo de Plasma Antu escrito en", DEST.relative_to(ROOT))


if __name__ == "__main__":
    main()
