# Auditoría visual de Antu OS — 3 de noviembre de 2026

Antu tiene una identidad propia reconocible. Paranal, la cumbre con el sol de lava, Inter y los objetos de obsidiana
forman una base valiosa. La mayor oportunidad está en la lectura diaria y en la continuidad entre las apps propias,
Dolphin, los ajustes, las notificaciones y el recorrido de encender, probar y jugar.

No hay evidencia para afirmar que Antu sea la distro número uno. Este informe propone condiciones concretas para
competir por ese nivel de calidad. Es una auditoría y una propuesta; no cambia interfaces ni arte aprobado.

## Alcance y evidencia

- Código actual de 17 archivos QML de las apps, componentes compartidos, SDDM, Plasma, ambos estilos de escritorio,
  colores, Plymouth, Eclipse, configuración de MangoHud y documentación de arte y cursores.
- 464 PNG instalables del tema Antu, ocho tamaños y tres fondos de contraste: #141418, #1C1C21 y #F5F5F7.
- 12 fondos JPG: seis de 3840×2160 y seis adaptaciones de 2560×1600. Los 4K proceden de la superresolución ya autorizada;
  no se presentan como generación 4K nativa.
- Capturas archivadas de la VM en `C:\Users\berna\AppData\Local\Temp\antu-bib\p3`: escritorio, menú, Dolphin,
  notificación, ajustes de pantalla/sonido/Bluetooth, bloqueo, inicio de sesión, Inicio, instalador, Zenit, Biblioteca,
  Observatorio, asistente y avisos. No se ha comprobado el commit exacto de ese archivo de capturas; se contrastó su
  contenido con los componentes actuales. Las situaciones «sin adaptador» de la VM no describen el Alienware.
- Prueba nueva de cinco ventanas en Qt 6.12 sobre Windows, por software, con datos de demostración, a tamaño mínimo
  y 1280×800. Se recorrió el foco con Tab. No prueba el lector de pantalla de Linux ni el mando.
- Zenit no completó la ejecución de este entorno Windows; se revisó su fuente y sus capturas de VM. No se cuenta ese
  fallo de la herramienta de inspección como un fallo de Antu. Observatorio se midió en su estado principal vacío;
  sus detalles con juegos se revisaron en las capturas archivadas.
- El Informe actual incorpora las correcciones de la sesión anterior. Su captura antigua se identifica como tal.
  No se confunde con la prueba actual de su ventana y su registro automático.

Mediciones completas: [JSON](AUDITORIA-VISUAL-2026-11-03-mediciones.json).

Hojas de revisión 3840×2160, fuera de los archivos instalables:

- [Recorrido del escritorio](../brand/previews/auditoria-visual-2026-11-03/01-recorrido-escritorio-4k.png).
- [Apps y estados](../brand/previews/auditoria-visual-2026-11-03/02-apps-y-estados-4k.png).
- Las capturas nuevas a tamaño real y los datos de tabulación están en
  `brand/previews/auditoria-visual-2026-11-03/runtime/`.

## Diagnóstico

La imagen de marca está más terminada que la experiencia de uso completa. En las apps hay material propio, mientras
que las ventanas KDE mantienen otra densidad, otra elevación y otro vocabulario de controles. Esa diferencia es
visible incluso manteniendo la misma paleta. Cambiar únicamente el color de selección no termina la integración.

Diagnóstico editorial de lectura y coherencia: **6/10**. Se calcula con cinco respuestas positivas de ocho criterios
de Refactoring UI, redondeando 5/8×10. No es una medición de satisfacción, un ranking de distribuciones ni una
certificación de accesibilidad.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Jerarquía reconocible al reducir la imagen | Sí | Títulos, cifras de Zenit y acciones principales se distinguen |
| Información comprensible sin depender solo del color | Sí | Compatibilidad y estados tienen texto, además de color |
| Espacio suficiente entre grupos | Sí | Bienvenida, instalador y paneles de control separan las tareas |
| Valores más importantes que sus etiquetas | Sí | Temperaturas y fotogramas destacan sobre la descripción |
| Escala compartida de tamaños y espaciados | No | Factores distintos por app y abundantes medidas locales |
| Longitud de lectura controlada de forma consistente | No | Párrafos anchos y pies muy pequeños en utilidades |
| Contraste suficiente en los elementos necesarios | No | Carpetas oscuras y zonas claras del botón lava |
| Elevación vinculada a interacción y agrupación | Sí | Botón, foco, selección y aviso tienen tratamientos reconocibles |

