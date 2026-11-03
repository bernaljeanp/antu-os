# Encargo: íconos de la Biblioteca y el Observatorio

Antu OS necesita dos íconos de aplicación nuevos, de la **misma familia** que los que ya existen (`antu`, `antu-inicio`, `antu-instalador`, `antu-eclipse`, `antu-ia`).

Lee primero `brand/ART-DIRECTION.md`, `scripts/render_art.py` y `scripts/make_brand.py`: ahí está cómo se hicieron. Usa ese mismo camino (la misma escena, la misma luz y el mismo cuadrado redondeado), agregando los dos nombres nuevos, en vez de inventar otro proceso. Blender 5.2 está instalado en este PC.

## Los dos íconos

- **`antu-biblioteca`**: una estantería o pila de cartuchos de juego, vista como objeto real. Un cartucho sobresale, con su etiqueta en lava, porque es el que se está revisando.
- **`antu-observatorio`**: la cúpula de un observatorio astronómico como la de Paranal, abierta, con una línea de luz lava que sale de la ranura hacia el cielo oscuro. No un telescopio de caricatura ni un velocímetro.

## Requisitos

- Mismo material que la familia: obsidiana, canto y lava `#FF5A1F`. Con volumen y luz real.
- **Nada plano, nada vectorial simple, nada que parezca del año 2000**: sin metal cromado, sin biseles marcados y sin brillo tipo Aqua.
- Que se reconozcan en 16 y 24 píxeles, como exige `brand/ART-DIRECTION.md`: los tamaños chicos se simplifican, no se reducen.
- Motivos originales. No copies íconos de otros sistemas ni logos de tiendas o juegos.
- Sin texto dentro del ícono.

## Entrega

- `files/system/usr/share/icons/hicolor/<tamaño>x<tamaño>/apps/antu-biblioteca.png` y `antu-observatorio.png`, en los mismos tamaños que `antu-eclipse` (16, 32, 48, 64, 128, 256, 512 y 1024).
- Los cambios mínimos en `scripts/render_art.py` y `scripts/make_brand.py` para que los dos nombres queden en el proceso normal.
- Una vista de la familia completa en `brand/previews/familia-con-nuevos.png`, a tamaño grande y en 24 píxeles, para que se pueda revisar.

## Límites

- No cambies los íconos existentes ni ningún otro archivo del proyecto.
- **No hagas commit ni push.** Deja los archivos listos en el árbol de trabajo.
- Al terminar, resume en español qué archivos creaste y cómo los comprobaste.
