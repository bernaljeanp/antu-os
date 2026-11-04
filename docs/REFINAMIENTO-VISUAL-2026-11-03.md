# Refinamiento visual de Antu · 3 de noviembre de 2026

Implementado en el repositorio, sin commit ni push. Preferencia confirmada: grafito mate, vidrio en cabeceras,
acentos lava. Las correcciones funcionales del informe físico de la sesión anterior se conservan.
**El USB ya grabado no contiene estos cambios y no fue modificado.** Claude debe revisar e integrar; después hace
falta construir y probar una nueva ISO. Este informe no presenta las capturas aisladas como una sesión real de Antu.

## Resultado y alcance

| Hallazgo | Cambio preparado | Verificación y límite |
|---|---|---|
| V01 · Iconos | Carpetas iluminadas, pestaña y canto continuo; SSD y otras siluetas corregidas. 464 PNG finales | P90 del borde y cuerpo ≥3:1 sobre ambos fondos oscuros; cuerpo ≥3:1 sobre claro. Todos los tamaños medidos |
| V02 · Letra pequeña | Mínimo 14 px lógicos y preferencia de fuente Qt; filas adaptables, detalles compactos y desplazamiento | Ventanas mínimas y 1280×800; oscuro/claro y fuente al 200 % en ejecución QML aislada |
| V03 · Botones | Caras lava más profundas y texto blanco sin relieve | Contraste numérico de las caras; foco, selección y deshabilitado en las muestras Qt/QML |
| V04 · Continuidad | Dos estilos originales Kvantum para Qt Widgets; tokens comunes para las apps propias | Motor Qt/Kvantum real renderizado en Debian; falta Dolphin y Ajustes en la nueva ISO. Kirigami conserva controles KDE |
| V05 · Nitidez | Fotografía cargada según píxeles físicos, hasta 3840; título de Plymouth renderizado a doble resolución | Capturas QML y Qt Widgets 3840×2160; sin ampliar los iconos de las hojas |
| V06 · USB | Bienvenida con Probar, Instalar e Informe; estado real del registro y guardado | Modo demo ejecutado; integración en autostart, layouts y galería. La prueba no ejecuta instalación |
| V07 · Claro | Paleta Qt, superficies y símbolos adecuados a Salar; contraste de Header corregido | Paleta clara y texto grande revisados; alto contraste personalizado pendiente de prueba específica |
| V08 · Fotografías | Herramientas sobre grafito estable; fotografía reservada a la bienvenida | Preferencia del dueño aplicada; originales aprobados conservados |
| V09 · Compatibilidad | “Muy buen/Buen soporte en Linux”; SteamOS separado de pruebas en Antu; fecha de consulta/copia cuando existe | Autoprueba de veredictos. Sin inventar que un juego fue probado en este portátil |
| V10 · Encendido | Símbolo estático, título y progreso de Plymouth; sin registro o métricas decorativas | Callbacks de progreso, mensajes y contraseña conservados; render completo durante arranque pendiente |
| V11 · Movimiento | Preferencia global KDE en las apps; animaciones continuas detenidas con factor 0; sin sacudida en SDDM | Pruebas de lectura y prioridad de preferencias; inspección de las rutas animadas |
| V12 · Coste | Halos de 10 a 6 piezas, menos intensidad; sin transparencia de ventana completa en Qt Widgets | Reducción de estructura comprobada. Consumo, tiempos de cuadro y biblioteca grande pendientes de GPU real |
| V13 · Defaults | Theme=Antu en la base y ambos layouts; Kvantum empaquetado y seleccionado | Regresión de ambos layouts y presencia de estilos en CI; perfiles existentes pendientes en ISO |
| V14 · Accesibilidad | Tab desplaza al foco, Ctrl+F y retorno en Biblioteca, gráfico con flechas, avisos/errores accesibles, diálogos desplazables | Carga y recorrido parcial de teclado. Lector de pantalla Linux y mando requieren prueba real |
| V15 · Rutas de dibujo | Pruebas por software y controles Qt nativos con casos ampliados, selección, foco y error | No sustituyen la ruta Qt Quick acelerada, HDR o Gamescope físico |
| V16 · Contexto | PRODUCT actualizado y DESIGN vigente | Se eliminan descripciones de consola inicial y de ausencia de Steam/instalador/firma |

