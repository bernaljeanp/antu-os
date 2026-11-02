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

> **Estado: Hito 0, prueba de concepto.** Arranca con KDE Plasma y la identidad Antu, pero todavía no trae Steam
> ni instalador gráfico. No la uses aún como sistema principal.

## Probar en una VM (5 minutos, desde Windows)

1. En este repositorio: *Actions → disco-vm → Run workflow*. Al terminar, descarga el artefacto `antu-nvidia-vmdk`.
2. En VMware Workstation: nueva VM personalizada → Linux 6.x 64-bit → usar disco existente → `antu-nvidia.vmdk`.
3. Antes de arrancarla, en *VM → Settings → Options → Advanced* elige firmware **UEFI** y desactiva Secure Boot.
4. Arranca y crea tu usuario (ver [Primer arranque](#primer-arranque)).

`disco-vm` usa la última imagen publicada en `ghcr.io/bernaljeanp/antu-nvidia`.

## Instalar en un PC (SSD o USB externo, sin tocar tu disco)

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

`systemd-homed` pide crear el primer usuario en la consola (nombre y contraseña) antes de que aparezca SDDM.
El teclado de la consola es inglés (US) por ahora.

Ese usuario es administrador (grupo `wheel`). La cuenta root está bloqueada: para tareas de sistema se usa
`run0`, el reemplazo de `sudo` de systemd:

```bash
run0 bootc upgrade     # descargar la imagen nueva; se aplica al reiniciar
run0 bootc rollback    # volver a la versión anterior
```

## Cómo está hecha

```
Containerfile                 la imagen: Arch + bootc + NVIDIA + KDE + identidad Antu
files/system/                 archivos que se copian tal cual a la raíz de la imagen
files/scripts/                scripts que corren al compilar
scripts/install-to-disk.sh    instala en un disco externo o en un .img
scripts/check_colors.py       contraste WCAG de los esquemas de color
.github/workflows/build.yml   compila, arranca la imagen en una VM y la publica en ghcr.io
.github/workflows/disk.yml    genera el disco VMware de prueba
third_party/                  licencias de terceros
```

En cada push y cada día, GitHub Actions compila la imagen y la arranca en una VM con
[bcvk](https://github.com/bootc-dev/bcvk). La prueba falla si hay unidades de systemd con error, si NetworkManager
o SDDM no están activos, si falta el módulo `nvidia`, si el tema Antu no está configurado, si alguna cuenta no tiene
contraseña o si root no está bloqueado. Solo si pasa se publica `antu-nvidia:latest` y una etiqueta con la fecha.

La imagen de prueba activa SSH y desactiva el asistente de primer arranque, que esperaría en la consola;
la publicada no tiene ninguno de los dos cambios.

## Hoja de ruta

| Hito | Contenido |
|---|---|
| **0** | Arch + bootc + NVIDIA + KDE + identidad, con prueba de arranque automática *(en curso)* |
| **0b** | Usuario de primer arranque e instalación en disco o VM *(en curso)* |
| **1** | Capa de juegos (Steam, Gamescope, modo Eclipse), instalador gráfico, Secure Boot y firma de imágenes, canales `testing` / `stable` |
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
- La licencia del proyecto se definirá antes de aceptar contribuciones de código.

## Límites conocidos

- La prueba en VM no tiene GPU: comprueba que el módulo NVIDIA existe, no que funcione en una RTX real.
- La imagen base está fijada por digest, pero los paquetes de Arch se toman del día; faltan canales
  `testing` / `stable` con fecha fija de repositorios.
- Sin firma de imágenes ni Secure Boot todavía.
- La interfaz «macOS gamer» (vidrio de obsidiana, acento de lava, Inter) está en construcción: ya hay pantalla de
  arranque e inicio de sesión; faltan la barra superior y el dock, el símbolo de Antu y un fondo propio (el actual
  es provisional). Cada compilación sube capturas del inicio de sesión y del arranque (artefacto `capturas`).

## Licencias y terceros

- **Por decidir:** licencia del repositorio y de los fondos (los metadatos proponen GPL-3.0 y CC-BY-SA-4.0).
- Fuentes Inter (The Inter Project Authors) y JetBrains Mono: SIL OFL, licencias en `files/system/usr/share/fonts/antu/`.
- Los esquemas de color salen de `scripts/make_colors.py`, la marca y los recursos del arranque de `scripts/make_brand.py`
  y los fondos de `scripts/make_wallpapers.py`.
- La parte bootc del `Containerfile` está adaptada de [bootcrew/mono](https://github.com/bootcrew/mono)
  (Apache-2.0, Copyright 2025 tulilirockz). Licencia en `third_party/bootcrew-LICENSE`.
