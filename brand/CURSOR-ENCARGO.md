# Encargo: tema de cursores de Antu OS, opción «Punta»

Antu OS es una distro gamer chilena (Arch, KDE Plasma 6, NVIDIA). Hoy usa Breeze, el cursor de KDE.

**El dueño rechazó la primera entrega porque «parece del año 2000».** Tenía razón: el canto fino de plata, el bisel, los
reflejos y el interior casi transparente son la estética de los temas de hace 20 años. Ese arte se descarta entero. Lo que sí
sirve de esa entrega es la técnica: el escritor y el lector de Xcursor, los 115 nombres, los puntos activos y el validador
de `scripts/make_cursors.py`. Reutiliza eso y rehaz todo el dibujo.

El dueño aprobó esta maqueta: `brand/previews/cursors/maqueta-moderna.png`, **opción 2, «Punta»**. Su código está en
`brand/previews/cursors/maqueta-moderna.py`, y sus funciones `punta`, `filo`, `obsidiana_con_filo` y `sombra_de` son la referencia
exacta del estilo. Míralas antes de empezar. Tu trabajo es llevar esa imagen a un tema completo y mejor resuelto, no reinterpretarla.

## Estilo

Actual, como un cursor de 2026: silueta **redonda y sólida**, **contorno blanco firme**, sombra suave y **una sola nota de lava**.

Valores de la maqueta, en una rejilla de 32 unidades (a 24 px cada unidad mide 0,75 px):

- **Flecha:** punta sin cola. Vértices `(4,6; 3,6)`, `(11,2; 28,6)`, `(15,2; 18,6)`, `(27,2; 13,4)`, con esquinas muy redondeadas.
- **Cuerpo:** un solo color plano, `#111115`. Sin degradados, sin brillos y sin transparencia.
- **Contorno:** blanco puro `#FFFFFF`, de unas 1,75 unidades, uniforme y bien redondeado. No gris ni plata, y nunca fino.
- **Sombra:** negra, suave, 1,3 unidades hacia abajo, desenfoque de 2,1 y opacidad de 0,5.
- **Filo de lava:** una grieta por el borde izquierdo, por dentro del contorno. Nace fina en la punta, engorda al centro y se
  apaga al final, con un resplandor suave hacia el interior. Color de `#FF963C` arriba a `#FF5A1F` abajo.

**Prohibido:** plata, metal, bisel, relieve, reflejos, luz especular, contornos dobles, cuerpo translúcido, o render 3D. Si una
forma se ve «técnica» o de líneas finas, está mal. Tampoco calques Breeze, macOS, Windows, Figma ni otro tema.

## Toda la familia, con el mismo lenguaje

Todas las formas son siluetas gruesas, redondas y sólidas, con el mismo contorno y la misma sombra. Tienen que verse hermanas de
la flecha. Son lo que peor quedó en la maqueta y lo que más cuidado necesita:

- **Manos** (enlace, abierta, cerrada): gorditas, simples y amables, con los dedos bien legibles. Sin arrugas ni líneas interiores.
- **Texto:** barra gruesa y redondeada, no un marco de líneas. Debe verse sobre gris.
- **Flechas de borde y de doble sentido:** gordas, con puntas redondas y cuerpo sólido, no flechas de alambre.
- **Cruz de precisión y celda:** trazo grueso con contorno.
- **Prohibido, ayuda, copiar, enlace, menú, acercar, alejar, lápiz, cuentagotas:** sin detalles pequeños; lo que no se lee a 24 px
  se quita. Las que combinan la flecha con un símbolo usan la misma punta.
- **El filo de lava:** una grieta por el borde izquierdo o superior, en proporción a la forma. Donde la forma es demasiado fina para
  llevarla bien, usa un acento de lava mínimo o déjala sin lava. Nunca sacrifiques la lectura.
- **Espera:** aro grueso de obsidiana con contorno blanco, y un tramo de lava que gira. `progress` es la punta con ese aro pequeño al
  lado. Entre 24 y 36 cuadros, a unos 30 ms, en un bucle sin salto. Solo giran estos dos.

## Entrega

Tema instalable en `files/system/usr/share/icons/Antu-Cursores/`, reemplazando lo anterior:

- `cursors/`, `index.theme` (`Name=Antu Cursores`, `Inherits=breeze_cursors`), `COPYING` (CC-BY-SA-4.0) y `alias.tsv`, una línea por alias
  (`alias<TAB>original`). **No crees enlaces simbólicos**: yo los creo al compilar, porque el repositorio se edita en Windows.
- **Tamaños:** 24, 32, 36, 48, 64, 72 y 96 dentro de cada archivo. Cada tamaño se dibuja por separado desde la geometría. Ajusta a mano 24 y
  32 px, que son los más usados: bordes nítidos alineados al píxel, contorno de al menos 1,3 px a 24 px, y un filo que se siga viendo
  como lava sin manchar. La silueta de la flecha debe ocupar unos 20 px de alto a 24 px: no la achiques.
- **Puntos activos exactos:** la punta visible de la flecha cae en su píxel. Centro de cruz, texto y aro, también.
- **Nombres:** todos los de Breeze, sin que falte ninguno, como en la entrega anterior.
- **Sin Blender:** dibújalo en 2D con Python y Pillow, con supermuestreo, desde `scripts/make_cursors.py`. Quita de ese archivo el código de
  Blender, los materiales y lo que ya no se use. Borra lo obsoleto de `brand/masters/cursors/`.
- Comentarios y documentos en español, con el estilo del repositorio.

## Comprobación obligatoria

`python scripts/make_cursors.py --validar` debe fallar si algo está mal. Conserva lo que ya comprobaba: formato, tamaños, cuadros, puntos
activos, alfa premultiplicado, alias y nombres de Breeze. Agrega esto, que la entrega anterior no cumplía:

- **Contraste medido** sobre negro, gris de valor 128 y blanco, para cada forma a 24 y 32 px: cuenta los píxeles con contraste de al menos
  3:1 contra ese fondo. Ninguna forma puede quedar invisible sobre gris. En la entrega anterior, `text` tenía 1 píxel y `crosshair` 3, y eso
  es justo lo que hay que corregir. Define un mínimo, documéntalo y haz que falle si no se cumple. Publica los números en
  `brand/cursor-validation.json`.

## Vistas para revisar

En `brand/previews/cursors/`, regeneradas:

- Una hoja con todas las formas a 24, 32, 48 y 96 px, a tamaño real, sobre negro, blanco, gris 128 y `Paranal`.
- Una ampliación ×8 de la flecha a 24 y 32 px con el punto activo marcado.
- Un GIF de `wait` y `progress`.
- **Una imagen de comparación:** tu flecha, mano y texto al lado de la maqueta, para comprobar que no te alejaste de lo aprobado.

Míralas de verdad antes de darlo por terminado. **La prueba es simple: si alguien dice «esto parece de hace 20 años», falló.**
Actualiza `brand/CURSOR-THEME.md` con las decisiones nuevas y cómo regenerarlo.

## Límites

- Toca solo: `files/system/usr/share/icons/Antu-Cursores/`, `scripts/make_cursors.py`, `brand/masters/cursors/`, `brand/previews/cursors/`,
  `brand/CURSOR-THEME.md` y `brand/cursor-validation.json`.
- **No hagas commit ni push.** No cambies la configuración del sistema ni actives el tema. Hay otros trabajos subiéndose al mismo repositorio.
- Si algo no se puede cumplir, dilo claramente en `brand/CURSOR-THEME.md`; no lo escondas.
