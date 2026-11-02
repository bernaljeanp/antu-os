<p align="center">
  <img src="brand/antu-icon-256.png" width="112" alt="Símbolo de Antu: una A con forma de cumbre y un sol de lava">
</p>

<h1 align="center">Antu OS</h1>

<p align="center"><b>Desde los cielos más claros de la Tierra.</b><br>
Distro gamer chilena: Arch atómico para portátiles gamer con NVIDIA.</p>

---

Antu significa *sol* en mapudungun, y es también el nombre de uno de los telescopios VLT de Paranal.

- **NVIDIA primero:** SteamOS no soporta NVIDIA; Antu sí, con `nvidia-open` compilado para el kernel de la imagen.
- **Atómica:** el sistema es una imagen ([bootc](https://github.com/bootc-dev/bootc)). Se actualiza entero o no se
  actualiza, y si algo falla vuelves a la versión anterior desde el menú de arranque.
- **Arch:** kernel y drivers recientes para hardware nuevo; las actualizaciones bajan solo las capas que cambian.

> **Estado: prueba de concepto.** Arranca con KDE Plasma y la interfaz «macOS gamer» de Antu, y trae Steam, el modo
> juego Eclipse, Brave, Discover, un USB en vivo con instalador gráfico e Inicio para el primer arranque. Aún no se ha
> probado en hardware real: no la uses todavía como sistema principal.

## Jugar

- **Steam** viene instalado, con las librerías de 32 bits y el controlador NVIDIA de la misma versión.
- **Modo Eclipse:** en el inicio de sesión, elige la sesión *Antu Eclipse* (arriba a la derecha) para entrar
  directo a Steam en su interfaz para mando, a pantalla completa y sin el escritorio. Al salir de Big Picture
  vuelves al inicio de sesión.
- **GameMode** y **MangoHud** están disponibles: en las opciones de lanzamiento de un juego de Steam, escribe
  `gamemoderun mangohud %command%`.
- **Portátiles híbridos (Intel + NVIDIA):** `prime-run %command%` lanza el juego en la gráfica NVIDIA, que se
  apaga sola cuando no se usa (RTD3) para cuidar la batería. Dynamic Boost (`nvidia-powerd`) arranca solo si hay
  NVIDIA. El cambio automático Advanced Optimus de algunos portátiles no existe en Linux: el modo MUX se fija en
  la BIOS.
- **NVIDIA:** DLSS (incluida la generación de fotogramas), Reflex y ray tracing en Proton; G-Sync/VRR y HDR en
  Plasma con Wayland. La suspensión guarda la memoria de la GPU en disco para despertar sin errores.
- **Zenit** (portátiles Alienware y Dell), la app de control del equipo, siempre junto al reloj: temperaturas del
  procesador y la gráfica, ventiladores, perfil térmico (automático: Equilibrado+ con cargador, Equilibrado con batería
  y Rendimiento al abrir un juego), un perfil para cada juego, color y brillo de las luces del teclado, límite de carga
  de la batería. Las teclas F6 (Performance Boost), F7 (Sigilo) y F9 (luces) funcionan sin
  Alienware Command Center. Es el mismo Zenit Engine de Windows sobre las interfaces del kernel; falta probarlo en
  hardware real.
- **Más juegos:** Heroic (Epic, GOG, Amazon), Lutris y Bottles (otras tiendas y programas de Windows), ProtonPlus
  (versiones extra de Proton), Discord y Sober (Roblox, no oficial). Se instalan solas en el primer arranque.
- **Navegador:** Brave, desde Flathub. Se instala solo en el primer arranque con internet y se actualiza aparte
  del sistema.
- **Oficina:** WordCraft (documentos), DeckCraft (presentaciones), GridCraft (hojas de cálculo) y PdfCraft (PDF),
  apps de código abierto de [ArtCraft](https://getartcraft.com/apps). Se instalan solas como Flatpak en el primer
  arranque con internet. Están en desarrollo o alfa, y su repositorio aún no firma los paquetes (vista previa):
  por eso van aisladas como Flatpak y no dentro del sistema base.
- **Básicos:** VLC, Mission Center (administrador de tareas), OBS Studio y EasyEffects (sonido: reemplaza el
  ajuste Dolby de Windows, que no existe en Linux), desde Flathub en el primer arranque. En la imagen: Ark (abre
  RAR, 7z y ZIP), Gwenview, Spectacle, Kate, KCalc y USBoot.
- **IA local opcional:** «Instalar IA local» en el menú (o `antu-ia`) instala Alpaca con Ollama; no viene
  preinstalada porque ocupa varios GB.
- **Programar:** con «Voy a programar» en Inicio, Antu prepara al iniciar sesión una caja de Arch (Distrobox) con
  VS Code, Git, Node, Python, Rust, Go, Claude Code y Codex, y deja VS Code y «Terminal de desarrollo» en el menú.
  Dentro de la caja se instala lo que cada proyecto necesite sin tocar el sistema base.
- **Apps:** Discover instala aplicaciones desde Flathub sin tocar el sistema base. Sin relleno: Antu no trae
  LibreOffice.
- **Primer arranque:** las apps de Flathub y ArtCraft se descargan solas (varios GB) en cuanto hay internet.

## Instalar desde un USB

1. Descarga la ISO: en este repositorio, *Actions → iso →* la última ejecución verde *→* artefacto `antu-live-iso`
   (unos 7 GB). Trae `antu-live.iso.sha256` para comprobar la descarga.
2. Grábala en un USB de 16 GB o más con [USBoot](https://github.com/bernaljeanp/usboot), o con cualquier grabador en
   modo imagen (DD). El USB se borra entero.
3. Desactiva **Secure Boot** en la BIOS: la ISO aún no está firmada.
4. Arranca desde el USB (en Alienware y Dell, con F12). Antu arranca en vivo, sin tocar el disco, y abre
   **Instalar Antu**. Si la pantalla se queda negra, elige en el menú de arranque *modo seguro: sin NVIDIA*.
5. Elige el disco, confirma el borrado y espera entre 5 y 20 minutos. No hace falta internet: la imagen viaja en el USB.
6. Reinicia y quita el USB. Inicio te pide idioma, zona horaria y tu cuenta (ver [Primer arranque](#primer-arranque)).

El instalador ocupa el disco entero. Para conservar Windows, instala Antu en otro disco: la instalación junto a Windows
en el mismo disco aún no existe.

Cada ISO se prueba sola en una VM antes de publicarse: arranca en vivo, se instala en un disco virtual vacío y ese
disco arranca hasta Inicio. Las capturas quedan en el artefacto `pruebas-iso`.

## Probar en una VM (desde Windows)

- **Con la ISO:** en VMware Workstation, nueva VM → Linux 6.x 64-bit, 8 GB de RAM y un disco de 64 GB. En *VM →
  Settings → Options → Advanced*, firmware **UEFI** sin Secure Boot. Arranca con `antu-live.iso` y sigue los pasos de
  arriba.
- **Con un disco ya instalado:** *Actions → disco-vm → Run workflow* y descarga el artefacto `antu-nvidia-vmdk`. En
  VMware, nueva VM personalizada → usar disco existente → `antu-nvidia.vmdk`, también con UEFI y sin Secure Boot.

Las dos usan la última versión estable de `ghcr.io/bernaljeanp/antu-nvidia`.

## Instalar desde otro Linux (SSD o USB externo)

1. Desactiva **Secure Boot** en la BIOS. Las imágenes aún no están firmadas.
2. Arranca un USB de Fedora Workstation en modo en vivo (puedes crearlo con [USBoot](https://github.com/bernaljeanp/usboot)).
3. Conecta el disco externo, abre una terminal y ejecuta:
   ```bash
   curl -LO https://raw.githubusercontent.com/bernaljeanp/antu-os/main/scripts/install-to-disk.sh
   lsblk
   sudo bash install-to-disk.sh /dev/sdX
   ```
   `/dev/sdX` es el disco externo y **se borra entero**. El script se niega a usar discos montados o el disco del
   sistema en ejecución, y pide escribir el nombre del disco para confirmar.
4. Arranca desde el disco externo (en Alienware y Dell, con F12).

Equipo de referencia: Alienware 16X Aurora (Core Ultra 9 275HX, RTX 5070 Laptop), con pruebas en curso.

## Primer arranque

**Inicio**, el asistente gráfico, aparece solo la primera vez: idioma y teclado, zona horaria, tu cuenta, el
escritorio (barra inferior centrada o barra superior y dock) y extras como la IA local, todo en una página. Al
terminar aparece el inicio de sesión con tu cuenta. Corre en una cuenta de sistema sin privilegios; las acciones de
administrador las hace un ayudante que valida cada dato y deja de funcionar en cuanto existe una cuenta.

**Actualizaciones:** Antu se actualiza solo (en la app «Actualizaciones de Antu» ves qué versión tienes, buscas una
ahora o vuelves a la anterior). Cada 6 horas busca la versión nueva, la baja en segundo plano (con la
prioridad más baja, para no molestar mientras juegas, y nunca con datos móviles) y te avisa cuando está lista. Se
aplica la próxima vez que reinicias; si algo falla, en el menú de arranque eliges la versión anterior.

Ese usuario es administrador (grupo `wheel`). La cuenta root está bloqueada; para las pocas tareas de sistema que
no tienen botón se usa `run0`, el reemplazo de `sudo` de systemd.

## Cómo está hecha

```
Containerfile                 la imagen: Arch + bootc + NVIDIA + KDE + identidad Antu
Containerfile.live            el sistema en vivo del USB: la imagen + usuario en vivo + instalador
files/system/                 archivos que se copian tal cual a la raíz de la imagen
files/live/                   lo que añade el sistema en vivo (instalador gráfico, su ayudante, autologin)
files/scripts/                scripts que corren al compilar
scripts/make-iso.sh           crea la ISO híbrida UEFI con la imagen dentro para instalar sin internet
scripts/install-to-disk.sh    instala en un disco externo o en un .img desde otro Linux
scripts/check_colors.py       contraste WCAG de los esquemas de color
ci/iso-test.sh                prueba la ISO en QEMU: en vivo, instalación y arranque del disco instalado
.github/workflows/build.yml   compila, arranca la imagen en una VM y la publica en ghcr.io
.github/workflows/iso.yml     crea y prueba la ISO después de cada imagen publicada
.github/workflows/disk.yml    genera el disco VMware de prueba
third_party/                  licencias de terceros
```

En cada push y cada día, GitHub Actions compila la imagen y la arranca en una VM con
[bcvk](https://github.com/bootc-dev/bcvk). La prueba falla si hay unidades de systemd con error, si NetworkManager
o SDDM no están activos, si falta el módulo `nvidia`, si el tema Antu no está configurado, si alguna cuenta no tiene
contraseña o si root no está bloqueado.

**Canales y firma.** La versión que pasa esa prueba se reempaqueta por paquetes (cada paquete de Arch en su capa,
con [chunkah](https://github.com/coreos/chunkah), así una actualización solo baja lo que cambió), se firma y se
publica en el canal de prueba `antu-nvidia:testing`. Después `iso.yml` crea la ISO con esa misma versión y la prueba
entera: arranque en vivo, instalación sin internet y arranque del disco instalado. Solo si pasa, la versión sube al
canal estable `antu-nvidia:stable`, el que siguen los equipos instalados. La firma es de cosign sin llaves, con la
identidad del workflow de este repositorio, y cualquiera puede comprobarla:

```bash
cosign verify ghcr.io/bernaljeanp/antu-nvidia:stable \
  --certificate-identity-regexp '^https://github.com/bernaljeanp/antu-os/' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

La imagen de prueba activa SSH y desactiva el asistente de primer arranque, que esperaría en la consola;
la publicada no tiene ninguno de los dos cambios.

## Hoja de ruta

| Hito | Contenido |
|---|---|
| **0** | Arch + bootc + NVIDIA + KDE + identidad, con prueba de arranque automática *(en curso)* |
| **0b** | Inicio (primer arranque gráfico), USB en vivo e instalador gráfico *(en curso)* |
| **1** | Capa de juegos (Steam, Gamescope, modo Eclipse), instalación junto a Windows, Secure Boot y verificación de la firma en cada equipo |
| **1** | Zenit en Linux (perfiles térmicos, AlienFX, teclas Fn, límite de carga) y USBoot como instalador oficial |
| **2** | Inicio (primer arranque en español), Biblioteca (compatibilidad antes de instalar), modo Familia |
| **3** | Asistente local y opcional que explica en español por qué falla un juego |

El Hito 0 se da por cumplido cuando: la imagen compila, arranca hasta SDDM en la VM de CI, `bootc upgrade` y
`bootc rollback` funcionan entre dos imágenes, y arranca en hardware real con la GPU NVIDIA funcionando.
Si `bootc` no cumple en Arch, el plan B es systemd-sysupdate (el modelo de KDE Linux).

## Contribuir

- Abre un *issue* con tu modelo de PC y lo que funciona o falla: los informes de hardware son lo más valioso ahora.
- Los cambios entran por *pull request* y deben pasar el workflow `antu` (compilación y prueba de arranque).
- Si tocas los colores, ejecuta `python scripts/check_colors.py` (contraste WCAG ≥ 4.5:1).
- Al contribuir aceptas que tu código se publique con la licencia del proyecto (GPL-3.0-or-later) y tu arte con
  CC-BY-SA-4.0.

## Límites conocidos

- La prueba en VM no tiene GPU: comprueba que el módulo NVIDIA existe, no que funcione en una RTX real.
- La imagen base está fijada por digest, pero los paquetes de Arch se toman del día: el canal estable es lo que
  protege a los equipos instalados de una actualización de Arch con fallas.
- Cada versión va firmada, pero los equipos instalados todavía no comprueban la firma por sí mismos antes de
  actualizar. Sin Secure Boot todavía: la ISO y el sistema instalado necesitan Secure Boot desactivado.
- El instalador usa el disco entero; instalar junto a Windows en el mismo disco aún no está disponible.
- `bootc upgrade` en un sistema instalado necesita que el paquete `ghcr.io/bernaljeanp/antu-nvidia` sea público.
- La interfaz «macOS gamer» (vidrio de obsidiana, acento de lava, Inter) ya tiene arranque animado «Amanecer», inicio de
  sesión, Inicio, instalador, íconos y tres fondos (Antu, Paranal y Salar); falta revisarla en hardware real. Cada
  compilación sube capturas (artefactos `capturas` y `pruebas-iso`).

## Licencias y terceros

- **Código de Antu** (scripts, Inicio, el instalador, temas y configuración): GNU GPL 3.0 o posterior
  (GPL-3.0-or-later), texto completo en [`LICENSE`](LICENSE).
- **Arte de Antu** (fondos, logos e íconos): [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.es).
  Puedes reutilizarlo dando crédito a Antu OS y compartiendo tus cambios con la misma licencia.
- Los programas que trae la imagen (kernel, KDE, Steam, controladores de NVIDIA, Brave, etc.) mantienen cada uno su
  propia licencia.
- Fuentes Inter (The Inter Project Authors) y JetBrains Mono: SIL OFL, licencias en `files/system/usr/share/fonts/antu/`.
- Los esquemas de color salen de `scripts/make_colors.py`, la marca y los recursos del arranque de `scripts/make_brand.py`
  y los fondos de `scripts/make_wallpapers.py`. Los íconos se renderizan en Blender (`scripts/render_art.py`) y los
  fondos se generaron con IA y superresolución 4K; el proceso y los prompts están en `brand/ART-DIRECTION.md`.
- La parte bootc del `Containerfile` está adaptada de [bootcrew/mono](https://github.com/bootcrew/mono)
  (Apache-2.0, Copyright 2025 tulilirockz). Licencia en `third_party/bootcrew-LICENSE`.