## Prioridades antes de una presentación pública

### V01 · P1 · Carpetas y dispositivos difíciles de distinguir sobre oscuro

Ubicación: `files/system/usr/share/icons/Antu/`, especialmente la familia de carpetas y SSD pequeño.

La carpeta genérica da aproximadamente **1,38:1 a 16 px, 1,40:1 a 22 px y 1,49:1 a 32 px** sobre #1C1C21,
según el percentil 90 del borde detectado. El resultado coincide con el problema de lectura señalado en la revisión
anterior. En Dolphin se reconoce antes el grabado que la propia carcasa. El borde del SSD a 22 px queda en torno
a 2,86:1 con este método.

**Propuesta:** grafito iluminado, pestaña independiente y canto continuo de plata mate. Conservar los objetos 3D y
las variantes ópticas. Probar primero 16/22/24/32 px en Lugares y lista, con selección y sin selección, sobre las dos
superficies oscuras y sobre claro. La presencia de un grabado brillante no debe hacer pasar una carcasa ilegible.

El barrido de los 464 PNG arroja 311 candidatos por debajo de 3:1 en al menos un fondo oscuro, de los cuales 96 son
variantes de carpetas. **No son 311 fallos WCAG confirmados.** El detector de borde por alfa también puede incluir
sombras y no segmenta a mano las partes funcionales. Sirve para priorizar inspecciones. No se contradice con una
medición anterior de las hojas: se están midiendo regiones diferentes. Revisar los candidatos antes de redibujar.

### V02 · P1 · Reducir la ventana también reduce demasiado la tipografía

Ubicación: propiedad `u` al principio de Biblioteca.qml, Observatorio.qml, Actualizaciones.qml, Informe.qml e
Instalador.qml; tamaños de los componentes compartidos.

| Ventana mínima probada | Menor texto visible medido | Ejemplo de impacto |
|---|---:|---|
| Actualizaciones, 760×580 | 10 px | Explicación de la actualización y recuperación demasiado pequeña |
| Biblioteca, 960×640 | 9 px | Procedencia y privacidad; buscador y acción Eclipse quedan en 12 px |
| Observatorio vacío, 960×640 | 9 px | Pie explicativo; falta medir todos los detalles a ese tamaño |
| Informe, 900×660 | 11 px | Información de la prueba y uso del registro |
| Instalador, 900×640 | 12 px | Datos que ayudan a elegir un disco |

**Propuesta:** mantener el tamaño base de lectura al estrechar una ventana. Cambiar columnas, permitir desplazamiento
y ajustar el detalle visible. Usar una escala tipográfica común con un mínimo editorial de aproximadamente 13–14 px
lógicos para información necesaria. Ese mínimo es una propuesta de producto; WCAG no impone un tamaño de letra mínimo.
Probar también el tamaño de texto del sistema, 125/150/200 %, panel 16:10 y pantalla externa 16:9.

### V03 · P1 · Contraste del texto blanco en botones lava

Ubicación: `files/system/usr/lib/antu/inicio/LavaButton.qml`.

Blanco sobre los colores base del botón: **2,67:1 en #F97A3C, 4,06:1 en #E2480F y 5,72:1 en #B93A0A**.
El degradado cruza esos valores. En varias ventanas la etiqueta se dibuja a 12–16 px, por lo que no puede tratarse
como texto grande. La sombra del texto mejora su percepción, pero estos colores por sí solos no permiten declarar
que todo el botón cumpla 4,5:1. Hay que revisar la zona real bajo las letras en cada estado.

