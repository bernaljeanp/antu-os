---
version: 1
slug: "and-feel-org-antuos-desktop-metadata-json-7d9a51b4"
primary_target: "files/system/usr/share/plasma/look-and-feel/org.antuos.desktop/metadata.json"
related_targets: []
---

# Superficie: encender hasta escritorio

Modo: Operate. Recorrido de los primeros dos minutos: arranque (Plymouth), inicio de sesión (SDDM), primer
arranque (creación de usuario) y escritorio con su panel (KDE Plasma 6.8).

Audiencia y tarea: gamer con portátil NVIDIA que viene de Windows; quiere saber dónde está y llegar a jugar sin
aprender Linux. Debe ser propio pero intuitivo; rechazos explícitos: parecer KDE con otro tema, folclore de postal.

Restricciones: todo por mecanismos de KDE/Qt/SDDM/Plymouth, instalado en /usr; ningún efecto que cueste frames;
controles estándar de la plataforma. Inspirado en la señalética del Metro de Santiago sin copiar su marca:
colores de línea propios, sin pictogramas ni logotipo del Metro.

Momento memorable: el arranque avanza como un tren de estación en estación y deja al usuario en su andén.

Sin resolver: pantalla gráfica de primer arranque (hoy es consola de systemd-homed); modo juego Eclipse.

## Direction contract

THESIS: Antu como red de metro: cada espacio es una línea con color y número, cada app una estación. Rechaza el
escritorio gamer negro con neón y el Breeze por defecto recoloreado.

OWN-WORLD: placas esmaltadas de color pleno. Líneas: Jugar rojo esmalte #C8281E, Trabajar mostaza #E9A800, Familia
verde #138A4B, Sistema azul #1450A0. Noche «Túnel» por defecto (grafito #141517, superficies #1E2023, tinta
#F2F1EC); día «Andén» (esmalte #F7F6F2, tinta #1C1C1B). Archivo (Omnibus-Type) en ancho semiexpandido para
nombres de estación, normal para interfaz; numerales tabulares; JetBrains Mono solo en terminal. Firma: el trazo
grueso de línea con estaciones como círculos.

STORY: en segundos sabe en qué línea está, confía en que el sistema lo lleva y entra a jugar.

FIRST VIEWPORT: login SDDM como andén: arriba, la línea de arranque con sus estaciones ya recorridas; al centro,
placa de usuario con círculo de línea e inicial y campo de contraseña estándar; arriba a la derecha, hora en
numerales grandes; abajo, apagar, reiniciar y teclado. Escritorio: panel inferior como línea de recorrido con las
apps como estaciones y el espacio actual como círculo numerado.

FORM: señalética del Metro de Santiago, posición 1 de la lista ordenada (elección de Impeccable), semilla 533d93b9.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
