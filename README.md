<p align="center">
  <img src="brand/symbol-white.png" width="96" alt="Antu">
</p>

<h1 align="center">Antu OS</h1>

<p align="center"><b>Desde los cielos más claros de la Tierra.</b><br>
Distro gamer chilena: Arch atómico para portátiles gamer con NVIDIA.</p>

---

Antu significa *sol* en mapudungun, y es también el nombre de uno de los telescopios VLT de Paranal.

**Estado: Hito 0 (prueba de concepto).** Arch Linux atómico con [bootc](https://github.com/bootc-dev/bootc),
NVIDIA open y KDE Plasma, con la identidad Antu. Todavía no hay instalador gráfico: se instala con un script.

## Por qué así

- **Arch:** drivers y kernel más recientes; `nvidia-open` viene compilado para el kernel, sin compilar en el equipo.
- **Atómico con bootc:** el sistema es una imagen de contenedor. Se actualiza entero o no se actualiza, y si algo
  falla se vuelve a la versión anterior desde el menú de arranque. Las actualizaciones bajan solo las capas que cambian.
- **NVIDIA primero:** SteamOS no soporta NVIDIA; Antu sí.

## Estructura

```
Containerfile                 la imagen: Arch + bootc + NVIDIA + KDE + identidad Antu
files/system/                 archivos que se copian tal cual a la raíz de la imagen
files/scripts/                scripts que corren al compilar
.github/workflows/build.yml   compila, arranca la imagen en una VM y la publica en ghcr.io
scripts/check_colors.py       contraste WCAG de los esquemas de color
third_party/                  licencias de terceros
```

## Cómo se prueba cada imagen

En cada push y cada día, GitHub Actions:

1. Compila la imagen (bootc se compila desde la versión fijada en `BOOTC_VERSION`).
2. La arranca en una VM con [bcvk](https://github.com/bootc-dev/bcvk) y comprueba: ninguna unidad de systemd con
   fallo, NetworkManager y SDDM activos, módulo `nvidia` presente para el kernel, tema Antu configurado, bootc funcional.
3. Solo si pasa, publica `ghcr.io/<dueño>/antu-nvidia:latest` y una etiqueta con la fecha (para volver atrás).

La imagen de prueba activa SSH y desactiva el asistente de primer arranque (esperaría en la consola);
la publicada no tiene ninguno de los dos cambios.

## Primer arranque

`systemd-homed` pide crear el primer usuario en la consola (nombre y contraseña) antes de que aparezca SDDM.
El teclado de la consola es inglés (US) por ahora.

Ese usuario es administrador (grupo `wheel`). La cuenta root está bloqueada: para tareas de sistema se usa
`run0`, el reemplazo de `sudo` de systemd, por ejemplo `run0 bootc upgrade`.

## Probar en una VM desde Windows (VMware)

1. En GitHub: *Actions → disco-vm → Run workflow*. Al terminar, descarga el artefacto `antu-nvidia-vmdk`.
2. En VMware Workstation: nueva VM personalizada → Linux 6.x 64-bit → usar disco existente → `antu-nvidia.vmdk`.
3. Antes de arrancarla, en *VM → Settings → Options → Advanced* elige firmware **UEFI** y desactiva Secure Boot.

## Probar en el Alienware (SSD o USB externo, sin tocar Windows)

1. Desactiva **Secure Boot** en la BIOS (F2). Las imágenes aún no están firmadas.
2. Crea un USB de Fedora Workstation (por ejemplo con USBoot) y arranca en modo en vivo (F12).
3. Conecta el SSD externo, abre una terminal y ejecuta:
   ```bash
   curl -LO https://raw.githubusercontent.com/bernaljeanp/antu-os/main/scripts/install-to-disk.sh
   lsblk
   sudo bash install-to-disk.sh /dev/sdX
   ```
   `/dev/sdX` es el SSD externo: **se borra entero**. El script se niega a usar discos montados o el disco del
   sistema en ejecución, y pide escribir el nombre del disco para confirmar.
4. Arranca desde el SSD externo con F12.

## Publicar

1. Crea el repositorio en GitHub (recomendado: organización `antuos`, repositorio `antu-os`) y sube este código.
2. Espera a que termine el workflow `antu`.
3. Haz público el paquete en *Packages → antu-nvidia → Package settings*.

## Criterios del Hito 0

| | Criterio | Cómo se comprueba |
|---|---|---|
| 1 | La imagen se compila | Workflow en GitHub |
| 2 | Arranca hasta SDDM | Prueba de arranque en VM del workflow |
| 3 | `bootc upgrade` pasa a una imagen nueva y `bootc rollback` vuelve | En una VM, con dos imágenes publicadas |
| 4 | Arranca en el Alienware desde un SSD externo y la RTX 5070 funciona | Manual, con `scripts/install-to-disk.sh` |

Si el criterio 3 falla con bootc, el plan B es systemd-sysupdate (el modelo de KDE Linux).

## Comprobar

```bash
python scripts/check_colors.py   # contraste WCAG >= 4.5:1 en ambos esquemas
```

## Hoja de ruta

| Hito | Contenido |
|---|---|
| **0** | Arch + bootc + NVIDIA + KDE + identidad, con prueba de arranque automática (en curso) |
| **0b** | Usuario de primer arranque (systemd-homed) e instalación en disco o VM (en curso) |
| **1** | Instalador, Secure Boot, capa de juegos (Steam, Gamescope, multilib), canales `testing` / `stable`, firma de imágenes |
| **1** | Zenit en Linux (perfiles térmicos, AlienFX, teclas Fn, límite de carga) y USBoot como instalador |
| **2** | Inicio (primer arranque en español), Biblioteca (compatibilidad antes de instalar), modo Familia |
| **3** | Asistente local y opcional que explica en español por qué falla un juego |

## Límites conocidos

- **No compilado todavía:** la primera compilación será la del primer push. Revisa el run de Actions.
- La prueba en VM no tiene GPU: comprueba que el módulo NVIDIA existe, no que funcione en una RTX real.
- SDDM sin GPU en la VM podría fallar y marcar la prueba en rojo aunque el sistema esté bien; se ajustará con el primer run.
- La imagen sigue `archlinux:latest`: falta fijar fecha de repositorios y canales `testing` / `stable` (Hito 1).
- Sin firma de imágenes ni Secure Boot todavía.
- Los fondos miden 1672×941; Breeze no permite los radios de esquina del diseño.
- **Licencias por decidir:** repositorio y fondos (los metadatos dicen GPL-3.0 y CC-BY-SA-4.0 como propuesta).
  Las fuentes son OFL (licencias incluidas).

## Terceros

La parte bootc del `Containerfile` está adaptada de [bootcrew/mono](https://github.com/bootcrew/mono)
(Apache-2.0, Copyright 2025 tulilirockz). Licencia en `third_party/bootcrew-LICENSE`.
