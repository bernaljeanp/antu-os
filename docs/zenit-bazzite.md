# Zenit en Bazzite

Antu ya incluye el port Linux de Zenit. Este instalador permite usarlo de forma independiente en Bazzite (KDE/Wayland, x86_64), sin instalar Antu OS, sin cambiar `/usr` y sin superponer paquetes con rpm-ostree.

## Instalar desde este checkout

Requiere Python 3 con `venv`/pip, Internet para descargar PyQt6, systemd y una cuenta administradora del grupo `wheel` con sudo. Ejecuta en el sistema anfitrión, **fuera de Distrobox/Toolbox**, como tu usuario habitual:

```bash
bash scripts/install-zenit-bazzite.sh
```

La interfaz y Qt se instalan en `${XDG_DATA_HOME:-~/.local/share}/zenit`. Se añaden entradas al menú y al inicio de sesión. El instalador pide sudo para copiar el motor a `/var/opt/zenit/zenit.py` (propiedad de root), crear `/etc/systemd/system/zenit.service` y arrancarlo. El estado queda en `/var/lib/zenit`. Solo root y el grupo wheel acceden al socket. No ejecuta como root código desde la carpeta del usuario.

Abre **Zenit** desde el menú. Con las rutas por defecto:

```bash
~/.local/share/zenit/zenit-cli estado
~/.local/share/zenit/zenit-cli perfil auto
journalctl -u zenit -b
```

`--sin-servicio` instala únicamente la interfaz y CLI para probarlas; no prepara control de hardware. La interfaz acepta `--demo` para mostrar datos ficticios claramente indicados. Repetir el instalador actualiza las copias sin borrar las preferencias del motor. No sobrescribe un servicio incluido por la distribución.

## Alienware / Dell

Objetivo solicitado: Alienware descrito como «X16 Aurora R6, RTX 5070, i9». El modelo DMI exacto y la versión del kernel deben comprobarse en el equipo; no se da por equivalente al AC16251 de referencia de Antu.

El motor detecta `alienware-wmi`, perfiles de plataforma (interfaz nueva y ACPI), `hwmon`, límites de batería y Dell WMI sysman. AlienFX usa HID cuando reconoce el controlador. La presencia de una RTX 5070 no garantiza soporte de estas interfaces. No instala módulos de terceros ni controladores de Windows. NVIDIA se consulta cuando corresponde mediante `nvidia-smi`; se evita despertar la GPU dedicada en reposo.

Antes de atribuir un fallo al programa, recoge estos datos de solo lectura:

```bash
cat /sys/class/dmi/id/product_name
uname -r
ls /sys/class/platform-profile/ /sys/class/hwmon/ /sys/class/firmware-attributes/ 2>/dev/null
systemctl status zenit --no-pager
~/.local/share/zenit/zenit-cli estado
```

Si el kernel no expone un control, la interfaz lo deshabilita. Comprueba también que el gestor de energía de Bazzite (por ejemplo tuned o power-profiles-daemon) no esté cambiando el perfil a la vez: Zenit tiene su propia política automática. El instalador no desactiva esos servicios ni modifica tu configuración energética.

## Validación y límites

Se han ejecutado las 12 pruebas de `ci/zenit-test.py`, `zenit.py autoprueba`, instalación de usuario repetida y carga de la interfaz instalada con Qt sin pantalla. No se ha instalado ni iniciado el servicio privilegiado en Bazzite ni validado luces, teclas, batería o térmicas en el Alienware físico. Esta instalación independiente es experimental hasta completar esas comprobaciones.

```bash
python3 ci/zenit-test.py
python3 files/system/usr/lib/antu/zenit/zenit.py autoprueba
# Con PyQt6 instalado:
python3 ci/zenit-ui-test.py
```

## Desinstalar (rutas por defecto)

```bash
sudo systemctl disable --now zenit.service
sudo rm /etc/systemd/system/zenit.service
sudo systemctl daemon-reload
sudo rm /var/opt/zenit/zenit.py
sudo rmdir /var/opt/zenit
rm ~/.local/share/applications/zenit.desktop ~/.config/autostart/zenit.desktop
rm -r ~/.local/share/zenit
```

Si usaste XDG_DATA_HOME o XDG_CONFIG_HOME distintos, ajusta las tres rutas de usuario. Las preferencias de `/var/lib/zenit` se conservan. Desinstalar no revierte los valores ya escritos a la BIOS; elige los ajustes deseados de carga y perfil antes de hacerlo.
