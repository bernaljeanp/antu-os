Antu Cursores sigue la opción 2, «Punta», aprobada en [maqueta-moderna.png](previews/cursors/maqueta-moderna.png). La flecha conserva los cuatro vértices (4,6; 3,6), (11,2; 28,6), (15,2; 18,6) y (27,2; 13,4), el redondeo y la grieta interior de [su código](previews/cursors/maqueta-moderna.py). Ambas referencias se conservaron intactas. Se descartó todo el dibujo de la entrega anterior; se conservaron el escritor y lector Xcursor, los nombres, los puntos activos y las comprobaciones técnicas.

El cuerpo es #111115 opaco y plano, con un único contorno blanco #FFFFFF. La lava pasa de #FF963C a #FF5A1F; su resplandor queda recortado al cuerpo. La grieta nace y acaba fina, manteniendo color pleno en el tramo central. La sombra negra usa desplazamiento vertical de 1,3 unidades, desenfoque de 2,1 y opacidad de 0,5, sobre una rejilla de 32 unidades. Se extingue en el último margen del lienzo para evitar un corte rectangular y nunca se envuelve al borde opuesto. No hay plata, materiales, biseles, reflejos, volumen ni dependencias de un renderizador 3D.

Las tres manos son siluetas nuevas, gorditas y sin arrugas: índice extendido, dedos abiertos y puño, con curvas y remates redondos. Texto tiene una barra central maciza de 4,6 unidades y dos remates gruesos; el texto vertical mantiene ese cuerpo. La cruz, la celda y las flechas direccionales tienen núcleos sólidos. Las insignias comparten la misma punta; copiar usa dos folios, enlace dos eslabones, menú dos renglones y ayuda una curva continua con su punto. Las lupas usan signos grandes. En las formas pequeñas el acento se reduce a un tramo de borde, o se omite cuando no ayuda a leer; no se añaden grabados ni detalles decorativos.

**Entrega y compatibilidad.** [El tema](../files/system/usr/share/icons/Antu-Cursores/) contiene 34 archivos Xcursor reales, siete tamaños por archivo y 81 alias directos en [alias.tsv](../files/system/usr/share/icons/Antu-Cursores/alias.tsv): 115/115 nombres del inventario congelado de Breeze. No se crearon enlaces simbólicos ni copias de alias. El dueño debe materializar esos enlaces relativos al compilar, como indica el encargo. index.theme declara Name=Antu Cursores e Inherits=breeze_cursors; COPYING conserva CC-BY-SA-4.0 y la atribución a Antu OS.

Se conserva el inventario independiente y el mapa semántico anteriores, incorporados en el generador, con las URL de procedencia y su SHA-256 en el informe. Esta entrega no vuelve a consultar ni amplía el inventario de Breeze. No se reutiliza su dibujo.

**Tamaños y puntos activos.** Cada tamaño se rasteriza por separado desde su geometría. Nunca se reduce un PNG de 96 para obtener los otros tamaños. A 24 y 32 se revisaron y compensaron el blanco, el filo y la posición subpíxel. La punta visible se encaja en la celda del punto activo conservado: (3, 2) a 24 y (4, 3) a 32. Su altura visible es aproximadamente 20 px a 24. Los centros de texto, cruz, celda y aro coinciden con el píxel activo; progreso conserva el punto activo de la punta.

| Tamaño | Contorno blanco, px | Supermuestreo |
| --- | ---: | ---: |
| 24 | 1,45 | 12× |
| 32 | 1,80 | 12× |
| 36 | 1,97 | 8× |
| 48 | 2,625 | 8× |
| 64 | 3,50 | 8× |
| 72 | 3,9375 | 8× |
| 96 | 5,25 | 8× |

El contorno pequeño supera el mínimo nominal de 1,3 px. Las máscaras se supermuestrean y se reducen una sola vez con Lanczos. Los ajustes y PNG de referencia nuevos están en brand/masters/cursors/recetas-opticas.json y brand/masters/cursors/2d/. Se eliminaron los renders, registros, caché y arte de iteraciones obsoletos de esa carpeta.

**Animación.** Solo wait y progress tienen 32 cuadros por tamaño, de 30 ms, con bucle de 960 ms. El aro de obsidiana, el blanco y la punta permanecen inmóviles; se desplaza un tramo de lava 360/32 grados por cuadro. No se duplica el cuadro inicial al final. El aro pequeño tiene geometría propia y margen suficiente para no recortarse. El GIF exportado contiene los 32 cuadros, todos a 30 ms, y repetición infinita.

**Regeneración.** [scripts/make_cursors.py](../scripts/make_cursors.py) es la fuente completa. Se probó con Python 3.12.14 y Pillow 12.3.0. Se requiere Pillow para generar; el lector y --validar solo usan la biblioteca estándar.

~~~powershell
python scripts/make_cursors.py
python scripts/make_cursors.py --validar
~~~