**Propuesta:** conservar volumen, canto, reflejo y respuesta al pulsar. Reservar el brillo más intenso para los bordes
y conseguir una cara más profunda justo detrás de la etiqueta. Verificar reposo, foco, hover y pulsación. No hace
falta convertir el botón en una superficie plana para que sea legible.

### V04 · P1 · Falta continuidad en las superficies de uso diario

Ubicación: los dos `contents/defaults` de Plasma, `desktoptheme/antu`, Dolphin, ajustes y notificaciones de las capturas.

Se mantienen `widgetStyle=Breeze` y decoración `org.kde.breeze`, mientras que las apps propias usan botones Lava,
campos hundidos y avisos con otro acabado. La notificación de Plasma tampoco se siente como el aviso propio.

**Propuesta:** definir una sola familia de títulos, bordes, densidad, menús, selección, barra de herramientas,
diálogos y notificaciones. Empezar por Dolphin y Ajustes, las ventanas que más se ven. Preparar una comparación visual
antes de elegir el mecanismo de Qt/KDE que lo implementará. No adoptar otro motor de estilo sin comprobar compatibilidad,
estados de foco y coste. Mantener los controles y mecanismos nativos.

Los iconos pequeños de acciones y estado de Breeze y los logos de otras apps son excepciones previstas: no deben
redibujarse como solución a este problema. Los cursores 2D también son una excepción funcional acertada.

### V05 · P1 · Algunos fondos 4K se decodifican a 1920 px

Ubicación: `sourceSize.width: 1920` en Biblioteca.qml, Observatorio.qml, Actualizaciones.qml, Informe.qml e Instalador.qml.

El JPG puede ser 3840×2160, pero la petición de imagen limita la anchura de su decodificación a 1920. En una ventana
4K maximizada puede ampliarse de nuevo. Tener el archivo 4K no basta para garantizar nitidez al mostrarlo.

**Propuesta:** solicitar la resolución necesaria según la superficie y la densidad de píxeles, con límite razonable.
Mantener miniaturas ajustadas a su uso. Revisar también la resolución de las portadas de juegos cuando se agrandan las
tarjetas. La prueba de nitidez debe mirar la imagen mostrada al 100 %, además de las dimensiones del archivo.

### V06 · P1 · El primer contacto del USB invita a instalar antes de explicar la prueba

Ubicación: autoinicio del instalador y primera pantalla de Instalador.qml.

La pantalla abre con «Instalar Antu» y una lista de discos. Es correcto para instalar, pero no comunica de inmediato
que se puede probar el sistema en vivo. La confusión apareció en esta propia sesión. Cerrar una ventana es una salida
poco evidente para descubrir el modo de prueba.

**Propuesta:** bienvenida del USB con «Probar Antu» y «Instalar Antu», y un estado breve del registro automático.
Mantener toda la advertencia y confirmación de borrado dentro del recorrido de instalación. La confirmación actual
ya muestra modelo, capacidad, particiones y pérdida de Windows: es un punto fuerte que debe conservarse.

## Segunda tanda de mejoras

