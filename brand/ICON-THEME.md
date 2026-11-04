La familia Antu trata cada ícono como un objeto: obsidiana pulida, canto anodizado y grabado de plata, bajo la misma luz superior izquierda de las cinco apps aprobadas.
Las carpetas comparten una única carcasa; cambia el grabado y Juegos incorpora una pestaña de esmalte lava. Los documentos son folios oscuros con una esquina de plata doblada y acentos de material discretos, sin letras.
Los dispositivos conservan su silueta física; las apps usan el cuadrado redondeado original. Todos los motivos son originales y no reproducen logos de proveedores.

**Entrega.** Tema instalable en `files/system/usr/share/icons/Antu/`: 58 nombres × 8 tamaños = **464 PNG RGBA**, más `index.theme` y `COPYING`. Son 17 lugares, 13 dispositivos, 16 tipos de archivo y 12 apps; tamaños 16, 22, 24, 32, 48, 64, 128 y 256 px. Las 32 carpetas están declaradas individualmente con `Size`, `Type=Fixed` y los contextos `Places`, `Devices`, `MimeTypes` y `Applications`. Licencia CC-BY-SA-4.0 en el tema y en los metadatos de cada PNG.

`Inherits=breeze-dark,hicolor` conserva los recursos que no proporciona Antu. No se añadieron acciones, estados ni logos de Steam, Brave, Discord o NVIDIA. Los nombres `text-x-generic` y `application-zip` son copias PNG de `text-plain` y `application-x-archive`, respectivamente. `start-here` procede de la geometría aprobada de Antu, rasterizada a cada tamaño. La estructura y la herencia siguen la [especificación freedesktop](https://specifications.freedesktop.org/icon-theme/latest/).

**Ajustes definidos a mano.** Cada tamaño se renderiza por separado; los chicos no son reducciones del ícono grande. Se escribieron recetas ópticas para 16, 22, 24 y 32 px:

| Tamaño | Trazo del motivo, unidades de escena | Ampliación del motivo de app | Decisiones |
| --- | --- | --- | --- |
| 16 | 0,140 | 1,31× | Siluetas fuertes; se eliminan ranuras, tornillos, perforaciones de vídeo y palancas pequeñas. Menos líneas en texto y grillas. |
| 22 | 0,115 | 1,27× | Trazo próximo a un píxel iluminado; se mantienen las simplificaciones de lista y los puntos de color útiles. |
| 24 | 0,108 | 1,24× | Compensación propia del trazo y del motivo; grilla y folio reducidos a las divisiones esenciales. |
| 32 | 0,090 | 1,20× | Vuelven detalles útiles del contenido; se mantienen ocho dientes en los engranajes y se omiten incisiones subpíxel. |

En las carpetas de 16–32 el grabado crece de 0,69 a 0,78 de escala. La papelera llena contiene una hoja visible; el teclado pasa de nueve a cinco columnas; desaparecen tornillos, óptica frontal del teléfono, pequeños surcos, ranuras de impresora y palancas pequeñas del mando. La firma de color de los folios gana grosor. A 48 px en adelante vuelve el detalle progresivo. La pestaña de Juegos y las siluetas de casa, descarga, música, imagen y vídeo permanecen reconocibles.

Los íconos de 256 se renderizan nativamente a 1024×1024 y se reducen; los demás tienen supermuestreo de su propia escena (mínimo 128×128), nunca ampliación del resultado final. Los renders ópticos se guardan en `brand/masters/icon-theme-v2/`, dentro de la ruta de másteres ya excluida de Git. Todos los PNG necesarios para la distro están en el tema y sí son archivos del repositorio.

**Integración.** Solo cambia `Theme=breeze-dark` por `Theme=Antu` en el bloque `[kdeglobals][Icons]` de los defaults de `org.antuos.desktop` y `org.antuos.mac`. El arte aprobado, sus generadores, hicolor, los fondos y Plymouth se conservan byte por byte.

**Vistas fuera de `files/`.** En `brand/previews/icon-theme/`:

- [Carpetas y lugares](previews/icon-theme/places.png): cada nombre a 16, 32, 64 y 256 px, a tamaño real.
- [Tipos de archivo](previews/icon-theme/mimetypes.png): la misma comparación.
- [Dispositivos y apps](previews/icon-theme/devices-apps.png): la misma comparación.
- [Lectura pequeña](previews/icon-theme/small-sizes.png): todos los nombres a 16, 22, 24 y 32 px, sin ampliar.
- [Fondo claro](previews/icon-theme/light-background-check.png): comprobación adicional de las carpetas.
- [Maqueta de Dolphin 4K](previews/icon-theme/dolphin-mockup-4k.png): vista de íconos de 256 px y lista de 32 px. Es una maqueta de revisión, no una captura de una sesión KDE ejecutada.

Las vistas usan los PNG finales del tema. Esta ruta ya está excluida de Git; se conserva localmente y se reconstruye con el generador.

**Fuentes y regeneración.** Se añadieron `scripts/antu_icon_catalog.py`, `render_icon_theme.py`, `make_icon_theme.py` y `preview_icon_theme.py`. El renderer importa las funciones de geometría y luz de `render_art.py` sin modificarlo ni invocar su exportación. Solo escribe sus nuevas escenas bajo `brand/masters/icon-theme-v2/`. No requiere imágenes de stock, red ni modelos generativos.

`python scripts/make_icon_theme.py --render` renderiza las escenas que falten y empaqueta el tema (Blender 5.2 y Pillow). Sin `--render`, exporta los renders existentes, genera el índice, las vistas y valida. `--check` comprueba el tema instalado. Para rehacer deliberadamente una escena nueva: `blender -b --python-exit-code 1 -P scripts/render_icon_theme.py -- --only folder-games --sizes 16,22,24,32 --force`; después volver a empaquetar. No se ejecuta `make_brand.py` ni `make_wallpapers.py`.

**Inventario y verificación.** [icon-theme-files.csv](icon-theme-files.csv) lista cada archivo creado o cambiado, con tamaño y SHA-256, distinguiendo los renders y las vistas locales excluidos de Git; [icon-theme-validation.json](icon-theme-validation.json) registra nombres, dimensiones, transparencia, licencia, contextos, herencia, integración y LF. El tema instalado ocupa 2,73 MB. Los hashes de 187 archivos del arte aprobado coinciden con los anteriores al encargo. Se revisaron visualmente las tres familias y los tamaños pequeños. La integración se verificó estáticamente en Windows; falta comprobar el tema en una sesión Linux/Dolphin real. No se hizo commit ni push.


## Revisión de contraste · 3 de noviembre de 2026

Las carpetas ahora tienen cuerpo de grafito iluminado, canto continuo y pestaña con brillo propio. Se ajustaron de nuevo 16, 22, 24 y 32 px; también se corrigieron SSD, mando, altavoces, teléfono y otras siluetas que lo necesitaban. `start-here` conserva el símbolo aprobado, montado en una base de grafito para leerlo en claro y oscuro. Los másteres nuevos van en `brand/masters/icon-theme-v2`; no se sobrescriben los anteriores.

Los 464 PNG pasan el objetivo de P90 ≥3 para borde y cuerpo sobre #141418 y #1C1C21. El mínimo del borde es 3,2664 y 3,0207, respectivamente. Sobre #F5F5F7 pasa el cuerpo; se publica también el contraste del canto de plata. Método y resultados por tamaño en `icon-theme-validation.json`, sin presentar este criterio operativo como una certificación WCAG. Las seis hojas/maqueta finales son 3840×2160 y muestran los recursos pequeños sin ampliar. La maqueta de Dolphin usa una ventana opaca #1C1C21.

El tema instalado ocupa 3.05 MiB. La verificación adicional de integridad conserva 167 archivos de arte previo enumerados en `visual-refinement-validation.json` (conjunto explícito de fondos, símbolos, cursores, iconos originales y PNG anteriores de Plymouth). Las pruebas Qt nativas y QML de esta revisión no sustituyen la nueva sesión real de Dolphin ni el arranque físico. Véase `docs/REFINAMIENTO-VISUAL-2026-11-03.md`.