El primer comando redibuja las 34 formas y los siete tamaños, empaqueta, actualiza los maestros y todas las vistas y valida. No necesita renders previos, Blender ni xcursorgen. La comparación ejecuta únicamente las funciones de dibujo de maqueta-moderna.py para representar fielmente la referencia aprobada. Las opciones antiguas --render y --forzar se retiraron porque ya no hay escenas ni caché que reconstruir. El segundo comando lee los archivos entregados y escribe [cursor-validation.json](cursor-validation.json); no regenera ni repara los cursores.

**Validación y contraste.** Se mantienen cabecera, TOC, límites, fragmentos contiguos, tamaños, cuadros, retardos, puntos activos, imágenes no vacías, transparencia del margen, ausencia de datos sobrantes, ARGB premultiplicado, metadatos, alias directos y cobertura independiente de nombres. El lector rechaza seis corrupciones: firma, offset, hotspot, canal mayor que alfa, truncamiento y residuo. Para las animaciones se exigen cuadros únicos y una transición de cierre comparable a los pasos internos.

La medición nueva compone los bytes ARGB premultiplicados del Xcursor final sobre RGB (0,0,0), (128,128,128) y (255,255,255), redondea los canales a 8 bits y calcula luminancia relativa sRGB. Cuenta los píxeles cuya razón (Lmayor+0,05)/(Lmenor+0,05) es al menos 3:1. Se exigen **40 píxeles a 24 y 72 a 32** en cada fondo, aproximadamente el 7 % del lienzo. El criterio es común a todas las formas y se aplica a todos los cuadros; el informe publica los conteos por cuadro y su mínimo. Las sombras y la transparencia se componen de verdad, sin tratarlas como siluetas opacas.

Conteos finales sobre gris 128; cada cifra indica píxeles que alcanzan al menos 3:1. En las animaciones se usa el cuadro con el menor conteo.

| Forma | 24 px | 32 px |
| --- | ---: | ---: |
| Texto | 107 | 198 |
| Texto vertical | 109 | 182 |
| Lápiz | 108 | 182 |
| Progreso | 112 | 193 |
| Cruz de precisión | 141 | 237 |

La forma más débil sobre gris a 24 es texto, con 107 píxeles; a 32 empatan texto vertical y lápiz, con 182. Ambas superan ampliamente el mínimo. Los valores completos, los tres fondos, los siete tamaños, los puntos activos y los hashes se publican en el JSON.

Se probó además el rechazo real: se sustituyeron temporalmente los colores de default por gris 128 conservando el formato, el alfa y los puntos activos. --validar terminó con código 1 y exactamente dos errores de contraste (0 < 40 y 0 < 72 sobre gris). Se restauró el Xcursor original byte por byte antes de la validación final. No basta con que la función imprima un resultado favorable.

La ejecución final de --validar terminó con código 0, sin errores: 34 Xcursor, 81 alias, 115/115 nombres, siete tamaños, 672 fragmentos y seis corrupciones rechazadas; 68 combinaciones de forma/tamaño medidas sobre tres fondos, con todos los cuadros animados incluidos.

**Vistas revisadas.** Se generan leyendo los Xcursor finales, con el mismo lector que los valida:

- [Hoja completa](previews/cursors/hoja-todas.png): todas las formas a 24, 32, 48 y 96, a tamaño real, sobre negro, blanco, gris 128 y Paranal.
- Hojas separadas: [negro](previews/cursors/formas-negro.png), [blanco](previews/cursors/formas-blanco.png), [gris](previews/cursors/formas-gris.png) y [Paranal](previews/cursors/formas-paranal.png).
- [Lectura diaria de 24/32](previews/cursors/lectura-24-32.png), sin ampliar los cursores.
- [Flecha ×8](previews/cursors/flecha-pixeles.png), con vecino más cercano y la celda activa marcada en cian.
- [Comparación con la maqueta](previews/cursors/comparacion-maqueta.png): punta, mano y texto, referencia a la izquierda y entrega a la derecha; 96 a tamaño real y 24/32 ampliados ×4.
- [GIF de espera y progreso](previews/cursors/espera-progreso.gif) y [contacto de los 32 cuadros](previews/cursors/animacion-contacto.png).
- [Fondos adicionales](previews/cursors/contraste-fondos.png): Paranal, Antu, Salar y una escena de juego sintética.

Se miraron las vistas, la lectura pequeña, el píxel ampliado, la comparación y el contacto de animación. Después de la primera revisión se reforzó la lava para evitar que se apagara a 24/32; se suavizó la interrogación, se limitaron los acentos a un borde y se corrigieron los márgenes del enlace y del aro pequeño. Las hojas de tamaño real deben abrirse al 100 %: reducir la hoja también reduce los cursores.

**Límites.** No fue posible ejecutar el tema en KDE Plasma 6, Wayland o X11 desde este equipo Windows, ni probarlo dentro de un juego real. La escena de juego de las vistas es sintética. La prueba técnica y visual no sustituye esa comprobación en Linux. No se activó el tema, no se cambió la configuración del sistema y no se materializaron los alias, según lo solicitado. No se hizo commit ni push y solo se tocaron las rutas autorizadas por el encargo.