| ID / prioridad | Hallazgo y evidencia | Mejora concreta |
|---|---|---|
| V07 · P2 | Antu Salar existe, pero las apps fijan fondos oscuros y colores en sus QML. Hay 186 literales hexadecimales en los 17 archivos inspeccionados; la repetición sola no es un defecto, pero facilita divergencias | Paleta semántica compartida y decisión explícita sobre modo claro, oscuro y alto contraste. Evitar mezclar marco claro con contenido oscuro sin intención |
| V08 · P2 | La misma fotografía reaparece recortada dentro de distintas ventanas y detrás del escritorio | Reservar la escena completa para bienvenida y superficies de marca. En herramientas diarias, dar al contenido un grafito estable con vidrio controlado en cabeceras y bordes. Mostrar una opción conservadora y otra más expresiva antes de cambiarlo |
| V09 · P2 | «Funciona perfecto» procede de categorías de compatibilidad, no de una prueba en este Alienware; el detalle advierte que cada equipo es distinto, pero el titular pesa más | Expresar «Buen soporte en Linux» y diferenciar «Probado en tu equipo» de «Informes de la comunidad». Hacer visible procedencia y antigüedad del dato |
| V10 · P2 | Encendido muestra un registro y paneles decorativos generados con valores aleatorios; el propio generador lo documenta | Mantener la firma de arranque, pero separar la secuencia artística de los diagnósticos reales. Ofrecer un recorrido tranquilo con movimiento reducido; no presentar números decorativos como salud del equipo |
| V11 · P2 | Animaciones de Halo, secciones, sacudida de contraseña y Plymouth no declaran una alternativa común de movimiento reducido en las fuentes revisadas | Respetar una preferencia global y conservar foco, selección y progreso mediante transiciones discretas. No se ha medido un incumplimiento por destellos |
| V12 · P2 | Los halos repiten diez rectángulos cada uno; botones y tarjetas pueden incluir más de un halo, y las portadas tienen una máscara por efecto | Medir fluidez y consumo con GPU real, caché caliente y fría y una biblioteca grande. Reutilizar/cachar efectos cuando ayude. Mantener el material si entra en presupuesto; no declarar que ya cuesta FPS sin medir |
| V13 · P2 | `kdeglobals.base` todavía declara `Theme=breeze-dark`, mientras ambos paquetes globales declaran `Theme=Antu` | Dejar una autoridad inequívoca para los valores iniciales y comprobar perfiles nuevos y existentes. Las capturas sí muestran iconos de Antu: no es evidencia de que el tema siempre falle |
| V14 · P2 | La tabla de Observatorio ofrece alternativa al gráfico, y hay focos y nombres accesibles en numerosos controles; falta probar el recorrido completo con tecnologías de asistencia y mando | Recorrer entrada, selección, detalle, retorno y errores con teclado, lector de pantalla y mando. Confirmar nombres/estados y anuncio de errores. No inferir ausencia de accesibilidad por no encontrar ARIA en QML |
| V15 · P2 | Las capturas por software muestran una ruta distinta de la acelerada; Portada.qml desactiva deliberadamente la máscara en software | Mantener referencias visuales por software y por GPU, comparar esquinas, sombras y transparencias, y añadir estados vacío, carga, error, selección y foco. Los sensores ausentes de la VM no son fallos de diseño del portátil |
| V16 · P3 | PRODUCT.md y la superficie de Impeccable describen etapas antiguas: primer arranque de consola y ausencia de instalador/Steam/firma, que ya existen en el código | Actualizar el contexto antes del próximo trabajo de diseño y documentar un sistema de diseño vigente. No se ha reparado como efecto lateral de esta auditoría |

Eclipse usa Steam Big Picture y Gamescope. La vuelta está contemplada en el código, pero no hay aquí una captura de
un juego real en Eclipse. Su acabado con mando, errores de entrada, salida y superposición de rendimiento queda pendiente.
Conviene resolver esa prueba antes de diseñar una consola propia alrededor de una experiencia aún no validada.

## Qué conviene conservar

- **Identidad del norte de Chile:** Paranal funciona como firma reconocible y tiene una versión de producción de buena
  resolución. El símbolo es sencillo y legible; no necesita competir con otro emblema.
- **Material original:** conservar obsidiana, plata anodizada y lava. Subir la luz que dibuja la forma y moderar los
  reflejos cuando perjudiquen la silueta. Una buena superficie 3D también debe funcionar a 16 px.
- **Cursores:** contorno claro, siluetas simples y acento contenido. La hoja de 24/32 px demuestra una mejor prioridad
  de lectura; falta la comprobación real de hotspots, escalado y juegos en Linux.
- **Paletas KDE:** 111 de las 112 parejas nominales de primer plano/fondo normal inspeccionadas alcanzan 4,5:1.
  La excepción es ForegroundActive de Header en Antu Salar, aproximadamente 4,35:1. Esto no certifica transparencias,
  controles completos ni todos los estados. La base de color es sólida y no necesita rehacerse entera.
