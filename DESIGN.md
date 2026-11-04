# Sistema visual de Antu

Decisión del dueño, 3 de noviembre de 2026: **grafito mate, vidrio en cabeceras y acentos lava**.
La obsidiana, la plata anodizada y el esmalte lava conservan volumen, con luz arriba a la izquierda.
El símbolo, las apps originales, los fondos aprobados y los cursores se conservan.

## Superficies y color

| Función | Obsidiana | Salar |
|---|---|---|
| Ventana | `#1C1C21` | `#F5F5F7` |
| Panel | `#141418` | base de la paleta KDE |
| Texto | `#F5F5F7` | `#1D1D1F` |
| Texto secundario | `#C7C7CC` | `#4F4F57` |
| Texto auxiliar | `#A1A1A6` | `#5E5E64` |
| Lava para información | `#FF783D` | `#AE330C` |
| Selección con texto blanco | `#B9370D` | `#B9370D` |

Las herramientas trabajan sobre una superficie estable. Paranal se reserva para la bienvenida y el primer arranque.
Plasma mantiene vidrio al 94 % de opacidad y un brillo fino en el canto superior. Sin transparencia de ventana completa
en Kvantum. No se colocan imágenes dentro de formularios de trabajo para simular material.

## Implementación

- `inicio/Antu.qml`: tokens compartidos, paleta Qt, tamaños de letra y duración de transiciones.
- `AntuBackdrop.qml`: grafito y luz de cabecera; la fotografía carga hasta 3840 píxeles físicos, según el dispositivo.
- `FocusScroll.qml`: mantiene visible el foco al recorrer formularios con teclado.
- `LavaButton`, `GlassField`, `GlassCombo`, `Aviso`: controles con material y estados de foco, error y deshabilitado.
- Qt Widgets: estilos originales `AntuObsidiana` y `AntuSalar`, mediante el motor Kvantum. Dolphin usa este motor.
  Ajustes de KDE conserva los controles Qt Quick/Kirigami, con la paleta de Antu; no se afirma que Kvantum los dibuje.
- La selección Salar/Obsidiana se sincroniza al abrir aplicaciones. Algunas ventanas Qt Widgets requieren cerrarse
  y abrirse tras cambiar de paleta. El sincronizador respeta otros estilos y temas elegidos por la persona.

## Tipografía, adaptación y movimiento

Inter para interfaz, JetBrains Mono para datos monoespaciados. Tamaño mínimo de texto propio: 14 píxeles lógicos,
antes de aplicar la preferencia de fuente del sistema. El escalado del monitor lo gestiona Qt. Reducir la ventana
reorganiza filas y activa desplazamiento; no reduce la letra. Los detalles de juegos ocupan la ventana pequeña.
No se usa texto grabado o sombra de texto para compensar un contraste insuficiente.

Inicio y Zenit apilan controles con fuente grande. El gráfico reserva márgenes según su letra y tiene alternativa
en tabla y selección de sesiones con flechas. El foco debe ser visible en oscuro y claro.
`AnimationDurationFactor=0` elimina transiciones y animaciones continuas propias. SDDM explica el error sin sacudir
el formulario; Plymouth usa identidad estática y progreso comunicado por el sistema, sin consola decorativa.

## Arte y verificación

Iconos PNG transparentes a 16, 22, 24, 32, 48, 64, 128 y 256 px. Escenas ópticas propias para los pequeños:
menos mecanizado, trazos más gruesos y símbolos ampliados. Las carpetas comparten grafito iluminado, canto de plata
continuo y pestaña iluminada; Juegos conserva lava. Acciones y estados siguen en Breeze; marcas ajenas, en cada app.
Arte original CC-BY-SA-4.0; código GPL-3.0-or-later.

Los fondos aprobados son 4K con superresolución, no generación 4K nativa. Las hojas finales son 3840×2160, con iconos
pegados a tamaño real. Las pruebas en tamaños de ventana pequeños se guardan a su resolución de prueba.
Contraste reproducible en `brand/icon-theme-validation.json`; método y límites en el informe de refinamiento.
No hay certificación global WCAG, alto contraste, lector de pantalla, mando o rendimiento de GPU sin esas pruebas.

## Barra y bandeja

Barra inferior flotante de 56 px lógicos como mínimo, ajustada a la fuente mediante `gridUnit`.
Contenido de referencia de 48 px, iconos de tarea de unos 36 px y separación horizontal ampliada.
Cinco apps fijadas más el menú en el sistema instalado; el USB añade Bienvenida e Informe en lugar de Brave.
Zenit tiene su control permanente en la bandeja. Su ventana abierta sigue apareciendo como una tarea normal.
Ajustes y Discover se encuentran en el menú. No se cambian las marcas que proporciona cada aplicación.

Punto de texto para abierta, marca lava más larga para activa y trazo hueco para minimizada. El estado se conserva
al pasar el cursor. La atención y el progreso usan estados nativos; el tema no añade parpadeos. La bandeja conserva
el orden por categorías de Plasma y deja portapapeles/multimedia en su desplegable. El reloj tiene 12 px de separación.
La migración de sesiones Antu retira solo el pin de Zenit; no reconstruye paneles ni sustituye accesos personales.
Comprobaciones y límites en `docs/BARRA-DE-TAREAS-2026-11-03.md`.

## Preparación y protección de datos — 2026-11-04

Centro de Antu usa Qt Widgets con los estilos Kvantum y paletas existentes: pestañas nativas para aplicaciones,
copias, pruebas del equipo y comparación de registros. Las operaciones largas viven fuera del hilo de interfaz;
los estados de descarga y verificación vienen del motor real. Las restauraciones terminan en una carpeta nueva.
Zenit conserva sus materiales y confirma perfiles/carga; las funciones ausentes se desactivan. La instalación
muestra un plan revisable, distingue conservar/borrar y separa la frase LUKS2 de la cuenta de usuario.
La página de descargas mantiene grafito/lava, Inter y el símbolo aprobado; no usa arte de sustitución.
