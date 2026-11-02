"""Piezas de «Encendido», la animación de arranque (antu.script): una consola de lava a toda velocidad, una falla digital
y el símbolo de Antu. Están medidas para una pantalla de 1600 de alto; antu.script las escala.

El registro y los paneles son decorativos: nombran etapas reales del arranque, pero no dicen cómo le fue a este equipo.

Uso: python scripts/make_plymouth.py   (requiere Pillow y la fuente Cascadia Mono, licencia OFL)
"""
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFont

from make_brand import FONT, LAVA, ROOT, TRACK, symbol_png

PLY = ROOT / "files/system/usr/share/plymouth/themes/antu"
MONO = next(p for p in ("C:/Windows/Fonts/CascadiaMono.ttf", "/usr/share/fonts/TTF/CascadiaMono.ttf",
                        "/usr/share/fonts/TTF/DejaVuSansMono.ttf") if os.path.exists(p))
TENUE = "#963A18"
INK = "#F5F5F7"
FONDO = "#050507"  # el mismo de Window.SetBackground en antu.script

LINEA = 26  # alto de una línea del registro
LINEAS = 120
ETAPAS = ["núcleo: cargando", "núcleo: mapa de memoria {h}-{h}", "pci {p}:00.0: buscando dispositivo",
          "composefs: montando capa {n}", "composefs: verificando {h}{h}", "nvidia: preparando controlador",
          "pipewire: preparando sonido", "red: buscando interfaces", "systemd: alcanzando destino {d}",
          "zram: preparando memoria comprimida", "vulkan: preparando gráficos", "plasma: abriendo el escritorio"]
PANELES = ["PROCESADOR", "GRÁFICA", "MEMORIA", "DISCO", "RED", "SONIDO"]
ANCHO_FALLA, ALTO_FALLA = 1000, 480
ANCHO_TITULO, ALTO_TITULO = 640, 110
TITULO = "ANTU OS"
ESPACIO = 20  # entre letras del título


def mono(tam):
    return ImageFont.truetype(MONO, tam)


def titulo_font():
    f = ImageFont.truetype(str(FONT), 76)
    f.set_variation_by_axes([32, 700])
    return f


def guardar(im, nombre):
    im.save(PLY / nombre, optimize=True)


def texto(cadena, tam, color):
    f = mono(tam)
    ancho = int(f.getlength(cadena)) + 2
    im = Image.new("RGBA", (ancho, int(tam * 1.4)))
    ImageDraw.Draw(im).text((1, 0), cadena, font=f, fill=color)
    return im


def registro():
    azar = random.Random(7)
    lineas = []
    for i in range(LINEAS):
        plantilla = azar.choice(ETAPAS)
        lineas.append(f"[{i * 0.021:7.3f}] " + plantilla.format(
            h=f"{azar.randrange(65536):04x}", p=f"{azar.randrange(9):02x}", n=azar.randrange(1, 129),
            d=azar.choice(["basic", "sysinit", "network", "multi-user", "graphical"])))
    f = mono(22)
    im = Image.new("RGBA", (int(max(f.getlength(x) for x in lineas)) + 4, LINEAS * LINEA))
    d = ImageDraw.Draw(im)
    for i, x in enumerate(lineas):
        d.text((2, i * LINEA), x, font=f, fill=LAVA)
    guardar(im, "registro.png")
    # Velo: oscurece lo más antiguo, arriba; lo último que aparece, abajo, queda encendido.
    velo = Image.new("RGBA", (1, 256), FONDO)
    velo.putalpha(Image.linear_gradient("L").resize((1, 256)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                  .point(lambda v: round(v * 0.9)))
    guardar(velo, "velo.png")
    Image.new("RGBA", (1, 1), FONDO).save(PLY / "franja.png")
    Image.new("RGBA", (14, 22), LAVA).save(PLY / "cursor.png")


def paneles():
    f, f2 = mono(18), mono(19)
    ancho, alto, hueco = 360, 150, 30
    for k in range(4):
        azar = random.Random(100 + k)
        im = Image.new("RGBA", (ancho, len(PANELES) * (alto + hueco) - hueco))
        d = ImageDraw.Draw(im)
        for j, nombre in enumerate(PANELES):
            y = j * (alto + hueco)
            d.rectangle((0, y, ancho - 1, y + alto - 1), outline=TENUE, width=2)
            d.text((16, y + 12), nombre, font=f2, fill=LAVA)
            for fila in range(3):
                d.text((16, y + 50 + fila * 30), " ".join(f"{azar.randrange(256):02X}" for _ in range(10)), font=f, fill=TENUE)
        guardar(im, f"panel-{k}.png")


def marco():
    largo, grueso = 60, 3
    for n, (voltear_x, voltear_y) in enumerate([(False, False), (True, False), (False, True), (True, True)], 1):
        im = Image.new("RGBA", (largo, largo))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, largo - 1, grueso - 1), fill=TENUE)
        d.rectangle((0, 0, grueso - 1, largo - 1), fill=TENUE)
        if voltear_x:
            im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if voltear_y:
            im = im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        guardar(im, f"esquina-{n}.png")
    guardar(texto("ANTU OS // SECUENCIA DE ARRANQUE", 20, TENUE), "rotulo-arriba.png")
    guardar(texto("núcleo · bootc · composefs", 20, TENUE), "rotulo-abajo.png")
    # Contador: letras de ancho fijo, para que los dígitos no bailen.
    for c in "0123456789":
        guardar(texto(c, 20, TENUE), f"dig-{c}.png")
    guardar(texto(".", 20, TENUE), "dig-punto.png")
    guardar(texto("T+", 20, TENUE), "dig-t.png")


