"""Marca cada archivo de la imagen con el paquete de Arch al que pertenece (atributo user.component).

chunkah, que reempaqueta la imagen publicada (build.yml), agrupa por ese atributo: cada paquete queda en su propia
capa, o compartiendo capa con otros pequeños, así una actualización solo baja los paquetes que cambiaron.
"""
import glob
import os

DB = "/usr/lib/sysimage/lib/pacman/local"  # pacman guarda su estado aquí en Antu (ver Containerfile)

marcados = 0
for desc in glob.glob(f"{DB}/*/desc"):
    with open(desc) as f:
        lineas = f.read().split("\n")
    nombre = lineas[lineas.index("%NAME%") + 1]
    with open(os.path.join(os.path.dirname(desc), "files")) as f:
        lista = f.read().split("%FILES%\n", 1)[-1].split("\n\n", 1)[0].split("\n")
    for rel in lista:
        ruta = "/" + rel
        # Carpetas y enlaces no llevan el atributo; lo que vivía en /var ya no existe en la imagen.
        if not rel or rel.endswith("/") or os.path.islink(ruta) or not os.path.isfile(ruta):
            continue
        os.setxattr(ruta, "user.component", nombre.encode())
        marcados += 1
print(f"Reempaquetado: {marcados} archivos marcados con su paquete")