- **Controles nativos:** AbstractButton, Button, TextField, ComboBox, GridView con navegación, nombres accesibles y focos
  visibles ya aportan una base útil. El estilo debe ampliarla sin romperla.
- **Explicaciones en español y estados sin datos:** hay avisos claros de compatibilidad, equipo sin sensores e informes
  insuficientes. Mantener esa honestidad y mejorar su visibilidad.

## Orden recomendado y criterios de aceptación

1. **Lectura y nitidez:** V01, V02, V03 y V05. Carpetas identificables en lista/Lugares; etiquetas de controles pequeñas
   con 4,5:1 y gráficos necesarios con 3:1; texto importante legible al reducir la ventana; fondos sin ampliación
   innecesaria desde 1920 en 4K. Documentar cada tamaño y estado comprobado.
2. **Continuidad:** V04, V07, V08 y V13. Aprobar una comparación de Dolphin, Ajustes, notificación y una app propia con
   los mismos controles, márgenes, luz y tipografía. La primera prueba visual puede usar Biblioteca como referencia.
3. **Recorrido completo:** V06, V09, V10, V11 y V14. Desde el USB se entiende cómo probar; la instalación informa de
   pérdidas; el juego abre y vuelve con claridad; los errores se recuperan; no es necesario usar la terminal.
4. **Comprobación final:** V12 y V15. Capturas de GPU real a 100/125/150/200 %, dos proporciones de pantalla, tema oscuro,
   claro/alto contraste según el soporte elegido y navegación con teclado. Probar una biblioteca grande y un juego real.
   A 240 Hz, un cuadro dura unos 4,17 ms: es una referencia de presupuesto, no un resultado obtenido por Antu.

La aspiración de liderar requiere comprobar estos resultados con personas que vengan de Windows y con uso real en
el portátil. La prioridad es una experiencia consistente, clara y fiable en todas las ventanas que se utilizan cada día.

## Método y límites de las mediciones

Para cada PNG se compuso el alfa sobre los tres fondos y se calculó luminancia sRGB. El borde se obtuvo como máscara
alfa≥0,5 menos una erosión de 3×3; se publican su percentil 90, porcentaje que alcanza 3:1 y percentil 90 de todo lo visible.
Es una ayuda de inspección reproducible, **no** el algoritmo normativo de WCAG ni una máscara semántica manual de cada
objeto. Sombras, huecos y detalles requieren revisión humana. Los PNG originales no se modificaron.

Los colores de botones y paletas se midieron numéricamente. Las fuentes y tabulación se observaron sobre las copias
temporales de QML; esa tabulación parcial no equivale a completar todos los recorridos. No se midió rendimiento,
consumo, HDR, brillo de pantalla, lector de pantalla de Linux ni Gamescope físico. No se propone un ranking de FPS.

Se utilizaron las guías Impeccable y Refactoring UI. El contexto automático de Impeccable no reconoce `linux-desktop`
y lo interpreta como web; se corrigió esa interpretación en el método de auditoría, no en los archivos de producto.
No se trasladaron criterios de navegador, ARIA o iPhone a KDE. Su detector web no es una prueba válida de estos QML.
La herramienta informa de una actualización opcional 4.8.0 y de falta de un modo de construcción registrado. No se
actualizó la herramienta ni se eligió un nuevo modo de diseño durante esta auditoría.

No se cambiaron interfaces, arte instalado, configuración del equipo ni el USB. Las correcciones de funcionamiento
de la sesión anterior se conservan. Sin commit ni push.

## Referencias

- [W3C: contraste de texto](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html): 4,5:1 para texto normal y
  3:1 para texto grande, con las excepciones que establece el criterio.
- [W3C: contraste de componentes y gráficos](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html): 3:1
  para las partes necesarias y los estados visuales pertinentes; no exige un borde en todos los controles.
- [Qt: accesibilidad en Qt Quick](https://doc.qt.io/qt-6/accessible-qtquick.html): controles estándar con funciones
  incorporadas y metadatos adicionales cuando la función necesita aclararse.