def titulo(letras):
    f = titulo_font()
    im = Image.new("RGBA", (ANCHO_TITULO, ALTO_TITULO))
    d = ImageDraw.Draw(im)
    total = sum(f.getlength(c) + ESPACIO for c in TITULO) - ESPACIO
    x = (ANCHO_TITULO - total) / 2
    for c in TITULO[:letras]:
        d.text((x, 0), c, font=f, fill=INK)
        x += f.getlength(c) + ESPACIO
    return im


def falla():
    """El símbolo y el título cortados en franjas que se van acomodando, con un fantasma de lava."""
    limpio = Image.new("RGBA", (ANCHO_FALLA, ALTO_FALLA))
    limpio.alpha_composite(symbol_png(240), ((ANCHO_FALLA - 240) // 2, 30))  # centro del símbolo a 150 del borde de arriba
    limpio.alpha_composite(titulo(len(TITULO)), ((ANCHO_FALLA - ANCHO_TITULO) // 2, 300))
    pasos = 6
    for k in range(pasos):
        fuerza = 1 - k / pasos
        azar = random.Random(40 + k)
        cortado = Image.new("RGBA", limpio.size)
        y = 0
        while y < ALTO_FALLA:
            alto = azar.randrange(8, 44)
            dx = int(azar.choice((-1, 1)) * azar.random() * 150 * fuerza) if azar.random() < 0.55 else 0
            cortado.paste(limpio.crop((0, y, ANCHO_FALLA, y + alto)), (dx, y))
            y += alto
        fantasma = Image.new("RGBA", limpio.size, LAVA)
        fantasma.putalpha(ImageChops.offset(cortado, int(22 * fuerza) + 3, 0).getchannel("A").point(lambda v: round(v * 0.55)))
        fantasma.alpha_composite(cortado)
        guardar(fantasma, f"falla-{k}.png")


def main():
    PLY.mkdir(parents=True, exist_ok=True)
    registro()
    paneles()
    marco()
    falla()
    guardar(symbol_png(512), "simbolo.png")
    for n in range(1, len(TITULO) + 1):
        guardar(titulo(n), f"titulo-{n}.png")
    for n, etapa in enumerate(["cargando el sistema", "preparando los gráficos", "abriendo el escritorio"]):
        guardar(texto(etapa, 22, LAVA), f"etapa-{n}.png")
    # Halo: degradado radial suave que se apaga antes del borde, para que nunca se vea el cuadrado.
    halo = Image.new("RGBA", (512, 512), LAVA)
    halo.putalpha(Image.radial_gradient("L").resize((512, 512), Image.Resampling.BICUBIC)
                  .point(lambda v: round(255 * 0.75 * max(0.0, 1 - v / 250) ** 2.4)))
    guardar(halo, "halo.png")
    Image.new("RGBA", (1, 1), TRACK).save(PLY / "track.png")
    Image.new("RGBA", (1, 1), LAVA).save(PLY / "fill.png")
    barrido = Image.new("RGBA", (1, 1), LAVA)
    barrido.putalpha(36)
    barrido.save(PLY / "barrido.png")


if __name__ == "__main__":
    main()
