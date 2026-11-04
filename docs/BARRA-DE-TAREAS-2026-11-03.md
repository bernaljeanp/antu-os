# Barra de tareas de Antu · 3 de noviembre de 2026

Preparado en el repositorio por encargo del dueño. Se conserva grafito mate, vidrio al 94 %, el arte original y los
widgets nativos de Plasma. **No se modificó el USB, no se construyó una nueva ISO y no se hizo commit ni push.**

## Cambios

- Barra inferior: mínimo 56 px lógicos, creciendo con la fuente del escritorio. El área de referencia disponible para
  tareas es 48 px; márgenes del tema dejan unos 36 px para el icono. Más separación horizontal y una sola fila de tareas.
- Sistema instalado: menú de Antu, Brave, Dolphin, Steam, Biblioteca y Observatorio. El USB usa Bienvenida e Informe en
  lugar de Brave. Ajustes y Discover siguen disponibles en el menú. Se conserva la variante de barra superior y dock.
- **Zenit deja de estar fijado en la zona central.** Su control permanente sigue junto al reloj, con perfiles rápidos.
  Cuando se abre su ventana aparece una tarea normal; al cerrar la ventana queda su control de bandeja. No se altera
  Alt+Tab ni se esconde una ventana abierta para simular que no existe.
- Tareas agrupadas por app, lanzador y ventana integrados, sin duplicar el acceso cuando arranca una aplicación.
- Punto para abierta; marca lava más larga para activa; marca hueca para minimizada. Pasar el cursor conserva el estado.
  Atención y progreso se dibujan con los prefijos que consume Plasma; no se añade animación al tema.
- Bandeja con espaciado nativo y categorías de Plasma; portapapeles y control multimedia en el desplegable, conservando
  su función. Separación fija de 12 px antes del reloj y letra mínima configurada de 12 puntos, que crece con `gridUnit`.
- Un script de actualización retira únicamente el pin de Zenit en sesiones Antu existentes. Es idempotente y conserva
  los otros accesos y tamaños personalizados. El resto de la distribución nueva corresponde a los layouts iniciales.

El ensayo con KSVG detectó un `url(#brillo)` sin definición en el generador de superficies. Se añadió su degradado
superior tenue y se regeneraron panel, diálogos y tooltip sin cambiar su geometría. Una regresión comprueba todas las
referencias de pintura del tema para impedir que vuelva a ocurrir.

## Verificación

- `node ci/panel-test.cjs`: **24 combinaciones** de ambos layouts, instalado/USB, tres tamaños de fuente y bandeja
  directa/heredada; **6 casos de migración**, con conservación de accesos propios, otro tema e idempotencia.
  Es ejecución JavaScript con la API de Plasma simulada, no una prueba del shell completo.
- `python ci/visual-test.py`: **7 regresiones**, incluidos hashes y contraste de los 464 PNG anteriores, preferencias,
  defaults y referencias SVG. Integradas en el workflow de compilación junto a las pruebas funcionales anteriores.
- `scripts/preview_panel.py`: **5 imágenes de 3840×2160**, dibujadas mediante Qt Quick 6.8/KSVG 6.13 reales en Debian
  WSL, por software y con configuración de color temporal. Última ejecución sin avisos de QML/KSVG ni iconos ausentes.
  Son escenas de revisión ensambladas, **no capturas de una sesión Plasma arrancada**.
- En las muestras renderizadas se comprobaron el punto blanco `#F5F5F7` sobre oscuro y el oscuro `#1D1D1F` sobre Salar.
  La marca activa usa el acento de la paleta `#C93A0C`: aproximadamente 3,58:1 sobre `#141418` y 4,71:1 sobre `#F5F5F7`.
  Se registra el muestreo y sus límites en `brand/panel-validation.json`; no es una certificación de toda la barra.
- Las imágenes de apps propias no se regeneraron. Para las marcas de la maqueta se usaron recursos originales de las
  instalaciones locales de Steam y Brave. El PNG de Brave se conserva intacto y QML omite solo su margen transparente
  de mosaico de Windows. Son recursos locales de revisión y no se instalan en Antu. El icono de Informe ya era
  `computer-laptop`; se corrigió una referencia errónea del ensayo, sin cambiar la app.

## Archivos y reproducción

`brand/panel-files.csv` enumera los archivos de esta pasada y sus hashes. Los anteriores cambios visuales y funcionales
se conservan; su inventario conjunto sigue en `docs/REFINAMIENTO-VISUAL-2026-11-03-archivos.csv`.

Principales archivos:

- Layouts de `org.antuos.desktop` y `org.antuos.mac`, en `contents/layouts/org.kde.plasma.desktop-layout.js`.
- `scripts/make_plasma_theme.py` y los siete SVG regenerados de `plasma/desktoptheme/antu`.
- `plasma/shells/org.kde.plasma.desktop/contents/updates/antu-2026-11-zenit-tray.js`.
- `scripts/preview_panel.py`, `ci/panel-test.cjs`, `ci/visual-test.py` y `.github/workflows/build.yml`.
- `DESIGN.md`, este informe y los inventarios/validación.

Vistas fuera de `files/`, en `brand/previews/barra/`:

- `panel-installed-dark-4k.png`: barra principal, sin pin central de Zenit.
- `panel-live-dark-4k.png`: variante de prueba desde USB.
- `panel-mac-dark-4k.png`: barra superior y dock.
- `panel-states-dark-4k.png` y `panel-states-light-4k.png`: estados nativos, en ambas paletas.

Regeneración: `python scripts/make_plasma_theme.py`. El ensayo requiere Linux, PyQt6/QtQuick, KSVG,
`org.kde.desktop` de Kirigami y Breeze; usa archivos de marca locales bajo `--brands` y no necesita una sesión del usuario.
Las marcas no están vendorizadas. Las herramientas de desarrollo no forman parte de un flujo del usuario de Antu.

## Integración pendiente

Claude debe revisar e integrar. Después, construir y arrancar la nueva ISO para comprobar el shell real: métricas,
bandeja, migración con perfil existente, desbordamiento con muchas ventanas, teclado, escalados 100/125/150/200 % y
monitor externo. La galería de ISO ya captura escritorio y Dolphin con la barra visible. Falta esa ejecución y la
prueba física en el Alienware; las escenas KSVG y los dobles de API no la sustituyen. No se declara una mejora de FPS.

## Referencias de implementación

Las claves de tareas y sus estados se comprobaron en las fuentes oficiales de KDE:
[configuración del gestor](https://github.com/KDE/plasma-desktop/blob/master/applets/taskmanager/main.xml),
[selección de estados](https://github.com/KDE/plasma-desktop/blob/master/applets/taskmanager/qml/Task.qml) y
[prefijos direccionales/hover](https://github.com/KDE/plasma-desktop/blob/master/applets/taskmanager/qml/code/TaskTools.js).
La configuración de bandeja y espaciador sigue sus esquemas:
[bandeja](https://github.com/KDE/plasma-workspace/blob/master/applets/systemtray/main.xml),
[espaciador](https://github.com/KDE/plasma-workspace/blob/master/applets/panelspacer/main.xml).
Se consultaron también los esquemas de Plasma 6.5 para mantener las claves compartidas, la
[API de scripting](https://develop.kde.org/docs/plasma/scripting/api/) y el
[contrato SVG de tareas](https://develop.kde.org/docs/plasma/theme/theme-elements/#widgetstaskssvg).