## Familia y tamaños ópticos

La carpeta es un objeto de grafito iluminado con un canto continuo de plata anodizada y brillo independiente en la
pestaña. Cambia el grabado, no la carcasa; Juegos añade esmalte lava. Archivos, dispositivos y apps mantienen la luz
superior izquierda y la misma familia de materiales.

Se ajustaron explícitamente **16, 22, 24 y 32 px**: trazos, canto, escala de grabados y supresión de detalles pequeños.
No son solo reducciones del render de 256. También se revisaron las siluetas de dispositivos en los tamaños grandes.
Los másteres nuevos se guardan en `brand/masters/icon-theme-v2`; los másteres aprobados anteriores no se sobrescriben.

## Mediciones

`brand/icon-theme-validation.json` contiene cada archivo, hash, tamaño y medición sobre `#141418`, `#1C1C21` y `#F5F5F7`.
Píxel visible: alfa ≥128. Borde: máscara visible menos erosión 3×3. El percentil discreto P90 aproxima el mínimo del
décimo más claro. Se compone el PNG final sobre cada fondo antes de calcular luminancia sRGB. Es un criterio operativo
solicitado para el arte, **no una certificación WCAG** ni una segmentación semántica perfecta de todas las siluetas.
En oscuro se exige P90 ≥3 al borde y al conjunto visible; en claro se exige al cuerpo visible y se publica además el
borde de plata, que naturalmente puede ser claro. La inspección sobre claro acompaña esta distinción explícita.

`brand/visual-refinement-validation.json` reúne los resultados y las dimensiones de las vistas finales.
`ci/visual-test.py` comprueba que ningún PNG medido cambió después del informe, además de preferencias y defaults.
El inventario `REFINAMIENTO-VISUAL-2026-11-03-archivos.csv` incluye el árbol de trabajo actual; también contiene los
cambios funcionales anteriores descritos en `PRUEBA-ALIENWARE-2026-11-03.md`.

## Vistas y reproducción

- `brand/previews/icon-theme/`: carpetas, archivos, dispositivos/apps, prueba de tamaños pequeños, fondo claro y
  maqueta de Dolphin sobre ventana sólida `#1C1C21`. Hojas finales 3840×2160, fuera de `files/`.
- `brand/previews/refinamiento-v2/`: controles Qt nativos oscuro/claro, iconos/lista y capturas de apps a 4K.
  El aviso es una ventana nativa centrada sin ampliar en una hoja 4K; SDDM se ensayó con modelos ficticios, sin autenticación. Las subcarpetas de ventanas mínimas y texto grande son pruebas a su resolución real; no se amplían para aparentar 4K.
- `python scripts/make_icon_theme.py --render`: genera las escenas faltantes de la familia nueva y empaqueta.
  `--check` mide y comprueba los PNG instalados. Blender 5.2 y Pillow; no ejecuta el generador del arte aprobado.
- `python scripts/make_widget_theme.py` y `python scripts/make_plasma_theme.py`: piezas originales del estilo.
  `python scripts/make_boot_identity.py`: solo el título estático nuevo; no regenera los efectos antiguos.
- `python ci/visual-test.py`: seis regresiones sin GUI. `python ci/diagnostico-test.py`: veinte regresiones funcionales
  en Linux. Las capturas integradas de CI incluyen bienvenida y siguen fallando si QML no carga.

## Antes de dar por validada una versión

Construir la imagen/ISO y recorrer arranque, SDDM, bienvenida, Dolphin, Ajustes, errores, instalación de prueba y vuelta
de Eclipse. En Alienware: 100/125/150/200 %, oscuro/claro, 16:9 y 16:10; teclado, lector de pantalla y mando; caché fría
y caliente, biblioteca grande y un juego real. Medir coste de composición y batería. Repetir Bluetooth, DNS, audio y
suspensión con el registro automático. Ninguna captura aislada acredita esas pruebas ni un puesto en un ranking.
